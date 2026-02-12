
import asyncio
import logging
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from backend.market_data.providers.bybit_provider import BybitProvider

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("verify_bybit")

async def main():
    logger.info("--- Starting Bybit Live Data Verification ---")
    
    queue = asyncio.Queue()
    provider = BybitProvider(name="bybit_verifier", out_queue=queue, symbols=["BTC/USDT", "ETH/USDT"])
    
    # Start provider in background
    task = asyncio.create_task(provider.run_forever())
    
    try:
        logger.info("Waiting for data...")
        count = 0
        while count < 5:
            item = await asyncio.wait_for(queue.get(), timeout=10.0)
            logger.info(f"Received: {item['event_type']} {item['symbol']} @ {item['price']} (Venue: {item['venue']})")
            count += 1
            
        logger.info("✅ SUCCESS: Received 5 live events from Bybit.")
        
    except asyncio.TimeoutError:
        logger.error("❌ FAILED: Timed out waiting for data.")
    except Exception as e:
        logger.error(f"❌ ERROR: {e}")
    finally:
        provider.stop()
        await task
        logger.info("Verification Complete.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
