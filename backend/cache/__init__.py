"""
Caching layer using Redis for performance optimization.

Caches:
- Leaderboards (TTL: 60s)
- Tournament data (TTL: 300s)
- User profiles (TTL: 600s)
- Strategy listings (TTL: 300s)
"""

from .redis_cache import RedisCache, cached, redis_cache

__all__ = [
    "RedisCache",
    "cached",
    "redis_cache",
]
