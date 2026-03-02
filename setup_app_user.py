
import asyncio
import asyncpg
import sys

# Connect as Superuser (trader)
DB_URL = 'postgresql://trader:trading_secure@localhost:5455/trading_db'

async def setup_app_user():
    print("--- Setting up 'app' user ---")
    
    conn = await asyncpg.connect(DB_URL)
    try:
        # Create user if not exists
        try:
            await conn.execute("CREATE USER app WITH PASSWORD 'app_secure'")
            print("User 'app' created.")
        except asyncpg.DuplicateObjectError:
            print("User 'app' already exists.")
            
        # Grant Connect
        await conn.execute("GRANT CONNECT ON DATABASE trading_db TO app")
        print("Granted CONNECT.")
        
        # Grant Schema Usage
        await conn.execute("GRANT USAGE ON SCHEMA public TO app")
        print("Granted USAGE on public.")
        
        # Grant Table Permissions
        await conn.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app")
        print("Granted table permissions.")
        
        # Configure default privileges for future tables
        await conn.execute("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app")
        
        # Grant Sequence permissions (for ID generation if needed, though we use UUIDs)
        await conn.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app")

        print("\n[SUCCESS] User 'app' is ready.")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(setup_app_user())
