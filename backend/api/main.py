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

import sys
import logging
from contextlib import asynccontextmanager

# CRITICAL: All logging to stderr (MCP compatibility)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.routers import backtest, trading, health, agents, navagraha, ooda
from backend.api.websocket_endpoints import router as websocket_router


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
    lifespan=lifespan
)

# CORS middleware for React frontend
# Note: WebSocket CORS is handled at the endpoint level, not here
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "*",  # Allow all in development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
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
app.include_router(agents.router, prefix="/api/v1")
app.include_router(navagraha.router, prefix="/api/v1")
app.include_router(ooda.router, prefix="/api/v1")
app.include_router(websocket_router)


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
            "consensus": "/api/v1/tools/consensus"
        }
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
            "portfolio_optimization"
        ]
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
            "detail": str(exc) if isinstance(exc, HTTPException) else "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Uvicorn server...")
    uvicorn.run(
        "backend.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
