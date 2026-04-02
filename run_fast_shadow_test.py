import asyncio
import logging
from backend.services.real_paper_trading_v18_direct import RealPaperTradingV18
from backend.services.data_prefetch_agent import get_data_agent

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("CognitiveTest")

async def main():
    logger.info("Directly testing cognitive evaluate_entry...")
    engine = RealPaperTradingV18(initial_capital=5000)

    try:
        await engine.initialize()

        test_symbol = "BTC/EUR"

        logger.info(f"Fetching current market snapshot for {test_symbol}...")
        # Get live data bypassing the agent cache delay
        prices = await engine.data_agent.get_price_history(test_symbol, lookback=30)

        if not prices:
            logger.error("Failed to fetch live prices from exchange")
            return

        current_price = prices[-1].price
        price_history = [p.price for p in prices]

        logger.info(f"Current {test_symbol} price: €{current_price:,.2f}. Handing over to V18 Cognitive Engine...")

        # Fire the evaluation loop!
        decision_made = await engine._evaluate_entry(test_symbol, current_price, price_history)

        if decision_made:
            logger.info("V18 decided to BUY/ENTER!")
        else:
            logger.info("V18 decided to SKIP/HOLD.")

        print("\nReview backend/data/audit_logs/ for the JSON reasoning!")

    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
    finally:
        await engine.close()

if __name__ == "__main__":
    asyncio.run(main())
