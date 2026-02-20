#!/usr/bin/env python3
"""
Fix orders table schema to match the model.
"""

import asyncio
import os
import sys

from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from backend.core.database import engine


COLUMNS_TO_ADD = [
    ('rejection_reason', 'VARCHAR'),
    ('risk_check_result', 'JSONB'),
    ('approved_at', 'TIMESTAMP'),
    ('approved_by', 'VARCHAR'),
    ('exchange_order_id', 'VARCHAR'),
    ('filled_qty', 'FLOAT'),
    ('avg_price', 'FLOAT'),
    ('commission', 'FLOAT'),
]

async def fix_schema():
    """Add missing columns to orders table."""
    
    async with engine.begin() as conn:
        for col_name, col_type in COLUMNS_TO_ADD:
            result = await conn.execute(text(f"""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'orders' AND column_name = '{col_name}'
            """))
            
            if result.scalar() is None:
                print(f"Adding missing '{col_name}' column to orders table...")
                await conn.execute(text(f"""
                    ALTER TABLE orders 
                    ADD COLUMN {col_name} {col_type}
                """))
                print(f"[OK] Column '{col_name}' added successfully")
            else:
                print(f"Column '{col_name}' already exists")
    
    print("\n[OK] Schema fix complete!")


if __name__ == "__main__":
    asyncio.run(fix_schema())
