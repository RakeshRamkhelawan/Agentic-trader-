#!/usr/bin/env python3
"""
Monitor ongoing paper trading session.
Shows live stats from the database.
"""

import asyncio
import os
import sys
import time
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import desc, func, select
from backend.core.database import AsyncSessionLocal
from backend.models.orders import Order


async def monitor():
    """Monitor trading session."""
    print("="*80)
    print("     PAPER TRADING MONITOR")
    print("="*80)
    print("Press Ctrl+C to exit")
    print()

    last_count = 0

    while True:
        try:
            async with AsyncSessionLocal() as session:
                # Get stats
                count_result = await session.execute(
                    select(func.count()).select_from(Order).where(Order.tenant_id == "paper_trading")
                )
                total = count_result.scalar()

                # Get recent trades
                result = await session.execute(
                    select(Order)
                    .where(Order.tenant_id == "paper_trading")
                    .order_by(desc(Order.created_at))
                    .limit(5)
                )
                recent = result.scalars().all()

                # Get unique symbols
                symbols_result = await session.execute(
                    select(Order.symbol, func.count().label('count'))
                    .where(Order.tenant_id == "paper_trading")
                    .group_by(Order.symbol)
                )
                symbols = symbols_result.all()

                # Clear screen (works on Unix/Windows)
                os.system('cls' if os.name == 'nt' else 'clear')

                print("="*80)
                print("     PAPER TRADING MONITOR")
                print("="*80)
                print(f"Last update: {datetime.now().strftime('%H:%M:%S')}")
                print()
                print(f"Total Trades: {total}")
                print(f"Unique Symbols: {len(symbols)}")

                if total > last_count:
                    new_trades = total - last_count
                    print(f"New trades: +{new_trades}")
                    last_count = total

                if recent:
                    print()
                    print("Recent trades:")
                    for trade in recent:
                        time_str = trade.created_at.strftime("%H:%M:%S")
                        side = trade.side.upper()
                        print(f"  [{time_str}] {side:4} {trade.quantity:.6f} {trade.symbol:12} @ EUR {trade.avg_price or 0:,.2f}")

                if symbols:
                    print()
                    print("Top symbols:")
                    sorted_symbols = sorted(symbols, key=lambda x: x[1], reverse=True)[:10]
                    for sym, count in sorted_symbols:
                        print(f"  {sym:15} {count:3} trades")

                print()
                print("Refreshing in 10 seconds... (Ctrl+C to exit)")

        except Exception as e:
            print(f"Error: {e}")

        await asyncio.sleep(10)


if __name__ == "__main__":
    try:
        asyncio.run(monitor())
    except KeyboardInterrupt:
        print("\nMonitor stopped")
