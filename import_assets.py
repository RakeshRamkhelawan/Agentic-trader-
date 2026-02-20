import sys
import os
import asyncio
import csv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert
from dotenv import load_dotenv

# Add project root to sys.path for backend imports
project_root = r"c:\Users\rsram\Downloads\agentic_trader_platform_1734_20260109_210621"
if project_root not in sys.path:
    sys.path.append(project_root)

from backend.assets.models import Asset, AssetStatus, Base

async def import_assets():
    # Load environment variables
    load_dotenv(os.path.join(project_root, ".env"))
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found in .env")
        return

    # Ensure URL is async-compatible for asyncpg
    if "postgresql://" in db_url and "asyncpg" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # 1. Ensure Table Exists
    try:
        async with engine.begin() as conn:
            print("Creating table 'assets' if it doesn't exist...")
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        print(f"Error creating table: {e}")

    # 2. Read CSV
    csv_path = os.path.join(project_root, "data", "bitvavo_assets.csv")
    if not os.path.exists(csv_path):
        print(f"CSV path does not exist: {csv_path}")
        return
        
    print(f"Reading CSV from {csv_path}...")
    
    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        records = list(reader)

    print(f"Found {len(records)} records in CSV.")

    # 3. Batch Insert with Conflict Handling
    async with async_session() as session:
        try:
            for i in range(0, len(records), 50):
                batch = records[i:i+50]
                values = []
                for r in batch:
                    # Basic mapping, adjust column names if necessary based on CSV audit
                    values.append({
                        "symbol": r.get("symbol", ""),
                        "name": r.get("name", ""),
                        "status": AssetStatus.DISCOVERED,
                        "metadata_info": {"source": "bitvavo_import"}
                    })
                
                if not values:
                    continue
                    
                stmt = insert(Asset).values(values).on_conflict_do_nothing(index_elements=["symbol"])
                await session.execute(stmt)
            
            await session.commit()
            print("Import committed successfully.")
        except Exception as e:
            await session.rollback()
            print(f"Error during import: {e}")
            raise
        
        # 4. Verification Check
        result = await session.execute(text("SELECT count(*) FROM assets"))
        count = result.scalar()
        print(f"Final count in 'assets' table: {count}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(import_assets())
