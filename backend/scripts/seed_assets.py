import asyncio
import logging
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.core.database import AsyncSessionLocal
from backend.assets.models import Asset, AssetStatus

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CATEGORY_MAP = {
    "BTC": "layer1", "ETH": "layer1", "SOL": "layer1", "DOT": "layer1",
    "ADA": "layer1", "AVAX": "layer1", "LINK": "oracle", "UNI": "defi",
    "AAVE": "defi", "DOGE": "meme", "SHIB": "meme", "PEPE": "meme",
}

async def seed_assets():
    async with AsyncSessionLocal() as session:
        # Strategy for 448 assets: use mapping or API
        symbols = [
            ("BTC/EUR", "bitvavo"), ("ETH/EUR", "bitvavo"), ("SOL/EUR", "bitvavo"),
            ("ADA/EUR", "bitvavo"), ("DOT/EUR", "bitvavo"), ("XRP/EUR", "bitvavo"),
            ("LINK/EUR", "bitvavo"), ("DOGE/EUR", "bitvavo"), ("LTC/EUR", "bitvavo"),
            ("XLM/EUR", "bitvavo")
        ]
        
        from sqlalchemy import select
        for symbol, exchange in symbols:
            base = symbol.split("/")[0]
            category = CATEGORY_MAP.get(base, "other")
            
            result = await session.execute(
                select(Asset).where(Asset.symbol == symbol, Asset.exchange == exchange)
            )
            if not result.scalar_one_or_none():
                asset = Asset(
                    symbol=symbol,
                    exchange=exchange,
                    status=AssetStatus.ACTIVE if category != "other" else AssetStatus.DISCOVERED,
                    category=category
                )
                session.add(asset)
        
        await session.commit()
        logger.info("Successfully seeded foundation assets with categorization.")

if __name__ == "__main__":
    asyncio.run(seed_assets())
