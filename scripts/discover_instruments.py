import asyncio
import logging
import json
from backend.services.trading_service import get_trading_service
from backend.core.database import AsyncSessionLocal
from backend.core.config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_instruments():
    service = get_trading_service()
    async with AsyncSessionLocal() as db:
        # Try to get Revolut adapter for 'system' or any tenant
        # Using a dummy tenant_id for discovery
        tenant_id = "system_discovery"

        logger.info(f"Checking instruments for exchange: revolut")
        adapter = await service._get_exchange_adapter(db, tenant_id, "revolut")

        if adapter:
            try:
                instruments = await adapter.get_instruments()
                logger.info(f"Successfully retrieved {len(instruments)} instruments")

                # Filter for things that look like ETFs or are not just BTC/ETH
                etfs = [
                    i
                    for i in instruments
                    if any(x in str(i).upper() for x in ["ETF", "TRUST", "FUND"])
                ]

                print(f"\n--- Total Instruments: {len(instruments)} ---")
                print("\n--- Sample Instruments ---")
                for i in instruments[:20]:
                    print(i)

                print(f"\n--- Detected ETFs ({len(etfs)}) ---")
                for e in etfs[:20]:
                    print(e)

            except Exception as e:
                logger.error(f"Failed to fetch instruments: {e}")
        else:
            logger.error(
                "No Revolut adapter found. Check your .env for REVOLUT_API_KEY and REVOLUT_PRIVATE_KEY"
            )


if __name__ == "__main__":
    asyncio.run(check_instruments())
