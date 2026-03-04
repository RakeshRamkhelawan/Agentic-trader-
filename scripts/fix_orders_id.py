#!/usr/bin/env python3
"""
Fix orders table id column type.
"""

import asyncio
import os
import sys

from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from backend.core.database import engine


async def fix_id_column():
    """Change id column from integer to varchar."""

    async with engine.begin() as conn:
        # Check current id column type
        result = await conn.execute(text("""
            SELECT data_type
            FROM information_schema.columns
            WHERE table_name = 'orders' AND column_name = 'id'
        """))

        current_type = result.scalar()
        print(f"Current id column type: {current_type}")

        if current_type == 'integer':
            print("Converting id column from INTEGER to VARCHAR...")

            # Drop dependent foreign key first
            await conn.execute(text("""
                ALTER TABLE trades DROP CONSTRAINT IF EXISTS trades_order_id_fkey
            """))

            # Drop and recreate the table with correct schema
            await conn.execute(text("""
                DROP TABLE IF EXISTS orders CASCADE
            """))

            await conn.execute(text("""
                CREATE TABLE orders (
                    id VARCHAR PRIMARY KEY,
                    tenant_id VARCHAR NOT NULL,
                    symbol VARCHAR NOT NULL,
                    side VARCHAR NOT NULL,
                    quantity FLOAT NOT NULL,
                    price FLOAT,
                    order_type VARCHAR DEFAULT 'market',
                    status VARCHAR DEFAULT 'PENDING_APPROVAL',
                    risk_check_result JSONB,
                    rejection_reason VARCHAR,
                    approved_at TIMESTAMP,
                    approved_by VARCHAR,
                    exchange_order_id VARCHAR,
                    filled_qty FLOAT DEFAULT 0.0,
                    avg_price FLOAT,
                    commission FLOAT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """))

            await conn.execute(text("""
                CREATE INDEX ix_orders_tenant_id ON orders(tenant_id)
            """))

            print("[OK] Orders table recreated with VARCHAR id")
        else:
            print("Id column already correct type")

    print("\n[OK] Fix complete!")


if __name__ == "__main__":
    asyncio.run(fix_id_column())
