"""
FastAPI REST API - Main Application.

SaaS-ready API providing HTTP endpoints for:
- Backtest execution (direct Python imports)
- Tool execution (VedAstro, Elemental)
- Real-time market signals
- Performance metrics

Dual-interface architecture:
- LLM/AI: Use MCP Server (stdio)
- SaaS Dashboard: Use this REST API (HTTP)
- Internal: Use direct Python imports
"""

import logging
import sys
from contextlib import asynccontextmanager

# CRITICAL: All logging to stderr (MCP compatibility)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.auth_api import router as auth_router
from backend.api.competitions_api import router as competitions_router
from backend.api.kyc_api import router as kyc_router
from backend.api.metrics_middleware import MetricsMiddleware
from backend.api.paper_trading_api import router as paper_trading_router
from backend.api.paper_trading_ws_simple import router as paper_trading_ws_router
from backend.api.routers import (
    agents,
    backtest,
    federated,
    health,
    navagraha,
    ooda,
    routing,
    trading,
)
from backend.api.security_middleware import SecurityHeadersMiddleware
from backend.api.user_settings_api import router as user_settings_router
from backend.api.websocket_endpoints import router as websocket_router
from backend.core.config.settings import settings
from backend.observability.metrics import metrics_endpoint


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("=" * 60)
    logger.info("Starting Agentic Trader REST API")
    logger.info("=" * 60)

    # Startup: Initialize connections
    logger.info("Initializing Redis cache connection...")
    # Cache is initialized lazily in endpoints

    yield

    # Shutdown: Cleanup
    logger.info("Shutting down REST API...")


# Create FastAPI app
app = FastAPI(
    title="Agentic Trader API",
    description="SaaS-ready trading platform API with VedAstro integration",
    version="1.0.0",
    lifespan=lifespan,
)

# Security Headers Middleware (first for all responses)
app.add_middleware(SecurityHeadersMiddleware)

# Prometheus Metrics & Middleware
app.add_middleware(MetricsMiddleware)
app.get("/metrics")(metrics_endpoint)

# CORS middleware for React frontend
# In production, use specific origins from settings

cors_origins = settings.BACKEND_CORS_ORIGINS or [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
    "http://localhost",
    "http://127.0.0.1",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Accept",
        "Origin",
    ],
    expose_headers=["X-Total-Count", "X-Page-Count"],
    max_age=600,  # 10 minutes
)


# WebSocket-specific middleware for better logging
@app.middleware("http")
async def websocket_logging_middleware(request, call_next):
    """Log WebSocket upgrade requests."""
    if request.headers.get("upgrade") == "websocket":
        logger.info(f"WebSocket upgrade request from: {request.client}")
    response = await call_next(request)
    return response


# Include routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(backtest.router, prefix="/api/v1")
app.include_router(trading.router, prefix="/api/v1")
app.include_router(routing.router, prefix="/api/v1")
app.include_router(paper_trading_router)
app.include_router(agents.router, prefix="/api/v1")
app.include_router(navagraha.router, prefix="/api/v1")
app.include_router(ooda.router, prefix="/api/v1")
app.include_router(federated.router, prefix="/api/v1")
app.include_router(websocket_router)
app.include_router(paper_trading_ws_router)

# Authentication & User Management routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(kyc_router, prefix="/api/v1/kyc", tags=["KYC"])
app.include_router(user_settings_router, prefix="/api/v1/settings", tags=["Settings"])
app.include_router(competitions_router, prefix="/api/v1/competitions", tags=["Competitions"])

# Include MCP ToolBroker router (if available)
try:
    from backend.api.mcp_api import router as mcp_router

    app.include_router(mcp_router, prefix="/api/v1")
    logger.info("MCP ToolBroker router registered")
except ImportError:
    logger.warning("MCP ToolBroker router not available")


@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": "Agentic Trader API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "endpoints": {
            "health": "/api/v1/health",
            "backtest": "/api/v1/backtest/run",
            "vedastro": "/api/v1/tools/vedastro",
            "consensus": "/api/v1/tools/consensus",
        },
    }


@app.get("/api")
async def api_info():
    """API information endpoint."""
    return {
        "version": "1.0.0",
        "architecture": "Dual-Interface (MCP + REST + Direct)",
        "capabilities": [
            "backtest_execution",
            "vedastro_signals",
            "elemental_consensus",
            "portfolio_optimization",
        ],
    }


@app.get("/api/v1/config")
async def get_config():
    """
    Get public configuration for frontend.

    Returns non-sensitive configuration that the frontend needs
    to initialize properly.
    """
    return {
        "auth": {
            "enabled": not settings.AUTH_DISABLED,
            "domain": settings.AUTH0_DOMAIN if settings.AUTH0_DOMAIN else None,
            "audience": (settings.AUTH0_API_AUDIENCE if settings.AUTH0_API_AUDIENCE else None),
        },
        "features": {
            "websocket_public": True,
            "realtime_updates": True,
            "backtest": True,
            "vedastro": True,
        },
        "environment": "development" if settings.AUTH_DISABLED else "production",
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle all unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": (
                str(exc) if isinstance(exc, HTTPException) else "An unexpected error occurred"
            ),
        },
    )


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Uvicorn server...")
    uvicorn.run(
        "backend.api.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )  # nosec B104 - Required for Docker/containerized deployment
