"""
VedAstro HTTP Bridge

Provides HTTP API for VedAstro calculations when C# interop
is not available (containerized deployments).

This acts as a fallback service that can be deployed separately
and called via HTTP from the main application.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

# Try to import VedAstro connector
try:
    from .connector import VedAstroConfig, VedAstroConnector

    VEDASTRO_AVAILABLE = True
except ImportError:
    VEDASTRO_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# Pydantic Models
# ============================================================================


class KundliRequest(BaseModel):
    """Request for Kundli calculation."""

    datetime: str = Field(..., description="ISO format datetime")
    latitude: float = Field(40.7128, ge=-90, le=90)
    longitude: float = Field(-74.0060, ge=-180, le=180)
    timezone_offset: int = Field(-5, ge=-12, le=12)
    symbol: str = Field("ASSET", description="Asset symbol for caching")


class TransitRequest(BaseModel):
    """Request for transit calculation."""

    datetime: str = Field(..., description="Current ISO format datetime")
    kundli: dict[str, Any] = Field(..., description="Birth chart (Kundli)")


class KundliResponse(BaseModel):
    """Response with Kundli data."""

    planets: dict[str, Any]
    lagna: str
    lagna_lord: str
    vargas: dict[str, Any]
    timestamp: str
    location: dict[str, float]


class TransitResponse(BaseModel):
    """Response with transit data."""

    aspects: list
    retrograde_count: int
    exalted_planets: list
    debilitated_planets: list
    current_positions: dict[str, Any]


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    vedastro_available: bool
    cache_stats: dict[str, int]


# ============================================================================
# FastAPI Application
# ============================================================================

# Global connector instance
connector: VedAstroConnector | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global connector

    # Startup
    logger.info("Starting VedAstro HTTP Bridge...")

    if VEDASTRO_AVAILABLE:
        config = VedAstroConfig(use_http_fallback=False)
        connector = VedAstroConnector(config)
        logger.info("VedAstro connector initialized")
    else:
        logger.warning("VedAstro not available - running in mock mode")

    yield

    # Shutdown
    if connector:
        connector.clear_cache()
        logger.info("VedAstro connector shutdown")


app = FastAPI(
    title="VedAstro HTTP Bridge",
    description="HTTP API for Vedic astrology calculations",
    version="1.0.0",
    lifespan=lifespan,
)


# ============================================================================
# API Endpoints
# ============================================================================


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    cache_stats = connector.get_cache_stats() if connector else {}

    return HealthResponse(
        status="healthy", vedastro_available=VEDASTRO_AVAILABLE, cache_stats=cache_stats
    )


@app.post("/calculate/kundli", response_model=KundliResponse)
async def calculate_kundli(request: KundliRequest):
    """
    Calculate complete Kundli (birth chart).

    Returns planetary positions, lagna, and vargas.
    """
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="VedAstro connector not available",
        )

    try:
        birth_date = datetime.fromisoformat(request.datetime.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid datetime format. Use ISO format (YYYY-MM-DDTHH:MM:SS)",
        )

    try:
        result = await connector.calculate_kundli(
            symbol=request.symbol,
            birth_date=birth_date,
            lat=request.latitude,
            lon=request.longitude,
            timezone_offset=request.timezone_offset,
        )

        return KundliResponse(**result)

    except Exception as e:
        logger.error(f"Error calculating Kundli: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Calculation error: {str(e)}",
        )


@app.post("/calculate/transits", response_model=TransitResponse)
async def calculate_transits(request: TransitRequest):
    """
    Calculate current transits vs birth chart.

    Returns aspects, retrogrades, and dignities.
    """
    if not connector:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="VedAstro connector not available",
        )

    try:
        current_date = datetime.fromisoformat(request.datetime.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid datetime format"
        )

    try:
        result = await connector.calculate_transits(date=current_date, kundli=request.kundli)

        return TransitResponse(**result)

    except Exception as e:
        logger.error(f"Error calculating transits: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Calculation error: {str(e)}",
        )


@app.get("/cache/stats")
async def cache_stats():
    """Get cache statistics."""
    if not connector:
        return {"error": "Connector not available"}

    return connector.get_cache_stats()


@app.post("/cache/clear")
async def clear_cache():
    """Clear all caches."""
    if connector:
        connector.clear_cache()

    return {"status": "Cache cleared"}


# ============================================================================
# Mock Mode Endpoints (for testing without C#)
# ============================================================================


@app.post("/mock/kundli", response_model=KundliResponse)
async def mock_kundli(request: KundliRequest):
    """Generate mock Kundli for testing."""
    import random

    signs = [
        "Aries",
        "Taurus",
        "Gemini",
        "Cancer",
        "Leo",
        "Virgo",
        "Libra",
        "Scorpio",
        "Sagittarius",
        "Capricorn",
        "Aquarius",
        "Pisces",
    ]

    planets = {}
    for planet in [
        "Sun",
        "Moon",
        "Mars",
        "Mercury",
        "Jupiter",
        "Venus",
        "Saturn",
        "Rahu",
        "Ketu",
    ]:
        planets[planet] = {
            "longitude": random.uniform(0, 360),
            "sign": random.choice(signs),
            "house": random.randint(1, 12),
            "nakshatra": random.choice(["Ashwini", "Bharani", "Krittika"]),
            "pada": random.randint(1, 4),
            "retrograde": random.random() > 0.8,
            "exalted": random.random() > 0.9,
            "debilitated": random.random() > 0.95,
        }

    lagna = random.choice(signs)

    return KundliResponse(
        planets=planets,
        lagna=lagna,
        lagna_lord={"Aries": "Mars", "Taurus": "Venus"}.get(lagna, "Unknown"),
        vargas={
            "D9": {
                p: {"sign": random.choice(signs), "house": random.randint(1, 12)} for p in planets
            }
        },
        timestamp=request.datetime,
        location={"lat": request.latitude, "lon": request.longitude},
    )


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "vedastro.http_bridge:app",
        host="0.0.0.0",  # nosec B104 - Required for Docker/containerized deployment
        port=5000,
        log_level="info",
        reload=False,
    )
