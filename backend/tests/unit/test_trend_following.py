"""
Unit tests for TrendFollowingStrategy.

Tests MA crossover detection, RSI confirmation, volume filtering,
and edge cases (insufficient data, invalid ticks).
"""

from datetime import datetime, timezone

import pytest

from backend.core.market_data.models import EventType, UnifiedMarketEvent
from backend.strategies.trend_following import TrendFollowingStrategy


def _make_tick(symbol: str, price: float, volume: float = 100.0) -> UnifiedMarketEvent:
    """Create a UnifiedMarketEvent for testing."""
    return UnifiedMarketEvent(
        event_type=EventType.TICKER,
        symbol=symbol,
        price=price,
        volume=volume,
        timestamp=datetime.now(timezone.utc),
        exchange="test",
    )


@pytest.mark.asyncio
async def test_insufficient_data_returns_none():
    """Strategy should return None when there's not enough price history."""
    config = {"short_window": 3, "long_window": 5, "rsi_period": 3}
    strategy = TrendFollowingStrategy(config)

    # Only feed 4 ticks (need 5 for long_window)
    for price in [100.0, 101.0, 102.0, 103.0]:
        result = await strategy.on_tick(_make_tick("BTC/USD", price))
        assert result is None, "Should return None with insufficient data"


@pytest.mark.asyncio
async def test_golden_cross_bullish_signal():
    """
    Golden Cross: short MA crosses above long MA with RSI > 50.
    Should emit BULLISH_TREND signal.
    """
    config = {
        "short_window": 3,
        "long_window": 5,
        "rsi_period": 3,
        "rsi_threshold": 50,
        "volume_multiplier": 0,  # Disable volume filter for this test
    }
    strategy = TrendFollowingStrategy(config)

    # Phase 1: Establish a DEATH cross (short < long)
    # Feed declining prices so short MA < long MA
    declining = [110.0, 108.0, 106.0, 104.0, 102.0, 100.0, 98.0]
    for p in declining:
        await strategy.on_tick(_make_tick("BTC/USD", p))

    # Phase 2: Rapid price increase to trigger golden cross
    # Short MA (3-bar) should cross above Long MA (5-bar)
    rising = [105.0, 112.0, 120.0, 125.0, 130.0]
    result = None
    for p in rising:
        r = await strategy.on_tick(_make_tick("BTC/USD", p))
        if r is not None:
            result = r

    assert result is not None, "Should detect a bullish trend signal"
    assert result["signal"] == "BULLISH_TREND"
    assert result["symbol"] == "BTC/USD"
    assert result["strategy"] == "trend_following_ma_rsi"
    assert result["metrics"]["rsi"] > 50
    assert "short_ma" in result["metrics"]
    assert "long_ma" in result["metrics"]


@pytest.mark.asyncio
async def test_death_cross_bearish_signal():
    """
    Death Cross: short MA crosses below long MA with RSI < 50.
    Should emit BEARISH_TREND signal.
    """
    config = {
        "short_window": 3,
        "long_window": 5,
        "rsi_period": 3,
        "rsi_threshold": 50,
        "volume_multiplier": 0,
    }
    strategy = TrendFollowingStrategy(config)

    # Phase 1: Establish a GOLDEN cross (short > long)
    rising = [90.0, 95.0, 100.0, 105.0, 110.0, 115.0, 120.0]
    for p in rising:
        await strategy.on_tick(_make_tick("BTC/USD", p))

    # Phase 2: Sharp decline to trigger death cross
    declining = [110.0, 100.0, 90.0, 80.0, 70.0]
    result = None
    for p in declining:
        r = await strategy.on_tick(_make_tick("BTC/USD", p))
        if r is not None:
            result = r

    assert result is not None, "Should detect a bearish trend signal"
    assert result["signal"] == "BEARISH_TREND"


@pytest.mark.asyncio
async def test_no_signal_without_crossover_change():
    """Strategy should not signal when MA relationship doesn't change."""
    config = {
        "short_window": 3,
        "long_window": 5,
        "rsi_period": 3,
        "volume_multiplier": 0,
    }
    strategy = TrendFollowingStrategy(config)

    # Feed steady uptrend (golden cross established, never changes)
    prices = [100 + i for i in range(20)]
    results = []
    for p in prices:
        r = await strategy.on_tick(_make_tick("BTC/USD", p))
        if r is not None:
            results.append(r)

    # Should get at most one signal (the initial crossover)
    # After that, no more signals since cross state doesn't change
    assert len(results) <= 1


@pytest.mark.asyncio
async def test_volume_filter_blocks_signal():
    """Signal should be blocked when volume is below the multiplier threshold."""
    config = {
        "short_window": 3,
        "long_window": 5,
        "rsi_period": 3,
        "rsi_threshold": 50,
        "volume_multiplier": 10.0,  # Very high threshold
    }
    strategy = TrendFollowingStrategy(config)

    # Establish death cross
    for p in [110.0, 108.0, 106.0, 104.0, 102.0, 100.0, 98.0]:
        await strategy.on_tick(_make_tick("BTC/USD", p, volume=100.0))

    # Try golden cross with LOW volume (should be blocked)
    results = []
    for p in [105.0, 112.0, 120.0, 125.0, 130.0]:
        r = await strategy.on_tick(_make_tick("BTC/USD", p, volume=50.0))  # Low volume
        if r is not None:
            results.append(r)

    # BULLISH signal should be filtered out due to volume
    bullish_signals = [r for r in results if r["signal"] == "BULLISH_TREND"]
    assert len(bullish_signals) == 0, "Volume filter should block low-volume crossover"


@pytest.mark.asyncio
async def test_invalid_tick_returns_none():
    """Ticks with price 0 or negative should return None."""
    config = {"short_window": 3, "long_window": 5, "rsi_period": 3}
    strategy = TrendFollowingStrategy(config)

    result = await strategy.on_tick(_make_tick("BTC/USD", 0.0))
    assert result is None

    result = await strategy.on_tick(_make_tick("BTC/USD", -10.0))
    assert result is None


@pytest.mark.asyncio
async def test_multiple_symbols_independent():
    """Each symbol should maintain independent state."""
    config = {
        "short_window": 3,
        "long_window": 5,
        "rsi_period": 3,
        "volume_multiplier": 0,
    }
    strategy = TrendFollowingStrategy(config)

    # Feed data for two symbols
    for p in [100.0, 101.0, 102.0, 103.0, 104.0, 105.0]:
        await strategy.on_tick(_make_tick("BTC/USD", p))
        await strategy.on_tick(_make_tick("ETH/USD", 200 + p))

    # Internal state should be separate
    assert "BTC/USD" in strategy._price_history
    assert "ETH/USD" in strategy._price_history
    assert len(strategy._price_history["BTC/USD"]) == 6
    assert len(strategy._price_history["ETH/USD"]) == 6
