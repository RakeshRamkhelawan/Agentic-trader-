from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.api.main import app

# We need to test:
# 1. Startup event initializes pipeline
# 2. Shutdown event stops pipeline
# 3. /health endpoint reports status


@pytest.fixture
def mock_pipeline():
    mock = MagicMock()
    mock.start = AsyncMock()
    mock.stop = AsyncMock()
    mock.raw_queue.qsize.return_value = 10
    mock.providers = [MagicMock(), MagicMock()]
    mock.providers[0].name = "bybit"
    mock.providers[0].connect_count = 5  # internal state?
    mock.providers[1].name = "kraken"

    # We patch initialize_market_data to return this mock
    with patch("backend.api.main.initialize_market_data", return_value=mock):
        yield mock


@pytest.mark.asyncio
async def test_startup_shutdown_lifecycle():
    """Test that pipeline starts and stops with app."""
    # This is tricky with TestClient because startup/shutdown hooks run in context manager.

    with patch("backend.api.main.initialize_market_data") as init_mock:
        init_mock.return_value.start = AsyncMock()
        init_mock.return_value.stop = AsyncMock()

        with TestClient(app):
            # Startup runs on enter
            assert init_mock.called
            pipeline = init_mock.return_value
            assert pipeline.start.called

        # Shutdown runs on exit
        assert pipeline.stop.called


def test_health_endpoint_market_data(mock_pipeline):
    """Test /health/market-data endpoint."""
    with TestClient(app) as client:
        response = client.get("/api/v1/health/market-data")
        # Expect 404 initially if not implemented
        if response.status_code == 404:
            pytest.fail("Endpoint not implemented")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["queue_size"] == 10
        assert "providers" in data
