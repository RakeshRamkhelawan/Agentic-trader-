"""
Tests voor Synthetic Data Generator.

Test trending, ranging, volatile, en flash crash scenarios.
"""

from datetime import UTC, datetime

import pytest

from backend.testing.synthetic_data import (
    generate_flash_crash,
    generate_ranging_market,
    generate_trending_market,
    generate_volatile_market,
)


class TestGenerateTrendingMarket:
    """Tests for generate_trending_market."""

    def test_generates_correct_number_of_candles(self):
        """Generate correct number of candles."""
        candles = generate_trending_market(num_days=30)

        assert len(candles) == 30

    def test_uptrend_increases_price(self):
        """Uptrend results in price increase."""
        candles = generate_trending_market(
            start_price=40000.0, trend_strength=0.02, num_days=30, volatility=0.01  # 2% daily
        )

        start_price = candles[0].open
        end_price = candles[-1].close

        # Should be significantly higher
        assert end_price > start_price * 1.3  # At least 30% gain

    def test_downtrend_decreases_price(self):
        """Downtrend results in price decrease."""
        candles = generate_trending_market(
            start_price=60000.0, trend_strength=-0.02, num_days=30, volatility=0.01  # -2% daily
        )

        start_price = candles[0].open
        end_price = candles[-1].close

        # Should be significantly lower
        assert end_price < start_price * 0.7  # At least 30% loss

    def test_ohlcv_constraints_respected(self):
        """All candles respect OHLCV constraints."""
        candles = generate_trending_market(num_days=20)

        for candle in candles:
            assert candle.high >= candle.close
            assert candle.low <= candle.close
            assert candle.high >= candle.low
            assert candle.volume >= 0


class TestGenerateRangingMarket:
    """Tests for generate_ranging_market."""

    def test_generates_correct_number_of_candles(self):
        """Generate correct number of candles."""
        candles = generate_ranging_market(num_days=30)

        assert len(candles) == 30

    def test_prices_stay_within_range(self):
        """Prices oscillate within range."""
        center = 50000.0
        range_pct = 0.05
        candles = generate_ranging_market(center_price=center, range_pct=range_pct, num_days=30)

        range_low = center * (1 - range_pct)
        range_high = center * (1 + range_pct)

        for candle in candles:
            # Allow small overshoot voor high/low
            assert candle.low >= range_low * 0.98
            assert candle.high <= range_high * 1.02

    def test_no_strong_trend(self):
        """Ranging market has no strong trend."""
        candles = generate_ranging_market(center_price=50000.0, num_days=50)

        start_price = candles[0].close
        end_price = candles[-1].close

        # Should end near starting price
        price_change_pct = abs(end_price - start_price) / start_price
        assert price_change_pct < 0.15  # Less than 15% total change


class TestGenerateVolatileMarket:
    """Tests for generate_volatile_market."""

    def test_generates_correct_number_of_candles(self):
        """Generate correct number of candles."""
        candles = generate_volatile_market(num_days=30)

        assert len(candles) == 30

    def test_has_large_daily_swings(self):
        """Volatile market has large daily swings."""
        candles = generate_volatile_market(
            start_price=50000.0, volatility=0.08, num_days=30  # 8% swings
        )

        large_moves = 0

        for candle in candles:
            daily_range = (candle.high - candle.low) / candle.close
            if daily_range > 0.05:  # 5% daily range
                large_moves += 1

        # Most days should have large moves
        assert large_moves > 20


class TestGenerateFlashCrash:
    """Tests for generate_flash_crash."""

    def test_includes_crash_candle(self):
        """Scenario includes crash candle."""
        candles = generate_flash_crash(start_price=50000.0, crash_depth=0.20, recovery_hours=6)

        # Find crash candle (highest volume)
        crash_candle = max(candles, key=lambda c: c.volume)

        # Should have massive volume spike
        assert crash_candle.volume > 100000

        # Should have deep low
        expected_crash_price = 50000.0 * 0.80  # -20%
        assert crash_candle.low < expected_crash_price * 1.05

    def test_recovers_after_crash(self):
        """Price recovers after crash."""
        start_price = 50000.0
        candles = generate_flash_crash(start_price=start_price, crash_depth=0.20, recovery_hours=6)

        # Last candle should be near start price
        final_price = candles[-1].close

        # Should recover to within 5% of start
        assert abs(final_price - start_price) / start_price < 0.05

    def test_total_duration(self):
        """Flash crash has expected duration."""
        recovery_hours = 6
        candles = generate_flash_crash(recovery_hours=recovery_hours)

        # Pre-crash (24h) + crash (1h) + recovery (6h) = 31 candles
        expected_candles = 24 + 1 + recovery_hours
        assert len(candles) == expected_candles
