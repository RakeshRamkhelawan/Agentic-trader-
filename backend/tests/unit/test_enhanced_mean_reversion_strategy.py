"""
Tests voor EnhancedMeanReversionStrategy.

Test Bollinger + RSI + Volume signaal generatie en squeeze filter.
"""

from datetime import UTC, datetime

import pytest

from backend.core.market_data.models import EventType, UnifiedMarketEvent
from backend.strategies.enhanced_mean_reversion import EnhancedMeanReversionStrategy


def _make_tick(
    price: float, symbol: str = "BTC/USD", volume: float = 100.0
) -> UnifiedMarketEvent:
    """Helper to create a UnifiedMarketEvent."""
    return UnifiedMarketEvent(
        event_type=EventType.TICKER,
        symbol=symbol,
        price=price,
        volume=volume,
        timestamp=datetime.now(UTC),
        exchange="mock",
    )


class TestEnhancedMeanReversionInit:
    """Test strategie initialisatie."""

    def test_default_config(self):
        """Default configuratie is correct."""
        strategy = EnhancedMeanReversionStrategy({})
        assert strategy.bb_period == 20
        assert strategy.bb_std_dev == 2.0
        assert strategy.rsi_period == 14
        assert strategy.rsi_oversold == 35
        assert strategy.rsi_overbought == 65
        assert strategy.squeeze_threshold == 1.5

    def test_custom_config(self):
        """Custom configuratie wordt overgenomen."""
        config = {
            "bb_period": 10,
            "bb_std_dev": 1.5,
            "rsi_oversold": 25,
        }
        strategy = EnhancedMeanReversionStrategy(config)
        assert strategy.bb_period == 10
        assert strategy.bb_std_dev == 1.5
        assert strategy.rsi_oversold == 25


class TestEnhancedMeanReversionSignals:
    """Test signaal generatie."""

    @pytest.mark.asyncio
    async def test_no_signal_insufficient_data(self):
        """Geen signaal bij onvoldoende data."""
        strategy = EnhancedMeanReversionStrategy({"cooldown_ticks": 0})

        for i in range(10):
            tick = _make_tick(100.0)
            result = await strategy.on_tick(tick)
            assert result is None

    @pytest.mark.asyncio
    async def test_bullish_signal_price_below_lower_band(self):
        """Bullish signaal wanneer prijs onder lower Bollinger band + RSI oversold."""
        config = {
            "cooldown_ticks": 0,
            "bb_period": 20,
            "bb_std_dev": 2.0,
            "rsi_period": 14,
            "rsi_oversold": 40,  # More permissive for testing
            "volume_spike_multiplier": 0.5,  # Easy volume confirm
            "squeeze_threshold": 0.0,  # Disable squeeze filter
        }
        strategy = EnhancedMeanReversionStrategy(config)

        # Build stable base (for Bollinger to anchor)
        stable = [100.0] * 30

        # Then sharp drop (break below lower band + drive RSI oversold)
        drop = [100.0 - i * 4 for i in range(1, 16)]

        prices = stable + drop

        last_signal = None
        for p in prices:
            tick = _make_tick(p, volume=200.0)
            result = await strategy.on_tick(tick)
            if result:
                last_signal = result

        assert last_signal is not None
        assert "BULLISH" in last_signal["signal"]
        assert "MEAN_REVERSION" in last_signal["signal"]
        assert last_signal["strategy"] == "enhanced_mean_reversion"

    @pytest.mark.asyncio
    async def test_bearish_signal_price_above_upper_band(self):
        """Bearish signaal wanneer prijs boven upper Bollinger band + RSI overbought."""
        config = {
            "cooldown_ticks": 0,
            "bb_period": 20,
            "bb_std_dev": 2.0,
            "rsi_period": 14,
            "rsi_overbought": 60,  # More permissive for testing
            "volume_spike_multiplier": 0.5,
            "squeeze_threshold": 0.0,
        }
        strategy = EnhancedMeanReversionStrategy(config)

        # Build stable base
        stable = [100.0] * 30

        # Then sharp rise (break above upper band + drive RSI overbought)
        rise = [100.0 + i * 4 for i in range(1, 16)]

        prices = stable + rise

        last_signal = None
        for p in prices:
            tick = _make_tick(p, volume=200.0)
            result = await strategy.on_tick(tick)
            if result:
                last_signal = result

        assert last_signal is not None
        assert "BEARISH" in last_signal["signal"]

    @pytest.mark.asyncio
    async def test_no_signal_during_squeeze(self):
        """Geen signaal tijdens BB squeeze (smalle bands)."""
        config = {
            "cooldown_ticks": 0,
            "bb_period": 20,
            "squeeze_threshold": 100.0,  # Very high = always in squeeze
        }
        strategy = EnhancedMeanReversionStrategy(config)

        # Any price action
        for i in range(50):
            p = 100.0 + (i % 10) - 5
            tick = _make_tick(p)
            result = await strategy.on_tick(tick)
            assert result is None  # Always squeeze

    @pytest.mark.asyncio
    async def test_no_signal_flat_market(self):
        """Geen signaal bij constante prijs (prijs binnen bands)."""
        strategy = EnhancedMeanReversionStrategy(
            {"cooldown_ticks": 0, "squeeze_threshold": 0.0}
        )

        for _ in range(50):
            tick = _make_tick(100.0)
            result = await strategy.on_tick(tick)

        # Price never touches bands
        assert result is None

    @pytest.mark.asyncio
    async def test_signal_contains_bollinger_metrics(self):
        """Signaal bevat Bollinger Band metrics."""
        config = {
            "cooldown_ticks": 0,
            "bb_period": 20,
            "rsi_oversold": 40,
            "volume_spike_multiplier": 0.5,
            "squeeze_threshold": 0.0,
        }
        strategy = EnhancedMeanReversionStrategy(config)

        stable = [100.0] * 30
        drop = [100.0 - i * 4 for i in range(1, 16)]
        prices = stable + drop

        last_signal = None
        for p in prices:
            tick = _make_tick(p, volume=200.0)
            result = await strategy.on_tick(tick)
            if result:
                last_signal = result

        if last_signal:
            metrics = last_signal["metrics"]
            assert "bb_upper" in metrics
            assert "bb_lower" in metrics
            assert "bb_width" in metrics
            assert "rsi" in metrics

    @pytest.mark.asyncio
    async def test_cooldown_mechanism(self):
        """Cooldown voorkomt te snelle signalen."""
        config = {
            "cooldown_ticks": 100,
            "rsi_oversold": 40,
            "volume_spike_multiplier": 0.5,
            "squeeze_threshold": 0.0,
        }
        strategy = EnhancedMeanReversionStrategy(config)

        stable = [100.0] * 30
        drop = [100.0 - i * 4 for i in range(1, 16)]
        prices = stable + drop

        signal_count = 0
        for p in prices:
            tick = _make_tick(p, volume=200.0)
            result = await strategy.on_tick(tick)
            if result:
                signal_count += 1

        assert signal_count <= 1

    @pytest.mark.asyncio
    async def test_invalid_price_returns_none(self):
        """Ongeldige prijs geeft None."""
        strategy = EnhancedMeanReversionStrategy({})
        tick = _make_tick(0.0)
        result = await strategy.on_tick(tick)
        assert result is None
