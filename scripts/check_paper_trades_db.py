#!/usr/bin/env python3
"""Check paper trades in database."""

import asyncio
import os
import sys

from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import desc, func, select
from backend.core.database import AsyncSessionLocal
from backend.models.orders import Order


async def check_trades():
    """Check paper trades in database."""
    
    async with AsyncSessionLocal() as session:
        # Get total count
        count_result = await session.execute(
            select(func.count()).select_from(Order)
        )
        total = count_result.scalar()
        
        # Get paper trading count
        paper_count_result = await session.execute(
            select(func.count()).select_from(Order).where(Order.tenant_id == "paper_trading")
        )
        paper_total = paper_count_result.scalar()
        
        print("="*70)
        print("     PAPER TRADES IN DATABASE")
        print("="*70)
        print()
        print(f"Total orders: {total}")
        print(f"Paper trading orders: {paper_total}")
        print()
        
        # Get recent trades
        result = await session.execute(
            select(Order)
            .where(Order.tenant_id == "paper_trading")
            .order_by(desc(Order.created_at))
            .limit(10)
        )
        recent_trades = result.scalars().all()
        
        if recent_trades:
            print("Recent paper trades:")
            print()
            for trade in recent_trades:
                side = trade.side.upper()
                symbol = trade.symbol
                qty = trade.quantity
                price = trade.avg_price or 0
                value = qty * price
                status = trade.status
                time = trade.created_at.strftime("%Y-%m-%d %H:%M:%S")
                print(f"  [{time}] {side:4} {qty:.6f} {symbol} @ EUR {price:,.2f} = EUR {value:,.2f} [{status}]")
        else:
            print("No paper trades found in database")
        
        # Get unique symbols
        symbols_result = await session.execute(
            select(Order.symbol, func.count().label('count'))
            .where(Order.tenant_id == "paper_trading")
            .group_by(Order.symbol)
        )
        symbols = symbols_result.all()
        
        if symbols:
            print()
            print("Symbols traded:")
            for symbol, count in symbols:
                print(f"  {symbol}: {count} trades")


if __name__ == "__main__":
    asyncio.run(check_trades())
