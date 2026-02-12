"""
Execution Gateway Service.
Handles interaction with Kraken (and other exchanges) via CCXT.
"""

import asyncio
import logging
import os
import json
from typing import Dict, Any, Optional

try:
    import ccxt.pro as ccxt
except ImportError:
    import ccxt.async_support as ccxt

from backend.execution.exchange_adapter import ExchangeAdapter
from backend.schemas.orders import OrderRequest, OrderSide, OrderType

logger = logging.getLogger(__name__)

class ExecutionGateway:
    """
    Gateway for executing orders on crypto exchanges.
    Enforces safety checks (Trading Mode).
    """
    def __init__(self, exchange_id: str = "kraken"):
        from backend.core.config.settings import settings
        self.settings = settings
        self.exchange_id = exchange_id.lower()
        self.exchange = None # CCXT Instance or ExchangeAdapter
        
        self.trading_mode = settings.TRADING_MODE.lower()
        self.dry_run = self.trading_mode != "live"
        
        logger.info(f"ExecutionGateway initialized for {self.exchange_id.upper()}. Mode: {self.trading_mode.upper()}")

        # API Keys loading
        if self.exchange_id == "revolut":
            self.api_key = settings.REVOLUT_API_KEY
            self.secret = settings.REVOLUT_PRIVATE_KEY # PEM Content
        else:
            self.api_key = os.getenv(f"{self.exchange_id.upper()}_API_KEY")
            self.secret = os.getenv(f"{self.exchange_id.upper()}_SECRET_KEY")
        
        if self.trading_mode == "live" and (not self.api_key or not self.secret):
             # For Revolut, secret is Private Key
            logger.critical(f"Starting in LIVE mode but missing API Keys for {exchange_id}!")
            
    async def start(self):
        """Initialize exchange connection."""
        try:
            if self.exchange_id == "revolut":
                self.exchange = ExchangeAdapter(
                    api_key=self.api_key, 
                    private_key_pem=self.secret,
                    base_url="https://sandbox-revx.revolut.com" if self.settings.REVOLUT_SANDBOX else "https://revx.revolut.com"
                )
                if not self.dry_run:
                     if self.settings.KILL_SWITCH:
                         logger.warning("Global Kill Switch is ON!")
                     # Verify connection
                     try:
                         markets = await self.exchange.get_instruments()
                         logger.info(f"Connected to Revolut X (LIVE). Instruments found: {len(markets)}")
                     except Exception as e:
                         logger.error(f"Revolut Connection Check Failed: {e}")
                else:
                    logger.info("Revolut X (PAPER) initialized.")
                return

            # CCXT Initialization
            exchange_class = getattr(ccxt, self.exchange_id)
            
            exchange_options = {
                'apiKey': self.api_key,
                'secret': self.secret,
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'} 
            }
            
            if self.exchange_id == 'bybit' and self.settings.BYBIT_USE_EU:
                logger.info("Configuring Bybit for EU Endpoint (api.bybit.eu)")
                exchange_options['hostname'] = 'bybit.eu'
                
            self.exchange = exchange_class(exchange_options)
            
            # If live, check connection
            if not self.dry_run:
                # Double check kill switch
                if self.settings.KILL_SWITCH:
                     logger.warning("Global Kill Switch is ON during startup!")
                
                await self.exchange.load_markets()
                balance = await self.exchange.fetch_balance()
                logger.info(f"Connected to {self.exchange_id} (LIVE). Free USD: {balance.get('USD', {}).get('free', 'N/A')}")
            else:
                logger.info(f"Connected to {self.exchange_id} (PAPER/MOCK). No real connection made.")

        except Exception as e:
            logger.error(f"Failed to initialize exchange {self.exchange_id}: {e}")
            self.exchange = None

    async def stop(self):
        if self.exchange:
            if hasattr(self.exchange, 'close'): # CCXT
                await self.exchange.close()
            elif hasattr(self.exchange, 'client') and hasattr(self.exchange.client, 'aclose'): # Adapter
                await self.exchange.client.aclose()

    async def execute_order(self, symbol: str, side: str, amount: float, order_type: str = "market", price: Optional[float] = None) -> Dict[str, Any]:
        """
        Execute an order.
        If PAPER mode, returns a mock fill.
        If LIVE mode, sends to exchange.
        """
        # SECOND LINE OF DEFENSE: Kill Switch
        if self.settings.KILL_SWITCH:
            logger.critical("EXECUTION BLOCKED: GLOBAL KILL SWITCH IS ACTIVE")
            return {"status": "failed", "reason": "KILL SWITCH ACTIVE"}

        logger.info(f"Execution Request: {side.upper()} {amount} {symbol} @ {order_type} ({self.trading_mode.upper()})")
        
        if self.dry_run:
            # Mock Execution
            await asyncio.sleep(0.5) # Simulate latency
            return {
                "id": f"mock_{int(asyncio.get_event_loop().time())}",
                "symbol": symbol,
                "status": "closed",
                "filled": amount,
                "price": price or 100000.0, # Dummy price
                "info": {"msg": "This was a PAPER trade"}
            }
            
        # LIVE EXECUTION
        if not self.exchange:
            logger.error("Exchange not initialized!")
            return {"status": "failed", "reason": "Exchange not initialized"}
            
        try:
            # Map symbol if needed? CCXT usually handles 'BTC/USD'
            # For Kraken, input might need to be compliant. 
            
            # Safety check: Amount > 0
            if amount <= 0:
                 raise ValueError("Amount must be positive")
                 
            # LIVE EXECUTION
            
            # Revolut Logic
            if self.exchange_id == "revolut":
                # Convert standard params to OrderRequest
                import uuid
                # Revolut symbol usually 'BTC-USD', we might need mapping
                rev_symbol = symbol.replace("/", "-") 
                
                req = OrderRequest(
                    client_order_id=uuid.uuid4(),
                    symbol=rev_symbol,
                    side=OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL,
                    order_type=OrderType.MARKET if order_type.lower() == 'market' else OrderType.LIMIT,
                    qty=amount,
                    limit_price=price 
                )
                
                res = await self.exchange.submit_order(req)
                logger.info(f"Revolut Order Placed! ID: {res.order_id}")
                return {
                    "id": res.order_id,
                    "symbol": symbol,
                    "status": res.status.value,
                    "filled": res.filled_qty, # Might be 0 initially
                    "info": res.raw_response
                }

            # CCXT Logic
            order = await self.exchange.create_order(
                symbol=symbol,
                type=order_type,
                side=side,
                amount=amount,
                price=price
            )
            logger.info(f"Order Placed! ID: {order['id']}")
            return order
            
        except Exception as e:
            logger.error(f"Order Execution Failed: {e}")
            return {"status": "failed", "reason": str(e)}

    async def get_balance(self):
        if self.dry_run or not self.exchange:
            return {"USD": {"free": 100000.0, "total": 100000.0}, "BTC": {"free": 0.0, "total": 0.0}}
            
        if self.exchange_id == "revolut":
            # Adapter returns dict { 'USD': 100.0, 'BTC': 1.0 }
            balances = await self.exchange.get_balance()
            # Normalize to CCXT structure roughly
            normalized = {}
            for k, v in balances.items():
                normalized[k] = {"free": v, "total": v, "used": 0.0}
            return normalized
            
        return await self.exchange.fetch_balance()

# Singleton logic or Main wrapper? 
# Orchestrator will clone/import this class.

