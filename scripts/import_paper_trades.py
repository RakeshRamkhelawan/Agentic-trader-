#!/usr/bin/env python3
"""
Import paper trading session data into the database.

Usage:
    python scripts/import_paper_trades.py <paper_trading_session_file.json>
"""

import asyncio
import json
import os
import sys
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.database import AsyncSessionLocal
from backend.models.orders import Order, OrderStatus


async def import_paper_trades(json_file: str, tenant_id: str = "paper_trading"):
    """Import paper trades from JSON file into database."""
    
    print(f"Importing paper trades from: {json_file}")
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    trades = data.get('trades', [])
    print(f"Found {len(trades)} trades to import")
    
    async with AsyncSessionLocal() as session:
        imported = 0
        for trade in trades:
            # Parse timestamp - make it naive (no timezone) for database
            try:
                from datetime import timezone
                created_at = datetime.fromisoformat(trade['timestamp'].replace('Z', '+00:00'))
                # Convert to naive datetime
                if created_at.tzinfo:
                    created_at = created_at.replace(tzinfo=None)
            except:
                created_at = datetime.utcnow()
            
            # Create order record
            order = Order(
                tenant_id=tenant_id,
                symbol=trade['symbol'],
                side=trade['side'].lower(),
                quantity=trade['qty'],
                order_type="market",
                status=OrderStatus.FILLED,
                filled_qty=trade.get('filled_qty', trade['qty']),
                avg_price=trade.get('avg_price'),
                exchange_order_id=trade['order_id'],
                created_at=created_at,
                updated_at=created_at,
            )
            
            session.add(order)
            imported += 1
            
            # Commit every 10 records
            if imported % 10 == 0:
                await session.commit()
                print(f"  Committed {imported} trades...")
        
        # Final commit
        await session.commit()
        print(f"\n[OK] Successfully imported {imported} paper trades to database")
        
        # Show summary
        from sqlalchemy import func, select
        count_result = await session.execute(
            select(func.count()).select_from(Order).where(Order.tenant_id == tenant_id)
        )
        total_in_db = count_result.scalar()
        print(f"Total paper trades in database: {total_in_db}")


def main():
    if len(sys.argv) < 2:
        # Find most recent paper trading session file
        import glob
        files = glob.glob("paper_trading_session_*.json")
        if not files:
            print("Error: No paper trading session file found")
            print("Usage: python scripts/import_paper_trades.py <json_file>")
            sys.exit(1)
        json_file = max(files, key=os.path.getctime)
        print(f"Using most recent file: {json_file}")
    else:
        json_file = sys.argv[1]
    
    if not os.path.exists(json_file):
        print(f"Error: File not found: {json_file}")
        sys.exit(1)
    
    asyncio.run(import_paper_trades(json_file))


if __name__ == "__main__":
    main()
