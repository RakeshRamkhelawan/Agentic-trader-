import asyncio
import asyncpg
import sys


async def enable_timescale():
    dsn = "postgresql://postgres:postgres@localhost:5455/trading_db"
    print(f"Connecting to {dsn}...")
    try:
        conn = await asyncpg.connect(dsn)
        print("[SUCCESS] Connected to 'trading_db'")

        try:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")
            print("[ENABLED] Extension 'timescaledb'")
        except Exception as e:
            print(f"[FAILED] TimescaleDB extension: {e}")

        await conn.close()
        print("\n[OK] TimescaleDB Setup Complete")

    except Exception as e:
        print(f"[FAILED] {e}")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(enable_timescale())
