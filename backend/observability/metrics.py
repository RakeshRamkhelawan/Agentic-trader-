from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.requests import Request
from starlette.responses import Response

from backend.core.telemetry.metrics import PrometheusMetrics

# Constants
SERVICE_NAME = "api_server"
api_metrics = PrometheusMetrics(SERVICE_NAME)


async def metrics_endpoint(request: Request):
    """
    Expose Prometheus metrics for the entire platform.
    """
    # Use the shared registry from PrometheusMetrics
    data = generate_latest(PrometheusMetrics._registry)
    return Response(data, media_type=CONTENT_TYPE_LATEST)
