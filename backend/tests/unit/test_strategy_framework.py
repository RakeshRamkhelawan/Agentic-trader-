import asyncio
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.core.market_data.models import EventType, UnifiedMarketEvent
from backend.schemas.agent_messages import AgentMessage
from backend.services.research_agent import ResearchAgent
from backend.strategies.simple_tremor import SimpleTremorStrategy


def _make_tick(price: float, symbol: str = "BTC/USD") -> UnifiedMarketEvent:
    """Helper to create a UnifiedMarketEvent with keyword arguments."""
    return UnifiedMarketEvent(
        event_type=EventType.TICKER,
        symbol=symbol,
        price=price,
        volume=0.0,
        timestamp=datetime.now(UTC),
        exchange="mock",
    )


@pytest.mark.asyncio
async def test_simple_tremor_logic_bullish():
    """Test that SimpleTremorStrategy emits BULLISH signal on positive deviation."""
    config = {"window_size": 3, "deviation_threshold": 0.05, "max_history": 10}  # 5%
    strategy = SimpleTremorStrategy(config)

    # Tick 1: 100
    t1 = _make_tick(100.0)
    res1 = await strategy.on_tick(t1)
    assert res1 is None

    # Tick 2: 100
    t2 = _make_tick(100.0)
    await strategy.on_tick(t2)

    # Tick 3: 100 (Avg is now 100)
    t3 = _make_tick(100.0)
    await strategy.on_tick(t3)

    # Tick 4: 110 (10% jump > 5% threshold)
    # Window is last 3: [100, 100, 110] -> Avg ~103.33
    # Price 110 vs Avg 103.33. Deviation = (110 - 103.33) / 103.33 = 6.4% > 5%.
    t4 = _make_tick(110.0)
    res4 = await strategy.on_tick(t4)

    assert res4 is not None
    assert res4["signal"] == "BULLISH_MOMENTUM"
    assert res4["symbol"] == "BTC/USD"
    assert res4["price"] == 110.0
    assert res4["deviation"] > 0.05


@pytest.mark.asyncio
async def test_research_agent_integration():
    """Test that ResearchAgent correctly delegates to the strategy and emits AgentMessage."""
    mock_bus = AsyncMock()

    # Inject config for fast triggering
    strategy = SimpleTremorStrategy({"window_size": 2, "deviation_threshold": 0.01})
    agent = ResearchAgent(message_bus=mock_bus, strategy=strategy)

    # Payload can be dict or object. ResearchAgent handles both.
    tick1 = {"symbol": "ETH/USD", "price": 2000.0, "venue": "bybit"}
    tick2 = {"symbol": "ETH/USD", "price": 2000.0, "venue": "bybit"}
    tick3 = {"symbol": "ETH/USD", "price": 2100.0, "venue": "bybit"}  # Jump

    msg1 = AgentMessage(source="orchestrator", target="research", type="TICK_DATA", payload=tick1)
    await agent.handle_message(msg1)

    msg2 = AgentMessage(source="orchestrator", target="research", type="TICK_DATA", payload=tick2)
    await agent.handle_message(msg2)

    msg3 = AgentMessage(source="orchestrator", target="research", type="TICK_DATA", payload=tick3)
    await agent.handle_message(msg3)

    # Verify mock_bus was called with SIGNAL
    assert mock_bus.called
    last_call_args = mock_bus.call_args[0][0]  # First arg of last call
    assert isinstance(last_call_args, AgentMessage)
    assert last_call_args.type == "SIGNAL"
    assert "BULLISH_MOMENTUM" in last_call_args.payload["signal"]
    assert last_call_args.payload["price"] == 2100.0
