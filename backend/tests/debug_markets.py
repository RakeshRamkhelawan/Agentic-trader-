import asyncio
import os
import sys

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.services.trading_service import TradingService
from backend.services.user_settings_service import UserSettingsService


async def test_get_markets():
    # Setup minimal DB engine (mocking)
    DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/agentic_trader"
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    tenant_id = "test-tenant"  # Or a known tenant id

    # Initialize services
    settings_service = UserSettingsService()
    trading_service = TradingService()
    trading_service.settings_service = settings_service

    async with async_session() as db:
        print(f"Calling get_markets for tenant {tenant_id}...")
        markets = await trading_service.get_markets(db, tenant_id)
        print(f"Result: Found {len(markets)} markets")
        for m in markets[:5]:
            print(f" - {m['symbol']}: {m['price']} {m['change']}%")


if __name__ == "__main__":
    asyncio.run(test_get_markets())
