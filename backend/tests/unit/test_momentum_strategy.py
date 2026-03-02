from datetime import UTC, datetime

import pytest

from backend.core.market_data.models import EventType, UnifiedMarketEvent
from backend.strategies.momentum import MomentumStrategy


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
async def test_momentum_rsi_logic():
    """Test RSI calculation and signal emission."""
    config = {
        "rsi_period": 5,  # Short period for easy testing
        "overbought": 70,
        "oversold": 30,
        "max_history": 20,
    }
    strategy = MomentumStrategy(config)

    # 1. Feed flat prices (RSI should be 50 or undefined initially)
    # Need at least period+1 (6) ticks
    initial_prices = [100.0] * 7
    for p in initial_prices:
        tick = _make_tick(p)
        res = await strategy.on_tick(tick)
        assert res is None  # No movement, no signal

    # 2. Strong uptrend to trigger Overbought (BEARISH signal expected)
    uptrend = [105.0, 110.0, 115.0, 120.0, 125.0, 130.0]

    last_res = None
    for p in uptrend:
        tick = _make_tick(p)
        res = await strategy.on_tick(tick)
        if res:
            last_res = res

    # Verify we got a signal eventually
    assert last_res is not None
    assert "BEARISH_RSI" in last_res["signal"]
    assert last_res["metrics"]["rsi"] > 70

    # 3. Strong downtrend to trigger Oversold (BULLISH signal expected)
    downtrend = [120.0, 110.0, 100.0, 90.0, 80.0, 70.0, 60.0]

    bull_res = None
    for p in downtrend:
        tick = _make_tick(p)
        res = await strategy.on_tick(tick)
        if res and "BULLISH" in res["signal"]:
            bull_res = res

    assert bull_res is not None
    assert "BULLISH_RSI" in bull_res["signal"]
    assert bull_res["metrics"]["rsi"] < 30
