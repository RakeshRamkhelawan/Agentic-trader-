"""
Async Cache Layer - High-performance Redis-based caching.
"""

import json
import logging
from typing import Any, Dict, List, Optional

import redis.asyncio as redis  # type: ignore[import-untyped]

from backend.core.config.settings import settings

logger = logging.getLogger(__name__)


class AsyncCacheLayer:
    """
    Asynchronous cache manager for the Agentic Trader Platform.
    Wraps Redis to provide typed access and standard patterns.
    """

    _instance: Optional["AsyncCacheLayer"] = None

    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or settings.REDIS_URL
        self.client: Optional[redis.Redis] = None

    @classmethod
    def get_instance(cls) -> "AsyncCacheLayer":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def connect(self):
        """Initialize Redis connection."""
        if not self.client:
            try:
                self.client = redis.from_url(self.redis_url, decode_responses=True)
                # Verify connection
                await self.client.ping()
                logger.info(f"Connected to Redis at {self.redis_url}")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self.client = None

    async def disconnect(self):
        """Close Redis connection."""
        if self.client:
            await self.client.aclose()
            self.client = None

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache and deserialize from JSON."""
        if not self.client:
            await self.connect()
        if not self.client:
            return None

        try:
            data = await self.client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.warning(f"Cache get failed for {key}: {e}")
        return None

    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in cache with TTL, serializing to JSON."""
        if not self.client:
            await self.connect()
        if not self.client:
            return

        try:
            serialized_value = json.dumps(value)
            await self.client.set(key, serialized_value, ex=ttl)
        except Exception as e:
            logger.warning(f"Cache set failed for {key}: {e}")

    async def delete(self, key: str):
        """Remove key from cache."""
        if not self.client:
            await self.connect()
        if not self.client:
            return

        try:
            await self.client.delete(key)
        except Exception as e:
            logger.warning(f"Cache delete failed for {key}: {e}")

    # --- Domain Specific Helpers ---

    async def get_tickers(self, source: str = "aggregator") -> Optional[Dict[str, Any]]:
        """Get cached tickers."""
        return await self.get(f"tickers:{source}")

    async def set_tickers(
        self, tickers: Dict[str, Any], source: str = "aggregator", ttl: int = 60
    ):
        """Cache tickers."""
        await self.set(f"tickers:{source}", tickers, ttl=ttl)

    async def get_instruments(self, exchange: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached instruments list for an exchange."""
        return await self.get(f"instruments:{exchange}")

    async def set_instruments(
        self, instruments: List[Dict[str, Any]], exchange: str, ttl: int = 3600
    ):
        """Cache instruments list."""
        await self.set(f"instruments:{exchange}", instruments, ttl=ttl)


# Global Accessor
def get_cache() -> AsyncCacheLayer:
    return AsyncCacheLayer.get_instance()
