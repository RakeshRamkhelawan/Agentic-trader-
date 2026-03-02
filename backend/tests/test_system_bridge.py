"""
Tests voor Cognitive Bridge adapter.

Verifieert correcte transformatie van OODA types naar SystemIdentity interface.
"""

from unittest.mock import AsyncMock, Mock

import numpy as np
import pytest

from backend.core.adapters.system_bridge import CognitiveBridge
from backend.core.schemas.ooda_types import Observation


@pytest.fixture
def mock_system_identity():
    """Mock SystemIdentity voor tests."""
    identity = Mock()
    identity.process_market_cycle = AsyncMock(
        return_value={"confidence": 0.75, "action": 1, "perception": {}, "tattva_traversal": {}}
    )
    identity.get_system_statistics = Mock(
        return_value={"total_experiences": 42, "avg_coherence": 0.8}
    )
    identity.system_state = {"total_experiences": 0}
    return identity


class TestCognitiveBridge:
    """Tests for CognitiveBridge adapter."""

    @pytest.mark.asyncio
    async def test_process_observation_happy_path(self, mock_system_identity):
        """Happy path: Observation correctly transformed and processed."""
        bridge = CognitiveBridge(system_identity=mock_system_identity, window_size=20)

        obs = Observation(
            symbol="BTC/USDT",
            price=50000.0,
            volume=100.5,
            orderbook={"bids": [[49999, 10.0], [49998, 5.0]], "asks": [[50001, 8.0], [50002, 3.0]]},
            funding_rate=0.0001,
            social_sentiment=0.5,
        )

        confidence = await bridge.process_observation(obs)

        assert 0.0 <= confidence <= 1.0
        assert confidence == 0.75  # From mock

        # Verify SystemIdentity was called correctly
        assert mock_system_identity.process_market_cycle.called
        call_args = mock_system_identity.process_market_cycle.call_args[1]

        # Check numpy arrays were passed
        assert isinstance(call_args["price_data"], np.ndarray)
        assert isinstance(call_args["volume_data"], np.ndarray)

        # Check other parameters
        assert -1.0 <= call_args["orderbook_imbalance"] <= 1.0
        assert call_args["funding_rate"] == 0.0001
        assert call_args["social_sentiment"] == 0.5

    @pytest.mark.asyncio
    async def test_buffer_management(self, mock_system_identity):
        """Buffers correctly maintain sliding window."""
        bridge = CognitiveBridge(
            system_identity=mock_system_identity, window_size=3  # Small window for testing
        )

        # Add observations
        for price in [100.0, 101.0, 102.0, 103.0]:
            obs = Observation(symbol="BTC/USDT", price=price, volume=10.0)
            await bridge.process_observation(obs)

        # Check buffer stats
        stats = bridge.get_buffer_stats()
        assert stats["price_buffer_size"] == 3  # Window size
        assert stats["price_latest"] == 103.0

        # Verify only last 3 prices kept
        call_args = mock_system_identity.process_market_cycle.call_args[1]
        price_array = call_args["price_data"]
        assert len(price_array) == 3
        assert np.allclose(price_array, [101.0, 102.0, 103.0])

    @pytest.mark.asyncio
    async def test_padding_insufficient_data(self, mock_system_identity):
        """Buffers correctly pad when insufficient data."""
        bridge = CognitiveBridge(system_identity=mock_system_identity, window_size=5)

        # Add only 2 observations
        obs1 = Observation(symbol="BTC/USDT", price=100.0, volume=10.0)
        obs2 = Observation(symbol="BTC/USDT", price=101.0, volume=11.0)

        await bridge.process_observation(obs1)
        await bridge.process_observation(obs2)

        # Check array was padded
        call_args = mock_system_identity.process_market_cycle.call_args[1]
        price_array = call_args["price_data"]

        assert len(price_array) == 5  # Padded to window_size
        # First elements should be padded with edge value
        assert price_array[0] == 100.0  # Edge padding

    def test_orderbook_imbalance_calculation(self, mock_system_identity):
        """Orderbook imbalance calculated correctly."""
        bridge = CognitiveBridge(mock_system_identity)

        # More bids than asks
        orderbook = {
            "bids": [[50000, 10.0], [49999, 5.0]],  # Total: 15
            "asks": [[50001, 5.0]],  # Total: 5
        }
        imbalance = bridge._extract_orderbook_imbalance(orderbook)

        # (15 - 5) / (15 + 5) = 10/20 = 0.5
        assert imbalance == 0.5

        # More asks than bids
        orderbook = {"bids": [[50000, 3.0]], "asks": [[50001, 9.0]]}
        imbalance = bridge._extract_orderbook_imbalance(orderbook)

        # (3 - 9) / (3 + 9) = -6/12 = -0.5
        assert imbalance == -0.5

    def test_orderbook_imbalance_empty(self, mock_system_identity):
        """Empty orderbook returns 0 imbalance."""
        bridge = CognitiveBridge(mock_system_identity)

        assert bridge._extract_orderbook_imbalance({}) == 0.0
        assert bridge._extract_orderbook_imbalance({"bids": []}) == 0.0
        assert bridge._extract_orderbook_imbalance({"asks": []}) == 0.0

    @pytest.mark.asyncio
    async def test_system_identity_exception_failsafe(self, mock_system_identity):
        """If SystemIdentity crashes, bridge returns low confidence."""
        bridge = CognitiveBridge(mock_system_identity)

        # Make SystemIdentity raise exception
        mock_system_identity.process_market_cycle = AsyncMock(side_effect=Exception("Core failure"))

        obs = Observation(symbol="BTC/USDT", price=50000, volume=100)

        # Should not raise, but return 0.0 confidence (fail-safe)
        confidence = await bridge.process_observation(obs)
        assert confidence == 0.0

    def test_buffer_reset(self, mock_system_identity):
        """Buffer reset clears history."""
        bridge = CognitiveBridge(mock_system_identity)

        # Add some data
        bridge._price_buffer = [100, 101, 102]
        bridge._volume_buffer = [10, 11, 12]

        # Reset
        bridge.reset_buffers()

        assert len(bridge._price_buffer) == 0
        assert len(bridge._volume_buffer) == 0
