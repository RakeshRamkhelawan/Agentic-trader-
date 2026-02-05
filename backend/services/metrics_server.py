from fastapi import FastAPI, Response
import uvicorn
from prometheus_client import generate_latest

from backend.core.telemetry.metrics import PrometheusMetrics
from backend.core.telemetry.tracing import setup_tracing, get_tracer
from backend.core.config.settings import settings

# Initialiseer FastAPI app
app = FastAPI()

# Initialiseer Telemetry
setup_tracing("metrics-server")
tracer = get_tracer("metrics.server")
# Metrics worden automatisch globaal geregistreerd

@app.get("/metrics")
async def get_metrics():
    """
    Expose Prometheus metrics endpoint.
    """
    with tracer.start_as_current_span("get_metrics_endpoint"):
        latest_metrics = generate_latest()
        return Response(content=latest_metrics, media_type="text/plain")

if __name__ == "__main__":
    # Start uvicorn server
    uvicorn.run(app, host="0.0.0.0", port=settings.METRICS_SERVER_PORT)
