"""
Unit tests for BreakoutStrategy.

Tests consolidation detection, bullish/bearish breakouts,
volume confirmation, and edge cases.
"""

from datetime import datetime, timezone

import pytest

from backend.core.market_data.models import EventType, UnifiedMarketEvent
from backend.strategies.breakout import BreakoutStrategy


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
    """Strategy should return None when there's not enough history."""
    config = {"consolidation_bars": 5, "range_threshold": 0.03}
    strategy = BreakoutStrategy(config)

    for price in [100.0, 100.5, 99.5, 100.0, 100.2]:
        result = await strategy.on_tick(_make_tick("BTC/USD", price))
        assert result is None, "Should return None with < consolidation_bars + 1 ticks"


@pytest.mark.asyncio
async def test_bullish_breakout_after_consolidation():
    """
    After a period of tight consolidation, a price breakout above
    the range with volume should emit BULLISH_BREAKOUT.
    """
    config = {
        "consolidation_bars": 5,
        "range_threshold": 0.02,  # 2% max range
        "volume_multiplier": 0,  # Disable volume filter
    }
    strategy = BreakoutStrategy(config)

    # Build consolidation: tight range around 100
    # Need consolidation_bars + 1 ticks to establish, then more to be "was_consolidating"
    consolidation = [100.0, 100.5, 99.8, 100.2, 100.1, 100.3]
    for p in consolidation:
        await strategy.on_tick(_make_tick("BTC/USD", p))

    # Now send another consolidation tick to set was_consolidating = True
    await strategy.on_tick(_make_tick("BTC/USD", 100.4))

    # Breakout above the range
    result = await strategy.on_tick(_make_tick("BTC/USD", 105.0))

    assert result is not None, "Should detect bullish breakout"
    assert result["signal"] == "BULLISH_BREAKOUT"
    assert result["symbol"] == "BTC/USD"
    assert result["strategy"] == "breakout_consolidation"
    assert "range_high" in result["metrics"]
    assert "range_low" in result["metrics"]


@pytest.mark.asyncio
async def test_bearish_breakout_after_consolidation():
    """
    After consolidation, a price breakout below the range should emit BEARISH_BREAKOUT.
    """
    config = {
        "consolidation_bars": 5,
        "range_threshold": 0.02,
        "volume_multiplier": 0,
    }
    strategy = BreakoutStrategy(config)

    # Build consolidation around 100
    consolidation = [100.0, 100.5, 99.8, 100.2, 100.1, 100.3]
    for p in consolidation:
        await strategy.on_tick(_make_tick("BTC/USD", p))

    # Tick to carry consolidation state forward
    await strategy.on_tick(_make_tick("BTC/USD", 100.0))

    # Breakout below range
    result = await strategy.on_tick(_make_tick("BTC/USD", 95.0))

    assert result is not None, "Should detect bearish breakout"
    assert result["signal"] == "BEARISH_BREAKOUT"


@pytest.mark.asyncio
async def test_no_signal_without_consolidation():
    """No breakout signal if there was no prior consolidation."""
    config = {
        "consolidation_bars": 5,
        "range_threshold": 0.01,  # Very tight range required
        "volume_multiplier": 0,
    }
    strategy = BreakoutStrategy(config)

    # Wide range (not consolidating): >1% range
    wide_range = [100.0, 105.0, 95.0, 110.0, 90.0, 100.0, 100.0]
    for p in wide_range:
        await strategy.on_tick(_make_tick("BTC/USD", p))

    # Attempt breakout, but no prior consolidation
    result = await strategy.on_tick(_make_tick("BTC/USD", 120.0))
    assert result is None, "Should not signal breakout without prior consolidation"


@pytest.mark.asyncio
async def test_volume_filter_blocks_breakout():
    """Breakout should be blocked when volume is below threshold."""
    config = {
        "consolidation_bars": 5,
        "range_threshold": 0.02,
        "volume_multiplier": 5.0,  # High volume requirement
    }
    strategy = BreakoutStrategy(config)

    # Build consolidation with consistent volume
    for p in [100.0, 100.5, 99.8, 100.2, 100.1, 100.3]:
        await strategy.on_tick(_make_tick("BTC/USD", p, volume=100.0))

    # Set was_consolidating
    await strategy.on_tick(_make_tick("BTC/USD", 100.4, volume=100.0))

    # Breakout with LOW volume (should be blocked)
    result = await strategy.on_tick(_make_tick("BTC/USD", 105.0, volume=50.0))
    assert result is None, "Volume filter should block low-volume breakout"


@pytest.mark.asyncio
async def test_invalid_tick_returns_none():
    """Ticks with invalid prices should return None."""
    config = {"consolidation_bars": 5}
    strategy = BreakoutStrategy(config)

    result = await strategy.on_tick(_make_tick("BTC/USD", 0.0))
    assert result is None

    result = await strategy.on_tick(_make_tick("BTC/USD", -5.0))
    assert result is None


@pytest.mark.asyncio
async def test_multiple_symbols_independent():
    """Each symbol should maintain independent consolidation state."""
    config = {
        "consolidation_bars": 3,
        "range_threshold": 0.02,
        "volume_multiplier": 0,
    }
    strategy = BreakoutStrategy(config)

    # Feed data for BTC
    for p in [100.0, 100.2, 100.1, 100.3]:
        await strategy.on_tick(_make_tick("BTC/USD", p))

    # Feed data for ETH
    for p in [2000.0, 2005.0, 1995.0, 2010.0]:
        await strategy.on_tick(_make_tick("ETH/USD", p))

    assert "BTC/USD" in strategy._price_history
    assert "ETH/USD" in strategy._price_history
    assert len(strategy._price_history["BTC/USD"]) == 4
    assert len(strategy._price_history["ETH/USD"]) == 4
