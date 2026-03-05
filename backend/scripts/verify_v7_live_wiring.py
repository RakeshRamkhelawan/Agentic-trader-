import asyncio
import logging
import sys
import os
from datetime import datetime, UTC
from unittest.mock import MagicMock, AsyncMock

# Ensure root directory is in path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(root_dir)

# Setup logging to see our filters in action
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("VerificationV7")

# Mock Redis to avoid connection errors
import redis.asyncio as redis
redis.from_url = MagicMock(return_value=AsyncMock())

from backend.core.eternal_soul_service import EternalSoulService
from backend.core.cognitive_mind_service import CognitiveMindService
from backend.execution.reflex_executor import ReflexExecutor
from backend.core.zero_copy_bridge import TradingIntent

async def verify_v7_wiring():
    logger.info("Starting V7 Live Wiring Verification...")

    # 1. Test Layer 1: Eternal Soul (Guna analysis)
    logger.info("\n--- TEST LAYER 1: Eternal Soul ---")
    soul = EternalSoulService()
    # Mock price history to ensure indicators work
    soul.price_history = [40000.0 + i*10 for i in range(250)]
    
    # Execute cycle
    soul_context = await soul.process_cycle()
    
    logger.info(f"Dominant Guna: {soul_context['guna_dominance']}")
    logger.info(f"Market Guna Vector: {soul_context['market_guna']}")
    assert "market_guna" in soul_context, "Market Guna missing from soul context"
    assert "cosmic_guna" in soul_context, "Cosmic Guna missing from soul context"

    # 2. Test Layer 2: Cognitive Mind (Viveka Filter)
    logger.info("\n--- TEST LAYER 2: Cognitive Mind ---")
    mind = CognitiveMindService()
    mind.redis_client = AsyncMock()
    mind.bridge = MagicMock()
    
    # Scenario A: Clear signal (Sattvic)
    soul_context["guna_dominance"] = "sattva"
    soul_context["market_metrics"]["volatility"] = 0.01
    await mind.process_cycle(soul_context=soul_context)
    
    # Scenario B: Maya (Rajasic/High Vol) - Should trigger Viveka reject
    logger.info("\n--- Testing Viveka Reject (Maya) ---")
    soul_context["guna_dominance"] = "rajas"
    soul_context["market_metrics"]["volatility"] = 0.08 # High vol
    await mind.process_cycle(soul_context=soul_context)

    # 3. Test Layer 3: Reflex Body (Shiva-Shakti Sync)
    logger.info("\n--- TEST LAYER 3: Reflex Body ---")
    executor = ReflexExecutor(trading_mode="paper")
    executor.market_bridge = MagicMock()
    
    # Mock intent
    intent = TradingIntent(
        action=1, # BUY
        size=0.1,
        confidence=0.8,
        stop_loss=39000.0,
        take_profit=42000.0,
        max_hold_ms=3600000,
        entry_price=40000.0,
        timestamp_ns=0 # Stale but we'll bypass check
    )
    
    # Mock market data for Spanda check
    executor.market_bridge.read_market_data.return_value = {
        "last": 40000.0,
        "volatility": 0.09 # High vibration (Disharmony)
    }
    
    # Simulate the sync check
    pnl = -5000.0 # 50% drawdown
    equity = 5000.0
    sync = executor.synchronizer.calculate_sync(
        strategy_pnl=pnl,
        market_vol=0.15, # 15% vol (Extreem)
        current_equity=equity
    )
    
    logger.info(f"Shiva-Shakti Harmony: {sync['harmony_level']}")
    logger.info(f"Sync Factor: {sync['sync_factor']}")
    logger.info(f"Advice: {sync['action_advice']}")
    
    if sync["harmony_level"] == "low":
        logger.info("VERIFICATION SUCCESS: Extreme conditions correctly detected disharmony.")
    else:
        logger.error(f"VERIFICATION FAILED: Harmony is {sync['harmony_level']}, expected 'low'")

    logger.info("\nVerification Complete.")

if __name__ == "__main__":
    asyncio.run(verify_v7_wiring())
