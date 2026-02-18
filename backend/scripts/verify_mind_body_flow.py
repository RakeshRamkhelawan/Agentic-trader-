import asyncio
import logging
import os
import sys
from unittest.mock import AsyncMock, MagicMock

# Add project root to path
sys.path.append(os.getcwd())

from backend.core.cognitive_mind_service import CognitiveMindService
from backend.core.config.settings import settings
from backend.core.eternal_soul_service import EternalSoulService
from backend.execution.reflex_executor import ReflexExecutor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("VerificationScript")


async def verify_flow():
    logger.info("--- Starting Mind-Body Flow Verification ---")

    # 0. Setup Redis Connection (Fallback Strategy)
    import redis.asyncio as redis

    redis_ports = [6379, 6380, 6381]
    connected = False

    for port in redis_ports:
        url = f"redis://localhost:{port}/0"
        try:
            r = redis.from_url(url, decode_responses=True)
            await r.ping()
            await r.close()
            settings.REDIS_URL = url  # Patch settings globally
            os.environ["REDIS_URL"] = url  # Patch for new Settings() instances
            logger.info(f"Verified Redis at {url}")
            connected = True
            break
        except Exception:
            pass

    if not connected:
        logger.error("Could not connect to Redis on any common port. Exiting.")
        return

    # 1. Initialize Services
    soul = EternalSoulService()
    mind = CognitiveMindService(shm_name="verify_intents_v2")
    body = ReflexExecutor(
        shm_name="verify_intents_v2", market_shm_name="market_data_v2"
    )

    # Define state classes before mocking
    class DummyGuna:
        def __init__(self, dominant):
            self.dominant_guna = dominant

    class DummyState:
        def __init__(self, rahu, consciousness, guna_str, gate):
            self.rahu_kala_active = rahu
            self.consciousness_level = consciousness
            self.guna_distribution = DummyGuna(guna_str)
            self.trading_gate_open = gate

    # 2. Setup normal state for mocking
    normal_state = DummyState(
        rahu=False, consciousness="Pure Awareness", guna_str="sattva", gate=True
    )

    # Mock Navagraha for Control
    # Use AsyncMock with explicit return_value for get_current_state
    mock_navagraha = MagicMock()
    mock_navagraha.get_current_state = AsyncMock(return_value=normal_state)
    soul.navagraha = mock_navagraha

    # 3. Start Services
    # We await start() to ensure resources are ready.
    # Note: soul.start() creates a background task.
    try:
        await soul.start()
    except Exception as e:
        logger.warning(f"Soul startup: {e}")

    try:
        await mind.start()
    except Exception as e:
        logger.warning(f"Mind startup: {e}")

    try:
        await body.start()
    except Exception as e:
        logger.warning(f"Body startup: {e}")

    try:
        # --- SCENARIO 1: NORMAL STATE ---
        logger.info("\n>>> SCENARIO 1: Normal State (Rahu Kala = False)")

        # Trigger Soul Cycle manually
        logger.info("Triggering Soul Cycle (Normal)...")
        if hasattr(soul, "process_cycle"):
            await soul.process_cycle()

        # Wait for propagation
        await asyncio.sleep(2)

        # --- SCENARIO 2: RAHU KALA (DEFENSIVE) ---
        logger.info("\n>>> SCENARIO 2: Rahu Kala Active (Rahu Kala = True)")

        # Setup Rahu Kala state
        rahu_state = DummyState(
            rahu=True, consciousness="Material Density", guna_str="tamas", gate=False
        )

        # Update mock to return rahu state
        mock_navagraha.get_current_state = AsyncMock(return_value=rahu_state)

        # Trigger Soul Cycle
        logger.info("Triggering Soul Cycle (Rahu Kala)...")
        if hasattr(soul, "process_cycle"):
            await soul.process_cycle()

        # Wait for propagation
        await asyncio.sleep(2)

        # --- SCENARIO 3: HIGH RISK TRADE (MIFID/GUNA CHECK) ---
        logger.info("\n>>> SCENARIO 3: High Risk Trade (Size > Limit)")

        # Reset to Normal State
        mock_navagraha.get_current_state = AsyncMock(return_value=normal_state)

        # Hack: Inject a High-Risk Strategy into Mind temporarily
        # We want to force the Mind to generate a huge order
        # Since logic is hardcoded in process_cycle, we can just observe if it *accepts* the normal one first.
        # To test rejection, we'd need to mock the strategy or chang params.
        # Let's verify the "Normal" trade above was logged with "Size=1.0000".
        # For this test, let's artificially set the max_loss_tolerance_pct to 0.0 in the profile to force rejection.
        original_tolerance = mind.profile.max_loss_tolerance_pct
        mind.profile.max_loss_tolerance_pct = 0.0  # Zero tolerance
        logger.info(
            "  [TEST] Set ClientProfile.max_loss_tolerance_pct = 0.0 to force rejection."
        )

        logger.info("Triggering Soul Cycle (Normal State + Zero Tolerance)...")
        if hasattr(soul, "process_cycle"):
            await soul.process_cycle()

        await asyncio.sleep(2)

        # Restore tolerance
        mind.profile.max_loss_tolerance_pct = original_tolerance
        logger.info("  [TEST] Restored ClientProfile tolerance.")

        # --- SCENARIO 4: VOLATILE REGIME ---
        logger.info("\n>>> SCENARIO 4: Volatile Regime Detection")

        # Populate Soul's price history with volatile data
        # Check if attribute exists (it might not if we failed prior edits, but we should have succeeded)
        if hasattr(soul, "price_history"):
            import random

            base_price = 45000.0
            # Generate 50 prices oscillating wildly
            volatile_history = []
            for i in range(
                200
            ):  # Need >50 for calculation (Soul needs 200 for SMA200 but Vol is 20)
                # +/- 5% swings
                swing = random.choice([-1, 1]) * random.uniform(0.03, 0.08)
                price = base_price * (1 + swing)
                volatile_history.append(price)

            soul.price_history = volatile_history
            logger.info(
                f"  [TEST] Injected {len(volatile_history)} volatile price points into Soul."
            )

            if hasattr(soul, "process_cycle"):
                await soul.process_cycle()

            await asyncio.sleep(2)
        else:
            logger.warning(
                "[TEST] SKIPPING Scenario 4: Soul does not have price_history attribute."
            )

        # --- SCENARIO 5: STRATEGY SWITCHING (BULL VS SIDEWAYS) ---
        logger.info("\n>>> SCENARIO 5: Strategy Switching")

        # 5A. Inject BULL Trend (Price > SMA50 > SMA200)
        # SMA200 needs 200 points.
        # Let's create a linear uptrend.
        logger.info("  [TEST] Injecting BULL Trend...")
        bull_history = [40000.0 + (i * 10) for i in range(250)]  # 40000 to 42500
        soul.price_history = bull_history

        if hasattr(soul, "process_cycle"):
            await soul.process_cycle()  # Should detect BULL -> Trend Strategy -> Size 1.0

        await asyncio.sleep(2)

        # 5B. Inject SIDEWAYS Trend (Price ~ SMA50)
        # Flat line
        logger.info("  [TEST] Injecting SIDEWAYS Trend...")
        sideways_history = [40000.0 for i in range(250)]
        soul.price_history = sideways_history

        # Force a small dip to trigger Mean Reversion Buy (-1.5%)
        # Strategy: Buy if < -1% deviation
        if hasattr(soul, "process_cycle"):
            # We need to manually tweak the "current_context" or ensuring fetch_market_context returns something relevant?
            # Actually, soul.process_cycle calls _fetch_market_context which currently does a random walk from last history.
            # If history is flat 40000, last is 40000. Next will be 40000 +/- 0.5%.
            # To force Mean Reversion BUY, we need price < SMA50 * 0.99.
            # Let's hack the history so the LAST item is the drop.
            soul.price_history[-1] = 39000.0  # Drop to 39k (SMA50 will be ~40k)

            await soul.process_cycle()  # Should detect SIDEWAYS -> MeanReversion -> Buy (Size 0.5)

        await asyncio.sleep(2)

    except Exception as e:
        logger.error(f"Verification Failed: {e}", exc_info=True)
    finally:
        logger.info("\n--- Stopping Services ---")
        await body.stop()
        await mind.stop()
        await soul.stop()


if __name__ == "__main__":
    try:
        asyncio.run(verify_flow())
    except KeyboardInterrupt:
        pass
