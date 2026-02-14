"""
Metrics middleware for FastAPI.

Automatically records request metrics (latency and count) for all endpoints.
"""
import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from backend.observability.metrics import REQUEST_COUNT, REQUEST_LATENCY

logger = logging.getLogger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect request metrics for Prometheus.
    
    Records:
    - Request count by method, endpoint, and status code
    - Request latency by method and endpoint
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and record metrics.
        
        Includes:
        - Request path (normalized to avoid high cardinality)
        - HTTP method
        - Response status code
        - Response latency
        """
        start_time = time.time()
        
        # Get the path without query parameters
        path = request.url.path
        method = request.method
        
        try:
            # Call the next middleware/route
            response = await call_next(request)
            
            # Record metrics after getting response
            duration = time.time() - start_time
            
            REQUEST_COUNT.labels(
                method=method,
                endpoint=path,
                status=response.status_code
            ).inc()
            
            REQUEST_LATENCY.labels(
                method=method,
                endpoint=path
            ).observe(duration)
            
            # Log slow requests
            if duration > 1.0:  # Log requests taking > 1 second
                logger.warning(
                    f"Slow request: {method} {path} took {duration:.2f}s "
                    f"(status: {response.status_code})"
                )
            
            return response
            
        except Exception as e:
            # Record error requests
            duration = time.time() - start_time
            
            REQUEST_COUNT.labels(
                method=method,
                endpoint=path,
                status=500
            ).inc()
            
            REQUEST_LATENCY.labels(
                method=method,
                endpoint=path
            ).observe(duration)
            
            logger.error(f"Error processing request {method} {path}: {e}")
            raise
