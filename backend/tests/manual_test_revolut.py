import asyncio
import logging
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from backend.core.config.settings import settings
from backend.services.trading_service import get_trading_service
from backend.core.database import AsyncSessionLocal
from backend.core.context import set_tenant_context

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestRevolut")

async def test_revolut_connection():
    logger.info("--- Testing Revolut Integration ---")
    
    # 1. Verify Settings
    logger.info(f"API Key present: {bool(settings.REVOLUT_API_KEY)}")
    logger.info(f"Private Key present: {bool(settings.REVOLUT_PRIVATE_KEY)}")
    
    if not settings.REVOLUT_API_KEY or not settings.REVOLUT_PRIVATE_KEY:
        logger.error("❌ Missing Credentials in Settings/Env!")
        return

    # 2. Test TradingService Fallback
    ts = get_trading_service()
    tenant_id = "test_tenant" # Dummy tenant
    
    logger.info("Requesting Revolut Adapter from TradingService...")
    # Mocking DB session as it's required signature but presumably not used if falling back to system creds
    # However, get_api_keys uses it.
    
    async with AsyncSessionLocal() as session:
        # Set valid tenant context for RLS policies
        try:
            await set_tenant_context(session, tenant_id)
        except Exception as e:
            logger.warning(f"Could not set tenant context (RLS might not be enabled or DB error): {e}")

        adapter = await ts._get_exchange_adapter(session, tenant_id, "revolut")
        
        if not adapter:
            logger.error("❌ Failed to get adapter! Fallback logic might be broken.")
            return
            
        logger.info("✅ Adapter obtained successfully.")
        
        # 3. Test Connection / Data
        # 3. Test Ticker (Might fail if public endpoint inactive/404)
        logger.info("Fetching Ticker for BTC-EUR...")
        try:
            ticker = await adapter.get_ticker("BTC-EUR")
            logger.info(f"Ticker: {ticker}")
            if ticker.get('last', 0) > 0:
                 logger.info("✅ Valid Ticker Data Received")
        except Exception as e:
            logger.error(f"❌ Ticker Fetch Failed: {e}")

        # 4. Test Balance (Proven to work)
        logger.info("Fetching Balance...")
        try:
            balance = await adapter.get_balance()
            logger.info(f"✅ Balance Retrieved: {balance}")
        except Exception as e:
            logger.error(f"❌ Balance Fetch Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_revolut_connection())
