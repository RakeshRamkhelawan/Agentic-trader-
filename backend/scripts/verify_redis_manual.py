import asyncio
import json
import logging
# Add project root to path
import os
import sys
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

sys.path.append(os.getcwd())

import redis.asyncio as redis

from backend.core.config.settings import settings
from backend.core.eternal_soul_service import EternalSoulService
from backend.core.navagraha.models import (GunaDistribution, NavagrahaState,
                                           PlanetName, PlanetState)
from backend.core.schemas.ooda_types import MarketRegime

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def verify_redis_updates():
    logger.info("--- Starting Manual Redis Verification ---")

    # 1. Connect to Real Redis
    logger.info(f"Connecting to Redis at {settings.REDIS_URL}...")
    redis_client = None

    # List of URLs to try if the default fails
    urls_to_try = [
        settings.REDIS_URL,
        settings.REDIS_URL.replace("localhost", "127.0.0.1"),
        "redis://127.0.0.1:6379/0",
        "redis://localhost:6379/0",
    ]

    for url in urls_to_try:
        try:
            logger.info(f"Attempting connection to {url}...")
            client = redis.from_url(url, decode_responses=True)
            await client.ping()
            logger.info(f"Successfully connected to Redis at {url}")
            redis_client = client
            break
        except Exception as e:
            logger.warning(f"Failed to connect to {url}: {e}")
            await client.close()

    if not redis_client:
        logger.error("Could not connect to any Redis instance.")
        logger.error("Please ensure Redis is running via Docker or locally.")
        return

    # 2. Setup Eternal Soul Service with Mocks
    logger.info("Initializing Eternal Soul Service...")
    soul_service = EternalSoulService()

    # Mock Dependencies to avoid external calls
    soul_service.navagraha = AsyncMock()
    soul_service.regime_detector = MagicMock()  # Not async - detect() is synchronous

    # Mock Navagraha Return
    now = datetime.now(timezone.utc)

    from pydantic import ValidationError

    try:

        def create_planet(name):
            try:
                # Defaults
                speed = 1.0
                is_retro = False
                lon = 0.0

                # Adjust for nodes
                if name in (PlanetName.RAHU, PlanetName.KETU):
                    speed = -0.1
                    is_retro = True
                    if name == PlanetName.RAHU:
                        lon = 180.0

                return PlanetState(
                    name=name,
                    longitude=lon,
                    latitude=0.0,
                    speed=speed,
                    is_retrograde=is_retro,
                    calculated_at=now,
                )
            except Exception as e:
                logger.error(f"Error creating planet {name}: {e}")
                raise

        mock_planets = {name: create_planet(name) for name in PlanetName}

        mock_state = NavagrahaState(
            planets=mock_planets,
            rahu_kala_active=True,
            guna_distribution=GunaDistribution(
                sattva=0.33, rajas=0.33, tamas=0.34, calculated_at=now
            ),
            calculated_at=now,
            location_lat=28.6139,
            location_lon=77.2090,
        )
        soul_service.navagraha.get_current_state.return_value = mock_state
    except ValidationError as e:
        logger.error(f"Validation Error creating mock state: {e}")
        # Print errors
        for error in e.errors():
            logger.error(f"Field: {error['loc']}, Error: {error['msg']}")
        return
    except Exception as e:
        logger.error(f"Error creating mock state: {e}")
        return

    # Mock Regime Return
    soul_service.regime_detector.detect.return_value = MarketRegime.VOLATILE

    # Inject real Redis client to avoid connection issues
    soul_service.redis_client = redis_client
    soul_service.running = True

    try:
        # 3. Trigger a Cycle
        logger.info("Triggering a cosmic cycle...")
        await soul_service.process_cycle()

        # 4. Verify Redis Content
        logger.info("Reading 'soul:context' from Redis...")
        context_json = await redis_client.get("soul:context")

        if context_json:
            context = json.loads(context_json)
            logger.info(f"Received Context: {json.dumps(context, indent=2)}")

            # Assertions
            if context.get("rahu_kala_active") is True:
                logger.info("✅ SUCCESS: Rahu Kala status (True) correctly persisted.")
            else:
                logger.error("❌ FAILURE: Rahu Kala status mismatch.")

            if context.get("market_regime") == "VOLATILE":
                logger.info("✅ SUCCESS: Market Regime (VOLATILE) correctly persisted.")
            else:
                logger.error(
                    f"❌ FAILURE: Market Regime mismatch. Got: {context.get('market_regime')}"
                )

            # Check TTL
            ttl = await redis_client.ttl("soul:context")
            logger.info(f"Key TTL: {ttl} seconds")
            if ttl > 0:
                logger.info("✅ SUCCESS: TTL is set.")
            else:
                logger.error("❌ FAILURE: TTL not set or key expired.")

        else:
            logger.error("❌ FAILURE: Key 'soul:context' not found in Redis.")

    finally:
        await soul_service.stop()
        await redis_client.close()
        logger.info("--- Verification Complete ---")


if __name__ == "__main__":
    try:
        asyncio.run(verify_redis_updates())
    except KeyboardInterrupt:
        pass
