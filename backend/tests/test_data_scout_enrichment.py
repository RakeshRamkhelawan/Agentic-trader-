"""
Tests for DataScout Agent Prediction Market Enrichment.
Run: pytest backend/tests/test_data_scout_enrichment.py -v
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.agents.data_scout_agent import DataScoutAgent
from backend.core.schemas.ooda_types import Observation


class TestDataScoutPredictionEnrichment:
    """Tests for prediction market enrichment in DataScout agent."""

    @pytest.fixture
    def data_scout(self):
        """Create DataScout agent for testing."""
        return DataScoutAgent(llm_provider=None, event_bus=None, data_source=None)

    # =========================================================================
    # HAPPY PATH TESTS
    # =========================================================================

    @pytest.mark.asyncio
    async def test_happy_path_fetch_prediction_signals_returns_list(self, data_scout):
        """Happy path: _fetch_prediction_signals returns list of signal dicts."""
        # Mock prediction market client
        mock_signal = MagicMock()
        mock_signal.id = "sig_123"
        mock_signal.market = "kalshi"
        mock_signal.category = "crypto"
        mock_signal.signal_type = "bullish"
        mock_signal.confidence = 0.85
        mock_signal.indicators = {"maker_advantage": 0.02, "volume_spike": 1.5}
        mock_signal.timestamp = datetime.fromisoformat("2026-02-13T10:00:00")
        mock_signal.metadata = {"source": "maker_taker", "period": "1h"}

        with patch("backend.agents.data_scout_agent.get_prediction_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.get_signals = AsyncMock(return_value=[mock_signal])
            mock_get.return_value = mock_client

            signals = await data_scout._fetch_prediction_signals("BTC")

            assert len(signals) == 1
            assert signals[0]["signal_type"] == "bullish"
            assert signals[0]["confidence"] == 0.85
            assert signals[0]["market"] == "kalshi"
            assert signals[0]["indicators"] == {
                "maker_advantage": 0.02,
                "volume_spike": 1.5,
            }

    @pytest.mark.asyncio
    async def test_happy_path_fetch_multiple_signals(self, data_scout):
        """Happy path: Fetch multiple prediction signals."""
        mock_signals = []
        for i in range(3):
            mock_signal = MagicMock()
            mock_signal.id = f"sig_{i}"
            mock_signal.market = "kalshi"
            mock_signal.category = "crypto"
            mock_signal.signal_type = "bullish" if i % 2 == 0 else "bearish"
            mock_signal.confidence = 0.7 + (i * 0.05)
            mock_signal.indicators = {}
            mock_signal.timestamp = datetime.fromisoformat("2026-02-13T10:00:00")
            mock_signal.metadata = {}
            mock_signals.append(mock_signal)

        with patch("backend.agents.data_scout_agent.get_prediction_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.get_signals = AsyncMock(return_value=mock_signals)
            mock_get.return_value = mock_client

            signals = await data_scout._fetch_prediction_signals("BTC")

            assert len(signals) == 3
            assert signals[0]["id"] == "sig_0"
            assert signals[1]["id"] == "sig_1"
            assert signals[2]["id"] == "sig_2"

    @pytest.mark.asyncio
    async def test_happy_path_observation_includes_signals(self, data_scout):
        """Happy path: Observation includes prediction signals."""
        obs = Observation(
            symbol="BTC/USDT",
            price=50000.0,
            volume=100.0,
            orderbook={"bids": [], "asks": []},
            raw_ticker={"last": 50000.0},
            prediction_signals=[
                {
                    "id": "sig_1",
                    "market": "kalshi",
                    "signal_type": "bullish",
                    "confidence": 0.8,
                }
            ],
        )

        assert len(obs.prediction_signals) == 1
        assert obs.prediction_signals[0]["signal_type"] == "bullish"
        assert obs.prediction_signals[0]["confidence"] == 0.8

    @pytest.mark.asyncio
    async def test_happy_path_observe_includes_prediction_signals(self, data_scout):
        """Happy path: observe() method includes prediction signals."""
        # Mock ticker fetch
        with patch.object(
            data_scout, "_fetch_ticker", new_callable=AsyncMock
        ) as mock_ticker:
            mock_ticker.return_value = {
                "last": 50000.0,
                "volume": 100.0,
                "bid": 49999.0,
                "ask": 50001.0,
                "timestamp": datetime.now().timestamp(),
            }

            # Mock prediction signals fetch
            with patch.object(
                data_scout, "_fetch_prediction_signals", new_callable=AsyncMock
            ) as mock_signals:
                mock_signals.return_value = [
                    {
                        "id": "sig_1",
                        "market": "kalshi",
                        "signal_type": "bullish",
                        "confidence": 0.85,
                    }
                ]

                # Mock funding rate
                with patch.object(
                    data_scout, "_fetch_funding_rate", new_callable=AsyncMock
                ) as mock_funding:
                    mock_funding.return_value = 0.0001

                    observation = await data_scout.observe("BTC/USDT", "trace_001")

                    assert observation.symbol == "BTC/USDT"
                    assert observation.price == 50000.0
                    assert len(observation.prediction_signals) == 1
                    assert observation.prediction_signals[0]["signal_type"] == "bullish"

    @pytest.mark.asyncio
    async def test_happy_path_signals_filtered_by_confidence(self, data_scout):
        """Happy path: Client filters signals by min_confidence."""
        with patch("backend.agents.data_scout_agent.get_prediction_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.get_signals = AsyncMock(return_value=[])
            mock_get.return_value = mock_client

            await data_scout._fetch_prediction_signals("BTC")

            # Verify call with min_confidence=0.5
            mock_client.get_signals.assert_called_once()
            call_kwargs = mock_client.get_signals.call_args.kwargs
            assert call_kwargs.get("min_confidence") == 0.5

    @pytest.mark.asyncio
    async def test_happy_path_signals_limited_by_limit(self, data_scout):
        """Happy path: Client limits signals by count."""
        with patch("backend.agents.data_scout_agent.get_prediction_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.get_signals = AsyncMock(return_value=[])
            mock_get.return_value = mock_client

            await data_scout._fetch_prediction_signals("ETH")

            # Verify call with limit=5
            mock_client.get_signals.assert_called_once()
            call_kwargs = mock_client.get_signals.call_args.kwargs
            assert call_kwargs.get("limit") == 5

    # =========================================================================
    # UNHAPPY PATH TESTS
    # =========================================================================

    @pytest.mark.asyncio
    async def test_unhappy_path_service_failure_returns_empty(self, data_scout):
        """Unhappy path: Service failure returns empty list."""
        with patch("backend.agents.data_scout_agent.get_prediction_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.get_signals = AsyncMock(
                side_effect=Exception("Connection failed")
            )
            mock_get.return_value = mock_client

            signals = await data_scout._fetch_prediction_signals("BTC")

            assert signals == []

    @pytest.mark.asyncio
    async def test_unhappy_path_timeout_returns_empty(self, data_scout):
        """Unhappy path: Request timeout returns empty list."""
        import asyncio

        with patch("backend.agents.data_scout_agent.get_prediction_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.get_signals = AsyncMock(
                side_effect=asyncio.TimeoutError("Request timeout")
            )
            mock_get.return_value = mock_client

            signals = await data_scout._fetch_prediction_signals("BTC")

            assert signals == []

    @pytest.mark.asyncio
    async def test_unhappy_path_observation_default_empty_signals(self):
        """Unhappy path: Observation defaults to empty signals list."""
        obs = Observation(symbol="BTC/USDT", price=50000.0, volume=100.0)

        assert obs.prediction_signals == []
        assert isinstance(obs.prediction_signals, list)

    @pytest.mark.asyncio
    async def test_unhappy_path_malformed_signal_handled(self, data_scout):
        """Unhappy path: Malformed signal response is handled gracefully."""
        with patch("backend.agents.data_scout_agent.get_prediction_client") as mock_get:
            mock_client = AsyncMock()
            # Simulate malformed response
            mock_client.get_signals = AsyncMock(
                side_effect=TypeError("Signal object missing required fields")
            )
            mock_get.return_value = mock_client

            signals = await data_scout._fetch_prediction_signals("BTC")

            assert signals == []

    @pytest.mark.asyncio
    async def test_unhappy_path_prediction_failure_does_not_break_observe(
        self, data_scout
    ):
        """Unhappy path: Prediction service failure doesn't break observe."""
        # Mock ticker fetch (success)
        with patch.object(
            data_scout, "_fetch_ticker", new_callable=AsyncMock
        ) as mock_ticker:
            mock_ticker.return_value = {
                "last": 50000.0,
                "volume": 100.0,
                "bid": 49999.0,
                "ask": 50001.0,
                "timestamp": datetime.now().timestamp(),
            }

            # Mock prediction signals fetch to return empty (graceful degradation)
            with patch.object(
                data_scout, "_fetch_prediction_signals", new_callable=AsyncMock
            ) as mock_signals:
                mock_signals.return_value = []  # Service returns empty, not error

                # Mock funding rate
                with patch.object(
                    data_scout, "_fetch_funding_rate", new_callable=AsyncMock
                ) as mock_funding:
                    mock_funding.return_value = 0.0001

                    observation = await data_scout.observe("BTC/USDT", "trace_002")

                    # Observation should still be created
                    assert observation.symbol == "BTC/USDT"
                    assert observation.price == 50000.0
                    # Signals are empty due to graceful degradation
                    assert observation.prediction_signals == []


class TestObservationSchema:
    """Tests for Observation schema with prediction_signals."""

    def test_happy_path_prediction_signals_field_exists(self):
        """Happy path: Observation schema has prediction_signals field."""
        obs = Observation(symbol="BTC/USDT", price=50000.0, volume=100.0)

        assert hasattr(obs, "prediction_signals")

    def test_happy_path_prediction_signals_default_empty_list(self):
        """Happy path: prediction_signals defaults to empty list."""
        obs = Observation(symbol="BTC/USDT", price=50000.0, volume=100.0)

        assert obs.prediction_signals == []
        assert isinstance(obs.prediction_signals, list)

    def test_happy_path_prediction_signals_accepts_list_of_dicts(self):
        """Happy path: prediction_signals accepts list of dicts."""
        signals = [
            {
                "id": "sig_1",
                "market": "kalshi",
                "signal_type": "bullish",
                "confidence": 0.8,
            },
            {
                "id": "sig_2",
                "market": "polymarket",
                "signal_type": "bearish",
                "confidence": 0.6,
            },
        ]

        obs = Observation(
            symbol="BTC/USDT", price=50000.0, volume=100.0, prediction_signals=signals
        )

        assert len(obs.prediction_signals) == 2
        assert obs.prediction_signals[0]["signal_type"] == "bullish"
        assert obs.prediction_signals[1]["signal_type"] == "bearish"

    def test_happy_path_observation_serialization(self):
        """Happy path: Observation with signals serializes to JSON."""
        obs = Observation(
            symbol="BTC/USDT",
            price=50000.0,
            volume=100.0,
            prediction_signals=[
                {
                    "id": "sig_1",
                    "market": "kalshi",
                    "signal_type": "bullish",
                    "confidence": 0.8,
                }
            ],
        )

        # Should serialize without errors
        json_data = obs.model_dump_json()
        assert "prediction_signals" in json_data
        assert "sig_1" in json_data
