"""
Prediction Market Intelligence Service - FastAPI Application
Main entry point for the API server.
"""
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app

# Import routers
from src.api.routes.health import router as health_router
from src.api.routes.signals import router as signals_router
from src.api.routes.analysis import router as analysis_router
from src.api.routes.analysis import initialize_services
from src.api.middleware import MetricsMiddleware

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # === STARTUP ===
    logger.info("🚀 Starting Prediction Market Intelligence Service...")
    logger.info("📊 Initializing DuckDB connection...")
    
    # Initialize services
    try:
        initialize_services(data_dir="/app/data")
        logger.info("✅ Analysis services initialized")
    except Exception as e:
        logger.warning(f"⚠️  Could not initialize analysis services: {e}")
    
    # Initialize connections (can be extended later)
    from datetime import datetime
    app.state.startup_time = datetime.now()
    
    yield
    
    # === SHUTDOWN ===
    logger.info("👋 Shutting down Prediction Market Intelligence Service...")



# Create FastAPI application
app = FastAPI(
    title="Prediction Market Intelligence API",
    description="Market intelligence signals from prediction markets (Kalshi & Polymarket)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Metrics Middleware (must be added after CORS)
app.add_middleware(MetricsMiddleware)


# === REGISTER ROUTERS ===
app.include_router(health_router, tags=["health"])
app.include_router(signals_router, prefix="/api/v1", tags=["signals"])
app.include_router(analysis_router, prefix="/api/v1", tags=["analysis"])

# === REGISTER METRICS ENDPOINT ===
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# === ROOT ENDPOINT ===
@app.get("/", include_in_schema=False)
async def root() -> Dict[str, Any]:
    """Root endpoint with service info."""
    return {
        "service": "prediction-market-intelligence",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# === EXCEPTION HANDLERS ===
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unexpected errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
            "detail": str(exc) if app.debug else None
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )
