#!/usr/bin/env python3
"""Import ultimate paper trades to database."""

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
    """Import ultimate paper trades."""
    
    print(f"Importing from: {json_file}")
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    trades = data.get('trades', [])
    stats = data.get('statistics', {})
    
    print(f"Session: {data['session_info']['exchanges']}")
    print(f"Trades to import: {len(trades)}")
    print(f"Unique symbols: {stats.get('unique_symbols', 0)}")
    print()
    
    async with AsyncSessionLocal() as session:
        imported = 0
        for trade in trades:
            try:
                created_at = datetime.fromisoformat(trade['timestamp'].replace('Z', '+00:00'))
                if created_at.tzinfo:
                    created_at = created_at.replace(tzinfo=None)
            except:
                created_at = datetime.utcnow()
            
            order = Order(
                tenant_id=tenant_id,
                symbol=trade['symbol'],
                side=trade['side'].lower(),
                quantity=trade['qty'],
                order_type='market',
                status=OrderStatus.FILLED,
                filled_qty=trade['qty'],
                avg_price=trade['price'],
                exchange_order_id=trade['order_id'],
                created_at=created_at,
                updated_at=created_at,
            )
            
            session.add(order)
            imported += 1
            
            if imported % 50 == 0:
                await session.commit()
                print(f"  Committed {imported}...")
        
        await session.commit()
        print()
        print(f"[OK] Imported {imported} trades")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/import_ultimate_trades.py <session_file.json>")
        sys.exit(1)
    
    asyncio.run(import_trades(sys.argv[1]))
