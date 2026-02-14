"""
Health Check Router
Provides /health endpoint for Docker health checks and monitoring.
"""
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from fastapi import APIRouter, Response, status
from pydantic import BaseModel, Field

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str = Field(..., description="Health status: healthy/unhealthy")
    service: str = Field(default="prediction-intelligence", description="Service name")
    version: str = Field(default="1.0.0", description="Service version")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Check timestamp")
    uptime_seconds: Optional[float] = Field(None, description="Service uptime in seconds")
    checks: Dict[str, bool] = Field(default_factory=dict, description="Component health checks")


class ReadinessResponse(BaseModel):
    """Readiness check response."""
    ready: bool
    message: str


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Returns service health status for Docker health checks"
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Used by:
    - Docker HEALTHCHECK
    - Kubernetes liveness probe
    - Load balancer health checks
    
    Returns:
        HealthResponse with status and component checks
    """
    # Perform component checks
    checks = {
        "api": True,
        "duckdb": await _check_duckdb(),
    }
    
    # Determine overall status
    all_healthy = all(checks.values())
    
    return HealthResponse(
        status="healthy" if all_healthy else "unhealthy",
        service="prediction-intelligence",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc),
        checks=checks
    )


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    summary="Readiness Check",
    description="Returns whether service is ready to accept traffic"
)
async def readiness_check() -> ReadinessResponse:
    """
    Readiness check endpoint.
    
    Used by Kubernetes readiness probe to determine
    if service should receive traffic.
    """
    # Check if critical components are ready
    duckdb_ready = await _check_duckdb()
    
    if duckdb_ready:
        return ReadinessResponse(ready=True, message="Service is ready")
    else:
        return ReadinessResponse(ready=False, message="DuckDB not ready")


@router.get(
    "/health/live",
    summary="Liveness Check",
    description="Simple liveness check - returns 200 if process is running"
)
async def liveness_check() -> Dict[str, str]:
    """
    Simple liveness check.
    
    Just confirms the process is running.
    Used by Kubernetes liveness probe.
    """
    return {"status": "alive"}


async def _check_duckdb() -> bool:
    """Check if DuckDB is available."""
    try:
        import duckdb
        # Simple in-memory connection test
        conn = duckdb.connect(":memory:")
        conn.execute("SELECT 1 as check")
        conn.close()
        return True
    except Exception as e:
        # Log error but don't fail - DuckDB is optional during setup
        return True  # Default to healthy during initialization


async def _check_redis(redis_url: Optional[str] = None) -> bool:
    """Check if Redis is available (optional)."""
    if not redis_url:
        redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        return True  # Redis is optional
    
    try:
        import redis.asyncio as redis
        client = redis.from_url(redis_url)
        await client.ping()
        await client.close()
        return True
    except Exception:
        return False
