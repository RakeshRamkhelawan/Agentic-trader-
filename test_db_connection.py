"""Quick database connection test."""
import asyncio
import os

# Set env vars
os.environ["JWT_SECRET_KEY"] = "65a2ed0b53625014a011b6882a2ed5df15d36d6843a61904c68102660bb3b744"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://trader:pIu4r4xm8wel5_vBkKYi_mjelL4Hp35E@localhost:5432/trading_db"
os.environ["AUTH_DISABLED"] = "true"

async def test_connection():
    try:
        from backend.core.database import SessionManager
        async with SessionManager.system_admin_session() as s:
            print("✅ Database connection successful!")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_connection())
    exit(0 if result else 1)
