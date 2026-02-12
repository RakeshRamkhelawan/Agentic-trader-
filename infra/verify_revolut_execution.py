
import asyncio
import logging
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from backend.services.execution_gateway import ExecutionGateway
from backend.core.config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("verify_revolut")

async def main():
    logger.info("--- Starting Revolut Gateway Verification (PAPER) ---")
    
    # Force PAPER mode for safety
    settings.TRADING_MODE = "paper"
    
    try:
        # Initialize Gateway for Revolut
        gateway = ExecutionGateway(exchange_id="revolut")
        await gateway.start()
        
        logger.info("Gateway Started. Attempting Mock Execution...")
        
        # Execute Mock Order
        result = await gateway.execute_order(
            symbol="BTC-USD", 
            side="buy", 
            amount=0.01, 
            order_type="market"
        )
        
        logger.info(f"Execution Result: {result}")
        
        if result["status"] == "closed" and "mock" in str(result["id"]):
            logger.info("✅ SUCCESS: Revolut Gateway handled mock order correctly.")
        else:
            logger.error("❌ FAILURE: Unexpected result structure.")
            
        await gateway.stop()
        
    except Exception as e:
        logger.error(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
