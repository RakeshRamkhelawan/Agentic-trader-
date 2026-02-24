"""
Metrics middleware for FastAPI.

Automatically records request metrics (latency and count) for all endpoints.
"""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.observability.metrics import api_metrics

logger = logging.getLogger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect request metrics for Prometheus.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and record metrics.
        """
        start_time = time.time()
        path = request.url.path
        method = request.method

        # Increment in-progress gauge
        api_metrics.requests_in_progress.inc()

        try:
            response = await call_next(request)
            duration = time.time() - start_time

            # Update general metrics
            # Note: PrometheusMetrics in its current form doesn't use labels for basic counters
            # but we can call .inc() and .observe() as defined in its __init__
            api_metrics.requests_total.inc()
            api_metrics.request_latency_seconds.observe(duration)

            # Log slow requests
            if duration > 1.0:
                logger.warning(
                    f"Slow request: {method} {path} took {duration:.2f}s "
                    f"(status: {response.status_code})"
                )

            return response

        except Exception as e:
            api_metrics.errors_total.inc()
            logger.error(f"Error processing request {method} {path}: {e}")
            raise
        finally:
            api_metrics.requests_in_progress.dec()
