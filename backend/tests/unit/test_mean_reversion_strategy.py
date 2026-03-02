from datetime import UTC, datetime

import pytest

from backend.core.market_data.models import EventType, UnifiedMarketEvent
from backend.strategies.mean_reversion import MeanReversionStrategy


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
async def test_bollinger_bands_logic():
    """Test Bollinger Bands signal emission."""
    config = {"window": 5, "std_dev": 2.0, "max_history": 20}
    strategy = MeanReversionStrategy(config)

    # 1. Feed stable prices (100)
    # SMA = 100, StdDev = 0. Bands = 100 +/- 0
    stable_prices = [100.0] * 5
    for p in stable_prices:
        tick = _make_tick(p)
        await strategy.on_tick(tick)

    # The spike must be extreme enough to exceed bands that include the spike itself.
    # With std_dev=2.0 and window=5, most spikes get absorbed.
    # Use std_dev=1.0 for easier testing:
    strategy.std_dev_multiplier = 1.0  # Hack for test

    # Spike to 200
    # History: [100, 100, 100, 100, 200]
    tick_spike = _make_tick(200.0)
    await strategy.on_tick(tick_spike)

    # Second spike to 200
    # History: [100, 100, 100, 200, 200]
    # SMA: 140, STD: ~54, Upper (1.0): 140 + 54 = 194.
    # Price 200 > 194. Should trigger BEARISH.
    tick_spike2 = _make_tick(200.0)
    res = await strategy.on_tick(tick_spike2)
    assert res is not None
    assert "BEARISH_BOLLINGER" in res["signal"]

    # 3. Drop to 50
    # History: [100, 100, 200, 200, 50]
    # SMA: 130, STD: ~67, Lower (1.0): 130 - 67 = 63.
    # Price 50 < 63. Should trigger BULLISH.
    tick_drop = _make_tick(50.0)
    res = await strategy.on_tick(tick_drop)

    assert res is not None
    assert "BULLISH_BOLLINGER" in res["signal"]
