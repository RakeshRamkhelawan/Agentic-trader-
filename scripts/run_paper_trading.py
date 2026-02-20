#!/usr/bin/env python3
"""
Paper Trading Runner voor Agentic Trader Platform

Dit script start paper trading om:
1. Data te genereren voor de applicatie
2. De trading flow te testen
3. Backtesting data te verzamelen

Usage:
    python scripts/run_paper_trading.py
"""

import asyncio
import os
import sys
import uuid
from datetime import UTC, datetime
from typing import Optional

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Ensure backend is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.execution.shadow_portfolio import ShadowPortfolioManager
from backend.schemas.orders import OrderRequest, OrderSide, OrderType
from backend.core.config.settings import settings


class PaperTrader:
    """Simple paper trading simulator."""
    
    def __init__(self, initial_balance: float = 10000.0):
        self.portfolio = ShadowPortfolioManager(initial_cash=initial_balance)
        self.trades_executed = []
        print(f"Paper Trading Portfolio initialized with EUR {initial_balance:,.2f}")
        
    async def simulate_market_data(self, symbol: str = "BTC-EUR"):
        """Simulate receiving market data updates."""
        import random
        
        # Simulate BTC price around 85k-95k EUR
        base_price = 90000.0
        price = base_price + random.uniform(-5000, 5000)
        
        self.portfolio.update_price(symbol, price)
        return price
        
    async def execute_paper_trade(
        self, 
        symbol: str, 
        side: OrderSide, 
        qty: float
    ) -> dict:
        """Execute a paper trade."""
        
        order = OrderRequest(
            symbol=symbol,
            side=side,
            qty=qty,
            order_type=OrderType.MARKET,
            client_order_id=uuid.uuid4()
        )
        
        result = await self.portfolio.submit_order(order)
        
        trade_record = {
            "timestamp": datetime.now(UTC).isoformat(),
            "symbol": symbol,
            "side": side.value,
            "qty": qty,
            "status": result.status.value,
            "order_id": result.order_id,
            "filled_qty": result.filled_qty if hasattr(result, 'filled_qty') else 0,
            "avg_price": result.avg_price if hasattr(result, 'avg_price') else 0,
        }
        
        self.trades_executed.append(trade_record)
        return trade_record
        
    async def run_trading_session(self, num_trades: int = 10):
        """Run a paper trading session."""
        
        print("\n" + "="*70)
        print("     STARTING PAPER TRADING SESSION")
        print("="*70)
        print(f"\nTrading Mode: {settings.TRADING_MODE.upper()}")
        print(f"Number of trades to simulate: {num_trades}")
        print("\n*** PAPER TRADING - NO REAL MONEY INVOLVED ***\n")
        
        symbol = "BTC-EUR"
        
        for i in range(num_trades):
            print(f"\n--- Trade {i+1}/{num_trades} ---")
            
            # Update market price
            current_price = await self.simulate_market_data(symbol)
            print(f"Market: {symbol} @ €{current_price:,.2f}")
            
            # Alternate buy/sell for testing
            side = OrderSide.BUY if i % 2 == 0 else OrderSide.SELL
            qty = 0.001  # Small BTC amount
            
            # Check if we have enough balance for buy
            if side == OrderSide.BUY:
                cost = qty * current_price
                if self.portfolio.cash_balance < cost:
                    print(f"  ⚠️ Insufficient funds for BUY (need €{cost:,.2f})")
                    continue
            else:
                # Check if we have position for sell
                position = self.portfolio.positions.get(symbol, 0)
                if position < qty:
                    print(f"  ⚠️ Insufficient position for SELL (have {position:.6f})")
                    continue
            
            # Execute trade
            result = await self.execute_paper_trade(symbol, side, qty)
            
            if result["status"] == "FILLED":
                print(f"  [OK] {side.value.upper()} {qty} {symbol}")
                print(f"     Filled @ EUR {result['avg_price']:,.2f}")
                print(f"     Order ID: {result['order_id'][:8]}...")
            else:
                print(f"  [FAILED] Order {result['status']}")
            
            # Show current balance
            balance = await self.portfolio.get_balance()
            print(f"  Cash: EUR {balance.get('EUR', 0):,.2f}")
            print(f"     Position: {balance.get(symbol, 0):.6f} BTC")
            
            # Small delay between trades
            await asyncio.sleep(0.5)
        
        # Final summary
        await self.print_summary()
        
    async def print_summary(self):
        """Print session summary."""
        print("\n" + "="*70)
        print("     PAPER TRADING SESSION COMPLETE")
        print("="*70)
        
        balance = await self.portfolio.get_balance()
        
        print(f"\nFinal Portfolio:")
        print(f"  Cash: EUR {balance.get('EUR', 0):,.2f}")
        print(f"  BTC Position: {balance.get('BTC-EUR', 0):.6f}")
        
        # Calculate total value
        btc_price = self.portfolio.market_prices.get("BTC-EUR", 0)
        total_value = balance.get('EUR', 0) + (balance.get('BTC-EUR', 0) * btc_price)
        print(f"  Total Value: EUR {total_value:,.2f}")
        
        print(f"\nTrades Executed: {len(self.trades_executed)}")
        
        # Save trades to file
        output_file = f"paper_trading_session_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json"
        import json
        with open(output_file, 'w') as f:
            json.dump({
                "session_time": datetime.now(UTC).isoformat(),
                "trades": self.trades_executed,
                "final_balance": balance,
            }, f, indent=2, default=str)
        print(f"\n[FILE] Session data saved to: {output_file}")


async def main():
    """Main entry point."""
    
    # Check trading mode
    if settings.TRADING_MODE != "paper":
        print("\n" + "***"*35)
        print("WARNING: TRADING_MODE is not set to 'paper'!")
        print(f"Current mode: {settings.TRADING_MODE}")
        print("\nSet TRADING_MODE=paper in your .env file")
        print("***"*35)
        return
    
    # Create and run paper trader
    trader = PaperTrader(initial_balance=10000.0)
    
    # Run session (default 10 trades)
    num_trades = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    await trader.run_trading_session(num_trades=num_trades)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[WARNING] Paper trading interrupted by user")
    except Exception as e:
        print(f"\n\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
