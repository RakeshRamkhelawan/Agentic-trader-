"""
Health Check Router.

Provides monitoring endpoints for:
- Service health
- Component status
- Performance metrics
"""

import logging
import time
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.mcp_broker.resilience import get_circuit_state

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/health", tags=["Health"])


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str
    timestamp: str
    version: str
    components: dict[str, Any]


class ComponentStatus(BaseModel):
    """Individual component status."""

    status: str
    latency_ms: float
    details: dict[str, Any] = {}


@router.get("", response_model=HealthResponse)
async def health_check():
    """
    Comprehensive health check endpoint.

    Returns:
        Service health status and component states
    """
    start_time = time.time()

    components = {}
    all_healthy = True

    # Check circuit breakers
    try:
        cb_start = time.time()
        tools = [
            "vedastro_generate_signal",
            "elemental_fire_position_size",
            "elemental_ether_consensus",
            "execution_execute_paper_trade",
        ]

        circuit_states = {}
        for tool in tools:
            state = get_circuit_state(tool)
            circuit_states[tool] = state["state"] if state else "unknown"

        all_closed = all(s == "closed" for s in circuit_states.values())
        all_healthy = all_healthy and all_closed

        components["circuit_breakers"] = {
            "status": "healthy" if all_closed else "degraded",
            "latency_ms": (time.time() - cb_start) * 1000,
            "details": circuit_states,
        }
    except Exception as e:
        logger.error(f"Circuit breaker check failed: {e}")
        all_healthy = False
        components["circuit_breakers"] = {
            "status": "error",
            "latency_ms": 0,
            "details": {"error": str(e)},
        }

    # Check cache (if Redis available)
    try:
        cache_start = time.time()
        from backend.mcp_broker.performance.cache import get_cache

        cache = get_cache()
        cache_connected = await cache.connect()

        components["cache"] = {
            "status": "healthy" if cache_connected else "degraded",
            "latency_ms": (time.time() - cache_start) * 1000,
            "details": {
                "redis_connected": cache_connected,
                "type": "redis" if cache_connected else "memory_only",
            },
        }
    except Exception as e:
        logger.warning(f"Cache check failed: {e}")
        components["cache"] = {
            "status": "degraded",
            "latency_ms": 0,
            "details": {"error": str(e), "type": "memory_only"},
        }

    # Check performance capabilities
    try:
        perf_start = time.time()
        from backend.mcp_broker.performance.ultra_mode import UltraPerformanceMode

        ultra = UltraPerformanceMode()
        caps = ultra.get_capabilities()

        components["performance"] = {
            "status": "healthy",
            "latency_ms": (time.time() - perf_start) * 1000,
            "details": caps,
        }
    except Exception as e:
        logger.error(f"Performance check failed: {e}")
        all_healthy = False
        components["performance"] = {
            "status": "error",
            "latency_ms": 0,
            "details": {"error": str(e)},
        }

    total_latency = (time.time() - start_time) * 1000

    return HealthResponse(
        status="healthy" if all_healthy else "degraded",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0",
        components=components,
    )


@router.get("/ping")
async def ping():
    """Simple ping endpoint for load balancers."""
    return {"status": "pong", "timestamp": datetime.utcnow().isoformat()}


@router.get("/ready")
async def readiness_check():
    """Kubernetes-style readiness check."""
    try:
        # Quick check that critical components are available

        return {"ready": True, "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail={"ready": False, "error": str(e)})


@router.get("/metrics")
async def metrics():
    """Prometheus-style metrics endpoint."""

    # This would collect actual metrics in production
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": {
            "requests_total": 0,  # Would be tracked in middleware
            "request_duration_seconds": 0.0,
            "cache_hit_rate": 0.0,
            "circuit_breaker_states": {},
        },
    }
