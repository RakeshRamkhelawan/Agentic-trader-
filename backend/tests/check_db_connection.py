import asyncio
import os

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://app:app_secure@localhost:5455/trading_db"
)


async def check():
    print(f"Connecting to {DATABASE_URL} ...")
    engine = create_async_engine(DATABASE_URL, echo=False)
    try:
        async with engine.connect() as conn:
            print("Connected!")
            res = await conn.execute(text("SELECT 1"))
            print(f"Result: {res.scalar()}")

            # Check RLS
            print("Checking Tenant Setting...")
            try:
                await conn.execute(text("SET app.current_tenant = 'test_conn'"))
                print("SET app.current_tenant Success")
            except Exception as e:
                print(f"SET app.current_tenant Failed: {e}")

    except Exception as e:
        print(f"CONNECTION FAILED: {e}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check())
