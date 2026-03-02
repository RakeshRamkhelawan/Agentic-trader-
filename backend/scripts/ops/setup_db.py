import asyncio
import os
import sys

import asyncpg


async def setup():
    # Use standard 5432 port by default, allow override via env var
    # Default to localhost if not specified (development mode)
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_user = os.getenv("POSTGRES_USER", "postgres")
    db_password = os.getenv("POSTGRES_PASSWORD", "postgres")

    # Connection string for administrative tasks (connecting to default 'postgres' db)
    dsn = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/postgres"

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
        dsn_trading = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/trading_db"
        conn_trading = await asyncpg.connect(dsn_trading)

        # Enable vector
        await conn_trading.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        print("[ENABLED] Extension 'vector'")

        # Enable timescaledb (if available)
        try:
            await conn_trading.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")
            print("[ENABLED] Extension 'timescaledb'")
        except Exception as e:
            print(
                f"[SKIPPING] TimescaleDB extension (might not be installed or requires library preload): {e}"
            )

        await conn_trading.close()
        print("\n[OK] Setup Complete")

    except Exception as e:
        print(f"[FAILED] {e}")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(setup())
