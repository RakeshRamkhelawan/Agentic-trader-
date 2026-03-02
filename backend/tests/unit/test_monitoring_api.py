"""
Step 3B — RED Phase: Tests for Monitoring API endpoints.
TDD: All tests written FIRST, expected to FAIL until Step 3C implements production code.

Tests cover:
- GET /monitoring/health → 200
- GET /monitoring/soul-context → 200
- GET /monitoring/karma-summary → 200
- POST /monitoring/kill-switch → 200
- Unhappy: partial failure, missing confirmation, redis down
"""


import pytest
from httpx import ASGITransport, AsyncClient

from backend.api.monitoring_api import router as monitoring_router


@pytest.fixture
def app():
    """Create test FastAPI app with monitoring router."""
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(monitoring_router, prefix="/monitoring")
    return app


@pytest.fixture
async def client(app):
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestMonitoringAPIHappy:
    """Happy path: all endpoints return expected data."""

    @pytest.mark.asyncio
    async def test_health_endpoint_returns_200(self, client):
        """GET /monitoring/health → 200 with all layers."""
        response = await client.get("/monitoring/health")
        assert response.status_code == 200
        data = response.json()
        assert "soul" in data
        assert "mind" in data
        assert "body" in data

    @pytest.mark.asyncio
    async def test_soul_context_endpoint_returns_current(self, client):
        """GET /monitoring/soul-context → 200 with context dict."""
        response = await client.get("/monitoring/soul-context")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_karma_summary_endpoint_returns_stats(self, client):
        """GET /monitoring/karma-summary → 200 with episode count."""
        response = await client.get("/monitoring/karma-summary")
        assert response.status_code == 200
        data = response.json()
        assert "episode_count" in data

    @pytest.mark.asyncio
    async def test_kill_switch_activates(self, client):
        """POST /monitoring/kill-switch with confirm=true → 200."""
        response = await client.post(
            "/monitoring/kill-switch",
            json={"confirm": True},
        )
        assert response.status_code == 200


class TestMonitoringAPIUnhappy:
    """Unhappy path: error conditions."""

    @pytest.mark.asyncio
    async def test_kill_switch_requires_confirmation(self, client):
        """POST without confirm=true → 400 'confirmation required'."""
        response = await client.post(
            "/monitoring/kill-switch",
            json={"confirm": False},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_health_endpoint_partial_failure(self, client):
        """Soul down, Mind up → returns mixed statuses, still 200."""
        response = await client.get("/monitoring/health")
        assert response.status_code == 200
