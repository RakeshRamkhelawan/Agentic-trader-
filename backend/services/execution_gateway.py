"""
Execution Gateway Service.
Handles interaction with Kraken (and other exchanges) via CCXT.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, Optional

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

    def __init__(self, default_exchange_id: str = "kraken"):
        from backend.core.config.settings import settings

        self.settings = settings
        self.default_exchange_id = default_exchange_id.lower()

        # Registry of active exchange instances
        self.exchanges: Dict[str, Any] = {}

        self.trading_mode = settings.TRADING_MODE.lower()
        self.dry_run = self.trading_mode != "live"

        logger.info(
            f"ExecutionGateway initialized. Default: {self.default_exchange_id.upper()}. Mode: {self.trading_mode.upper()}"
        )

    async def start(self):
        """Initialize all configured exchange connections."""
        # 1. Initialize Revolut
        if self.settings.REVOLUT_API_KEY and self.settings.REVOLUT_PRIVATE_KEY:
            try:
                logger.info("Initializing Revolut X...")
                rev_exchange = ExchangeAdapter(
                    api_key=self.settings.REVOLUT_API_KEY,
                    private_key_pem=self.settings.REVOLUT_PRIVATE_KEY,
                    base_url=(
                        "https://sandbox-revx.revolut.com"
                        if self.settings.REVOLUT_SANDBOX
                        else "https://revx.revolut.com"
                    ),
                )
                if not self.dry_run:
                    # Verify connection
                    try:
                        markets = await rev_exchange.get_instruments()
                        logger.info(
                            f"Connected to Revolut X (LIVE). Instruments: {len(markets)}"
                        )
                        self.exchanges["revolut"] = rev_exchange
                    except Exception as e:
                        logger.error(f"Revolut Connection Check Failed: {e}")
                else:
                    self.exchanges["revolut"] = rev_exchange
                    logger.info("Revolut X (PAPER) initialized.")
            except Exception as e:
                logger.error(f"Failed to init Revolut: {e}")

        # 2. Initialize CCXT Exchanges (Kraken, Bybit)
        for ex_id in ["kraken", "bybit"]:
            await self._init_ccxt_exchange(ex_id)

    async def _init_ccxt_exchange(self, exchange_id: str):
        """Helper to init CCXT exchange."""
        import os

        import ccxt.async_support as ccxt

        try:
            api_key = os.getenv(f"{exchange_id.upper()}_API_KEY")
            secret = os.getenv(f"{exchange_id.upper()}_SECRET_KEY")

            # Skip if no keys and we are in LIVE mode (unless we want to fail hard? No, allow partial init)
            if not self.dry_run and (not api_key or not secret):
                logger.warning(f"Skipping {exchange_id} (LIVE): Missing API Keys")
                return

            exchange_class = getattr(ccxt, exchange_id)

            exchange_options = {
                "apiKey": api_key,
                "secret": secret,
                "enableRateLimit": True,
                "options": {"defaultType": "spot"},
            }

            if exchange_id == "bybit" and self.settings.BYBIT_USE_EU:
                logger.info("Configuring Bybit for EU Endpoint (api.bybit.eu)")
                exchange_options["hostname"] = "bybit.eu"

            exchange = exchange_class(exchange_options)

            if not self.dry_run:
                await exchange.load_markets()
                balance = await exchange.fetch_balance()
                # logger.info(f"Connected to {exchange_id} (LIVE). Free USD: {balance.get('USD', {}).get('free', 'N/A')}")
                logger.info(f"Connected to {exchange_id} (LIVE).")
                self.exchanges[exchange_id] = exchange
            else:
                self.exchanges[exchange_id] = exchange
                logger.info(f"Connected to {exchange_id} (PAPER/MOCK).")

        except Exception as e:
            logger.error(f"Failed to initialize {exchange_id}: {e}")

    async def stop(self):
        """Close all exchange connections."""
        for ex_id, exchange in self.exchanges.items():
            try:
                if hasattr(exchange, "close"):  # CCXT
                    await exchange.close()
                elif hasattr(exchange, "client") and hasattr(
                    exchange.client, "aclose"
                ):  # Adapter
                    await exchange.client.aclose()
            except Exception as e:
                logger.error(f"Error closing {ex_id}: {e}")
        self.exchanges.clear()

    async def execute_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        order_type: str = "market",
        price: Optional[float] = None,
        target_exchange: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute an order on the target exchange.
        """
        # SECOND LINE OF DEFENSE: Kill Switch
        if self.settings.KILL_SWITCH:
            logger.critical("EXECUTION BLOCKED: GLOBAL KILL SWITCH IS ACTIVE")
            return {"status": "failed", "reason": "KILL SWITCH ACTIVE"}

        target = (target_exchange or self.default_exchange_id).lower()
        logger.info(
            f"Execution Request: {side.upper()} {amount} {symbol} @ {order_type} on {target.upper()} ({self.trading_mode.upper()})"
        )

        if self.dry_run:
            # Mock Execution
            await asyncio.sleep(0.5)  # Simulate latency
            return {
                "id": f"mock_{int(asyncio.get_event_loop().time())}",
                "symbol": symbol,
                "status": "closed",
                "filled": amount,
                "price": price or 100000.0,  # Dummy price
                "info": {"msg": f"This was a PAPER trade on {target}"},
            }

        # LIVE EXECUTION
        exchange = self.exchanges.get(target)
        if not exchange:
            logger.error(f"Exchange {target} not initialized/found!")
            return {"status": "failed", "reason": f"Exchange {target} not initialized"}

        try:
            # Safety check: Amount > 0
            if amount <= 0:
                raise ValueError("Amount must be positive")

            # LIVE EXECUTION

            # Revolut Logic
            if target == "revolut":
                # Convert standard params to OrderRequest
                import uuid

                from backend.adapters.revolut_adapter import (OrderRequest,
                                                              OrderSide,
                                                              OrderType)

                # Revolut symbol usually 'BTC-USD', we might need mapping
                rev_symbol = symbol.replace("/", "-")

                req = OrderRequest(
                    client_order_id=uuid.uuid4(),
                    symbol=rev_symbol,
                    side=OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL,
                    order_type=(
                        OrderType.MARKET
                        if order_type.lower() == "market"
                        else OrderType.LIMIT
                    ),
                    qty=amount,
                    limit_price=price,
                )

                res = await exchange.submit_order(req)
                logger.info(f"Revolut Order Placed! ID: {res.order_id}")
                return {
                    "id": res.order_id,
                    "symbol": symbol,
                    "status": res.status.value,
                    "filled": res.filled_qty,  # Might be 0 initially
                    "info": res.raw_response,
                }

            # CCXT Logic
            order = await exchange.create_order(
                symbol=symbol, type=order_type, side=side, amount=amount, price=price
            )
            logger.info(f"Order Placed on {target}! ID: {order['id']}")
            return order

        except Exception as e:
            logger.error(f"Order Execution Failed on {target}: {e}")
            return {"status": "failed", "reason": str(e)}

    async def get_balance(self, target_exchange: Optional[str] = None):
        """Get balance from specific exchange or aggregate?"""
        # Simplification: Return default exchange balance if not specified
        target = (target_exchange or self.default_exchange_id).lower()

        if self.dry_run:
            return {
                "USD": {"free": 100000.0, "total": 100000.0},
                "BTC": {"free": 0.0, "total": 0.0},
            }

        exchange = self.exchanges.get(target)
        if not exchange:
            return {}

        try:
            if target == "revolut":
                balances = await exchange.get_balance()
                # Normalize
                normalized = {}
                for k, v in balances.items():
                    normalized[k] = {"free": v, "total": v, "used": 0.0}
                return normalized

            return await exchange.fetch_balance()
        except Exception as e:
            logger.error(f"Failed to fetch balance from {target}: {e}")
            return {}


# Singleton logic or Main wrapper?
# Orchestrator will clone/import this class.
