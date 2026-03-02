"""
Phase 5b Integration Tests: Monitoring API + SoulObserver

Validates the monitoring API endpoints return correct data structures
and handle edge cases (kill switch, missing Redis, rahu blocking).
"""

import json
from unittest.mock import AsyncMock

import pytest

# Create a minimal FastAPI app for testing
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from backend.api.monitoring_api import _observer, router
from backend.monitoring.soul_observer import SoulObserver

_test_app = FastAPI()
_test_app.include_router(router, prefix="/monitoring")


@pytest.fixture
async def client():
    transport = ASGITransport(app=_test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_health_endpoint_returns_all_layers(client):
    """GET /monitoring/health should return soul/mind/body status."""
    response = await client.get("/monitoring/health")
    assert response.status_code == 200

    data = response.json()
    assert "soul" in data
    assert "mind" in data
    assert "body" in data
    assert "status" in data["soul"]


@pytest.mark.asyncio
async def test_soul_context_endpoint_returns_data(client):
    """GET /monitoring/soul-context should return 200."""
    response = await client.get("/monitoring/soul-context")
    assert response.status_code == 200
    # Without Redis, it should return a warning
    data = response.json()
    assert "warning" in data or "timestamp" in data


@pytest.mark.asyncio
async def test_karma_summary_endpoint(client):
    """GET /monitoring/karma-summary should return stats."""
    response = await client.get("/monitoring/karma-summary")
    assert response.status_code == 200

    data = response.json()
    assert "episode_count" in data
    assert "avg_karma" in data


@pytest.mark.asyncio
async def test_kill_switch_requires_confirmation(client):
    """POST /monitoring/kill-switch without confirm -> 400."""
    response = await client.post("/monitoring/kill-switch", json={"confirm": False})
    assert response.status_code == 400
    assert "confirmation" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_kill_switch_activates_with_confirmation(client):
    """POST /monitoring/kill-switch with confirm=true -> 200."""
    response = await client.post("/monitoring/kill-switch", json={"confirm": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "activated"
    assert data["kill_switch"] is True


@pytest.mark.asyncio
async def test_why_no_trade_with_rahu_kala():
    """SoulObserver.why_no_trade should detect Rahu Kala blocking."""
    observer = SoulObserver()
    # Inject mock Redis with rahu_kala context
    observer.redis_client = AsyncMock()

    rahu_context = {
        "timestamp": "2026-01-01T00:00:00+00:00",
        "rahu_kala_active": True,
        "trading_gate_open": False,
        "market_regime": "BULL",
    }
    observer.redis_client.get = AsyncMock(return_value=json.dumps(rahu_context))

    reasons = await observer.why_no_trade()
    assert any("Rahu Kala" in r for r in reasons)
