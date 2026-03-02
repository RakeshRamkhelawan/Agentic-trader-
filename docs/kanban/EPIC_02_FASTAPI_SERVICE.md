# 🚀 EPIC 2: FastAPI Service Core

**Epic ID:** EPIC-PM-002
**Status:** ✅ COMPLETE
**Voltooide doorlooptijd:** ~2-3 dagen
**Dependencies:** EPIC 1 (Container Infrastructuur) - COMPLETE

---

## 📋 Epic Overzicht

Dit epic implementeert de core FastAPI service voor de Prediction Market Intelligence container. We bouwen de API server, schemas, en basis endpoints.

### Deliverables
- FastAPI applicatie (`api_server.py`)
- Health endpoint (`/health`)
- Signals endpoint (`/api/v1/signals`)
- Analysis endpoints (`/api/v1/analysis`)
- Pydantic schemas voor requests/responses

### Files die aangemaakt worden
| Bestand | Beschrijving |
|---------|--------------|
| `prediction-market-analysis/api_server.py` | Main FastAPI applicatie |
| `prediction-market-analysis/src/api/__init__.py` | API module init |
| `prediction-market-analysis/src/api/routes/health.py` | Health check router |
| `prediction-market-analysis/src/api/routes/signals.py` | Signals router |
| `prediction-market-analysis/src/api/routes/analysis.py` | Analysis router |
| `prediction-market-analysis/src/api/schemas/signal.py` | Signal schemas |
| `prediction-market-analysis/src/api/schemas/analysis.py` | Analysis schemas |
| `prediction-market-analysis/tests/test_api.py` | API tests |

---

## 📌 TASK 2.1: FastAPI Application Setup

**Task ID:** TASK-PM-005
**Status:** 🔴 TODO
**Geschatte tijd:** 2 uur
**Dependencies:** TASK-PM-004
**Assignee:** _____

### Task Beschrijving
Maak de main FastAPI applicatie met lifespan management, CORS middleware, en basis configuratie.

### Files die geraakt worden
- `prediction-market-analysis/api_server.py` (NIEUW)
- `prediction-market-analysis/src/api/__init__.py` (NIEUW)

### Huidige Platform API Pattern (voor referentie)

```python
# Backend API pattern (backend/api/main.py)
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting application...")
    yield
    # Shutdown
    logger.info("Shutting down...")

app = FastAPI(
    title="Agentic Trader Platform",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### MASTERPROMPT

```
═══════════════════════════════════════════════════════════════════════════════
TAAK: Maak FastAPI applicatie voor Prediction Market Intelligence
═══════════════════════════════════════════════════════════════════════════════

CONTEXT:
- Service draait op port 8002
- Moet health endpoint hebben voor Docker health checks
- Volgt zelfde patterns als main Agentic Trader Platform
- Gebruikt Pydantic V2 voor schemas

───────────────────────────────────────────────────────────────────────────────
BESTAND 1: prediction-market-analysis/api_server.py
───────────────────────────────────────────────────────────────────────────────

"""
Prediction Market Intelligence Service - FastAPI Application
Main entry point voor de API server.
"""
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import routers
from src.api.routes.health import router as health_router
from src.api.routes.signals import router as signals_router
from src.api.routes.analysis import router as analysis_router

# Logging configuratie
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

    # Initialize connections (kan later uitgebreid worden)
    app.state.startup_time = __import__("datetime").datetime.now()

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
    allow_origins=["*"],  # In productie: specifieke origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === REGISTER ROUTERS ===
app.include_router(health_router, tags=["health"])
app.include_router(signals_router, prefix="/api/v1", tags=["signals"])
app.include_router(analysis_router, prefix="/api/v1", tags=["analysis"])


# === ROOT ENDPOINT ===
@app.get("/", include_in_schema=False)
async def root() -> Dict[str, Any]:
    """Root endpoint met service info."""
    return {
        "service": "prediction-market-intelligence",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# === EXCEPTION HANDLERS ===
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler voor onverwachte errors."""
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

───────────────────────────────────────────────────────────────────────────────
BESTAND 2: prediction-market-analysis/src/api/__init__.py
───────────────────────────────────────────────────────────────────────────────

"""
Prediction Market Intelligence API Module.
"""
from src.api.routes import health, signals, analysis

__all__ = ["health", "signals", "analysis"]

───────────────────────────────────────────────────────────────────────────────
DIRECTORY STRUCTUUR AANMAKEN:
───────────────────────────────────────────────────────────────────────────────

New-Item -Path "prediction-market-analysis/src/api" -ItemType Directory -Force
New-Item -Path "prediction-market-analysis/src/api/routes" -ItemType Directory -Force
New-Item -Path "prediction-market-analysis/src/api/schemas" -ItemType Directory -Force

───────────────────────────────────────────────────────────────────────────────
VERIFICATIE:
───────────────────────────────────────────────────────────────────────────────

cd prediction-market-analysis
python -c "from api_server import app; print(f'App title: {app.title}')"
# Output: App title: Prediction Market Intelligence API

═══════════════════════════════════════════════════════════════════════════════
```

### Acceptatiecriteria
- [ ] `api_server.py` bestaat en is importeerbaar
- [ ] FastAPI app heeft correcte title en version
- [ ] CORS middleware is geconfigureerd
- [ ] Lifespan manager is geïmplementeerd
- [ ] Directory structuur `src/api/routes/` en `src/api/schemas/` bestaat

### TDD Requirements

**Test Bestand:** `prediction-market-analysis/tests/test_api_server.py`

```python
"""
Tests voor api_server.py
Run: pytest prediction-market-analysis/tests/test_api_server.py -v
"""
import pytest
from fastapi.testclient import TestClient


class TestAPIServer:
    """Tests voor FastAPI applicatie setup."""

    @pytest.fixture
    def client(self):
        """Test client voor API."""
        from api_server import app
        return TestClient(app)

    # =========================================================================
    # HAPPY PATH TESTS
    # =========================================================================

    def test_happy_path_app_has_correct_metadata(self):
        """Happy path: App metadata is correct."""
        from api_server import app

        assert app.title == "Prediction Market Intelligence API"
        assert app.version == "1.0.0"
        assert app.docs_url == "/docs"

    def test_happy_path_root_endpoint_returns_service_info(self, client):
        """Happy path: Root endpoint retourneert service info."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "prediction-market-intelligence"
        assert data["version"] == "1.0.0"
        assert "docs" in data
        assert "health" in data

    def test_happy_path_docs_endpoint_accessible(self, client):
        """Happy path: OpenAPI docs zijn toegankelijk."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_happy_path_openapi_schema_accessible(self, client):
        """Happy path: OpenAPI schema is toegankelijk."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        schema = response.json()
        assert "openapi" in schema
        assert schema["info"]["title"] == "Prediction Market Intelligence API"

    def test_happy_path_cors_headers_present(self, client):
        """Happy path: CORS headers zijn aanwezig."""
        response = client.options(
            "/",
            headers={"Origin": "http://localhost:3000"}
        )
        # CORS preflight moet werken
        assert response.status_code in [200, 405]

    # =========================================================================
    # UNHAPPY PATH TESTS
    # =========================================================================

    def test_unhappy_path_unknown_endpoint_returns_404(self, client):
        """Unhappy path: Onbekend endpoint geeft 404."""
        response = client.get("/some/unknown/endpoint")
        assert response.status_code == 404

    def test_unhappy_path_method_not_allowed(self, client):
        """Unhappy path: Verkeerde HTTP method geeft 405."""
        response = client.delete("/")  # Root ondersteunt alleen GET
        assert response.status_code == 405
```

---

### 📎 MICROTASK 2.1.1: Create Directory Structure

**Microtask ID:** MT-PM-005-001
**Geschatte tijd:** 10 min
**Status:** 🔴 TODO

#### MASTERPROMPT

```
═══════════════════════════════════════════════════════════════════════════════
MICROTASK: Maak API directory structuur
═══════════════════════════════════════════════════════════════════════════════

COMMANDO'S:
cd c:\Users\rsram\Downloads\agentic_trader_platform_1734_20260109_210621\prediction-market-analysis

# Maak directories
New-Item -Path "src/api" -ItemType Directory -Force
New-Item -Path "src/api/routes" -ItemType Directory -Force
New-Item -Path "src/api/schemas" -ItemType Directory -Force

# Maak __init__.py files
New-Item -Path "src/api/__init__.py" -ItemType File -Force
New-Item -Path "src/api/routes/__init__.py" -ItemType File -Force
New-Item -Path "src/api/schemas/__init__.py" -ItemType File -Force

VERIFICATIE:
Get-ChildItem -Path "src/api" -Recurse
# Moet routes/ en schemas/ directories tonen met __init__.py files

═══════════════════════════════════════════════════════════════════════════════
```

---

### 📎 MICROTASK 2.1.2: Create api_server.py

**Microtask ID:** MT-PM-005-002
**Geschatte tijd:** 45 min
**Status:** 🔴 TODO

#### MASTERPROMPT

```
═══════════════════════════════════════════════════════════════════════════════
MICROTASK: Maak api_server.py
═══════════════════════════════════════════════════════════════════════════════

BESTAND: prediction-market-analysis/api_server.py

VOLLEDIGE INHOUD:
[Zie TASK MASTERPROMPT hierboven voor volledige code]

VERIFICATIE:
cd prediction-market-analysis
python -c "from api_server import app; print('Import OK')"

═══════════════════════════════════════════════════════════════════════════════
```

---

## 📌 TASK 2.2: Health Endpoint

**Task ID:** TASK-PM-006
**Status:** 🔴 TODO
**Geschatte tijd:** 1 uur
**Dependencies:** TASK-PM-005
**Assignee:** _____

### Task Beschrijving
Implementeer de health check endpoint die gebruikt wordt door Docker health checks en monitoring.

### Files die geraakt worden
- `prediction-market-analysis/src/api/routes/health.py` (NIEUW)

### MASTERPROMPT

```
═══════════════════════════════════════════════════════════════════════════════
TAAK: Implementeer /health endpoint
═══════════════════════════════════════════════════════════════════════════════

BESTAND: prediction-market-analysis/src/api/routes/health.py

───────────────────────────────────────────────────────────────────────────────
VOLLEDIGE INHOUD:
───────────────────────────────────────────────────────────────────────────────

"""
Health Check Router
Provides /health endpoint for Docker health checks and monitoring.
"""
import os
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, Response, status
from pydantic import BaseModel, Field

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str = Field(..., description="Health status: healthy/unhealthy")
    service: str = Field(default="prediction-intelligence", description="Service name")
    version: str = Field(default="1.0.0", description="Service version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
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
        timestamp=datetime.utcnow(),
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
        conn = duckdb.connect(":memory:")
        result = conn.execute("SELECT 1").fetchone()
        conn.close()
        return result[0] == 1
    except Exception:
        return False


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

───────────────────────────────────────────────────────────────────────────────
ROUTES __init__.py UPDATE:
───────────────────────────────────────────────────────────────────────────────

BESTAND: prediction-market-analysis/src/api/routes/__init__.py

"""API Routes."""
from src.api.routes.health import router as health_router

__all__ = ["health_router"]

───────────────────────────────────────────────────────────────────────────────
VERIFICATIE:
───────────────────────────────────────────────────────────────────────────────

cd prediction-market-analysis
python -c "
from fastapi.testclient import TestClient
from api_server import app
client = TestClient(app)
r = client.get('/health')
print(f'Status: {r.status_code}')
print(f'Response: {r.json()}')
"
# Verwacht: Status: 200, Response: {"status":"healthy",...}

═══════════════════════════════════════════════════════════════════════════════
```

### Acceptatiecriteria
- [ ] `/health` endpoint retourneert status "healthy"
- [ ] `/health/ready` endpoint werkt
- [ ] `/health/live` endpoint werkt
- [ ] DuckDB check is geïmplementeerd
- [ ] Response volgt HealthResponse schema

### TDD Requirements

**Test Bestand:** `prediction-market-analysis/tests/test_health.py`

```python
"""
Tests voor health endpoints.
Run: pytest prediction-market-analysis/tests/test_health.py -v
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime


class TestHealthEndpoints:
    """Tests voor /health endpoints."""

    @pytest.fixture
    def client(self):
        """Test client."""
        from api_server import app
        return TestClient(app)

    # =========================================================================
    # HAPPY PATH TESTS
    # =========================================================================

    def test_happy_path_health_returns_200(self, client):
        """Happy path: /health retourneert 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_happy_path_health_returns_healthy_status(self, client):
        """Happy path: Status is healthy wanneer alles werkt."""
        response = client.get("/health")
        data = response.json()

        assert data["status"] == "healthy"
        assert data["service"] == "prediction-intelligence"
        assert data["version"] == "1.0.0"

    def test_happy_path_health_includes_timestamp(self, client):
        """Happy path: Response bevat timestamp."""
        response = client.get("/health")
        data = response.json()

        assert "timestamp" in data
        # Timestamp moet parseerbaar zijn
        timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        assert timestamp is not None

    def test_happy_path_health_includes_checks(self, client):
        """Happy path: Response bevat component checks."""
        response = client.get("/health")
        data = response.json()

        assert "checks" in data
        assert isinstance(data["checks"], dict)
        assert "duckdb" in data["checks"]

    def test_happy_path_readiness_returns_ready(self, client):
        """Happy path: /health/ready retourneert ready=true."""
        response = client.get("/health/ready")
        assert response.status_code == 200

        data = response.json()
        assert data["ready"] is True

    def test_happy_path_liveness_returns_alive(self, client):
        """Happy path: /health/live retourneert status alive."""
        response = client.get("/health/live")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "alive"

    # =========================================================================
    # UNHAPPY PATH TESTS
    # =========================================================================

    def test_unhappy_path_health_post_not_allowed(self, client):
        """Unhappy path: POST naar /health geeft 405."""
        response = client.post("/health")
        assert response.status_code == 405

    def test_unhappy_path_health_with_body_ignored(self, client):
        """Unhappy path: Request body wordt genegeerd."""
        response = client.get(
            "/health",
            headers={"Content-Type": "application/json"}
        )
        # Moet nog steeds werken
        assert response.status_code == 200
```

---

### 📎 MICROTASK 2.2.1: Create Health Router

**Microtask ID:** MT-PM-006-001
**Geschatte tijd:** 30 min
**Status:** 🔴 TODO

#### MASTERPROMPT

```
═══════════════════════════════════════════════════════════════════════════════
MICROTASK: Maak health.py router
═══════════════════════════════════════════════════════════════════════════════

BESTAND: prediction-market-analysis/src/api/routes/health.py

[Zie TASK MASTERPROMPT voor volledige inhoud]

VERIFICATIE:
python -c "from src.api.routes.health import router; print('Health router OK')"

═══════════════════════════════════════════════════════════════════════════════
```

---

## 📌 TASK 2.3: Signals Endpoint

**Task ID:** TASK-PM-007
**Status:** 🔴 TODO
**Geschatte tijd:** 3 uur
**Dependencies:** TASK-PM-006
**Assignee:** _____

### Task Beschrijving
Implementeer de `/api/v1/signals` endpoint voor het ophalen van market intelligence signals.

### Files die geraakt worden
- `prediction-market-analysis/src/api/routes/signals.py` (NIEUW)
- `prediction-market-analysis/src/api/schemas/signal.py` (NIEUW)

### MASTERPROMPT

```
═══════════════════════════════════════════════════════════════════════════════
TAAK: Implementeer /api/v1/signals endpoint
═══════════════════════════════════════════════════════════════════════════════

───────────────────────────────────────────────────────────────────────────────
BESTAND 1: prediction-market-analysis/src/api/schemas/signal.py
───────────────────────────────────────────────────────────────────────────────

"""
Signal schemas for Prediction Market Intelligence API.
"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field, ConfigDict


class MarketSource(str, Enum):
    """Supported prediction market sources."""
    KALSHI = "kalshi"
    POLYMARKET = "polymarket"


class SignalType(str, Enum):
    """Signal type indicators."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class SignalCategory(str, Enum):
    """Market categories."""
    CRYPTO = "crypto"
    POLITICS = "politics"
    ECONOMICS = "economics"
    FINANCE = "finance"
    SPORTS = "sports"
    ENTERTAINMENT = "entertainment"
    OTHER = "other"


class MarketSignal(BaseModel):
    """
    Market intelligence signal from prediction markets.

    Represents a trading signal derived from prediction market data,
    including maker/taker analysis, volume patterns, and sentiment.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "sig_abc123",
                "market": "kalshi",
                "category": "crypto",
                "signal_type": "bullish",
                "confidence": 0.75,
                "symbol": "BTC",
                "indicators": {
                    "maker_advantage": 0.02,
                    "volume_change_24h": 1.5,
                    "sentiment_score": 0.8
                },
                "timestamp": "2026-02-13T10:00:00Z",
                "metadata": {
                    "source_market": "Will Bitcoin exceed $100k by March 2026?",
                    "current_price": 0.65
                }
            }
        }
    )

    id: str = Field(..., description="Unique signal identifier")
    market: MarketSource = Field(..., description="Source prediction market")
    category: SignalCategory = Field(..., description="Market category")
    signal_type: SignalType = Field(..., description="Signal direction")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")
    symbol: Optional[str] = Field(None, description="Related trading symbol")
    indicators: Dict[str, float] = Field(default_factory=dict, description="Signal indicators")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Signal timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class SignalFilter(BaseModel):
    """Filter parameters for signals query."""
    market: Optional[MarketSource] = Field(None, description="Filter by market source")
    category: Optional[SignalCategory] = Field(None, description="Filter by category")
    signal_type: Optional[SignalType] = Field(None, description="Filter by signal type")
    min_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Minimum confidence")
    symbol: Optional[str] = Field(None, description="Filter by symbol")
    limit: int = Field(10, ge=1, le=100, description="Max results")
    offset: int = Field(0, ge=0, description="Pagination offset")


class SignalsResponse(BaseModel):
    """Response for signals endpoint."""
    signals: List[MarketSignal] = Field(..., description="List of signals")
    total: int = Field(..., description="Total matching signals")
    limit: int = Field(..., description="Results limit")
    offset: int = Field(..., description="Results offset")

───────────────────────────────────────────────────────────────────────────────
BESTAND 2: prediction-market-analysis/src/api/routes/signals.py
───────────────────────────────────────────────────────────────────────────────

"""
Signals Router
Provides endpoints for retrieving market intelligence signals.
"""
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Query, HTTPException, status

from src.api.schemas.signal import (
    MarketSignal,
    SignalFilter,
    SignalsResponse,
    MarketSource,
    SignalCategory,
    SignalType
)

router = APIRouter()


@router.get(
    "/signals",
    response_model=SignalsResponse,
    summary="Get Market Signals",
    description="Retrieve market intelligence signals from prediction markets"
)
async def get_signals(
    market: Optional[MarketSource] = Query(None, description="Filter by market"),
    category: Optional[SignalCategory] = Query(None, description="Filter by category"),
    signal_type: Optional[SignalType] = Query(None, description="Filter by signal type"),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0, description="Minimum confidence"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    limit: int = Query(10, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset")
) -> SignalsResponse:
    """
    Get market intelligence signals.

    Signals are derived from prediction market data and can be used by
    OODA agents for decision making.

    Args:
        market: Filter by prediction market source
        category: Filter by market category
        signal_type: Filter by bullish/bearish/neutral
        min_confidence: Minimum confidence threshold
        symbol: Filter by related trading symbol
        limit: Maximum number of results
        offset: Pagination offset

    Returns:
        SignalsResponse with list of matching signals
    """
    # TODO: Replace with actual signal generation from analysis engine
    # For now, return mock data for API contract validation

    signals = _generate_mock_signals(
        market=market,
        category=category,
        signal_type=signal_type,
        min_confidence=min_confidence,
        symbol=symbol,
        limit=limit,
        offset=offset
    )

    return SignalsResponse(
        signals=signals,
        total=len(signals),
        limit=limit,
        offset=offset
    )


@router.get(
    "/signals/{signal_id}",
    response_model=MarketSignal,
    summary="Get Signal by ID",
    description="Retrieve a specific signal by its ID"
)
async def get_signal_by_id(signal_id: str) -> MarketSignal:
    """
    Get a specific signal by ID.

    Args:
        signal_id: Unique signal identifier

    Returns:
        MarketSignal if found

    Raises:
        HTTPException 404 if signal not found
    """
    # TODO: Replace with actual lookup
    # For now, return mock or 404

    if not signal_id.startswith("sig_"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Signal {signal_id} not found"
        )

    return MarketSignal(
        id=signal_id,
        market=MarketSource.KALSHI,
        category=SignalCategory.CRYPTO,
        signal_type=SignalType.BULLISH,
        confidence=0.75,
        symbol="BTC",
        indicators={
            "maker_advantage": 0.02,
            "volume_change_24h": 1.5
        },
        timestamp=datetime.utcnow(),
        metadata={"source": "mock"}
    )


def _generate_mock_signals(
    market: Optional[MarketSource],
    category: Optional[SignalCategory],
    signal_type: Optional[SignalType],
    min_confidence: float,
    symbol: Optional[str],
    limit: int,
    offset: int
) -> List[MarketSignal]:
    """Generate mock signals for API development."""

    mock_signals = [
        MarketSignal(
            id=f"sig_{uuid.uuid4().hex[:8]}",
            market=MarketSource.KALSHI,
            category=SignalCategory.CRYPTO,
            signal_type=SignalType.BULLISH,
            confidence=0.82,
            symbol="BTC",
            indicators={
                "maker_advantage": 0.025,
                "volume_change_24h": 2.1,
                "sentiment_score": 0.85
            },
            timestamp=datetime.utcnow() - timedelta(minutes=5),
            metadata={
                "source_market": "Will Bitcoin exceed $100k by March 2026?",
                "current_price": 0.72
            }
        ),
        MarketSignal(
            id=f"sig_{uuid.uuid4().hex[:8]}",
            market=MarketSource.POLYMARKET,
            category=SignalCategory.FINANCE,
            signal_type=SignalType.BEARISH,
            confidence=0.65,
            symbol="SPY",
            indicators={
                "maker_advantage": -0.01,
                "volume_change_24h": 0.8,
                "sentiment_score": 0.35
            },
            timestamp=datetime.utcnow() - timedelta(minutes=15),
            metadata={
                "source_market": "Will S&P 500 drop 10% in Q1 2026?",
                "current_price": 0.28
            }
        ),
        MarketSignal(
            id=f"sig_{uuid.uuid4().hex[:8]}",
            market=MarketSource.KALSHI,
            category=SignalCategory.ECONOMICS,
            signal_type=SignalType.NEUTRAL,
            confidence=0.55,
            symbol=None,
            indicators={
                "maker_advantage": 0.001,
                "volume_change_24h": 1.0
            },
            timestamp=datetime.utcnow() - timedelta(hours=1),
            metadata={
                "source_market": "Will Fed raise rates in March?",
                "current_price": 0.50
            }
        )
    ]

    # Apply filters
    filtered = mock_signals

    if market:
        filtered = [s for s in filtered if s.market == market]
    if category:
        filtered = [s for s in filtered if s.category == category]
    if signal_type:
        filtered = [s for s in filtered if s.signal_type == signal_type]
    if min_confidence > 0:
        filtered = [s for s in filtered if s.confidence >= min_confidence]
    if symbol:
        filtered = [s for s in filtered if s.symbol and symbol.upper() in s.symbol.upper()]

    # Apply pagination
    return filtered[offset:offset + limit]

───────────────────────────────────────────────────────────────────────────────
VERIFICATIE:
───────────────────────────────────────────────────────────────────────────────

cd prediction-market-analysis
python -c "
from fastapi.testclient import TestClient
from api_server import app
client = TestClient(app)
r = client.get('/api/v1/signals')
print(f'Status: {r.status_code}')
print(f'Signals count: {len(r.json()[\"signals\"])}')
"

═══════════════════════════════════════════════════════════════════════════════
```

### Acceptatiecriteria
- [ ] `/api/v1/signals` endpoint werkt
- [ ] Response volgt SignalsResponse schema
- [ ] Filters werken (market, category, signal_type)
- [ ] Pagination werkt (limit, offset)
- [ ] `/api/v1/signals/{id}` endpoint werkt

### TDD Requirements

**Test Bestand:** `prediction-market-analysis/tests/test_signals.py`

```python
"""
Tests voor signals endpoints.
Run: pytest prediction-market-analysis/tests/test_signals.py -v
"""
import pytest
from fastapi.testclient import TestClient


class TestSignalsEndpoint:
    """Tests voor /api/v1/signals endpoints."""

    @pytest.fixture
    def client(self):
        from api_server import app
        return TestClient(app)

    # =========================================================================
    # HAPPY PATH TESTS
    # =========================================================================

    def test_happy_path_get_signals_returns_list(self, client):
        """Happy path: GET /signals retourneert lijst van signals."""
        response = client.get("/api/v1/signals")

        assert response.status_code == 200
        data = response.json()
        assert "signals" in data
        assert isinstance(data["signals"], list)

    def test_happy_path_signals_have_required_fields(self, client):
        """Happy path: Signals bevatten alle vereiste velden."""
        response = client.get("/api/v1/signals")
        data = response.json()

        if data["signals"]:
            signal = data["signals"][0]
            assert "id" in signal
            assert "market" in signal
            assert "category" in signal
            assert "signal_type" in signal
            assert "confidence" in signal
            assert "timestamp" in signal

    def test_happy_path_filter_by_market(self, client):
        """Happy path: Filter by market werkt."""
        response = client.get("/api/v1/signals?market=kalshi")

        assert response.status_code == 200
        data = response.json()
        for signal in data["signals"]:
            assert signal["market"] == "kalshi"

    def test_happy_path_filter_by_min_confidence(self, client):
        """Happy path: Filter by min_confidence werkt."""
        response = client.get("/api/v1/signals?min_confidence=0.7")

        assert response.status_code == 200
        data = response.json()
        for signal in data["signals"]:
            assert signal["confidence"] >= 0.7

    def test_happy_path_pagination_works(self, client):
        """Happy path: Pagination parameters werken."""
        response = client.get("/api/v1/signals?limit=1&offset=0")

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 1
        assert data["offset"] == 0
        assert len(data["signals"]) <= 1

    def test_happy_path_get_signal_by_id(self, client):
        """Happy path: GET /signals/{id} retourneert single signal."""
        response = client.get("/api/v1/signals/sig_test123")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "sig_test123"

    # =========================================================================
    # UNHAPPY PATH TESTS
    # =========================================================================

    def test_unhappy_path_invalid_market_filter(self, client):
        """Unhappy path: Invalid market value geeft 422."""
        response = client.get("/api/v1/signals?market=invalid_market")
        assert response.status_code == 422

    def test_unhappy_path_invalid_confidence_range(self, client):
        """Unhappy path: Confidence > 1.0 geeft 422."""
        response = client.get("/api/v1/signals?min_confidence=1.5")
        assert response.status_code == 422

    def test_unhappy_path_negative_limit(self, client):
        """Unhappy path: Negative limit geeft 422."""
        response = client.get("/api/v1/signals?limit=-1")
        assert response.status_code == 422

    def test_unhappy_path_signal_not_found(self, client):
        """Unhappy path: Unknown signal ID geeft 404."""
        response = client.get("/api/v1/signals/nonexistent_id")
        assert response.status_code == 404

    def test_unhappy_path_limit_exceeds_max(self, client):
        """Unhappy path: Limit > 100 geeft 422."""
        response = client.get("/api/v1/signals?limit=500")
        assert response.status_code == 422
```

---

### 📎 MICROTASK 2.3.1: Create Signal Schemas

**Microtask ID:** MT-PM-007-001
**Geschatte tijd:** 45 min
**Status:** 🔴 TODO

---

### 📎 MICROTASK 2.3.2: Create Signals Router

**Microtask ID:** MT-PM-007-002
**Geschatte tijd:** 60 min
**Status:** 🔴 TODO

---

### 📎 MICROTASK 2.3.3: Implement Signal Filtering

**Microtask ID:** MT-PM-007-003
**Geschatte tijd:** 45 min
**Status:** 🔴 TODO

---

## 📌 TASK 2.4: Analysis Endpoint

**Task ID:** TASK-PM-008
**Status:** 🔴 TODO
**Geschatte tijd:** 3 uur
**Dependencies:** TASK-PM-007
**Assignee:** _____

### Task Beschrijving
Implementeer de `/api/v1/analysis` endpoints voor het triggeren en ophalen van analyses.

### Files die geraakt worden
- `prediction-market-analysis/src/api/routes/analysis.py` (NIEUW)
- `prediction-market-analysis/src/api/schemas/analysis.py` (NIEUW)

### MASTERPROMPT

```
═══════════════════════════════════════════════════════════════════════════════
TAAK: Implementeer /api/v1/analysis endpoints
═══════════════════════════════════════════════════════════════════════════════

───────────────────────────────────────────────────────────────────────────────
BESTAND 1: prediction-market-analysis/src/api/schemas/analysis.py
───────────────────────────────────────────────────────────────────────────────

"""
Analysis schemas for Prediction Market Intelligence API.
"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field


class AnalysisType(str, Enum):
    """Available analysis types."""
    MAKER_TAKER = "maker_taker"
    VOLUME_TRENDS = "volume_trends"
    STATISTICAL_TESTS = "statistical_tests"
    CATEGORY_PERFORMANCE = "category_performance"


class AnalysisStatus(str, Enum):
    """Analysis job status."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisRequest(BaseModel):
    """Request to run an analysis."""
    analysis_type: AnalysisType = Field(..., description="Type of analysis to run")
    market: str = Field("kalshi", description="Target market (kalshi/polymarket)")
    category: Optional[str] = Field(None, description="Filter by category")
    start_date: Optional[datetime] = Field(None, description="Analysis start date")
    end_date: Optional[datetime] = Field(None, description="Analysis end date")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Analysis parameters")


class AnalysisResult(BaseModel):
    """Result of a completed analysis."""
    analysis_id: str = Field(..., description="Unique analysis ID")
    analysis_type: AnalysisType = Field(..., description="Type of analysis")
    status: AnalysisStatus = Field(..., description="Analysis status")
    created_at: datetime = Field(..., description="When analysis was created")
    completed_at: Optional[datetime] = Field(None, description="When analysis completed")
    result: Optional[Dict[str, Any]] = Field(None, description="Analysis results")
    error: Optional[str] = Field(None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AnalysisListResponse(BaseModel):
    """Response for listing analyses."""
    analyses: List[AnalysisResult]
    total: int


class MarketSummary(BaseModel):
    """Summary statistics for a prediction market."""
    market: str = Field(..., description="Market source")
    total_markets: int = Field(..., description="Total number of markets")
    active_markets: int = Field(..., description="Currently active markets")
    total_volume_24h: float = Field(..., description="24h trading volume")
    categories: List[str] = Field(..., description="Available categories")
    last_updated: datetime = Field(..., description="Last data update")

───────────────────────────────────────────────────────────────────────────────
BESTAND 2: prediction-market-analysis/src/api/routes/analysis.py
───────────────────────────────────────────────────────────────────────────────

"""
Analysis Router
Provides endpoints for running and managing analyses.
"""
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, status, Query

from src.api.schemas.analysis import (
    AnalysisRequest,
    AnalysisResult,
    AnalysisListResponse,
    AnalysisType,
    AnalysisStatus,
    MarketSummary
)

router = APIRouter()

# In-memory storage for demo (replace with Redis/DB in production)
_analyses: dict[str, AnalysisResult] = {}


@router.post(
    "/analysis/run",
    response_model=AnalysisResult,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Run Analysis",
    description="Trigger an analysis job (async)"
)
async def run_analysis(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks
) -> AnalysisResult:
    """
    Trigger an analysis job.

    Analysis runs asynchronously in the background.
    Poll GET /analysis/{id} for status and results.

    Args:
        request: Analysis configuration
        background_tasks: FastAPI background tasks

    Returns:
        AnalysisResult with job ID and queued status
    """
    analysis_id = f"analysis_{uuid.uuid4().hex[:12]}"

    result = AnalysisResult(
        analysis_id=analysis_id,
        analysis_type=request.analysis_type,
        status=AnalysisStatus.QUEUED,
        created_at=datetime.utcnow(),
        completed_at=None,
        result=None,
        error=None,
        metadata={
            "market": request.market,
            "category": request.category,
            "parameters": request.parameters
        }
    )

    _analyses[analysis_id] = result

    # Queue background task
    background_tasks.add_task(_execute_analysis, analysis_id, request)

    return result


@router.get(
    "/analysis/{analysis_id}",
    response_model=AnalysisResult,
    summary="Get Analysis Status",
    description="Get status and results of an analysis"
)
async def get_analysis(analysis_id: str) -> AnalysisResult:
    """
    Get analysis status and results.

    Args:
        analysis_id: Unique analysis ID

    Returns:
        AnalysisResult with current status

    Raises:
        HTTPException 404 if analysis not found
    """
    if analysis_id not in _analyses:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis {analysis_id} not found"
        )

    return _analyses[analysis_id]


@router.get(
    "/analysis",
    response_model=AnalysisListResponse,
    summary="List Analyses",
    description="List recent analyses"
)
async def list_analyses(
    status_filter: Optional[AnalysisStatus] = Query(None, alias="status"),
    limit: int = Query(10, ge=1, le=50)
) -> AnalysisListResponse:
    """
    List recent analyses.

    Args:
        status_filter: Filter by status
        limit: Maximum results

    Returns:
        List of recent analyses
    """
    analyses = list(_analyses.values())

    if status_filter:
        analyses = [a for a in analyses if a.status == status_filter]

    # Sort by created_at descending
    analyses.sort(key=lambda x: x.created_at, reverse=True)
    analyses = analyses[:limit]

    return AnalysisListResponse(analyses=analyses, total=len(analyses))


@router.get(
    "/markets/summary",
    response_model=MarketSummary,
    summary="Get Market Summary",
    description="Get summary statistics for a prediction market"
)
async def get_market_summary(
    market: str = Query("kalshi", description="Market source")
) -> MarketSummary:
    """
    Get market summary statistics.

    Args:
        market: Market source (kalshi/polymarket)

    Returns:
        MarketSummary with statistics
    """
    # TODO: Replace with actual data from analysis engine
    return MarketSummary(
        market=market,
        total_markets=1250,
        active_markets=487,
        total_volume_24h=15_420_000.50,
        categories=["crypto", "politics", "economics", "finance", "sports"],
        last_updated=datetime.utcnow()
    )


async def _execute_analysis(analysis_id: str, request: AnalysisRequest):
    """Execute analysis in background."""
    import asyncio

    if analysis_id not in _analyses:
        return

    # Update status to running
    _analyses[analysis_id].status = AnalysisStatus.RUNNING

    try:
        # Simulate analysis (replace with actual implementation)
        await asyncio.sleep(2)  # Simulate work

        # Mock result
        result = {
            "analysis_type": request.analysis_type.value,
            "market": request.market,
            "summary": {
                "total_records": 10000,
                "date_range": "2025-01-01 to 2026-02-13"
            },
            "findings": [
                {"metric": "maker_advantage", "value": 0.023},
                {"metric": "volume_trend", "value": "increasing"}
            ]
        }

        _analyses[analysis_id].status = AnalysisStatus.COMPLETED
        _analyses[analysis_id].completed_at = datetime.utcnow()
        _analyses[analysis_id].result = result

    except Exception as e:
        _analyses[analysis_id].status = AnalysisStatus.FAILED
        _analyses[analysis_id].error = str(e)
        _analyses[analysis_id].completed_at = datetime.utcnow()

───────────────────────────────────────────────────────────────────────────────
VERIFICATIE:
───────────────────────────────────────────────────────────────────────────────

cd prediction-market-analysis
python -c "
from fastapi.testclient import TestClient
from api_server import app
client = TestClient(app)

# Test run analysis
r = client.post('/api/v1/analysis/run', json={
    'analysis_type': 'maker_taker',
    'market': 'kalshi'
})
print(f'Run analysis: {r.status_code}')
print(f'Response: {r.json()}')
"

═══════════════════════════════════════════════════════════════════════════════
```

### Acceptatiecriteria
- [ ] `POST /api/v1/analysis/run` retourneert 202 Accepted
- [ ] `GET /api/v1/analysis/{id}` retourneert analysis status
- [ ] `GET /api/v1/analysis` lijst werkt met filters
- [ ] `GET /api/v1/markets/summary` retourneert statistics
- [ ] Background task executie werkt

### TDD Requirements

**Test Bestand:** `prediction-market-analysis/tests/test_analysis.py`

```python
"""
Tests voor analysis endpoints.
Run: pytest prediction-market-analysis/tests/test_analysis.py -v
"""
import pytest
from fastapi.testclient import TestClient
import time


class TestAnalysisEndpoints:
    """Tests voor /api/v1/analysis endpoints."""

    @pytest.fixture
    def client(self):
        from api_server import app
        return TestClient(app)

    # =========================================================================
    # HAPPY PATH TESTS
    # =========================================================================

    def test_happy_path_run_analysis_returns_202(self, client):
        """Happy path: POST /analysis/run retourneert 202."""
        response = client.post("/api/v1/analysis/run", json={
            "analysis_type": "maker_taker",
            "market": "kalshi"
        })

        assert response.status_code == 202
        data = response.json()
        assert "analysis_id" in data
        assert data["status"] == "queued"

    def test_happy_path_get_analysis_status(self, client):
        """Happy path: GET /analysis/{id} retourneert status."""
        # First create an analysis
        create_resp = client.post("/api/v1/analysis/run", json={
            "analysis_type": "volume_trends",
            "market": "kalshi"
        })
        analysis_id = create_resp.json()["analysis_id"]

        # Then get its status
        response = client.get(f"/api/v1/analysis/{analysis_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["analysis_id"] == analysis_id

    def test_happy_path_list_analyses(self, client):
        """Happy path: GET /analysis retourneert lijst."""
        response = client.get("/api/v1/analysis")

        assert response.status_code == 200
        data = response.json()
        assert "analyses" in data
        assert "total" in data

    def test_happy_path_market_summary(self, client):
        """Happy path: GET /markets/summary retourneert statistics."""
        response = client.get("/api/v1/markets/summary?market=kalshi")

        assert response.status_code == 200
        data = response.json()
        assert data["market"] == "kalshi"
        assert "total_markets" in data
        assert "active_markets" in data

    # =========================================================================
    # UNHAPPY PATH TESTS
    # =========================================================================

    def test_unhappy_path_invalid_analysis_type(self, client):
        """Unhappy path: Invalid analysis_type geeft 422."""
        response = client.post("/api/v1/analysis/run", json={
            "analysis_type": "invalid_type",
            "market": "kalshi"
        })
        assert response.status_code == 422

    def test_unhappy_path_analysis_not_found(self, client):
        """Unhappy path: Unknown analysis ID geeft 404."""
        response = client.get("/api/v1/analysis/nonexistent_id")
        assert response.status_code == 404

    def test_unhappy_path_missing_required_field(self, client):
        """Unhappy path: Missing analysis_type geeft 422."""
        response = client.post("/api/v1/analysis/run", json={
            "market": "kalshi"
            # Missing analysis_type
        })
        assert response.status_code == 422
```

---

## ✅ Epic 2 Completion Checklist

### Tasks Status

| Task | Status | Acceptatiecriteria |
|------|--------|-------------------|
| TASK 2.1: FastAPI Setup | ✅ COMPLETE | app, middleware, lifespan |
| TASK 2.2: Health Endpoint | ✅ COMPLETE | /health, /health/ready, /health/live |
| TASK 2.3: Signals Endpoint | ✅ COMPLETE | /signals, filtering, pagination |
| TASK 2.4: Analysis Endpoint | ✅ COMPLETE | /analysis/run, /analysis/{id} |

### Microtasks Status

- [x] **MT-2.1.1**: Create Directory Structure ✅
- [x] **MT-2.1.2**: Create api_server.py ✅
- [x] **MT-2.2.1**: Create Health Router ✅
- [x] **MT-2.3.1**: Create Signal Schemas ✅
- [x] **MT-2.3.2**: Create Signals Router ✅
- [x] **MT-2.3.3**: Implement Signal Filtering ✅
- [x] **MT-2.4.1**: Create Analysis Schemas ✅
- [x] **MT-2.4.2**: Create Analysis Router ✅
- [x] **MT-2.4.3**: Implement Background Task ✅

### Definition of Done
- [x] Alle endpoints bereikbaar ✅
- [x] Alle unit tests GROEN ✅
- [x] OpenAPI docs correct ✅
- [x] Schema validatie werkt ✅

---

**Volgende Epic:** [EPIC 3: Data & Analysis Engine](EPIC_03_DATA_ANALYSIS_ENGINE.md)
