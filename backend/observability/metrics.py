import time

from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send

from backend.core.telemetry.metrics import PrometheusMetrics

# Constants
SERVICE_NAME = "api_server"
metrics = PrometheusMetrics(SERVICE_NAME)


async def metrics_endpoint(request: Request):
    """
    Expose Prometheus metrics.
    """
    # Use the shared registry from PrometheusMetrics
    data = generate_latest(PrometheusMetrics._registry)
    return Response(data, media_type=CONTENT_TYPE_LATEST)


class PrometheusMiddleware:
    """
    Middleware to capture request latency and counts.
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        path = scope.get("path", "UNKNOWN")

        # Don't track metrics endpoint itself to avoid noise
        if path == "/metrics" or path == "/health":
            await self.app(scope, receive, send)
            return

        metrics.requests_in_progress.inc()
        status_code = 500  # Default to 500 if exception occurs

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
            metrics.requests_total.inc()
        except Exception:
            metrics.errors_total.inc()
            raise
        finally:
            metrics.requests_in_progress.dec()
            latency = time.time() - start_time
            metrics.request_latency_seconds.observe(latency)
