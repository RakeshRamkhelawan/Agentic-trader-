"""
Tests for Prediction Market Client.
Run: pytest backend/tests/test_prediction_market_client.py -v
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from backend.services.prediction_market_client import (
    CircuitBreakerConfig,
    CircuitState,
    PredictionMarketClient,
    PredictionSignal,
    get_prediction_client,
)


class TestPredictionMarketClient:
    """Tests for PredictionMarketClient."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return PredictionMarketClient(base_url="http://test:8002", timeout=5.0, max_retries=2)

    # =========================================================================
    # HAPPY PATH TESTS
    # =========================================================================

    def test_happy_path_initialization(self, client):
        """Happy path: Client initializes with correct config."""
        assert client.base_url == "http://test:8002"
        assert client.timeout == 5.0
        assert client.max_retries == 2
        assert client.enabled is True

    def test_happy_path_circuit_starts_closed(self, client):
        """Happy path: Circuit breaker starts in CLOSED state."""
        assert client._circuit_state == CircuitState.CLOSED

    def test_happy_path_check_circuit_allows_when_closed(self, client):
        """Happy path: Closed circuit allows requests."""
        assert client._check_circuit() is True

    def test_happy_path_record_success_resets_failures(self, client):
        """Happy path: Success resets failure count."""
        client._failure_count = 3
        client._record_success()
        assert client._failure_count == 0

    def test_happy_path_record_success_closes_half_open(self, client):
        """Happy path: Success closes half-open circuit."""
        client._circuit_state = CircuitState.HALF_OPEN
        client._record_success()
        assert client._circuit_state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_happy_path_get_client_creates_AsyncClient(self, client):
        """Happy path: _get_client creates AsyncClient."""
        http_client = await client._get_client()
        assert isinstance(http_client, httpx.AsyncClient)
        assert http_client.base_url == "http://test:8002"
        await client.close()

    @pytest.mark.asyncio
    async def test_happy_path_health_check_success(self, client):
        """Happy path: Health check returns status when enabled."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "healthy"}

        with patch.object(client, "_get_client", new_callable=AsyncMock) as mock_get:
            mock_http_client = AsyncMock()
            mock_http_client.get = AsyncMock(return_value=mock_response)
            mock_get.return_value = mock_http_client

            result = await client.health_check()

            assert result["status"] == "healthy"
            mock_http_client.get.assert_called_once_with("/health")

    @pytest.mark.asyncio
    async def test_happy_path_get_signals_returns_list(self, client):
        """Happy path: get_signals returns list of signals."""
        mock_response_data = {
            "signals": [
                {
                    "id": "sig_123",
                    "market": "kalshi",
                    "category": "crypto",
                    "signal_type": "bullish",
                    "confidence": 0.85,
                    "symbol": "BTC",
                    "indicators": {"ma_20": 25000, "rsi": 65},
                    "timestamp": "2026-02-13T10:00:00Z",
                    "metadata": {"source": "maker_taker"},
                }
            ]
        }

        with patch.object(client, "_request_with_retry", new_callable=AsyncMock) as mock:
            mock.return_value = MagicMock(json=lambda: mock_response_data)

            signals = await client.get_signals(limit=10, min_confidence=0.5)

            assert len(signals) == 1
            assert signals[0].market == "kalshi"
            assert signals[0].symbol == "BTC"
            assert signals[0].confidence == 0.85

    @pytest.mark.asyncio
    async def test_happy_path_run_analysis(self, client):
        """Happy path: run_analysis triggers job."""
        with patch.object(client, "_request_with_retry", new_callable=AsyncMock) as mock:
            mock.return_value = MagicMock(json=lambda: {"job_id": "job_456", "status": "queued"})

            result = await client.run_analysis("maker_taker", market="kalshi")

            assert result["job_id"] == "job_456"
            assert result["status"] == "queued"

    @pytest.mark.asyncio
    async def test_happy_path_get_analysis_status(self, client):
        """Happy path: get_analysis_status returns job status."""
        with patch.object(client, "_request_with_retry", new_callable=AsyncMock) as mock:
            mock.return_value = MagicMock(
                json=lambda: {"job_id": "job_456", "status": "completed", "results": {}}
            )

            result = await client.get_analysis_status("job_456")

            assert result["job_id"] == "job_456"
            assert result["status"] == "completed"

    @pytest.mark.asyncio
    async def test_happy_path_get_market_summary(self, client):
        """Happy path: get_market_summary returns market data."""
        with patch.object(client, "_request_with_retry", new_callable=AsyncMock) as mock:
            mock.return_value = MagicMock(
                json=lambda: {"market": "kalshi", "total_volume": 1000000}
            )

            result = await client.get_market_summary("kalshi")

            assert result["market"] == "kalshi"
            assert result["total_volume"] == 1000000

    # =========================================================================
    # UNHAPPY PATH TESTS
    # =========================================================================

    def test_unhappy_path_circuit_opens_after_failures(self, client):
        """Unhappy path: Circuit opens after threshold failures."""
        config = CircuitBreakerConfig(failure_threshold=3)
        client._circuit_config = config

        for _ in range(3):
            client._record_failure()

        assert client._circuit_state == CircuitState.OPEN

    def test_unhappy_path_open_circuit_blocks_requests(self, client):
        """Unhappy path: Open circuit blocks requests."""
        client._circuit_state = CircuitState.OPEN
        client._last_failure_time = None

        assert client._check_circuit() is False

    def test_unhappy_path_half_open_allows_limited_calls(self, client):
        """Unhappy path: Half-open circuit allows limited calls."""
        config = CircuitBreakerConfig(half_open_max_calls=3)
        client._circuit_config = config
        client._circuit_state = CircuitState.HALF_OPEN

        # Should allow first 3 calls
        for i in range(3):
            assert client._check_circuit() is True
            assert client._half_open_calls == i + 1

        # 4th call should be blocked
        assert client._check_circuit() is False

    @pytest.mark.asyncio
    async def test_unhappy_path_disabled_service_returns_empty(self, client):
        """Unhappy path: Disabled service returns empty."""
        client.enabled = False

        signals = await client.get_signals()

        assert signals == []

    @pytest.mark.asyncio
    async def test_unhappy_path_disabled_service_health_check(self, client):
        """Unhappy path: Disabled service returns disabled status."""
        client.enabled = False

        result = await client.health_check()

        assert result["status"] == "disabled"

    @pytest.mark.asyncio
    async def test_unhappy_path_health_check_connection_error(self, client):
        """Unhappy path: Health check handles connection error."""
        with patch.object(client, "_get_client", new_callable=AsyncMock) as mock:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.ConnectError("Connection refused")
            mock.return_value = mock_client

            result = await client.health_check()

            assert result["status"] == "unhealthy"
            assert "error" in result

    @pytest.mark.asyncio
    async def test_unhappy_path_get_signals_open_circuit(self, client):
        """Unhappy path: get_signals returns empty when circuit open."""
        client._circuit_state = CircuitState.OPEN

        signals = await client.get_signals()

        assert signals == []

    @pytest.mark.asyncio
    async def test_unhappy_path_get_signals_api_error(self, client):
        """Unhappy path: get_signals handles API error."""
        with patch.object(client, "_request_with_retry", new_callable=AsyncMock) as mock:
            mock.side_effect = httpx.HTTPStatusError(
                "500 Server Error", request=None, response=None
            )

            signals = await client.get_signals()

            assert signals == []

    @pytest.mark.asyncio
    async def test_unhappy_path_run_analysis_disabled(self, client):
        """Unhappy path: run_analysis returns disabled when service disabled."""
        client.enabled = False

        result = await client.run_analysis("maker_taker")

        assert result["status"] == "disabled"

    @pytest.mark.asyncio
    async def test_unhappy_path_request_with_retry_max_retries(self, client):
        """Unhappy path: Retry logic exhausts retries."""
        with patch.object(client, "_get_client", new_callable=AsyncMock) as mock:
            mock_client = AsyncMock()
            mock_client.request.side_effect = httpx.TimeoutException("Timeout")
            mock.return_value = mock_client

            with pytest.raises(Exception):
                await client._request_with_retry("GET", "/api/v1/signals")

    # =========================================================================
    # RETRY LOGIC TESTS
    # =========================================================================

    @pytest.mark.asyncio
    async def test_happy_path_retry_succeeds_on_second_attempt(self, client):
        """Happy path: Retry succeeds on second attempt."""
        call_count = 0

        async def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise httpx.TimeoutException("Timeout")
            return MagicMock(json=lambda: {"signals": []}, raise_for_status=lambda: None)

        with patch.object(client, "_get_client", new_callable=AsyncMock) as mock:
            mock_client = AsyncMock()
            mock_client.request = mock_request
            mock.return_value = mock_client

            signals = await client.get_signals()

            assert call_count == 2
            assert signals == []


class TestGlobalClientInstance:
    """Tests for global client instance."""

    def test_get_prediction_client_singleton(self):
        """Test that get_prediction_client returns singleton."""
        client1 = get_prediction_client()
        client2 = get_prediction_client()

        assert client1 is client2


class TestPredictionSignalModel:
    """Tests for PredictionSignal Pydantic model."""

    def test_happy_path_signal_creation(self):
        """Happy path: Create PredictionSignal from dict."""
        signal_data = {
            "id": "sig_123",
            "market": "kalshi",
            "category": "crypto",
            "signal_type": "bullish",
            "confidence": 0.85,
            "symbol": "BTC",
            "indicators": {"ma_20": 25000},
            "timestamp": "2026-02-13T10:00:00Z",
            "metadata": {"source": "test"},
        }

        signal = PredictionSignal(**signal_data)

        assert signal.id == "sig_123"
        assert signal.confidence == 0.85
        assert signal.market == "kalshi"

    def test_unhappy_path_signal_missing_required_field(self):
        """Unhappy path: Signal without required field fails."""
        signal_data = {
            "id": "sig_123",
            "market": "kalshi",
            # Missing other required fields
        }

        with pytest.raises(Exception):
            PredictionSignal(**signal_data)
