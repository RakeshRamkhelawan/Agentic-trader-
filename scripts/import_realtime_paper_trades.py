#!/usr/bin/env python3
"""
Import realtime paper trades from session file into database.

Usage:
    python scripts/import_realtime_paper_trades.py <session_file.json>
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


async def import_trades(json_file: str, tenant_id: str = "paper_trading"):
    """Import paper trades from JSON file into database."""
    
    print(f"Importing paper trades from: {json_file}")
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    trades = data.get('trades', [])
    session_info = data.get('session_info', {})
    
    print(f"Session: {session_info.get('exchange', 'unknown')} - {session_info.get('symbol', 'unknown')}")
    print(f"Found {len(trades)} trades to import")
    print()
    
    async with AsyncSessionLocal() as session:
        imported = 0
        for trade in trades:
            # Parse timestamp
            try:
                created_at = datetime.fromisoformat(trade['timestamp'].replace('Z', '+00:00'))
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
                order_type=trade.get('order_type', 'market'),
                status=OrderStatus.FILLED,
                filled_qty=trade.get('filled_qty', trade['qty']),
                avg_price=trade.get('avg_price'),
                exchange_order_id=trade['order_id'],
                created_at=created_at,
                updated_at=created_at,
            )
            
            session.add(order)
            imported += 1
            
            # Show progress
            if imported % 5 == 0:
                print(f"  Imported {imported}/{len(trades)}...")
        
        # Commit all
        await session.commit()
        print()
        print(f"[OK] Successfully imported {imported} paper trades to database")
        
        # Show summary
        from sqlalchemy import func, select
        count_result = await session.execute(
            select(func.count()).select_from(Order).where(Order.tenant_id == tenant_id)
        )
        total_in_db = count_result.scalar()
        print(f"[INFO] Total paper trades in database: {total_in_db}")


def find_latest_session():
    """Find the most recent paper trading session file."""
    import glob
    
    # Look for both realtime and regular paper trading sessions
    patterns = ["realtime_paper_session_*.json", "paper_trading_session_*.json"]
    files = []
    
    for pattern in patterns:
        files.extend(glob.glob(pattern))
    
    if not files:
        return None
    
    return max(files, key=os.path.getctime)


def main():
    if len(sys.argv) < 2:
        # Find most recent session file
        json_file = find_latest_session()
        if not json_file:
            print("[ERROR] No paper trading session file found")
            print("Usage: python scripts/import_realtime_paper_trades.py <json_file>")
            sys.exit(1)
        print(f"[INFO] Using most recent file: {json_file}")
    else:
        json_file = sys.argv[1]
    
    if not os.path.exists(json_file):
        print(f"[ERROR] File not found: {json_file}")
        sys.exit(1)
    
    asyncio.run(import_trades(json_file))


if __name__ == "__main__":
    main()
