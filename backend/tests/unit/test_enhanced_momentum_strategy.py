"""
Tests voor EnhancedMomentumStrategy.

Test composite signaal generatie met 5 indicatoren.
"""

from datetime import UTC, datetime

import pytest

from backend.core.market_data.models import EventType, UnifiedMarketEvent
from backend.strategies.enhanced_momentum import EnhancedMomentumStrategy


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


def _feed_prices(strategy, prices, volumes=None, symbol="BTC/USD"):
    """Feed a list of prices into the strategy, return last result."""
    import asyncio

    last_result = None
    for i, p in enumerate(prices):
        v = volumes[i] if volumes else 100.0
        tick = _make_tick(p, symbol=symbol, volume=v)
        res = asyncio.get_event_loop().run_until_complete(strategy.on_tick(tick))
        if res:
            last_result = res
    return last_result


class TestEnhancedMomentumInit:
    """Test strategie initialisatie."""

    def test_default_config(self):
        """Default configuratie is correct."""
        strategy = EnhancedMomentumStrategy({})
        assert strategy.rsi_period == 14
        assert strategy.rsi_overbought == 70
        assert strategy.rsi_oversold == 30
        assert strategy.adx_threshold == 25.0
        assert strategy.min_consensus == 3
        assert strategy.cooldown_ticks == 10

    def test_custom_config(self):
        """Custom configuratie wordt overgenomen."""
        config = {
            "rsi_period": 7,
            "rsi_overbought": 80,
            "min_consensus": 2,
        }
        strategy = EnhancedMomentumStrategy(config)
        assert strategy.rsi_period == 7
        assert strategy.rsi_overbought == 80
        assert strategy.min_consensus == 2


class TestEnhancedMomentumSignals:
    """Test signaal generatie."""

    @pytest.mark.asyncio
    async def test_no_signal_insufficient_data(self):
        """Geen signaal bij onvoldoende data."""
        strategy = EnhancedMomentumStrategy({"cooldown_ticks": 0})

        # Feed only 10 ticks (need 35+)
        for i in range(10):
            tick = _make_tick(100.0 + i)
            result = await strategy.on_tick(tick)
            assert result is None

    @pytest.mark.asyncio
    async def test_no_signal_flat_market(self):
        """Geen signaal bij constante prijs (geen momentum)."""
        strategy = EnhancedMomentumStrategy({"cooldown_ticks": 0})

        for _ in range(60):
            tick = _make_tick(100.0)
            result = await strategy.on_tick(tick)

        # Flat market = RSI ~50, no EMA alignment, no signal
        assert result is None

    @pytest.mark.asyncio
    async def test_bullish_signal_strong_uptrend(self):
        """Bullish signaal bij sterke uptrend met consensus."""
        config = {
            "cooldown_ticks": 0,
            "min_consensus": 2,  # Lower threshold for testing
            "adx_threshold": 0.0,  # Disable ADX filter for test
        }
        strategy = EnhancedMomentumStrategy(config)

        # Strong consistent uptrend
        prices = [100.0 + i * 3 for i in range(80)]
        volumes = [100.0 + i * 5 for i in range(80)]  # Rising volume

        last_signal = None
        for i in range(len(prices)):
            tick = _make_tick(prices[i], volume=volumes[i])
            result = await strategy.on_tick(tick)
            if result:
                last_signal = result

        # Should have produced a bullish signal
        assert last_signal is not None
        assert "BULLISH" in last_signal["signal"]
        assert last_signal["strategy"] == "enhanced_momentum"
        assert "metrics" in last_signal

    @pytest.mark.asyncio
    async def test_bearish_signal_strong_downtrend(self):
        """Bearish signaal bij sterke downtrend."""
        config = {
            "cooldown_ticks": 0,
            "min_consensus": 2,
            "adx_threshold": 0.0,  # Disable ADX filter
            "rsi_oversold": 30,
            "rsi_overbought": 70,
        }
        strategy = EnhancedMomentumStrategy(config)

        # Start with slight uptrend (build neutral EMAs), then sharp reversal
        # This ensures MACD goes negative and RSI drops below 30
        up = [100.0 + i * 0.5 for i in range(40)]  # Gradual up to 120
        down = [120.0 - i * 3 for i in range(1, 60)]  # Sharp down to -57
        prices = up + down
        volumes = [100.0] * len(prices)

        bearish_signal = None
        for i in range(len(prices)):
            tick = _make_tick(max(prices[i], 1.0), volume=volumes[i])
            result = await strategy.on_tick(tick)
            if result and "BEARISH" in result.get("signal", ""):
                bearish_signal = result

        assert bearish_signal is not None
        assert "BEARISH" in bearish_signal["signal"]

    @pytest.mark.asyncio
    async def test_cooldown_prevents_rapid_signals(self):
        """Cooldown voorkomt signalen te snel na elkaar."""
        config = {
            "cooldown_ticks": 100,  # Very high cooldown
            "min_consensus": 2,
            "adx_threshold": 0.0,
        }
        strategy = EnhancedMomentumStrategy(config)

        prices = [100.0 + i * 3 for i in range(80)]
        signal_count = 0
        for i in range(len(prices)):
            tick = _make_tick(prices[i])
            result = await strategy.on_tick(tick)
            if result:
                signal_count += 1

        # At most 1 signal due to high cooldown
        assert signal_count <= 1

    @pytest.mark.asyncio
    async def test_signal_contains_required_fields(self):
        """Signaal bevat alle vereiste velden."""
        config = {
            "cooldown_ticks": 0,
            "min_consensus": 2,
            "adx_threshold": 0.0,
        }
        strategy = EnhancedMomentumStrategy(config)

        prices = [100.0 + i * 3 for i in range(80)]
        volumes = [100.0 + i * 5 for i in range(80)]

        last_signal = None
        for i in range(len(prices)):
            tick = _make_tick(prices[i], volume=volumes[i])
            result = await strategy.on_tick(tick)
            if result:
                last_signal = result

        if last_signal:
            assert "signal" in last_signal
            assert "symbol" in last_signal
            assert "price" in last_signal
            assert "confidence" in last_signal
            assert "metrics" in last_signal
            assert "strategy" in last_signal
            assert 0.0 <= last_signal["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_invalid_price_returns_none(self):
        """Ongeldige prijs geeft None."""
        strategy = EnhancedMomentumStrategy({})
        tick = _make_tick(0.0)
        result = await strategy.on_tick(tick)
        assert result is None

    @pytest.mark.asyncio
    async def test_multi_symbol_isolation(self):
        """Verschillende symbolen houden aparte state bij."""
        strategy = EnhancedMomentumStrategy({"cooldown_ticks": 0, "adx_threshold": 0.0})

        # Feed BTC/USD with 40 ticks
        for i in range(40):
            tick = _make_tick(100.0 + i, symbol="BTC/USD")
            await strategy.on_tick(tick)

        # Feed ETH/USD with only 10 ticks
        for i in range(10):
            tick = _make_tick(50.0 + i, symbol="ETH/USD")
            result = await strategy.on_tick(tick)
            assert result is None  # Not enough data for ETH
