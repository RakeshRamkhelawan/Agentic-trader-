
import asyncio
import logging
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("verify_bybit_eu")

async def main():
    logger.info("--- Verifying Bybit EU Config ---")
    
    try:
        # Import settings singleton
        from backend.core.config.settings import settings
        from backend.services.execution_gateway import ExecutionGateway

        # Manual Override
        logger.info(f"Original BYBIT_USE_EU: {getattr(settings, 'BYBIT_USE_EU', 'MISSING')}")
        settings.BYBIT_USE_EU = True
        settings.TRADING_MODE = "paper"
        logger.info(f"Overridden BYBIT_USE_EU: {settings.BYBIT_USE_EU}")
        
        gateway = ExecutionGateway(exchange_id="bybit")
        await gateway.start()
        
        if gateway.exchange:
            # Check hostname in options or direct attribute depending on CCXT
            # ccxt instances usually have .hostname
            hostname = getattr(gateway.exchange, 'hostname', None)
            # OR check urls
            api_url = gateway.exchange.urls['api'].get('public') if gateway.exchange.urls else "N/A"
            
            logger.info(f"Exchange Hostname: {hostname}")
            logger.info(f"Exchange API URL: {api_url}")
            
            success = False
            if hostname == 'bybit.eu':
                success = True
            elif 'bybit.eu' in str(api_url):
                 success = True
                 
            if success:
                logger.info("✅ SUCCESS: ExecutionGateway configured for Bybit EU.")
            else:
                logger.error(f"❌ FAILURE: Hostname is {hostname}, expected 'bybit.eu'")
        else:
            logger.error("❌ FAILURE: Exchange not initialized.")
            
        await gateway.stop()
        
    except Exception as e:
        logger.error(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
