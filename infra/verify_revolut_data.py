
import asyncio
import logging
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from backend.market_data.providers.revolut_provider import RevolutProvider
from backend.core.config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("verify_revolut_data")

async def main():
    logger.info("--- Starting Revolut Data Verification (Polling) ---")
    
    # Ensure keys are present or mock handles it
    # For now, if no keys, it might fail auth. 
    # But let's try.
    
    queue = asyncio.Queue()
    # Revolut X symbols usually BTC-USD
    provider = RevolutProvider(name="revolut_verifier", out_queue=queue, symbols=["BTC-USD", "ETH-USD"])
    
    # Start provider
    task = asyncio.create_task(provider.run_forever())
    
    try:
        logger.info("Waiting for data...")
        count = 0
        while count < 3:
            try:
                 item = await asyncio.wait_for(queue.get(), timeout=10.0)
                 logger.info(f"Received: {item['event_type']} {item['symbol']} @ {item['price']} (Venue: {item['venue']})")
                 count += 1
            except asyncio.TimeoutError:
                 logger.warning("Timeout waiting for polling data. Check API Keys/Connectivity.")
                 break
            
        if count > 0:
             logger.info("✅ SUCCESS: Received polling data from Revolut.")
        else:
             logger.warning("⚠️  WARNING: No data received. Might need real API Keys for polling.")
        
    except Exception as e:
        logger.error(f"❌ ERROR: {e}")
    finally:
        provider.stop()
        try:
            task.cancel()
            await task
        except asyncio.CancelledError:
            pass
        logger.info("Verification Complete.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
