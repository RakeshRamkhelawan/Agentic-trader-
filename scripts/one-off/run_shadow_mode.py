import asyncio
import logging
from datetime import datetime
from backend.services.real_paper_trading_v18_direct import RealPaperTradingV18

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ShadowModeRunner")

async def main():
    logger.info("Initializing Cognitive Shadow Mode Verification Run...")

    # Initialize engine with €5000 paper capital
    engine = RealPaperTradingV18(initial_capital=5000.0)

    try:
        await engine.initialize()

        # Override the active symbols to only a few known ones for the test run
        test_symbols = ["BTC/EUR", "ETH/EUR", "SOL/EUR"]
        logger.info(f"Forcing execution only on test symbols: {test_symbols}")

        # We monkey-patch the get_active_symbols method temporarily
        original_get_symbols = engine.data_agent.get_active_symbols
        def mock_get_symbols():
            return test_symbols
        engine.data_agent.get_active_symbols = mock_get_symbols

        # Run exactly 1 cycle (duration ~ 0 means it will run the while loop once if we break it,
        # but the engine uses sleep. Let's just call _execute_cycle directly for instant test!)
        logger.info("Starting a single forced cycle...")
        await engine._execute_cycle()

        logger.info("Shadow Mode Cycle Complete. Check the cognitive_logger files in data/audit_logs!")

    except Exception as e:
        logger.error(f"Shadow Mode Failed: {e}", exc_info=True)
    finally:
        await engine.close()
        logger.info("Engine closed.")

if __name__ == "__main__":
    asyncio.run(main())
