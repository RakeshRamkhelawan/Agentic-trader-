#!/usr/bin/env python3
"""
Realtime Paper Trading met echte marktdata

Dit script:
1. Verbindt met Revolut X en/of Bitvavo voor realtime prijzen
2. Voert paper trades uit (geen echt geld) tegen de echte marktprijs
3. Slaat trades op in de database

Usage:
    python scripts/realtime_paper_trading.py --exchange bitvavo --symbol BTC/EUR
    python scripts/realtime_paper_trading.py --exchange revolut --symbol BTC-USD
"""

import asyncio
import argparse
import os
import sys
import uuid
from datetime import UTC, datetime
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.execution.shadow_portfolio import ShadowPortfolioManager
from backend.schemas.orders import OrderRequest, OrderSide, OrderType
from backend.core.config.settings import settings


class RealtimePaperTrader:
    """Paper trading met echte marktdata."""

    # ...existing code...

    async def initialize(self):
        """Initialize exchange connection."""
        if self.exchange == "revolut":
            from backend.integrations.revolut_x_client import RevolutXClient, OrderSide
            self.client = RevolutXClient()
            connected = await self.client.connect()
            if not connected:
                raise RuntimeError("Failed to connect to Revolut X")
            print("[OK] Connected to Revolut X")

        elif self.exchange == "bitvavo":
            from backend.execution.bitvavo_adapter import BitvavoAdapter
            self.adapter = BitvavoAdapter()
            success = await self.adapter.initialize()
            if not success:
                raise RuntimeError("Failed to connect to Bitvavo")
            print("[OK] Connected to Bitvavo")

        else:
            raise ValueError(f"Unknown exchange: {self.exchange}")

    async def fetch_price(self) -> Optional[float]:
        """Fetch current market price."""
        try:
            if self.exchange == "revolut" and self.client:
                ticker = await self.client.get_ticker(self.symbol)
                price = ticker.get("last", 0)

            elif self.exchange == "bitvavo" and self.adapter:
                ticker = await self.adapter.fetch_ticker(self.symbol)
                price = ticker.get("last", 0) if ticker else 0
            else:
                return None

            return float(price) if price else None

        except Exception as e:
            print(f"[ERROR] Failed to fetch price: {e}")
            return None

    async def price_feed(self, interval: int = 5):
        """Background task to continuously update prices."""
        self.price_feed_active = True
        print(f"[FEED] Starting price feed (update every {interval}s)")
        print()

        while self.price_feed_active:
            price = await self.fetch_price()
            if price:
                self.current_price = price
                self.portfolio.update_price(self.symbol, price)
                timestamp = datetime.now(UTC).strftime("%H:%M:%S")
                print(f"[{timestamp}] {self.symbol} @ EUR {price:,.2f}")
            await asyncio.sleep(interval)

    def __init__(self, exchange: str, symbol: str, initial_balance: float = 10000.0):
        self.exchange = exchange.lower()
        self.symbol = symbol
        self.portfolio = ShadowPortfolioManager(initial_cash=initial_balance)
        self.price_feed_active = False
        self.current_price = 0.0
        self.trades_executed: list[dict] = []

        # Initialize exchange client
        self.client = None
        self.adapter = None

        print(f"[INIT] Realtime Paper Trader")
        print(f"       Exchange: {exchange.upper()}")
        print(f"       Symbol: {symbol}")
        print(f"       Initial Balance: EUR {initial_balance:,.2f}")
        print()

    async def execute_paper_trade(self, side: OrderSide, qty: float) -> dict:
        """Execute a paper trade against current market price."""
        if self.current_price <= 0:
            return {"error": "No valid market price available"}

        order = OrderRequest(
            symbol=self.symbol,
            side=side,
            qty=qty,
            order_type=OrderType.MARKET,
            client_order_id=uuid.uuid4()
        )

        result = await self.portfolio.submit_order(order)

        if result.status is not None and not isinstance(result.status, str) and hasattr(result.status, 'value'):
            status_str = result.status.value
        else:
            status_str = str(result.status)
        trade_record = {
            "timestamp": datetime.now(UTC).isoformat(),
            "exchange": self.exchange,
            "symbol": self.symbol,
            "side": side.value if hasattr(side, 'value') else str(side),
            "qty": qty,
            "market_price": self.current_price,
            "status": status_str,
            "order_id": result.order_id,
            "filled_qty": result.filled_qty if hasattr(result, 'filled_qty') else 0,
            "avg_price": result.avg_price if hasattr(result, 'avg_price') else 0,
        }

        # Store for later export
        self.trades_executed.append(trade_record)

        return trade_record

    async def interactive_trading(self):
        """Interactive trading loop."""
        print("="*70)
        print("     REALTIME PAPER TRADING - INTERACTIVE MODE")
        print("="*70)
        print()
        print("Commands:")
        print("  buy <amount>   - Buy (e.g., 'buy 0.001')")
        print("  sell <amount>  - Sell (e.g., 'sell 0.001')")
        print("  balance        - Show current balance")
        print("  status         - Show current price and position")
        print("  auto <n>       - Auto-trade n random trades")
        print("  quit           - Exit")
        print()

        while True:
            try:
                cmd = input("> ").strip().lower()

                if cmd == "quit" or cmd == "exit":
                    break

                elif cmd == "balance":
                    balance = await self.portfolio.get_balance()
                    btc_qty = balance.get(self.symbol, 0)
                    btc_value = btc_qty * self.current_price
                    total = balance.get('EUR', 0) + btc_value

                    print(f"  Cash: EUR {balance.get('EUR', 0):,.2f}")
                    print(f"  {self.symbol}: {btc_qty:.6f} (EUR {btc_value:,.2f})")
                    print(f"  Total Value: EUR {total:,.2f}")
                    print()

                elif cmd == "status":
                    print(f"  Current Price: EUR {self.current_price:,.2f}")
                    balance = await self.portfolio.get_balance()
                    print(f"  Position: {balance.get(self.symbol, 0):.6f}")
                    print()

                elif cmd.startswith("buy "):
                    try:
                        qty = float(cmd.split()[1])
                        if qty <= 0:
                            print("[ERROR] Amount must be positive")
                            continue

                        print(f"[EXEC] Buying {qty} {self.symbol} @ EUR {self.current_price:,.2f}")
                        result = await self.execute_paper_trade(OrderSide.BUY, qty)

                        if result["status"] == "FILLED":
                            print(f"[OK] Filled @ EUR {result['avg_price']:,.2f}")
                        else:
                            print(f"[FAILED] {result.get('error_message', 'Unknown error')}")
                    except (IndexError, ValueError):
                        print("[ERROR] Usage: buy <amount>")

                elif cmd.startswith("sell "):
                    try:
                        qty = float(cmd.split()[1])
                        if qty <= 0:
                            print("[ERROR] Amount must be positive")
                            continue

                        print(f"[EXEC] Selling {qty} {self.symbol} @ EUR {self.current_price:,.2f}")
                        result = await self.execute_paper_trade(OrderSide.SELL, qty)

                        if result["status"] == "FILLED":
                            print(f"[OK] Filled @ EUR {result['avg_price']:,.2f}")
                        else:
                            print(f"[FAILED] {result.get('error_message', 'Unknown error')}")
                    except (IndexError, ValueError):
                        print("[ERROR] Usage: sell <amount>")

                elif cmd.startswith("auto "):
                    try:
                        num_trades = int(cmd.split()[1])
                        await self.run_auto_trading(num_trades)
                    except (IndexError, ValueError):
                        print("[ERROR] Usage: auto <number>")

                else:
                    print("[ERROR] Unknown command. Type 'help' for available commands.")

            except KeyboardInterrupt:
                print("\n[EXIT] Interrupted by user")
                break
            except Exception as e:
                print(f"[ERROR] {e}")

    async def run_auto_trading(self, num_trades: int = 10):
        """Run automated paper trading."""
        print(f"[AUTO] Starting automated trading ({num_trades} trades)")

        import random
        trades_executed = []

        for i in range(num_trades):
            # Alternate buy/sell
            side = OrderSide.BUY if i % 2 == 0 else OrderSide.SELL
            qty = 0.001

            # Check balance before trading
            balance = await self.portfolio.get_balance()

            if side == OrderSide.BUY:
                cost = qty * self.current_price
                if balance.get('EUR', 0) < cost:
                    print(f"  [SKIP] Insufficient EUR for buy")
                    continue
            else:
                if balance.get(self.symbol, 0) < qty:
                    print(f"  [SKIP] Insufficient {self.symbol} for sell")
                    continue

            result = await self.execute_paper_trade(side, qty)
            trades_executed.append(result)

            if result["status"] == "FILLED":
                side_str = side.value.upper() if hasattr(side, 'value') else str(side).upper()
                print(f"  [OK] {side_str} {qty} @ EUR {result['avg_price']:,.2f}")
            else:
                print(f"  [FAILED] {result.get('error_message', 'Unknown')}")

            # Wait between trades
            await asyncio.sleep(2)

        print(f"[AUTO] Completed {len(trades_executed)} trades")
        return trades_executed

    async def save_session(self):
        """Save trading session to JSON file."""
        if not self.trades_executed:
            print("[INFO] No trades to save")
            return

        import json

        output_file = f"realtime_paper_session_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.json"

        session_data = {
            "session_info": {
                "exchange": self.exchange,
                "symbol": self.symbol,
                "start_time": datetime.now(UTC).isoformat(),
                "initial_balance": self.portfolio.cash_balance,
            },
            "trades": self.trades_executed,
            "final_balance": await self.portfolio.get_balance(),
        }

        with open(output_file, 'w') as f:
            json.dump(session_data, f, indent=2, default=str)

        print(f"[SAVE] Session saved to: {output_file}")
        return output_file

    async def close(self):
        """Cleanup."""
        self.price_feed_active = False

        if self.client:
            await self.client.disconnect()
        if self.adapter:
            await self.adapter.close()

        print("[OK] Connection closed")


async def main():
    parser = argparse.ArgumentParser(description="Realtime Paper Trading")
    parser.add_argument("--exchange", choices=["revolut", "bitvavo"], default="bitvavo",
                       help="Exchange to use")
    parser.add_argument("--symbol", default="BTC/EUR",
                       help="Trading symbol (e.g., BTC/EUR or BTC-USD)")
    parser.add_argument("--balance", type=float, default=10000.0,
                       help="Initial balance")
    parser.add_argument("--auto", type=int, default=0,
                       help="Number of auto-trades to execute")

    args = parser.parse_args()

    # Check trading mode
    if settings.TRADING_MODE != "paper":
        print("[WARNING] TRADING_MODE is not set to 'paper' in .env!")
        print(f"[WARNING] Current mode: {settings.TRADING_MODE}")
        response = input("Continue anyway? (yes/no): ")
        if response.lower() != "yes":
            return

    trader = RealtimePaperTrader(
        exchange=args.exchange,
        symbol=args.symbol,
        initial_balance=args.balance
    )

    try:
        await trader.initialize()

        # Start price feed in background
        price_task = asyncio.create_task(trader.price_feed(interval=5))

        # Wait a moment for first price
        await asyncio.sleep(2)

        if args.auto > 0:
            await trader.run_auto_trading(args.auto)
        else:
            await trader.interactive_trading()

        # Stop price feed
        trader.price_feed_active = False
        try:
            price_task.cancel()
            await price_task
        except asyncio.CancelledError:
            pass

        # Save session
        await trader.save_session()

    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        await trader.close()

        # Final summary
        print("\n" + "="*70)
        print("     SESSION COMPLETE")
        print("="*70)
        balance = await trader.portfolio.get_balance()
        btc_qty = balance.get(trader.symbol, 0)
        btc_value = btc_qty * trader.current_price
        total = balance.get('EUR', 0) + btc_value
        print(f"Final Balance:")
        print(f"  Cash: EUR {balance.get('EUR', 0):,.2f}")
        print(f"  {trader.symbol}: {btc_qty:.6f} (EUR {btc_value:,.2f})")
        print(f"  Total Value: EUR {total:,.2f}")

        # Import to database
        print()
        print("[IMPORT] Importing trades to database...")
        import subprocess
        result = subprocess.run(
            ["python", "scripts/import_realtime_paper_trades.py"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("[OK] Trades imported to database")
        else:
            print(f"[WARNING] Import failed: {result.stderr}")


if __name__ == "__main__":
    asyncio.run(main())
