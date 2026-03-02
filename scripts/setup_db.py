
import asyncio
import asyncpg
import sys

async def setup():
    dsn = "postgresql://postgres:postgres@localhost:5455/postgres"
    print(f"Connecting to {dsn}...")
    try:
        conn = await asyncpg.connect(dsn)
        print("[SUCCESS] Connected to 'postgres'")

        # 1. Create User
        try:
            await conn.execute("CREATE USER trader WITH PASSWORD 'trading_secure';")
            print("[CREATED] User 'trader'")
        except asyncpg.DuplicateObjectError:
            print("[EXISTS] User 'trader' already exists")
            # Ensure password is correct
            await conn.execute("ALTER USER trader WITH PASSWORD 'trading_secure';")
            print("[UPDATED] Password for 'trader'")

        # 2. Create Database
        try:
            await conn.execute("CREATE DATABASE trading_db OWNER trader;")
            print("[CREATED] Database 'trading_db'")
        except asyncpg.DuplicateDatabaseError:
            print("[EXISTS] Database 'trading_db' already exists")

        # 3. Grant Privileges (just in case)
        await conn.execute("GRANT ALL PRIVILEGES ON DATABASE trading_db TO trader;")
        print("[GRANTED] Privileges on 'trading_db' to 'trader'")

        # 4. Enable extensions in trading_db (needs new connection)
        await conn.close()

        # Connect to new DB to enable extensions
        # Note: We connect as postgres first to enable extensions (superuser required usually)
        dsn_trading = "postgresql://postgres:postgres@localhost:5455/trading_db"
        conn_trading = await asyncpg.connect(dsn_trading)

        # Enable vector
        await conn_trading.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        print("[ENABLED] Extension 'vector'")

        # Enable timescaledb (if available)
        try:
            await conn_trading.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")
            print("[ENABLED] Extension 'timescaledb'")
        except Exception as e:
            print(f"[SKIPPING] TimescaleDB extension (might not be installed or requires library preload): {e}")

        await conn_trading.close()
        print("\n[OK] Setup Complete")

    except Exception as e:
        print(f"[FAILED] {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(setup())
