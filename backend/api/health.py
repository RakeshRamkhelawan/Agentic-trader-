"""
Enterprise Health Check API
Provides comprehensive health status for all services
"""

import asyncio
import logging
import os
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.core.resiliency.circuit_breaker import get_circuit_breaker_registry

logger = logging.getLogger("HealthAPI")
router = APIRouter(prefix="/health", tags=["Health"])

# Global service registry (populated during startup)
_service_registry: dict[str, Any] = {}
_startup_time = datetime.now(UTC)


class HealthStatus(BaseModel):
    """Health status model"""

    status: str = Field(..., description="Overall health status: healthy, degraded, unhealthy")
    timestamp: str = Field(..., description="ISO8601 timestamp")
    version: str = Field(..., description="Application version")
    uptime_seconds: float = Field(..., description="Uptime in seconds")
    environment: str = Field(..., description="Environment: development, staging, production")
    trading_mode: str = Field(..., description="Trading mode: paper, live, backtest")


class ServiceHealth(BaseModel):
    """Individual service health"""

    name: str
    status: str  # healthy, degraded, unhealthy
    healthy: bool
    latency_ms: float | None = None
    last_check: str
    details: dict[str, Any] = Field(default_factory=dict)


class DetailedHealthResponse(BaseModel):
    """Detailed health check response"""

    summary: HealthStatus
    services: dict[str, ServiceHealth]
    circuit_breakers: dict[str, Any]


def register_service(name: str, service: Any, check_func: callable | None = None):
    """Register a service for health monitoring"""
    _service_registry[name] = {
        "instance": service,
        "check_func": check_func,
        "last_check": None,
        "last_status": "unknown",
    }
    logger.info(f"[Health] Registered service: {name}")


async def _check_redis_health() -> ServiceHealth:
    """Check Redis connection health"""
    start_time = asyncio.get_event_loop().time()

    try:
        # Import here to avoid circular dependency
        from backend.events.event_bus import EventBus

        event_bus = EventBus()
        # Try to ping Redis
        await event_bus.publish("health.check", {"ping": True})

        latency = (asyncio.get_event_loop().time() - start_time) * 1000

        return ServiceHealth(
            name="redis",
            status="healthy",
            healthy=True,
            latency_ms=round(latency, 2),
            last_check=datetime.now(UTC).isoformat(),
            details={"connected": True},
        )
    except Exception as e:
        return ServiceHealth(
            name="redis",
            status="unhealthy",
            healthy=False,
            latency_ms=None,
            last_check=datetime.now(UTC).isoformat(),
            details={"error": str(e)},
        )


async def _check_clickhouse_health() -> ServiceHealth:
    """Check ClickHouse connection health"""
    start_time = asyncio.get_event_loop().time()

    try:
        from backend.storage.clickhouse_client import ClickHouseClient

        client = ClickHouseClient()
        await client.execute("SELECT 1")

        latency = (asyncio.get_event_loop().time() - start_time) * 1000

        return ServiceHealth(
            name="clickhouse",
            status="healthy",
            healthy=True,
            latency_ms=round(latency, 2),
            last_check=datetime.now(UTC).isoformat(),
            details={"connected": True},
        )
    except Exception as e:
        return ServiceHealth(
            name="clickhouse",
            status="unhealthy",
            healthy=False,
            latency_ms=None,
            last_check=datetime.now(UTC).isoformat(),
            details={"error": str(e)},
        )


async def _check_chromadb_health() -> ServiceHealth:
    """Check ChromaDB connection health"""
    start_time = asyncio.get_event_loop().time()

    try:
        import chromadb

        from backend.core.config.settings import settings

        client = chromadb.HttpClient(host=settings.CHROMADB_HOST, port=settings.CHROMADB_PORT)
        client.heartbeat()

        latency = (asyncio.get_event_loop().time() - start_time) * 1000

        return ServiceHealth(
            name="chromadb",
            status="healthy",
            healthy=True,
            latency_ms=round(latency, 2),
            last_check=datetime.now(UTC).isoformat(),
            details={"connected": True},
        )
    except Exception as e:
        return ServiceHealth(
            name="chromadb",
            status="unhealthy",
            healthy=False,
            latency_ms=None,
            last_check=datetime.now(UTC).isoformat(),
            details={"error": str(e)},
        )


async def _check_llm_providers_health() -> ServiceHealth:
    """Check LLM provider availability via circuit breakers"""
    registry = get_circuit_breaker_registry()
    cb_health = await registry.health_check()

    if not cb_health:
        # No circuit breakers registered yet
        return ServiceHealth(
            name="llm_providers",
            status="healthy",
            healthy=True,
            last_check=datetime.now(UTC).isoformat(),
            details={"message": "No circuit breakers registered"},
        )

    healthy_count = sum(1 for h in cb_health.values() if h["healthy"])
    total_count = len(cb_health)

    if healthy_count == total_count:
        status = "healthy"
        healthy = True
    elif healthy_count > 0:
        status = "degraded"
        healthy = True
    else:
        status = "unhealthy"
        healthy = False

    return ServiceHealth(
        name="llm_providers",
        status=status,
        healthy=healthy,
        last_check=datetime.now(UTC).isoformat(),
        details={
            "providers": cb_health,
            "healthy_count": healthy_count,
            "total_count": total_count,
        },
    )


@router.get("", response_model=HealthStatus)
async def basic_health_check():
    """
    Basic health check endpoint
    Returns 200 if service is running, 503 if degraded/unhealthy
    """
    trading_mode = os.getenv("TRADING_MODE", "unknown")
    environment = os.getenv("ENVIRONMENT", "development")
    version = os.getenv("APP_VERSION", "1.0.0")

    uptime = (datetime.now(UTC) - _startup_time).total_seconds()

    # Check critical services
    services_to_check = [
        _check_redis_health(),
        _check_llm_providers_health(),
    ]

    results = await asyncio.gather(*services_to_check, return_exceptions=True)

    # Determine overall status
    unhealthy_count = 0
    degraded_count = 0

    for result in results:
        if isinstance(result, Exception) or not result.healthy:
            unhealthy_count += 1
        elif result.status == "degraded":
            degraded_count += 1

    if unhealthy_count > 0:
        status = "unhealthy"
    elif degraded_count > 0:
        status = "degraded"
    else:
        status = "healthy"

    response = HealthStatus(
        status=status,
        timestamp=datetime.now(UTC).isoformat(),
        version=version,
        uptime_seconds=uptime,
        environment=environment,
        trading_mode=trading_mode,
    )

    if status == "unhealthy":
        raise HTTPException(status_code=503, detail=response.dict())

    return response


@router.get("/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check():
    """
    Detailed health check with all services
    """
    trading_mode = os.getenv("TRADING_MODE", "unknown")
    environment = os.getenv("ENVIRONMENT", "development")
    version = os.getenv("APP_VERSION", "1.0.0")
    uptime = (datetime.now(UTC) - _startup_time).total_seconds()

    # Check all services
    services_to_check = [
        _check_redis_health(),
        _check_clickhouse_health(),
        _check_chromadb_health(),
        _check_llm_providers_health(),
    ]

    results = await asyncio.gather(*services_to_check, return_exceptions=True)

    services = {}
    unhealthy_count = 0
    degraded_count = 0

    for result in results:
        if isinstance(result, Exception):
            service_name = "unknown"
            services[service_name] = ServiceHealth(
                name=service_name,
                status="unhealthy",
                healthy=False,
                last_check=datetime.now(UTC).isoformat(),
                details={"error": str(result)},
            )
            unhealthy_count += 1
        else:
            services[result.name] = result
            if not result.healthy:
                unhealthy_count += 1
            elif result.status == "degraded":
                degraded_count += 1

    # Determine overall status
    if unhealthy_count > 0:
        status = "unhealthy"
    elif degraded_count > 0:
        status = "degraded"
    else:
        status = "healthy"

    # Get circuit breaker metrics
    registry = get_circuit_breaker_registry()
    cb_metrics = registry.get_all_metrics()

    summary = HealthStatus(
        status=status,
        timestamp=datetime.now(UTC).isoformat(),
        version=version,
        uptime_seconds=uptime,
        environment=environment,
        trading_mode=trading_mode,
    )

    return DetailedHealthResponse(summary=summary, services=services, circuit_breakers=cb_metrics)


@router.get("/ready")
async def readiness_check():
    """
    Kubernetes-style readiness probe
    Returns 200 when service is ready to accept traffic
    """
    # Check critical dependencies
    redis_health = await _check_redis_health()

    if not redis_health.healthy:
        raise HTTPException(
            status_code=503,
            detail={
                "ready": False,
                "reason": "Redis unavailable",
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )

    return {"ready": True, "timestamp": datetime.now(UTC).isoformat()}


@router.get("/live")
async def liveness_check():
    """
    Kubernetes-style liveness probe
    Returns 200 if service is alive (even if degraded)
    """
    return {
        "alive": True,
        "timestamp": datetime.now(UTC).isoformat(),
        "uptime_seconds": (datetime.now(UTC) - _startup_time).total_seconds(),
    }
