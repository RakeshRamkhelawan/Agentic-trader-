"""
Middleware components for the API.

Features:
- Rate limiting
- Authentication
- CORS
- Request logging
"""

from .rate_limiter import RateLimiter, rate_limit

__all__ = [
    "RateLimiter",
    "rate_limit",
]
