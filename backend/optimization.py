"""
Optimization improvements for FastAPI service.

This module contains common patterns and configurations for optimizing
FastAPI performance, security, and reliability.
"""

import logging
from typing import Optional, Any, Dict
from functools import lru_cache, wraps
import time

from fastapi import FastAPI, Request, Response
from fastapi.middleware.gzip import GZIPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


# =============================================================================
# CACHING IMPROVEMENTS
# =============================================================================


class ResponseCache:
    """
    Simple in-memory response cache with TTL support.

    Suitable for frequently accessed, slowly-changing data.
    For high-volume caching, use Redis.
    """

    def __init__(self, ttl_seconds: int = 300):
        self.cache: Dict[str, tuple[Any, float]] = {}
        self.ttl = ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired."""
        if key not in self.cache:
            return None

        value, timestamp = self.cache[key]
        if time.time() - timestamp > self.ttl:
            del self.cache[key]
            return None

        return value

    def set(self, key: str, value: Any) -> None:
        """Cache a value with current timestamp."""
        self.cache[key] = (value, time.time())

    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()


def cache_response(ttl_seconds: int = 300):
    """
    Decorator to cache endpoint responses.

    Args:
        ttl_seconds: Cache time-to-live in seconds

    Usage:
        @router.get("/expensive-endpoint")
        @cache_response(ttl_seconds=600)
        async def expensive_operation():
            return compute_result()
    """

    def decorator(func):
        cache = ResponseCache(ttl_seconds=ttl_seconds)

        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key from function name and args
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

            # Try to get from cache
            cached = cache.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached

            # Compute result
            result = await func(*args, **kwargs)
            cache.set(cache_key, result)
            return result

        return wrapper

    return decorator


# =============================================================================
# ERROR HANDLING IMPROVEMENTS
# =============================================================================


class APIException(Exception):
    """Base class for API exceptions."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ValidationError(APIException):
    """Raised when request validation fails."""

    def __init__(self, message: str):
        super().__init__(message, status_code=422)


class NotFoundError(APIException):
    """Raised when resource not found."""

    def __init__(self, resource: str):
        super().__init__(f"{resource} not found", status_code=404)


class InternalServerError(APIException):
    """Raised for unexpected server errors."""

    def __init__(self, message: str = "Internal server error"):
        super().__init__(message, status_code=500)


def api_exception_handler(app: FastAPI):
    """
    Register exception handlers for APIException subclasses.

    Usage:
        app = FastAPI()
        api_exception_handler(app)
    """

    @app.exception_handler(APIException)
    async def exception_handler(request: Request, exc: APIException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message, "path": str(request.url.path)},
        )


# =============================================================================
# MIDDLEWARE OPTIMIZATION
# =============================================================================


def add_security_headers(app: FastAPI):
    """
    Add important security headers to responses.

    Improves security posture and enables browser protections.
    """

    @app.middleware("http")
    async def add_headers(request: Request, call_next):
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Enable XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Disable browser caching for sensitive endpoints
        if "/api/" in request.url.path:
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, proxy-revalidate"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        return response


def add_request_id_header(app: FastAPI):
    """
    Add unique Request-ID to all responses for tracing.

    Helps with debugging and request correlation.
    """
    import uuid

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response


# =============================================================================
# DATABASE OPTIMIZATION
# =============================================================================


async def get_connection_pool_settings(db_url: str) -> Dict[str, Any]:
    """
    Get optimized connection pool settings for database.

    These settings provide a good balance between resource usage
    and concurrency for typical FastAPI applications.

    Args:
        db_url: Database connection URL

    Returns:
        Dictionary of connection pool settings
    """
    return {
        "pool_size": 20,  # Number of connections to maintain
        "max_overflow": 10,  # Additional connections beyond pool_size
        "pool_timeout": 30,  # Seconds to wait for a connection
        "pool_recycle": 3600,  # Recycle connections every hour (prevents stale connections)
        "pool_pre_ping": True,  # Verify connection before using
        "echo": False,  # Don't log SQL queries in production
    }


# =============================================================================
# PERFORMANCE MONITORING
# =============================================================================


def add_performance_monitoring(app: FastAPI):
    """
    Add request timing and performance monitoring middleware.

    Logs slow requests and provides timing metrics.
    """

    @app.middleware("http")
    async def measure_performance(request: Request, call_next):
        start_time = time.time()

        response = await call_next(request)

        process_time = (time.time() - start_time) * 1000  # Convert to milliseconds

        # Log slow requests (> 1 second)
        if process_time > 1000:
            logger.warning(
                f"Slow request: {request.method} {request.url.path} "
                f"took {process_time:.2f}ms"
            )

        # Add timing header
        response.headers["X-Process-Time"] = f"{process_time:.2f}"

        return response


# =============================================================================
# CONFIGURATION
# =============================================================================


def configure_optimized_app(app: FastAPI):
    """
    Configure FastAPI app with all optimizations.

    Usage:
        from fastapi import FastAPI
        from backend.optimization import configure_optimized_app

        app = FastAPI()
        configure_optimized_app(app)
    """
    # Add GZIP compression for responses > 500 bytes
    app.add_middleware(GZIPMiddleware, minimum_size=500)

    # Add request tracking and performance monitoring
    add_request_id_header(app)
    add_performance_monitoring(app)

    # Add security headers
    add_security_headers(app)

    # Register exception handlers
    api_exception_handler(app)

    logger.info("FastAPI app configured with optimizations")
