
import asyncio
import asyncpg
import sys

async def test_connection(user, password, database="trading_db", port=5455):
    dsn = f"postgresql://{user}:{password}@localhost:{port}/{database}"
    print(f"Testing connection for user '{user}'...")
    try:
        conn = await asyncpg.connect(dsn)
        print(f"[SUCCESS] Connected as '{user}'")
        await conn.close()
        return True
    except Exception as e:
        print(f"[FAILED] {e}")
        return False

async def main():
    # Test 1: Trader (from current .env)
    trader_success = await test_connection("trader", "trading_secure")
    
    # Test 2: App (from database.py default)
    app_success = await test_connection("app", "app_secure")
    
    # Test 3: Postgres (standard superuser, default password often postgres)
    postgres_success = await test_connection("postgres", "postgres") # common default
    postgres_secure_success = await test_connection("postgres", "trading_secure") # maybe shared pass
    
    if trader_success:
        print("\nCONCLUSION: Use 'trader'")
    elif app_success:
        print("\nCONCLUSION: Use 'app' (Legacy volume detected)")
    elif postgres_success:
         print("\nCONCLUSION: Use 'postgres'")
    else:
        print("\nCONCLUSION: No working credentials found.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
