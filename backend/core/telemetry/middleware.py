"""
FastAPI Middleware for Observability

Implements ADR-002: Observability - Metrics, Logs, Traces + Correlation IDs
Provides request tracing, metrics collection, and correlation propagation.

Author: Architecture Team
Date: 2026-02-20
"""

import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from backend.core.telemetry.correlation import CorrelationManager
from backend.core.telemetry.logging_config import get_logger
from backend.core.telemetry.slo_tracker import FlowType, slo_tracker

try:
    from prometheus_client import Counter, Histogram

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

logger = get_logger(__name__)


class CorrelationMiddleware(BaseHTTPMiddleware):
    """
    Injects correlation IDs into request context.

    Extracts trace info from headers or creates new context.
    Propagates context through the request lifecycle.
    """

    async def dispatch(self, request: Request, call_next):
        # Extract or create correlation context from headers
        ctx = CorrelationManager.from_headers(dict(request.headers))

        # Override with auth info if available
        if hasattr(request.state, "user"):
            ctx.user_id = getattr(request.state.user, "id", None)
            ctx.tenant_id = getattr(request.state.user, "tenant_id", None)

        # Set as current context
        ctx.set_current()

        # Store in request state for access in routes
        request.state.correlation = ctx

        # Process request
        start_time = time.time()

        try:
            response = await call_next(request)

            # Add correlation headers to response
            for key, value in CorrelationManager.to_headers().items():
                if value:
                    response.headers[key] = value

            # Log request
            duration_ms = (time.time() - start_time) * 1000
            status_code = response.status_code

            log_level = logger.warning if status_code >= 400 else logger.info
            log_level(
                f"{request.method} {request.url.path} - {status_code}",
                extra={
                    "http_method": request.method,
                    "http_path": request.url.path,
                    "http_status": status_code,
                    "duration_ms": duration_ms,
                    "client_ip": request.client.host if request.client else None,
                    "user_agent": request.headers.get("user-agent", "unknown"),
                    "trace_id": ctx.trace_id,
                    "span_id": ctx.span_id,
                    "user_id": ctx.user_id,
                    "tenant_id": ctx.tenant_id,
                    "request_id": ctx.request_id,
                },
            )

            return response

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            logger.error(
                f"{request.method} {request.url.path} - ERROR: {e}",
                extra={
                    "http_method": request.method,
                    "http_path": request.url.path,
                    "duration_ms": duration_ms,
                    "error": str(e),
                    "trace_id": ctx.trace_id,
                    "span_id": ctx.span_id,
                    "user_id": ctx.user_id,
                    "tenant_id": ctx.tenant_id,
                    "request_id": ctx.request_id,
                },
                exc_info=True,
            )
            raise


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Collects Prometheus metrics for all requests.

    Tracks:
    - Request count (by method, endpoint, status)
    - Request duration (by method, endpoint)
    - Request size
    - Response size
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

        if PROMETHEUS_AVAILABLE:
            self.request_count = Counter(
                "http_requests_total",
                "Total HTTP requests",
                ["method", "endpoint", "status_code"],
            )

            self.request_duration = Histogram(
                "http_request_duration_seconds",
                "HTTP request duration",
                ["method", "endpoint"],
                buckets=[
                    0.001,
                    0.005,
                    0.01,
                    0.025,
                    0.05,
                    0.1,
                    0.25,
                    0.5,
                    1.0,
                    2.5,
                    5.0,
                ],
            )

            self.request_size = Counter(
                "http_request_size_bytes", "HTTP request size", ["method", "endpoint"]
            )

            self.response_size = Counter(
                "http_response_size_bytes", "HTTP response size", ["method", "endpoint"]
            )
        else:
            self.request_count = None
            self.request_duration = None
            self.request_size = None
            self.response_size = None

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Get request size
        request_size = int(request.headers.get("content-length", 0))

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Get response size
        response_size = int(response.headers.get("content-length", 0))

        # Record metrics
        if PROMETHEUS_AVAILABLE and self.request_count:
            endpoint = request.url.path
            method = request.method
            status = str(response.status_code)

            self.request_count.labels(method=method, endpoint=endpoint, status_code=status).inc()

            self.request_duration.labels(method=method, endpoint=endpoint).observe(duration)

            self.request_size.labels(method=method, endpoint=endpoint).inc(request_size)

            self.response_size.labels(method=method, endpoint=endpoint).inc(response_size)

        return response


class SLOTrackingMiddleware(BaseHTTPMiddleware):
    """
    Tracks SLO metrics for critical endpoints.

    Maps specific endpoints to critical flows:
    - /api/v1/trading/orders/* → ORDER_EXECUTION
    - /ws / /ws/paper-trading → MARKET_DATA_STREAMING
    - /api/v1/agents/* → AGENT_DECISION
    """

    async def dispatch(self, request: Request, call_next):
        # Determine flow type from path
        flow = self._get_flow_type(request.url.path)

        if not flow:
            # Not a critical endpoint, just pass through
            return await call_next(request)

        # Determine stage
        stage = self._get_stage(request.url.path)

        start_time = time.time()
        success = True

        try:
            response = await call_next(request)

            # Consider 5xx as failure for SLO
            if response.status_code >= 500:
                success = False

            return response

        except Exception:
            success = False
            raise

        finally:
            duration_ms = (time.time() - start_time) * 1000
            slo_tracker.track_latency(flow, duration_ms / 1000, stage)
            slo_tracker.track_request(flow, success)

    def _get_flow_type(self, path: str) -> FlowType | None:
        """Map path to flow type."""
        if "/trading/" in path and "/orders" in path:
            return FlowType.ORDER_EXECUTION
        elif path.startswith("/ws"):
            return FlowType.MARKET_DATA_STREAMING
        elif "/agents/" in path:
            return FlowType.AGENT_DECISION
        return None

    def _get_stage(self, path: str) -> str:
        """Determine processing stage from path."""
        if "/risk" in path:
            return "risk_check"
        elif "/execution" in path:
            return "execution"
        elif "/validation" in path:
            return "validation"
        return "total"


class TimingMiddleware(BaseHTTPMiddleware):
    """
    Adds response timing headers for debugging.

    Adds X-Response-Time header with duration in milliseconds.
    """

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        response = await call_next(request)

        duration_ms = (time.time() - start_time) * 1000
        response.headers["X-Response-Time"] = f"{duration_ms:.3f}ms"

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds security headers to all responses.
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none';"

        # Remove server info
        response.headers.pop("Server", None)

        return response


# Combined middleware stack configuration
MIDDLEWARE_STACK = [
    (SecurityHeadersMiddleware, 0),
    (CorrelationMiddleware, 1),
    (MetricsMiddleware, 2),
    (SLOTrackingMiddleware, 3),
    (TimingMiddleware, 4),
]


def add_middleware_stack(app):
    """Add all observability middleware to FastAPI app."""
    for middleware_class, priority in sorted(MIDDLEWARE_STACK, key=lambda x: x[1]):
        app.add_middleware(middleware_class)
        logger.debug(f"Added middleware: {middleware_class.__name__}")
