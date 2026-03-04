"""Redis caching implementation for competitions."""

import json
from collections.abc import Callable
from datetime import datetime, timedelta
from functools import wraps
from typing import Any


# Mock Redis for development - replace with actual redis-py in production
class MockRedis:
    """Mock Redis client for development."""

    def __init__(self):
        self._data: dict[str, tuple] = {}  # key -> (value, expiry)

    def get(self, key: str) -> bytes | None:
        """Get value from cache."""
        if key in self._data:
            value, expiry = self._data[key]
            if expiry is None or datetime.utcnow() < expiry:
                return value
            else:
                del self._data[key]
        return None

    def set(
        self,
        key: str,
        value: bytes,
        ex: int | None = None,
    ) -> bool:
        """Set value in cache with optional expiry (seconds)."""
        expiry = datetime.utcnow() + timedelta(seconds=ex) if ex else None
        self._data[key] = (value, expiry)
        return True

    def delete(self, key: str) -> int:
        """Delete key from cache."""
        if key in self._data:
            del self._data[key]
            return 1
        return 0

    def keys(self, pattern: str) -> list[str]:
        """Get keys matching pattern."""
        import fnmatch

        return [k for k in self._data.keys() if fnmatch.fnmatch(k, pattern)]

    def flushall(self) -> bool:
        """Clear all cache."""
        self._data.clear()
        return True

    def exists(self, key: str) -> int:
        """Check if key exists."""
        return 1 if key in self._data else 0

    def ttl(self, key: str) -> int:
        """Get remaining TTL for key."""
        if key in self._data:
            value, expiry = self._data[key]
            if expiry:
                remaining = (expiry - datetime.utcnow()).total_seconds()
                return int(remaining)
            return -1  # No expiry
        return -2  # Key doesn't exist


class RedisCache:
    """
    Redis cache manager for competition data.

    Provides:
    - Leaderboard caching with automatic invalidation
    - Tournament data caching
    - User profile caching
    - Strategy listing caching
    """

    # Default TTLs (seconds)
    TTL_LEADERBOARD = 60  # 1 minute
    TTL_TOURNAMENT = 300  # 5 minutes
    TTL_USER_PROFILE = 600  # 10 minutes
    TTL_STRATEGY_LIST = 300  # 5 minutes
    TTL_ANALYTICS = 300  # 5 minutes
    TTL_CHAT = 60  # 1 minute

    def __init__(self):
        self._redis = MockRedis()  # Replace with redis.Redis() in production

    def _serialize(self, value: Any) -> bytes:
        """Serialize value to bytes using JSON (safe, no code execution)."""
        return json.dumps(value, default=str).encode("utf-8")

    def _deserialize(self, value: bytes) -> Any:
        """Deserialize bytes to value using JSON (safe, no code execution)."""
        return json.loads(value.decode("utf-8"))

    def get(self, key: str) -> Any | None:
        """Get value from cache."""
        value = self._redis.get(key)
        if value:
            return self._deserialize(value)
        return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> bool:
        """Set value in cache with optional TTL."""
        serialized = self._serialize(value)
        return self._redis.set(key, serialized, ex=ttl)

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        return self._redis.delete(key) > 0

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern."""
        keys = self._redis.keys(pattern)
        for key in keys:
            self._redis.delete(key)
        return len(keys)

    # Leaderboard caching
    def get_leaderboard(self, tier: str | None = None) -> list[dict] | None:
        """Get cached leaderboard."""
        key = f"leaderboard:{tier or 'global'}"
        return self.get(key)

    def set_leaderboard(
        self,
        data: list[dict],
        tier: str | None = None,
    ) -> bool:
        """Cache leaderboard."""
        key = f"leaderboard:{tier or 'global'}"
        return self.set(key, data, ttl=self.TTL_LEADERBOARD)

    def invalidate_leaderboard(self, tier: str | None = None) -> bool:
        """Invalidate leaderboard cache."""
        if tier:
            return self.delete(f"leaderboard:{tier}")
        else:
            return self.invalidate_pattern("leaderboard:*") > 0

    # Tournament caching
    def get_tournament(self, tournament_id: str) -> dict | None:
        """Get cached tournament data."""
        key = f"tournament:{tournament_id}"
        return self.get(key)

    def set_tournament(self, tournament_id: str, data: dict) -> bool:
        """Cache tournament data."""
        key = f"tournament:{tournament_id}"
        return self.set(key, data, ttl=self.TTL_TOURNAMENT)

    def invalidate_tournament(self, tournament_id: str) -> bool:
        """Invalidate tournament cache."""
        return self.delete(f"tournament:{tournament_id}")

    # User profile caching
    def get_user_profile(self, user_id: str) -> dict | None:
        """Get cached user profile."""
        key = f"user_profile:{user_id}"
        return self.get(key)

    def set_user_profile(self, user_id: str, data: dict) -> bool:
        """Cache user profile."""
        key = f"user_profile:{user_id}"
        return self.set(key, data, ttl=self.TTL_USER_PROFILE)

    def invalidate_user_profile(self, user_id: str) -> bool:
        """Invalidate user profile cache."""
        return self.delete(f"user_profile:{user_id}")

    # Strategy caching
    def get_strategy_list(self, query_hash: str) -> list[dict] | None:
        """Get cached strategy list."""
        key = f"strategy_list:{query_hash}"
        return self.get(key)

    def set_strategy_list(self, query_hash: str, data: list[dict]) -> bool:
        """Cache strategy list."""
        key = f"strategy_list:{query_hash}"
        return self.set(key, data, ttl=self.TTL_STRATEGY_LIST)

    def invalidate_strategy_list(self) -> int:
        """Invalidate all strategy list caches."""
        return self.invalidate_pattern("strategy_list:*")

    # Analytics caching
    def get_analytics(self, competitor_id: str, period: str) -> dict | None:
        """Get cached analytics."""
        key = f"analytics:{competitor_id}:{period}"
        return self.get(key)

    def set_analytics(
        self,
        competitor_id: str,
        period: str,
        data: dict,
    ) -> bool:
        """Cache analytics."""
        key = f"analytics:{competitor_id}:{period}"
        return self.set(key, data, ttl=self.TTL_ANALYTICS)

    # Chat caching
    def get_chat_history(self, tournament_id: str) -> list[dict] | None:
        """Get cached chat history."""
        key = f"chat:{tournament_id}"
        return self.get(key)

    def set_chat_history(self, tournament_id: str, data: list[dict]) -> bool:
        """Cache chat history."""
        key = f"chat:{tournament_id}"
        return self.set(key, data, ttl=self.TTL_CHAT)

    def append_chat_message(self, tournament_id: str, message: dict) -> bool:
        """Append message to cached chat history."""
        key = f"chat:{tournament_id}"
        history = self.get(key) or []
        history.append(message)
        # Keep only last 100 messages
        history = history[-100:]
        return self.set(key, history, ttl=self.TTL_CHAT)

    # Stats
    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        all_keys = self._redis.keys("*")
        by_prefix = {}

        for key in all_keys:
            prefix = key.split(":")[0]
            by_prefix[prefix] = by_prefix.get(prefix, 0) + 1

        return {
            "total_keys": len(all_keys),
            "by_prefix": by_prefix,
        }

    def clear_all(self) -> bool:
        """Clear all cache."""
        return self._redis.flushall()


# Global cache instance
redis_cache = RedisCache()


def cached(
    ttl: int = 300,
    key_prefix: str = "",
    invalidate_on: list[str] | None = None,
):
    """
    Decorator to cache function results.

    Args:
        ttl: Cache TTL in seconds
        key_prefix: Prefix for cache key
        invalidate_on: List of patterns to invalidate on success
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [key_prefix or func.__name__]
            key_parts.extend([str(a) for a in args[1:] if not callable(a)])  # Skip self
            key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
            cache_key = ":".join(key_parts)

            # Try cache
            cached_value = redis_cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Call function
            result = await func(*args, **kwargs)

            # Cache result
            if result is not None:
                redis_cache.set(cache_key, result, ttl=ttl)

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [key_prefix or func.__name__]
            key_parts.extend([str(a) for a in args[1:] if not callable(a)])  # Skip self
            key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
            cache_key = ":".join(key_parts)

            # Try cache
            cached_value = redis_cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Call function
            result = func(*args, **kwargs)

            # Cache result
            if result is not None:
                redis_cache.set(cache_key, result, ttl=ttl)

            return result

        return async_wrapper if func.__code__.co_flags & 0x80 else sync_wrapper

    return decorator


def cache_leaderboard(func: Callable) -> Callable:
    """Specialized decorator for leaderboard caching."""
    return cached(ttl=60, key_prefix="leaderboard")(func)


def cache_tournament(func: Callable) -> Callable:
    """Specialized decorator for tournament caching."""
    return cached(ttl=300, key_prefix="tournament")(func)
