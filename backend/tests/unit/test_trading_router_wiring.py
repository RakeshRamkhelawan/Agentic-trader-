import pytest
from fastapi.testclient import TestClient


def test_trading_endpoints_exist():
    """Verify all required trading endpoints are registered."""
    from backend.api.main import app

    routes = [r.path for r in app.routes]
    assert "/api/v1/trading/markets" in routes
    assert "/api/v1/trading/portfolio" in routes
    assert "/api/v1/trading/history" in routes
    assert "/api/v1/trading/orders" in routes
    assert "/api/v1/trading/orders/active" in routes
    assert "/api/v1/trading/orders/{order_id}" in routes
