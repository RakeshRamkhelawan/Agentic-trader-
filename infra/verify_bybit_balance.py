
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
logger = logging.getLogger("verify_bybit_balance")

async def main():
    logger.info("--- Verifying Bybit Wallet Balance ---")
    
    # Ensure Live Mode if checking real balance, or Paper for mock
    # settings.TRADING_MODE = "live" # Forced live check for verification
    
    try:
        gateway = ExecutionGateway(exchange_id="bybit")
        await gateway.start()
        
        logger.info(f"Gateway Mode: {gateway.trading_mode}")
        logger.info(f"Exchange Hostname: {getattr(gateway.exchange, 'hostname', 'Default')}")
        
        balance = await gateway.get_balance()
        logger.info(f"Wallet Balance: {balance}")
        
        await gateway.stop()
        
    except Exception as e:
        logger.error(f"❌ ERROR: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
