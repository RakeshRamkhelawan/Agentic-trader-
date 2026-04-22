import pytest
from httpx import ASGITransport, AsyncClient

from backend.api.main import app


@pytest.mark.asyncio
async def test_unauthenticated_trading_returns_401():
    """Trading endpoints MUST require authentication."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        endpoints = [
            ("GET", "/api/v1/trading/markets"),
            ("GET", "/api/v1/trading/portfolio"),
            ("GET", "/api/v1/trading/orders/active"),
            ("POST", "/api/v1/trading/orders"),
        ]
        for method, path in endpoints:
            resp = await client.request(method, path)
            assert (
                resp.status_code == 401
            ), f"{method} {path} should require auth, got {resp.status_code}"


@pytest.mark.asyncio
async def test_legacy_token_endpoint_removed():
    """The unauthenticated /auth/token endpoint must not exist."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/auth/token", json={"tenant_id": "x", "account_id": "y"})
        assert resp.status_code in (
            401,
            404,
            405,
        ), "Legacy token endpoint should be removed or secured"
