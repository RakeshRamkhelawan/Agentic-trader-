import time
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# --- Metrics Definitions ---

# Request Latency
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint", "status_code"],
)

# Request Count
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status_code"],
)

# LLM Token Usage (P2-13 Prep)
LLM_TOKEN_USAGE_TOTAL = Counter(
    "llm_token_usage_total",
    "Total LLM tokens used",
    ["model", "type"],  # type=prompt/completion
)

# LLM Errors
LLM_ERRORS_TOTAL = Counter(
    "llm_errors_total", "Total LLM API errors", ["provider", "error_type"]
)

# Active Agents
ACTIVE_AGENTS_GAUGE = Gauge(
    "active_agents_gauge", "Number of currently active agent workflows"
)

# System Health
SYSTEM_HEALTH = Gauge("system_health", "System health status (1=healthy, 0=unhealthy)")

# --- Middleware ---


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        method = request.method
        # Simplify path to avoid high cardinality (e.g. /api/v1/users/123 -> /api/v1/users/{id})
        # For now use path template if available, else path
        path = request.url.path

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            raise e
        finally:
            process_time = time.time() - start_time

            # Record metrics
            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=method, endpoint=path, status_code=status_code
            ).observe(process_time)

            HTTP_REQUESTS_TOTAL.labels(
                method=method, endpoint=path, status_code=status_code
            ).inc()

        return response


def metrics_endpoint(request: Request):
    """Expose Prometheus metrics."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
