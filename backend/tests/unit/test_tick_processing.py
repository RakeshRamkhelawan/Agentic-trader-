"""
Unit Tests for Market Data Consumer Logic (P2-16).

Tests:
1. UnifiedMarketEvent deserialization & validation
2. ResearchAgent tick processing & rolling-window signal generation
3. AgentMessage TICK_DATA/MARKET_TICK type validity
"""

import asyncio
import time
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# --- Test 1: AgentMessage Schema ---


class TestAgentMessageTypes:
    """Verify MARKET_TICK and TICK_DATA are valid message types."""

    def test_tick_data_is_valid(self):
        from backend.schemas.agent_messages import AgentMessage

        msg = AgentMessage(
            source="test",
            target="all",
            type="TICK_DATA",
            payload={"symbol": "BTC/USDT", "price": 50000},
        )
        assert msg.type == "TICK_DATA"

    def test_market_tick_is_valid(self):
        from backend.schemas.agent_messages import AgentMessage

        msg = AgentMessage(
            source="test",
            target="all",
            type="MARKET_TICK",
            payload={"symbol": "BTC/USDT", "price": 50000},
        )
        assert msg.type == "MARKET_TICK"

    def test_invalid_type_raises(self):
        from backend.schemas.agent_messages import AgentMessage

        with pytest.raises(ValueError, match="Invalid message type"):
            AgentMessage(source="test", target="all", type="TOTALLY_FAKE_TYPE", payload={})


# --- Test 2: UnifiedMarketEvent Validation ---


class TestUnifiedMarketEventValidation:
    """Verify deserialization and validation of market events."""

    def test_valid_ticker_event(self):
        from backend.market_data.models import EventType, UnifiedMarketEvent

        event = UnifiedMarketEvent(
            event_type=EventType.TICKER,
            venue="kraken",
            symbol="BTC/USDT",
            ts_exchange=time.time(),
            ts_received=time.time(),
            price=50000.0,
            bid=49999.0,
            ask=50001.0,
        )
        event.validate()  # Should not raise
        assert event.symbol == "BTC/USDT"
        assert event.price == 50000.0

    def test_negative_price_raises(self):
        from backend.market_data.models import EventType, UnifiedMarketEvent

        event = UnifiedMarketEvent(
            event_type=EventType.TICKER,
            venue="kraken",
            symbol="BTC/USDT",
            ts_exchange=time.time(),
            ts_received=time.time(),
            price=-100.0,
        )
        with pytest.raises(ValueError, match="Price must be positive"):
            event.validate()

    def test_negative_size_raises(self):
        from backend.market_data.models import EventType, UnifiedMarketEvent

        event = UnifiedMarketEvent(
            event_type=EventType.TRADE,
            venue="bybit",
            symbol="ETH/USDT",
            ts_exchange=time.time(),
            ts_received=time.time(),
            price=3000.0,
            size=-1.5,
            side="buy",
        )
        with pytest.raises(ValueError, match="Size must be positive"):
            event.validate()

    def test_to_dict_roundtrip(self):
        from backend.market_data.models import EventType, UnifiedMarketEvent

        event = UnifiedMarketEvent(
            event_type=EventType.TICKER,
            venue="kraken",
            symbol="BTC/USDT",
            ts_exchange=1000.0,
            ts_received=1001.0,
            price=50000.0,
        )
        d = event.to_dict()
        assert d["event_type"] == "ticker"
        assert d["venue"] == "kraken"
        assert d["price"] == 50000.0


# --- Test 3: ResearchAgent Tick Processing ---


class TestResearchAgentTickProcessing:
    """Verify rolling-window and MVP signal generation."""

    @pytest.fixture
    def agent(self):
        from backend.services.research_agent import ResearchAgent

        bus_mock = AsyncMock()
        agent = ResearchAgent(memory_agent=MagicMock(), message_bus=bus_mock)
        return agent

    @pytest.mark.asyncio
    async def test_process_tick_builds_history(self, agent):
        """Verify ticks are accumulated in the rolling window."""
        for i in range(10):
            await agent.process_tick({"symbol": "BTC/USDT", "price": 50000.0 + i})
        assert len(agent._price_history["BTC/USDT"]) == 10

    @pytest.mark.asyncio
    async def test_process_tick_max_window_100(self, agent):
        """Verify rolling window caps at 100."""
        for i in range(120):
            await agent.process_tick({"symbol": "BTC/USDT", "price": 50000.0})
        assert len(agent._price_history["BTC/USDT"]) == 100

    @pytest.mark.asyncio
    async def test_no_signal_below_threshold(self, agent):
        """No signal emitted when price deviation < 2%."""
        # All prices at 50000 -> no deviation
        for _ in range(10):
            await agent.process_tick({"symbol": "BTC/USDT", "price": 50000.0})
        agent.message_bus.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_bullish_signal_on_spike(self, agent):
        """BULLISH signal emitted when price spikes >2% above average."""
        # Build baseline at 50000
        for _ in range(10):
            await agent.process_tick({"symbol": "BTC/USDT", "price": 50000.0})

        # Spike to 52000 (4% above average)
        await agent.process_tick({"symbol": "BTC/USDT", "price": 52000.0})

        # The message_bus should have been called with a SIGNAL
        assert agent.message_bus.await_count >= 1
        call_args = agent.message_bus.await_args
        signal_msg = call_args[0][0]
        assert signal_msg.type == "SIGNAL"
        assert signal_msg.payload["signal"] == "BULLISH_MOMENTUM"
        assert signal_msg.payload["symbol"] == "BTC/USDT"

    @pytest.mark.asyncio
    async def test_bearish_signal_on_drop(self, agent):
        """BEARISH signal emitted when price drops >2% below average."""
        # Build baseline at 50000
        for _ in range(10):
            await agent.process_tick({"symbol": "BTC/USDT", "price": 50000.0})

        # Drop to 48000 (4% below average)
        await agent.process_tick({"symbol": "BTC/USDT", "price": 48000.0})

        assert agent.message_bus.await_count >= 1
        call_args = agent.message_bus.await_args
        signal_msg = call_args[0][0]
        assert signal_msg.type == "SIGNAL"
        assert signal_msg.payload["signal"] == "BEARISH_MOMENTUM"

    @pytest.mark.asyncio
    async def test_missing_price_is_ignored(self, agent):
        """Ticks without price data are gracefully ignored."""
        await agent.process_tick({"symbol": "BTC/USDT"})
        assert not hasattr(agent, "_price_history") or "BTC/USDT" not in agent._price_history

    @pytest.mark.asyncio
    async def test_multiple_symbols_tracked_independently(self, agent):
        """Different symbols maintain separate rolling windows."""
        for _ in range(5):
            await agent.process_tick({"symbol": "BTC/USDT", "price": 50000.0})
            await agent.process_tick({"symbol": "ETH/USDT", "price": 3000.0})

        assert len(agent._price_history["BTC/USDT"]) == 5
        assert len(agent._price_history["ETH/USDT"]) == 5
