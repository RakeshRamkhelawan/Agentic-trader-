
import asyncio
import logging
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from backend.market_data.providers.kraken_provider import KrakenProvider
from backend.market_data.models import UnifiedMarketEvent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("verify_kraken")

async def main():
    logger.info("--- Starting Kraken Live Data Verification ---")
    
    # Create Queue
    out_queue = asyncio.Queue()
    
    # Initialize Provider
    provider = KrakenProvider("kraken_test", out_queue=out_queue, symbols=["BTC/USD", "ETH/USD"])
    
    # Start Provider Task
    provider_task = asyncio.create_task(provider.run_forever())
    
    logger.info("Provider started. Waiting for data...")
    
    try:
        # Collect 5 events
        for i in range(5):
            try:
                # Wait for event with timeout
                event_dict = await asyncio.wait_for(out_queue.get(), timeout=10.0)
                
                # Check if it's a valid UnifiedMarketEvent dict
                # We can try to reconstruct it or just print it
                logger.info(f"✅ Received Event {i+1}: {event_dict['event_type']} {event_dict['symbol']} @ {event_dict.get('price') or event_dict.get('bid')}")
                # logger.debug(event_dict)
                
            except asyncio.TimeoutError:
                logger.error("❌ Timeout waiting for data from Kraken!")
                break
                
        logger.info("Verification Complete.")
        
    except Exception as e:
        logger.error(f"Verification Failed: {e}")
    finally:
        provider.stop()
        # Wait a bit for cleanup
        await asyncio.sleep(1)
        provider_task.cancel()
        try:
            await provider_task
        except asyncio.CancelledError:
            pass

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
