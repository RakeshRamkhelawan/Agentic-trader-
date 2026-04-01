"""
Tests voor Analyst Agent.

Test orientation generation, regime detection, en confidence calculation.
"""

import pytest

from backend.agents.analyst_agent import AnalystAgent
from backend.core.schemas.ooda_types import MarketRegime, Observation, Orientation


class TestAnalystAgent:
    """Tests for AnalystAgent."""

    @pytest.mark.asyncio
    async def test_orient_happy_path(self, sample_observation):
        """Happy path: Orientation correctly generated."""
        agent = AnalystAgent()

        orientation = await agent.orient(
            observation=sample_observation,
            core_sentiment=0.8,
            rag_context=["Historical pattern: Bull run"],
        )

        assert isinstance(orientation, Orientation)
        assert orientation.symbol == "BTC/USDT"
        assert isinstance(orientation.regime, MarketRegime)
        assert 0.0 <= orientation.confidence <= 1.0
        assert orientation.core_sentiment == 0.8
        assert len(orientation.rag_context) == 1
        assert len(orientation.indicators) > 0

    @pytest.mark.asyncio
    async def test_indicators_calculated(self, sample_observation):
        """Technical indicators zijn berekend."""
        agent = AnalystAgent()

        orientation = await agent.orient(observation=sample_observation, core_sentiment=0.5)

        indicators = orientation.indicators
        assert "rsi" in indicators
        assert "macd" in indicators
        assert "spread_pct" in indicators
        assert isinstance(indicators["spread_pct"], float)

    @pytest.mark.asyncio
    async def test_regime_detection_volatile(self):
        """Volatile regime gedetecteerd bij hoge spread."""
        agent = AnalystAgent()

        # Create observation met hoge spread
        obs = Observation(
            symbol="BTC/USDT",
            price=50000.0,
            volume=100.0,
            orderbook={
                "bids": [[49500, 10.0]],
                "asks": [[50500, 10.0]],
            },  # Grote spread
        )

        orientation = await agent.orient(obs, core_sentiment=0.5)

        assert orientation.regime == MarketRegime.VOLATILE

    @pytest.mark.asyncio
    async def test_confidence_weighting(self, sample_observation):
        """Confidence combineert core en technical."""
        agent = AnalystAgent(core_confidence_weight=0.7)

        orientation = await agent.orient(observation=sample_observation, core_sentiment=0.8)

        # Confidence zou tussen core_sentiment en technical zijn
        # met weighting naar core_sentiment
        assert 0.0 <= orientation.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_orient_without_orderbook(self):
        """Orient werkt zonder orderbook data."""
        agent = AnalystAgent()

        obs = Observation(symbol="BTC/USDT", price=50000.0, volume=100.0, orderbook={})  # Leeg

        orientation = await agent.orient(obs, core_sentiment=0.5)

        # Moet nog steeds werken
        assert isinstance(orientation, Orientation)
        assert orientation.indicators["spread_pct"] == 0.0

    @pytest.mark.asyncio
    async def test_orient_without_rag_context(self, sample_observation):
        """RAG context is optioneel."""
        agent = AnalystAgent()

        orientation = await agent.orient(
            observation=sample_observation, core_sentiment=0.5, rag_context=None
        )

        assert orientation.rag_context == []

    @pytest.mark.asyncio
    async def test_heartbeat_updated(self, sample_observation):
        """Heartbeat bijgewerkt bij orient."""
        agent = AnalystAgent()

        import time

        initial = agent.last_heartbeat
        time.sleep(0.1)

        await agent.orient(sample_observation, core_sentiment=0.5)

        assert agent.last_heartbeat > initial

    @pytest.mark.asyncio
    async def test_statistics(self, sample_observation):
        """Statistics tracking werkt."""
        agent = AnalystAgent()

        await agent.orient(sample_observation, core_sentiment=0.5)
        await agent.orient(sample_observation, core_sentiment=0.6)

        stats = agent.get_statistics()

        assert stats["analyses_completed"] == 2
        assert stats["processed_events"] == 2
        assert stats["status"] == "healthy"
