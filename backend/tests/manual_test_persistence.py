import asyncio
import logging
import os
import sys
from datetime import datetime

import numpy as np

# Add project root to path
sys.path.append(os.getcwd())

from sqlalchemy import select

from backend.core.database import AsyncSessionLocal
from backend.core.memory_system import MemorySystem
from backend.models.agent_experience import AgentExperience
from backend.models.market_data import MarketCandle, MarketTick
from backend.services.trading_service import get_trading_service

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestPersistence")


async def test_memory_persistence():
    logger.info("--- Testing Memory Persistence ---")

    # 1. Initialize System
    memory = MemorySystem(capacity=100)

    # 2. Store dummy experience
    state = {"price": 100.0, "rsi": 50.0}
    action = 1  # Buy
    outcome = 0.5  # Profit

    logger.info("Storing experience...")
    await memory.store(state, action, outcome, agent_id="test_agent")

    # 3. Verify in Memory Buffer
    assert len(memory.memory_buffer) > 0
    logger.info(f"Memory Buffer Size: {len(memory.memory_buffer)}")

    # 4. Verify in DB
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(AgentExperience).where(AgentExperience.agent_id == "test_agent")
        )
        db_exps = result.scalars().all()
        logger.info(f"Experiences in DB: {len(db_exps)}")
        assert len(db_exps) > 0
        logger.info(f"Latest Exp: {db_exps[-1].state_vector}")

    # 5. Clear Buffer and Load from DB
    memory.memory_buffer.clear()
    logger.info("Cleared Memory Buffer.")

    logger.info("Loading from DB...")
    await memory.load_from_db()
    logger.info(f"Memory Buffer Size after Load: {len(memory.memory_buffer)}")
    assert len(memory.memory_buffer) > 0
    logger.info("Memory Persistence Verified! ✅")


async def test_market_persistence():
    logger.info("--- Testing Market Persistence ---")
    ts = get_trading_service()

    # 1. Store Tick
    tick_data = {
        "symbol": "BTC-EUR",
        "price": 50000.0,
        "volume": 0.5,
        "timestamp": datetime.now().isoformat(),
        "side": "buy",
    }
    logger.info(f"Storing Tick: {tick_data}")
    await ts.store_market_tick(tick_data)

    # 2. Store Candle
    candle_data = {
        "symbol": "BTC-EUR",
        "timeframe": "1m",
        "timestamp": datetime.now().isoformat(),
        "open": 50000.0,
        "high": 50100.0,
        "low": 49900.0,
        "close": 50050.0,
        "volume": 10.5,
    }
    logger.info(f"Storing Candle: {candle_data}")
    await ts.store_market_candle(candle_data)

    # 3. Verify in DB
    async with AsyncSessionLocal() as session:
        # Check Tick
        result = await session.execute(
            select(MarketTick).where(MarketTick.symbol == "BTC-EUR")
        )
        ticks = result.scalars().all()
        logger.info(f"Ticks in DB: {len(ticks)}")
        assert len(ticks) > 0

        # Check Candle
        result = await session.execute(
            select(MarketCandle).where(MarketCandle.symbol == "BTC-EUR")
        )
        candles = result.scalars().all()
        logger.info(f"Candles in DB: {len(candles)}")
        assert len(candles) > 0

    logger.info("Market Persistence Verified! ✅")


async def main():
    try:
        await test_memory_persistence()
        await test_market_persistence()
        logger.info("ALL TESTS PASSED 🚀")
    except Exception as e:
        logger.error(f"Test Failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
