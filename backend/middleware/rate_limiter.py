"""API rate limiting middleware."""

import time
from functools import wraps


class RateLimiter:
    """
    Rate limiter for API endpoints.

    Supports:
    - Per-user rate limiting
    - Per-endpoint rate limiting
    - Sliding window algorithm
    """

    def __init__(self):
        # user_id -> {endpoint: [(timestamp)]}
        self._requests: dict[str, dict[str, list]] = {}
        self._default_limit = 60  # requests per minute
        self._default_window = 60  # seconds

    def is_allowed(
        self,
        user_id: str,
        endpoint: str,
        limit: int | None = None,
        window: int | None = None,
    ) -> tuple:
        """
        Check if request is allowed.

        Returns:
            (allowed: bool, remaining: int, reset_time: int)
        """
        limit = limit or self._default_limit
        window = window or self._default_window

        now = time.time()
        window_start = now - window

        # Initialize user tracking
        if user_id not in self._requests:
            self._requests[user_id] = {}

        if endpoint not in self._requests[user_id]:
            self._requests[user_id][endpoint] = []

        # Clean old requests
        self._requests[user_id][endpoint] = [
            ts for ts in self._requests[user_id][endpoint]
            if ts > window_start
        ]

        # Check limit
        current_count = len(self._requests[user_id][endpoint])

        if current_count >= limit:
            # Rate limit exceeded
            reset_time = int(self._requests[user_id][endpoint][0] + window)
            return False, 0, reset_time

        # Allow request
        self._requests[user_id][endpoint].append(now)
        remaining = limit - current_count - 1
        reset_time = int(now + window)

        return True, remaining, reset_time


def rate_limit(
    requests: int = 60,
    window: int = 60,
):
    """
    Decorator to apply rate limiting to endpoints.

    Args:
        requests: Number of requests allowed
        window: Time window in seconds
    """
    limiter = RateLimiter()

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get user_id from kwargs or use anonymous
            user_id = kwargs.get("user_id", "anonymous")

            allowed, remaining, reset_time = limiter.is_allowed(
                user_id, func.__name__, requests, window
            )

            if not allowed:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded",
                    headers={"Retry-After": str(reset_time - int(time.time()))},
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator
