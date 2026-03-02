"""
Tests voor DataScout Agent.

Test observation collection, normalization, en failure handling.
"""

from unittest.mock import AsyncMock

import pytest

from backend.agents.data_scout_agent import DataScoutAgent
from backend.core.schemas.ooda_types import Observation


class TestDataScoutAgent:
    """Tests for DataScoutAgent."""

    @pytest.mark.asyncio
    async def test_observe_happy_path(self, mock_data_source, mock_event_bus):
        """Happy path: Succesvolle observation collection."""
        agent = DataScoutAgent(data_source=mock_data_source, event_bus=mock_event_bus)

        observation = await agent.observe(
            symbol="BTC/USDT", trace_id="trace-123", include_orderbook=True, include_funding=True
        )

        # Verify Observation is valid
        assert isinstance(observation, Observation)
        assert observation.symbol == "BTC/USDT"
        assert observation.price == 50000.0
        assert observation.volume == 100.5
        assert len(observation.orderbook["bids"]) == 2
        assert observation.funding_rate == 0.0001

        # Verify data source was called
        assert mock_data_source.fetch_ticker.called
        assert mock_data_source.fetch_orderbook.called
        assert mock_data_source.fetch_funding_rate.called

        # Verify audit log published
        assert mock_event_bus.publish.called
        call_args = mock_event_bus.publish.call_args[0]
        assert call_args[0] == "audit_log"
        assert call_args[1]["trace_id"] == "trace-123"
        assert call_args[1]["stage"] == "OBSERVE"

    @pytest.mark.asyncio
    async def test_observe_without_data_source(self):
        """Agent werkt met mock data als geen data source."""
        agent = DataScoutAgent()  # No data source

        observation = await agent.observe(symbol="BTC/USDT", trace_id="trace-456")

        # Moet mock data gebruiken
        assert isinstance(observation, Observation)
        assert observation.price > 0
        assert observation.volume > 0

    @pytest.mark.asyncio
    async def test_observe_orderbook_optional(self, mock_data_source):
        """Orderbook fetch is optioneel."""
        agent = DataScoutAgent(data_source=mock_data_source)

        observation = await agent.observe(
            symbol="BTC/USDT", trace_id="trace-789", include_orderbook=False
        )

        assert observation.orderbook == {}
        assert not mock_data_source.fetch_orderbook.called

    @pytest.mark.asyncio
    async def test_observe_funding_optional(self, mock_data_source):
        """Funding rate fetch is optioneel."""
        agent = DataScoutAgent(data_source=mock_data_source)

        observation = await agent.observe(
            symbol="BTC/USDT", trace_id="trace-abc", include_funding=False
        )

        assert observation.funding_rate is None
        assert not mock_data_source.fetch_funding_rate.called

    @pytest.mark.asyncio
    async def test_data_source_ticker_failure(self, mock_data_source):
        """Unhappy path: Data source ticker failure."""
        agent = DataScoutAgent(data_source=mock_data_source)

        # Make ticker fail
        mock_data_source.fetch_ticker = AsyncMock(side_effect=Exception("Exchange API down"))

        with pytest.raises(ValueError, match="Failed to fetch ticker"):
            await agent.observe("BTC/USDT", "trace-fail")

        # Verify failure recorded
        assert agent.failed_events > 0

    @pytest.mark.asyncio
    async def test_orderbook_failure_graceful(self, mock_data_source):
        """Orderbook failure niet fataal."""
        agent = DataScoutAgent(data_source=mock_data_source)

        # Make orderbook fail
        mock_data_source.fetch_orderbook = AsyncMock(side_effect=Exception("Orderbook error"))

        # Should still succeed with empty orderbook
        observation = await agent.observe(
            symbol="BTC/USDT", trace_id="trace-resilient", include_orderbook=True
        )

        assert observation.orderbook == {"bids": [], "asks": []}

    @pytest.mark.asyncio
    async def test_funding_rate_unavailable(self, mock_data_source):
        """Funding rate kan None zijn als niet beschikbaar."""
        agent = DataScoutAgent(data_source=mock_data_source)

        mock_data_source.fetch_funding_rate = AsyncMock(side_effect=Exception("Not a perpetual"))

        observation = await agent.observe(
            symbol="BTC/USDT", trace_id="trace-spot", include_funding=True
        )

        assert observation.funding_rate is None

    @pytest.mark.asyncio
    async def test_heartbeat_updated(self, mock_data_source):
        """Heartbeat wordt bijgewerkt bij observe."""
        agent = DataScoutAgent(data_source=mock_data_source)

        import time

        initial_heartbeat = agent.last_heartbeat

        time.sleep(0.1)

        await agent.observe("BTC/USDT", "trace-hb")

        assert agent.last_heartbeat > initial_heartbeat

    @pytest.mark.asyncio
    async def test_statistics(self, mock_data_source):
        """Statistics tracking werkt."""
        agent = DataScoutAgent(data_source=mock_data_source)

        # Collect multiple observations
        await agent.observe("BTC/USDT", "trace-1")
        await agent.observe("ETH/USDT", "trace-2")

        stats = agent.get_statistics()

        assert stats["observations_collected"] == 2
        assert stats["processed_events"] == 2
        assert stats["failed_events"] == 0
        assert stats["status"] == "healthy"
