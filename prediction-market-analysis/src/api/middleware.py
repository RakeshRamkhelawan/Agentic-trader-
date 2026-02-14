"""
Metrics middleware for Prediction Market Intelligence service.

This middleware automatically records request metrics for all endpoints.
"""
import logging
import time
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.observability.metrics import REQUEST_COUNT, REQUEST_LATENCY

logger = logging.getLogger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect and record request metrics.
    
    Automatically records:
    - Request count by method, endpoint, and status code
    - Request latency by method and endpoint
    - Slow requests (> 1 second)
    - Exceptions and error rates
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and record metrics.
        
        Args:
            request: The incoming HTTP request
            call_next: The next middleware/route handler
            
        Returns:
            The HTTP response
        """
        start_time = time.time()
        
        try:
            # Call next middleware/route
            response = await call_next(request)
            
            # Record metrics after request completes
            duration = time.time() - start_time
            self._record_metrics(request, response.status_code, duration)
            
            # Log slow requests
            if duration > 1.0:
                logger.warning(
                    f"Slow request: {request.method} {request.url.path} "
                    f"took {duration:.2f}s"
                )
            
            return response
            
        except Exception as exc:
            # Record error metrics
            duration = time.time() - start_time
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status="exception"
            ).inc()
            REQUEST_LATENCY.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)
            
            logger.error(f"Request error: {request.method} {request.url.path}: {exc}")
            raise

    def _record_metrics(self, request: Request, status_code: int, duration: float) -> None:
        """
        Record request metrics in Prometheus.
        
        Args:
            request: The HTTP request
            status_code: The HTTP response status code
            duration: Request duration in seconds
        """
        try:
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status=status_code
            ).inc()
            
            REQUEST_LATENCY.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(duration)
        except Exception as e:
            logger.error(f"Failed to record metrics: {e}")
