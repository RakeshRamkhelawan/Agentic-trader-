"""
Tests for Prediction Market Proxy API.
Run: pytest backend/tests/api/test_prediction_api.py -v
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.api.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


class TestPredictionSignalsAPI:
    """Tests for signals endpoints."""

    # =========================================================================
    # HAPPY PATH TESTS
    # =========================================================================

    def test_happy_path_get_signals_success(self, client):
        """Happy path: GET /api/v1/prediction/signals returns signals."""
        mock_signal = MagicMock()
        mock_signal.id = "sig_123"
        mock_signal.market = "kalshi"
        mock_signal.category = "crypto"
        mock_signal.signal_type = "bullish"
        mock_signal.confidence = 0.85
        mock_signal.symbol = "BTC"
        mock_signal.indicators = {"maker_advantage": 0.02}
        mock_signal.timestamp = datetime.fromisoformat("2026-02-13T10:00:00")
        mock_signal.metadata = {"source": "maker_taker"}

        with patch("backend.api.prediction_api.get_prediction_client") as mock_get:
            mock_http_client = AsyncMock()
            mock_http_client.enabled = True
            mock_http_client.get_signals = AsyncMock(return_value=[mock_signal])
            mock_get.return_value = mock_http_client

            response = client.get("/api/v1/prediction/signals")

            assert response.status_code == 200
            data = response.json()
            assert "signals" in data
            assert "total" in data
            assert data["total"] == 1
            assert data["signals"][0]["signal_type"] == "bullish"

    def test_happy_path_get_signals_with_filters(self, client):
        """Happy path: GET /api/v1/prediction/signals with query parameters."""
        with patch("backend.api.prediction_api.get_prediction_client") as mock_get:
            mock_http_client = AsyncMock()
            mock_http_client.enabled = True
            mock_http_client.get_signals = AsyncMock(return_value=[])
            mock_get.return_value = mock_http_client

            response = client.get(
                "/api/v1/prediction/signals",
                params={
                    "market": "kalshi",
                    "symbol": "BTC",
                    "min_confidence": 0.7,
                    "limit": 20,
                },
            )

            assert response.status_code == 200
            # Verify parameters were passed correctly
            mock_http_client.get_signals.assert_called_once()
            call_kwargs = mock_http_client.get_signals.call_args.kwargs
            assert call_kwargs.get("market") == "kalshi"
            assert call_kwargs.get("symbol") == "BTC"
            assert call_kwargs.get("min_confidence") == 0.7
            assert call_kwargs.get("limit") == 20

    def test_happy_path_get_signal_by_id(self, client):
        """Happy path: GET /api/v1/prediction/signals/{id} returns signal."""
        mock_signal = MagicMock()
        mock_signal.id = "sig_123"
        mock_signal.market = "kalshi"
        mock_signal.category = "crypto"
        mock_signal.signal_type = "bullish"
        mock_signal.confidence = 0.85
        mock_signal.symbol = "BTC"
        mock_signal.indicators = {}
        mock_signal.timestamp = datetime.fromisoformat("2026-02-13T10:00:00")
        mock_signal.metadata = {}

        with patch("backend.api.prediction_api.get_prediction_client") as mock_get:
            mock_http_client = AsyncMock()
            mock_http_client.enabled = True
            mock_http_client.get_signal_by_id = AsyncMock(return_value=mock_signal)
            mock_get.return_value = mock_http_client

            response = client.get("/api/v1/prediction/signals/sig_123")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "sig_123"
            assert data["market"] == "kalshi"

    # =========================================================================
    # UNHAPPY PATH TESTS
    # =========================================================================

    def test_unhappy_path_service_disabled(self, client):
        """Unhappy path: Service disabled returns 503."""
        with patch("backend.api.prediction_api.get_prediction_client") as mock_get:
            mock_http_client = AsyncMock()
            mock_http_client.enabled = False
            mock_get.return_value = mock_http_client

            response = client.get("/api/v1/prediction/signals")

            assert response.status_code == 503
            data = response.json()
            assert "disabled" in data["detail"].lower()

    def test_unhappy_path_signal_not_found(self, client):
        """Unhappy path: Signal not found returns 404."""
        with patch("backend.api.prediction_api.get_prediction_client") as mock_get:
            mock_http_client = AsyncMock()
            mock_http_client.enabled = True
            mock_http_client.get_signal_by_id = AsyncMock(return_value=None)
            mock_get.return_value = mock_http_client

            response = client.get("/api/v1/prediction/signals/nonexistent")

            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"].lower()

    def test_unhappy_path_service_error(self, client):
        """Unhappy path: Service error returns 502."""
        with patch("backend.api.prediction_api.get_prediction_client") as mock_get:
            mock_http_client = AsyncMock()
            mock_http_client.enabled = True
            mock_http_client.get_signals = AsyncMock(side_effect=Exception("Connection failed"))
            mock_get.return_value = mock_http_client

            response = client.get("/api/v1/prediction/signals")

            assert response.status_code == 502


class TestPredictionAnalysisAPI:
    """Tests for analysis endpoints."""

    def test_happy_path_run_analysis(self, client):
        """Happy path: POST /api/v1/prediction/analysis starts job."""
        with patch("backend.api.prediction_api.get_prediction_client") as mock_get:
            mock_http_client = AsyncMock()
            mock_http_client.enabled = True
            mock_http_client.run_analysis = AsyncMock(
                return_value={"job_id": "job_456", "status": "queued"}
            )
            mock_get.return_value = mock_http_client

            response = client.post(
                "/api/v1/prediction/analysis",
                json={"analysis_type": "maker_taker", "market": "kalshi"},
            )

            assert response.status_code == 202
            data = response.json()
            assert data["job_id"] == "job_456"
            assert data["status"] == "queued"

    def test_happy_path_get_analysis_status(self, client):
        """Happy path: GET /api/v1/prediction/analysis/{id} returns status."""
        with patch("backend.api.prediction_api.get_prediction_client") as mock_get:
            mock_http_client = AsyncMock()
            mock_http_client.enabled = True
            mock_http_client.get_analysis_status = AsyncMock(
                return_value={
                    "status": "completed",
                    "progress": 100.0,
                    "results": {"metric1": 0.5},
                }
            )
            mock_get.return_value = mock_http_client

            response = client.get("/api/v1/prediction/analysis/job_456")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "completed"
            assert data["progress"] == 100.0
            assert data["results"]["metric1"] == 0.5

    def test_unhappy_path_analysis_not_found(self, client):
        """Unhappy path: Analysis not found returns 404."""
        with patch("backend.api.prediction_api.get_prediction_client") as mock_get:
            mock_http_client = AsyncMock()
            mock_http_client.enabled = True
            mock_http_client.get_analysis_status = AsyncMock(
                return_value={"status": "error", "error": "Job not found"}
            )
            mock_get.return_value = mock_http_client

            response = client.get("/api/v1/prediction/analysis/nonexistent")

            assert response.status_code == 404


class TestPredictionMarketAPI:
    """Tests for market data endpoints."""

    def test_happy_path_get_market_summary(self, client):
        """Happy path: GET /api/v1/prediction/markets/summary returns data."""
        with patch("backend.api.prediction_api.get_prediction_client") as mock_get:
            mock_http_client = AsyncMock()
            mock_http_client.enabled = True
            mock_http_client.get_market_summary = AsyncMock(
                return_value={
                    "market": "kalshi",
                    "total_volume": 1000000.0,
                    "total_trades": 5000,
                    "active_contracts": 150,
                    "timestamp": "2026-02-13T10:00:00",
                }
            )
            mock_get.return_value = mock_http_client

            response = client.get("/api/v1/prediction/markets/summary")

            assert response.status_code == 200
            data = response.json()
            assert data["market"] == "kalshi"
            assert data["total_volume"] == 1000000.0
            assert data["active_contracts"] == 150

    def test_happy_path_market_summary_with_filter(self, client):
        """Happy path: GET /api/v1/prediction/markets/summary with market filter."""
        with patch("backend.api.prediction_api.get_prediction_client") as mock_get:
            mock_http_client = AsyncMock()
            mock_http_client.enabled = True
            mock_http_client.get_market_summary = AsyncMock(return_value={})
            mock_get.return_value = mock_http_client

            response = client.get(
                "/api/v1/prediction/markets/summary", params={"market": "polymarket"}
            )

            assert response.status_code == 200
            # Verify market parameter passed
            mock_http_client.get_market_summary.assert_called_once_with("polymarket")


class TestPredictionHealthAPI:
    """Tests for health/status endpoints."""

    def test_happy_path_get_status_healthy(self, client):
        """Happy path: GET /api/v1/prediction/health returns healthy status."""
        with patch("backend.api.prediction_api.get_prediction_client") as mock_get:
            mock_http_client = AsyncMock()
            mock_http_client.enabled = True
            mock_http_client.base_url = "http://prediction:8002"
            mock_http_client._circuit_state = MagicMock(value="closed")
            mock_http_client.health_check = AsyncMock(return_value={"status": "healthy"})
            mock_get.return_value = mock_http_client

            response = client.get("/api/v1/prediction/health")

            assert response.status_code == 200
            data = response.json()
            assert data["enabled"] is True
            assert data["healthy"] is True
            assert data["circuit_state"] == "closed"
            assert "timestamp" in data

    def test_happy_path_get_status_unhealthy(self, client):
        """Happy path: GET /api/v1/prediction/health reports unhealthy."""
        with patch("backend.api.prediction_api.get_prediction_client") as mock_get:
            mock_http_client = AsyncMock()
            mock_http_client.enabled = True
            mock_http_client.base_url = "http://prediction:8002"
            mock_http_client._circuit_state = MagicMock(value="open")
            mock_http_client.health_check = AsyncMock(return_value={"status": "unhealthy"})
            mock_get.return_value = mock_http_client

            response = client.get("/api/v1/prediction/health")

            assert response.status_code == 200
            data = response.json()
            assert data["enabled"] is True
            assert data["healthy"] is False
            assert data["circuit_state"] == "open"

    def test_happy_path_get_status_health_check_failure(self, client):
        """Happy path: Health check failure doesn't break status endpoint."""
        with patch("backend.api.prediction_api.get_prediction_client") as mock_get:
            mock_http_client = AsyncMock()
            mock_http_client.enabled = True
            mock_http_client.base_url = "http://prediction:8002"
            mock_http_client._circuit_state = MagicMock(value="half_open")
            mock_http_client.health_check = AsyncMock(side_effect=Exception("Connection refused"))
            mock_get.return_value = mock_http_client

            response = client.get("/api/v1/prediction/health")

            assert response.status_code == 200
            data = response.json()
            assert data["healthy"] is False  # Service checks still returns gracefully


class TestPredictionAPIValidation:
    """Tests for request validation."""

    def test_happy_path_limit_parameter_validation(self, client):
        """Happy path: Limit parameter accepts valid values."""
        with patch("backend.api.prediction_api.get_prediction_client") as mock_get:
            mock_http_client = AsyncMock()
            mock_http_client.enabled = True
            mock_http_client.get_signals = AsyncMock(return_value=[])
            mock_get.return_value = mock_http_client

            # Valid limit
            response = client.get("/api/v1/prediction/signals?limit=50")
            assert response.status_code == 200

    def test_unhappy_path_limit_too_large(self, client):
        """Unhappy path: Limit exceeding max returns validation error."""
        response = client.get("/api/v1/prediction/signals?limit=150")
        # FastAPI returns 422 for validation errors
        assert response.status_code == 422

    def test_unhappy_path_confidence_out_of_range(self, client):
        """Unhappy path: Confidence outside [0, 1] returns validation error."""
        response = client.get("/api/v1/prediction/signals?min_confidence=1.5")
        assert response.status_code == 422

    def test_happy_path_analysis_request_validation(self, client):
        """Happy path: Analysis request requires analysis_type."""
        with patch("backend.api.prediction_api.get_prediction_client") as mock_get:
            mock_http_client = AsyncMock()
            mock_http_client.enabled = True
            mock_http_client.run_analysis = AsyncMock(
                return_value={"job_id": "job_123", "status": "queued"}
            )
            mock_get.return_value = mock_http_client

            response = client.post(
                "/api/v1/prediction/analysis", json={"analysis_type": "maker_taker"}
            )
            assert response.status_code == 202

    def test_unhappy_path_analysis_missing_type(self, client):
        """Unhappy path: Analysis without type returns validation error."""
        response = client.post("/api/v1/prediction/analysis", json={"market": "kalshi"})
        assert response.status_code == 422


class TestPredictionAPIDocumentation:
    """Tests for API documentation and schemas."""

    def test_happy_path_openapi_schema_available(self, client):
        """Happy path: OpenAPI schema is available."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        schema = response.json()
        # Check prediction endpoints are in schema
        assert "/api/v1/prediction/signals" in schema["paths"]
        assert "/api/v1/prediction/analysis" in schema["paths"]
        assert "/api/v1/prediction/health" in schema["paths"]

    def test_happy_path_docs_available(self, client):
        """Happy path: Swagger docs are available."""
        response = client.get("/docs")
        assert response.status_code == 200
        assert b"swagger" in response.content.lower() or b"openapi" in response.content.lower()
