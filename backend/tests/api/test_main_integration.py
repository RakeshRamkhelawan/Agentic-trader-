from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

# We mock the entire app import because it doesn't exist yet in the TDD cycle
# In a real run, we would import app from backend.api.main
# but for the first "Red" phase, we'll try to import it and expect failure,
# or we just write the test expecting the file to exist soon.
# To make the test runnable (but failing on import or connection), we can't import what doesn't exist.
# However, standard TDD implies writing the test code that *uses* the new module.

# Since I cannot run a test file that crashes on import in a way that gives useful specific method failures,
# I will structure the test to import `app` inside a fixture or try/except block if needed.
# But for strict TDD, I will assume `backend.api.main` WILL exist.

try:
    from backend.api.main import app
except ImportError:
    app = None  # Will fail tests if not implemented


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    if not app:
        pytest.fail("backend.api.main.app not found - Implementation missing")
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_trading_service():
    with patch("backend.services.trading_service.get_trading_service") as mock:
        service_mock = AsyncMock()
        mock.return_value = service_mock
        yield service_mock


@pytest.mark.asyncio
async def test_api_health(client):
    """Test that the API server is up and running."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_websocket_connect(client):
    """Test WebSocket connection endpoint available."""
    # Note: httpx AsyncClient doesn't support WS out of the box easily.
    # We use TestClient for handshake check or specialized WS client.
    # For integration/smoke test, checking the endpoint exists (426 Upgrade Required) is a good start
    # or using Starlette's TestClient context.

    with TestClient(app) as tc:
        with tc.websocket_connect("/ws") as websocket:
            # simple connection check
            assert websocket
            # We expect it might accept or wait for auth
            # If our logic requires auth immediately, it might close.


@pytest.mark.asyncio
async def test_place_order_unauthorized(client):
    """Unhappy Path: Place order without token."""
    response = await client.post(
        "/api/v1/trading/orders",
        json={"symbol": "BTC-EUR", "side": "buy", "quantity": 0.1, "price": 50000},
    )
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_place_order_authorized(client, mock_trading_service):
    """Happy Path: Place order with valid (mock headers) auth."""
    # We mock the auth dependency overrides
    # Accessing app.dependency_overrides directly

    async def mock_get_current_user():
        return {"id": "test_user", "sub": "test_user", "email": "test@example.com"}

    async def mock_get_tenant():
        return "test_tenant"

    app.dependency_overrides["get_current_user"] = mock_get_current_user
    app.dependency_overrides["get_current_tenant_id"] = mock_get_tenant

    mock_trading_service.execute_order.return_value = {
        "status": "submitted",
        "order_id": "rev_12345",
    }

    response = await client.post(
        "/api/v1/trading/orders",
        json={"symbol": "BTC-EUR", "side": "buy", "quantity": 0.1, "price": 50000},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "submitted"
    assert data["order_id"] == "rev_12345"

    # Cleanup
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_place_order_validation_error(client):
    """Unhappy Path: Invalid payload (negative quantity)."""

    # Assuming we have validation
    async def mock_user_ok():
        return {"id": "u", "sub": "u"}

    app.dependency_overrides["get_current_user"] = mock_user_ok

    response = await client.post(
        "/api/v1/trading/orders",
        json={
            "symbol": "BTC-EUR",
            "side": "buy",
            "quantity": -5,  # Invalid
            "price": 50000,
        },
    )

    assert response.status_code == 422  # Validation Error

    app.dependency_overrides = {}
