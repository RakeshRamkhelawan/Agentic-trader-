"""
High-performance caching layer for backtest operations.

Provides intelligent caching for:
- VedAstro calculations (expensive, deterministic)
- Market data (time-series, batch-friendly)
- Elemental consensus results (reusable across symbols)
"""

import asyncio
import hashlib
import json
import logging
import pickle
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)

# Try to import Redis, fallback to memory cache
try:
    from redis.asyncio import Redis
    from redis.asyncio.connection import ConnectionPool

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis-py not available, using memory cache only")


@dataclass
class CacheConfig:
    """Configuration for caching behavior."""

    vedastro_ttl_seconds: int = 3600  # 1 hour for VedAstro
    market_data_ttl_seconds: int = 300  # 5 minutes for market data
    consensus_ttl_seconds: int = 60  # 1 minute for consensus
    max_memory_entries: int = 10000  # Max in-memory cache size
    enable_redis: bool = True
    # Read from environment variable, fallback to localhost
    redis_url: str = None
    compression: bool = True

    def __post_init__(self):
        """Initialize redis_url from environment if not provided."""
        import os

        if self.redis_url is None:
            self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")


class MemoryCache:
    """Thread-safe in-memory cache with LRU eviction."""

    def __init__(self, max_size: int = 10000):
        self._cache: dict[str, Any] = {}
        self._timestamps: dict[str, datetime] = {}
        self._access_order: list[str] = []
        self._max_size = max_size
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            if key in self._cache:
                # Update access order
                if key in self._access_order:
                    self._access_order.remove(key)
                self._access_order.append(key)
                return self._cache[key]
            return None

    async def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        async with self._lock:
            # Evict oldest if at capacity
            while len(self._cache) >= self._max_size:
                if self._access_order:
                    oldest = self._access_order.pop(0)
                    self._cache.pop(oldest, None)
                    self._timestamps.pop(oldest, None)

            self._cache[key] = value
            self._timestamps[key] = datetime.now()
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._cache.pop(key, None)
            self._timestamps.pop(key, None)
            if key in self._access_order:
                self._access_order.remove(key)

    async def clear(self) -> None:
        async with self._lock:
            self._cache.clear()
            self._timestamps.clear()
            self._access_order.clear()

    async def get_stats(self) -> dict[str, Any]:
        async with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self._max_size,
                "utilization": len(self._cache) / self._max_size,
            }


class BacktestCache:
    """
    High-performance caching system for backtest operations.

    Features:
    - Two-tier caching (memory + Redis)
    - Automatic serialization with compression
    - Cache key hashing for efficient lookup
    - TTL-based expiration
    - Docker-compatible Redis connection handling
    """

    def __init__(self, config: CacheConfig | None = None):
        self.config = config or CacheConfig()
        self._memory = MemoryCache(self.config.max_memory_entries)
        self._redis: Any | None = None
        self._redis_connected = False

        if REDIS_AVAILABLE and self.config.enable_redis:
            self._init_redis()

    def _init_redis(self):
        """Initialize Redis connection with Docker-compatible settings."""
        try:
            # Parse URL to get connection details
            import urllib.parse

            parsed = urllib.parse.urlparse(self.config.redis_url)

            host = parsed.hostname or "localhost"
            port = parsed.port or 6379
            db = int(parsed.path.lstrip("/")) if parsed.path else 0
            password = parsed.password

            logger.info(f"Initializing Redis connection to {host}:{port}/{db}")

            # Create connection pool with Docker-compatible settings
            # Key fixes for Docker networking issues:
            # 1. socket_keepalive=False (prevents connection issues)
            # 2. socket_connect_timeout (prevents hanging)
            # 3. health_check_interval=0 (disables health checks that can cause issues)
            # 4. retry_on_timeout=True
            # 5. socket_keepalive_options={} (empty to avoid TCP keepalive issues)

            pool = ConnectionPool(
                host=host,
                port=port,
                db=db,
                password=password,
                socket_keepalive=False,
                socket_connect_timeout=5,
                socket_timeout=5,
                health_check_interval=0,
                retry_on_timeout=True,
                retry_on_error=[ConnectionError, TimeoutError],
                max_connections=10,
            )

            self._redis = Redis(connection_pool=pool)
            logger.info("Redis client initialized successfully")

        except Exception as e:
            logger.warning(f"Redis initialization failed: {e}, will use memory cache")
            self._redis = None

    async def connect(self) -> bool:
        """Connect to Redis if available."""
        if self._redis and not self._redis_connected:
            try:
                # Use a timeout to prevent hanging
                await asyncio.wait_for(self._redis.ping(), timeout=3.0)
                self._redis_connected = True
                logger.info("Redis connection established successfully")
            except asyncio.TimeoutError:
                logger.warning("Redis connection timed out, using memory cache")
                self._redis_connected = False
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}, using memory cache")
                self._redis_connected = False
                # Close the connection pool to clean up
                try:
                    await self._redis.close()
                except:
                    pass
                self._redis = None

        return self._redis_connected

    def _generate_key(self, prefix: str, params: dict[str, Any]) -> str:
        """Generate deterministic cache key from parameters."""
        # Sort keys for deterministic hashing
        param_str = json.dumps(params, sort_keys=True, default=str)
        hash_val = hashlib.blake2b(param_str.encode(), digest_size=8).hexdigest()
        return f"{prefix}:{hash_val}"

    def _serialize(self, value: Any) -> bytes:
        """Serialize value to bytes with optional compression."""
        data = pickle.dumps(value)
        if self.config.compression:
            try:
                import zlib

                return zlib.compress(data)
            except ImportError:
                pass
        return data

    def _deserialize(self, data: bytes) -> Any:
        """Deserialize bytes to value with optional decompression."""
        if self.config.compression:
            try:
                import zlib

                data = zlib.decompress(data)
            except Exception:
                pass  # Wasn't compressed
        return pickle.loads(data)  # nosec B301 - Internal cache only

    async def get(self, prefix: str, params: dict[str, Any]) -> Any | None:
        """Get cached value with two-tier lookup."""
        key = self._generate_key(prefix, params)

        # Try memory first
        value = await self._memory.get(key)
        if value is not None:
            return value

        # Try Redis second (only if connected)
        if self._redis_connected and self._redis:
            try:
                data = await self._redis.get(key)
                if data:
                    value = self._deserialize(data)
                    # Promote to memory cache
                    await self._memory.set(key, value)
                    return value
            except Exception as e:
                logger.debug(f"Redis get failed: {e}")
                # Don't mark as disconnected for single failures

        return None

    async def set(
        self, prefix: str, params: dict[str, Any], value: Any, ttl_seconds: int = 300
    ) -> None:
        """Set cached value in both tiers."""
        key = self._generate_key(prefix, params)

        # Always set in memory
        await self._memory.set(key, value, ttl_seconds)

        # Set in Redis if connected
        if self._redis_connected and self._redis:
            try:
                data = self._serialize(value)
                await self._redis.setex(key, ttl_seconds, data)
            except Exception as e:
                logger.debug(f"Redis set failed: {e}")

    async def invalidate(self, prefix: str, params: dict[str, Any] | None = None) -> int:
        """Invalidate cached entries."""
        if params is not None:
            # Invalidate specific entry
            key = self._generate_key(prefix, params)
            await self._memory.delete(key)
            if self._redis_connected and self._redis:
                try:
                    await self._redis.delete(key)
                except Exception:
                    pass
            return 1
        else:
            # Invalidate all entries with prefix
            if self._redis_connected and self._redis:
                try:
                    pattern = f"{prefix}:*"
                    keys = await self._redis.keys(pattern)
                    if keys:
                        await self._redis.delete(*keys)
                        return len(keys)
                except Exception:
                    pass
            return 0

    async def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        memory_stats = await self._memory.get_stats()
        redis_stats = {"connected": self._redis_connected}

        if self._redis_connected and self._redis:
            try:
                info = await self._redis.info()
                redis_stats["used_memory_human"] = info.get("used_memory_human", "N/A")
                redis_stats["connected_clients"] = info.get("connected_clients", 0)
            except Exception:
                pass

        return {
            "memory": memory_stats,
            "redis": redis_stats,
        }


# Decorator for cached functions
def cached(prefix: str, ttl_seconds: int = 300):
    """Decorator to cache function results."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache()

            # Generate cache key from function name and arguments
            cache_params = {
                "func": func.__name__,
                "args": str(args),
                "kwargs": str(sorted(kwargs.items())),
            }

            # Try to get from cache
            cached_value = await cache.get(prefix, cache_params)
            if cached_value is not None:
                return cached_value

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache
            await cache.set(prefix, cache_params, result, ttl_seconds)

            return result

        return wrapper

    return decorator


# Specific cache decorators
def cached_vedastro_calculation(ttl_seconds: int = 3600):
    """Cache decorator for VedAstro calculations."""
    return cached("vedastro", ttl_seconds)


def cached_market_data(ttl_seconds: int = 300):
    """Cache decorator for market data."""
    return cached("market_data", ttl_seconds)


# Global cache instance
_cache_instance: BacktestCache | None = None


def get_cache() -> BacktestCache:
    """Get global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = BacktestCache()
    return _cache_instance


def reset_cache() -> None:
    """Reset global cache instance."""
    global _cache_instance
    _cache_instance = None
