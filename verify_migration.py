
import asyncio
from sqlalchemy import text
from backend.core.database import engine

async def verify_table():
    async with engine.connect() as conn:
        table_name = 'assets'
        result = await conn.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name = :table_name"),
            {"table_name": table_name}
        )
        row = result.fetchone()
        if row:
            print(f"SUCCESS: Table '{row[0]}' exists.")
            columns = await conn.execute(
                text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = :table_name"),
                {"table_name": table_name}
            )
            print("Columns:")
            for col in columns:
                print(f" - {col[0]} ({col[1]})")
        else:
            print(f"FAILURE: Table '{table_name}' NOT found.")

if __name__ == "__main__":
    asyncio.run(verify_table())
