"""
Tenant Rate Limiter - ADR-005
"""
import time
from typing import Dict, Tuple


class TenantRateLimiter:
    def __init__(self, redis_client):
        self.redis = redis_client

    async def check_rate_limit(
        self, tenant_id: str, resource: str, limit: int, window_seconds: int = 60
    ) -> Tuple[bool, Dict[str, str]]:
        key = f"ratelimit:{tenant_id}:{resource}"
        now = time.time()

        await self.redis.zremrangebyscore(key, 0, now - window_seconds)
        current = await self.redis.zcard(key)
        await self.redis.zadd(key, {str(now): now})
        await self.redis.expire(key, window_seconds)

        allowed = current < limit
        headers = {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(max(0, limit - current - 1)),
        }
        return allowed, headers
