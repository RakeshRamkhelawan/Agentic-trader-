
import asyncio
import asyncpg
import sys

async def inspect():
    dsn = "postgresql://postgres:postgres@localhost:5455/postgres"
    print(f"Connecting to {dsn}...")
    try:
        conn = await asyncpg.connect(dsn)
        print("[SUCCESS] Connected to 'postgres' DB as 'postgres'")
        
        # List Databases
        dbs = await conn.fetch("SELECT datname FROM pg_database WHERE datistemplate = false;")
        print("\nDatabases:")
        for db in dbs:
            print(f" - {db['datname']}")
            
        # List Users
        users = await conn.fetch("SELECT usename FROM pg_user;")
        print("\nUsers:")
        for user in users:
            print(f" - {user['usename']}")
            
        await conn.close()
    except Exception as e:
        print(f"[FAILED] {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(inspect())
