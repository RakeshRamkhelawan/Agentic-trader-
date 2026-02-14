
import asyncio
import os
import sys

from sqlalchemy import text

# Add current directory to path
sys.path.append(os.getcwd())

async def main():
    print("Starting SessionManager check...")
    try:
        from backend.core.database import AsyncSessionLocal, SessionManager
        
        print("Creating session with system_admin_session()...")
        async with SessionManager.system_admin_session() as session:
            print(f"Session object type: {type(session)}")
            print(f"Session dir: {dir(session)}")
            
            # Try basic execute
            print("Executing SELECT 1...")
            # We need a running DB for this, but let's try.
            # If DB is not reachable, we'll get ConnectionError, which is fine (means code reached execute).
            try:
                await session.execute(text("SELECT 1"))
                print("Execution Success!")
            except Exception as db_err:
                print(f"DB Error (Expected if DB down): {db_err}")
                if "async_generator" in str(db_err):
                    print("!!! FOUND THE BUG: session is a generator !!!")
                    
    except Exception as e:
        print(f"Caught TOP LEVEL error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
