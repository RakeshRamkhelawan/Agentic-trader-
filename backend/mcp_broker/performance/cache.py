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
import pickle
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from functools import wraps
from typing import Any

# Try to import Redis, fallback to memory cache
try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


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
    """

    def __init__(self, config: CacheConfig | None = None):
        self.config = config or CacheConfig()
        self._memory = MemoryCache(self.config.max_memory_entries)
        self._redis: Any | None = None
        self._redis_connected = False

        if REDIS_AVAILABLE and self.config.enable_redis:
            try:
                self._redis = redis.from_url(
                    self.config.redis_url, encoding="utf-8", decode_responses=False
                )
            except Exception:
                pass  # Fallback to memory only

    async def connect(self) -> bool:
        """Connect to Redis if available."""
        if self._redis and not self._redis_connected:
            try:
                await self._redis.ping()
                self._redis_connected = True
            except Exception:
                self._redis_connected = False
        return self._redis_connected

    def _generate_key(self, prefix: str, params: dict[str, Any]) -> str:
        """Generate deterministic cache key from parameters."""
        # Sort keys for deterministic hashing
        param_str = json.dumps(params, sort_keys=True, default=str)
        hash_val = hashlib.md5(param_str.encode()).hexdigest()[:16]
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
        return pickle.loads(data)

    async def get(self, prefix: str, params: dict[str, Any]) -> Any | None:
        """Get cached value with two-tier lookup."""
        key = self._generate_key(prefix, params)

        # Try memory first
        value = await self._memory.get(key)
        if value is not None:
            return value

        # Try Redis second
        if self._redis_connected:
            try:
                data = await self._redis.get(key)
                if data:
                    value = self._deserialize(data)
                    # Promote to memory cache
                    await self._memory.set(key, value)
                    return value
            except Exception:
                pass

        return None

    async def set(
        self, prefix: str, params: dict[str, Any], value: Any, ttl_seconds: int = 300
    ) -> None:
        """Set cached value in both tiers."""
        key = self._generate_key(prefix, params)

        # Set in memory
        await self._memory.set(key, value, ttl_seconds)

        # Set in Redis
        if self._redis_connected:
            try:
                data = self._serialize(value)
                await self._redis.setex(key, ttl_seconds, data)
            except Exception:
                pass

    async def get_vedastro_signal(
        self, symbol: str, date: datetime, params: dict | None = None
    ) -> dict | None:
        """Cached VedAstro signal lookup."""
        cache_params = {"symbol": symbol, "date": date.strftime("%Y-%m-%d"), **(params or {})}
        return await self.get("vedastro", cache_params)

    async def set_vedastro_signal(
        self, symbol: str, date: datetime, result: dict, params: dict | None = None
    ) -> None:
        """Cache VedAstro signal result."""
        cache_params = {"symbol": symbol, "date": date.strftime("%Y-%m-%d"), **(params or {})}
        await self.set("vedastro", cache_params, result, self.config.vedastro_ttl_seconds)

    async def get_market_data(
        self, symbol: str, start_date: datetime, end_date: datetime, interval: str = "1d"
    ) -> list[dict] | None:
        """Cached market data lookup."""
        cache_params = {
            "symbol": symbol,
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d"),
            "interval": interval,
        }
        return await self.get("market_data", cache_params)

    async def set_market_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        data: list[dict],
        interval: str = "1d",
    ) -> None:
        """Cache market data."""
        cache_params = {
            "symbol": symbol,
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d"),
            "interval": interval,
        }
        await self.set("market_data", cache_params, data, self.config.market_data_ttl_seconds)

    async def get_elemental_consensus(
        self, elemental_scores: dict[str, float], date: datetime
    ) -> dict | None:
        """Cached Elemental consensus lookup."""
        cache_params = {
            "scores": json.dumps(elemental_scores, sort_keys=True),
            "date": date.strftime("%Y-%m-%d"),
        }
        return await self.get("elemental_consensus", cache_params)

    async def set_elemental_consensus(
        self, elemental_scores: dict[str, float], date: datetime, result: dict
    ) -> None:
        """Cache Elemental consensus result."""
        cache_params = {
            "scores": json.dumps(elemental_scores, sort_keys=True),
            "date": date.strftime("%Y-%m-%d"),
        }
        await self.set(
            "elemental_consensus", cache_params, result, self.config.consensus_ttl_seconds
        )

    async def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        memory_stats = await self._memory.get_stats()
        redis_stats = {"connected": self._redis_connected}

        if self._redis_connected:
            try:
                info = await self._redis.info("memory")
                redis_stats["used_memory_mb"] = info.get("used_memory", 0) / (1024 * 1024)
                redis_stats["keys"] = await self._redis.dbsize()
            except Exception as e:
                redis_stats["error"] = str(e)

        return {"memory": memory_stats, "redis": redis_stats}

    async def clear(self) -> None:
        """Clear all caches."""
        await self._memory.clear()
        if self._redis_connected:
            try:
                await self._redis.flushdb()
            except Exception:
                pass


# Decorator helpers for easy caching


def cached_vedastro_calculation(cache: BacktestCache):
    """Decorator to cache VedAstro calculations."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(symbol: str, date: datetime, **kwargs) -> dict:
            # Try cache first
            cached = await cache.get_vedastro_signal(symbol, date, kwargs)
            if cached is not None:
                return cached

            # Execute and cache
            result = await func(symbol, date, **kwargs)
            await cache.set_vedastro_signal(symbol, date, result, kwargs)
            return result

        return wrapper

    return decorator


def cached_market_data(cache: BacktestCache):
    """Decorator to cache market data fetches."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            symbol: str, start_date: datetime, end_date: datetime, interval: str = "1d"
        ) -> list[dict]:
            # Try cache first
            cached = await cache.get_market_data(symbol, start_date, end_date, interval)
            if cached is not None:
                return cached

            # Execute and cache
            result = await func(symbol, start_date, end_date, interval)
            await cache.set_market_data(symbol, start_date, end_date, result, interval)
            return result

        return wrapper

    return decorator


# Global cache instance
_global_cache: BacktestCache | None = None


def get_cache(config: CacheConfig | None = None) -> BacktestCache:
    """Get or create global cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = BacktestCache(config)
    return _global_cache
