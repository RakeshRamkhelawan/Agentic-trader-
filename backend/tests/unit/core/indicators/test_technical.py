"""
Unit tests voor TechnicalIndicators library.

Test elke indicator met bekende datasets en edge cases.
"""

import pytest

from backend.core.indicators.technical import (
    BollingerResult,
    MACDResult,
    TechnicalIndicators,
)


class TestRSI:
    """Tests voor RSI berekening."""

    def test_insufficient_data_returns_none(self):
        """Te weinig data geeft None."""
        prices = [100.0] * 10  # Need 15 voor period=14
        assert TechnicalIndicators.calculate_rsi(prices, period=14) is None

    def test_flat_prices_returns_50(self):
        """Constante prijs geeft RSI ~50."""
        prices = [100.0] * 20
        rsi = TechnicalIndicators.calculate_rsi(prices, period=14)
        assert rsi is not None
        assert rsi == 50.0

    def test_strong_uptrend_above_70(self):
        """Sterke uptrend geeft RSI > 70."""
        prices = [100.0 + i * 5 for i in range(30)]  # 100, 105, 110, ...
        rsi = TechnicalIndicators.calculate_rsi(prices, period=14)
        assert rsi is not None
        assert rsi > 70.0

    def test_strong_downtrend_below_30(self):
        """Sterke downtrend geeft RSI < 30."""
        prices = [200.0 - i * 5 for i in range(30)]  # 200, 195, 190, ...
        rsi = TechnicalIndicators.calculate_rsi(prices, period=14)
        assert rsi is not None
        assert rsi < 30.0

    def test_rsi_bounded_0_100(self):
        """RSI is altijd tussen 0 en 100."""
        # Extreme uptrend
        prices = [100.0 + i * 50 for i in range(30)]
        rsi = TechnicalIndicators.calculate_rsi(prices, period=14)
        assert rsi is not None
        assert 0.0 <= rsi <= 100.0

    def test_custom_period(self):
        """Custom RSI period werkt correct."""
        prices = [100.0 + i * 2 for i in range(20)]
        rsi = TechnicalIndicators.calculate_rsi(prices, period=5)
        assert rsi is not None
        assert rsi > 50.0  # Uptrend


class TestMACD:
    """Tests voor MACD berekening."""

    def test_insufficient_data_returns_none(self):
        """Te weinig data geeft None."""
        prices = [100.0] * 20  # Need 26+9=35
        assert TechnicalIndicators.calculate_macd(prices) is None

    def test_returns_macd_result(self):
        """Geeft een MACDResult object terug."""
        prices = [100.0 + i * 0.5 for i in range(50)]
        result = TechnicalIndicators.calculate_macd(prices)
        assert result is not None
        assert isinstance(result, MACDResult)

    def test_uptrend_positive_macd(self):
        """Uptrend geeft positieve MACD lijn."""
        prices = [100.0 + i * 2 for i in range(50)]
        result = TechnicalIndicators.calculate_macd(prices)
        assert result is not None
        assert result.macd_line > 0

    def test_downtrend_negative_macd(self):
        """Downtrend geeft negatieve MACD lijn."""
        prices = [200.0 - i * 2 for i in range(50)]
        result = TechnicalIndicators.calculate_macd(prices)
        assert result is not None
        assert result.macd_line < 0

    def test_flat_prices_near_zero(self):
        """Constante prijs geeft MACD ~0."""
        prices = [100.0] * 50
        result = TechnicalIndicators.calculate_macd(prices)
        assert result is not None
        assert abs(result.macd_line) < 0.01
        assert abs(result.histogram) < 0.01


class TestBollingerBands:
    """Tests voor Bollinger Bands berekening."""

    def test_insufficient_data_returns_none(self):
        """Te weinig data geeft None."""
        prices = [100.0] * 10  # Need 20
        assert TechnicalIndicators.calculate_bollinger_bands(prices) is None

    def test_returns_bollinger_result(self):
        """Geeft een BollingerResult object terug."""
        prices = [100.0 + i * 0.1 for i in range(25)]
        result = TechnicalIndicators.calculate_bollinger_bands(prices)
        assert result is not None
        assert isinstance(result, BollingerResult)

    def test_upper_above_lower(self):
        """Upper band is altijd boven lower band."""
        prices = [100.0 + (i % 5) for i in range(30)]  # Some variance
        result = TechnicalIndicators.calculate_bollinger_bands(prices)
        assert result is not None
        assert result.upper > result.lower

    def test_middle_is_sma(self):
        """Middle is de SMA van de prijs."""
        prices = [100.0 + i for i in range(25)]
        result = TechnicalIndicators.calculate_bollinger_bands(prices, period=20)
        assert result is not None
        expected_sma = sum(prices[-20:]) / 20
        assert abs(result.middle - expected_sma) < 0.01

    def test_price_above_upper_percent_b_above_1(self):
        """Prijs boven upper band geeft percent_b > 1."""
        prices = [100.0] * 20 + [200.0]  # Spike
        result = TechnicalIndicators.calculate_bollinger_bands(prices, period=20)
        assert result is not None
        assert result.percent_b > 1.0

    def test_price_below_lower_percent_b_below_0(self):
        """Prijs onder lower band geeft percent_b < 0."""
        prices = [100.0] * 20 + [10.0]  # Drop
        result = TechnicalIndicators.calculate_bollinger_bands(prices, period=20)
        assert result is not None
        assert result.percent_b < 0.0

    def test_width_positive(self):
        """Band width is altijd positief."""
        prices = [100.0 + (i % 10) for i in range(30)]
        result = TechnicalIndicators.calculate_bollinger_bands(prices)
        assert result is not None
        assert result.width > 0.0


class TestADX:
    """Tests voor ADX berekening."""

    def test_insufficient_data_returns_none(self):
        """Te weinig data geeft None."""
        n = 10
        assert TechnicalIndicators.calculate_adx([1.0] * n, [1.0] * n, [1.0] * n, period=14) is None

    def test_strong_trend_high_adx(self):
        """Sterke trend geeft hoge ADX (>25)."""
        n = 60
        closes = [100.0 + i * 3 for i in range(n)]
        highs = [c + 2 for c in closes]
        lows = [c - 1 for c in closes]

        adx = TechnicalIndicators.calculate_adx(highs, lows, closes, period=14)
        assert adx is not None
        assert adx > 20.0  # Strong trend

    def test_adx_bounded_0_100(self):
        """ADX is altijd tussen 0 en 100."""
        n = 60
        closes = [100.0 + i * 5 for i in range(n)]
        highs = [c + 3 for c in closes]
        lows = [c - 2 for c in closes]

        adx = TechnicalIndicators.calculate_adx(highs, lows, closes, period=14)
        assert adx is not None
        assert 0.0 <= adx <= 100.0


class TestEMA:
    """Tests voor EMA berekening."""

    def test_insufficient_data_returns_none(self):
        """Te weinig data geeft None."""
        prices = [100.0] * 5
        assert TechnicalIndicators.calculate_ema(prices, period=10) is None

    def test_constant_price_equals_price(self):
        """EMA van constante prijs is gelijk aan die prijs."""
        prices = [100.0] * 20
        ema = TechnicalIndicators.calculate_ema(prices, period=10)
        assert ema is not None
        assert abs(ema - 100.0) < 0.01

    def test_uptrend_ema_below_last_price(self):
        """In uptrend is EMA onder de laatste prijs (EMA is lagging)."""
        prices = [100.0 + i * 2 for i in range(30)]
        ema = TechnicalIndicators.calculate_ema(prices, period=10)
        assert ema is not None
        assert ema < prices[-1]


class TestEMAStack:
    """Tests voor EMA stack alignment."""

    def test_insufficient_data_returns_none(self):
        """Te weinig data geeft None."""
        prices = [100.0] * 30  # Need 55
        assert TechnicalIndicators.calculate_ema_stack(prices) is None

    def test_returns_dict_with_periods(self):
        """Geeft dict terug met alle periodes."""
        prices = [100.0 + i * 0.5 for i in range(60)]
        result = TechnicalIndicators.calculate_ema_stack(prices)
        assert result is not None
        assert 8 in result
        assert 21 in result
        assert 55 in result

    def test_bullish_alignment_in_uptrend(self):
        """Uptrend geeft bullish alignment (8 > 21 > 55)."""
        prices = [100.0 + i * 2 for i in range(80)]
        result = TechnicalIndicators.calculate_ema_stack(prices)
        assert result is not None
        assert TechnicalIndicators.is_ema_bullish_aligned(result)

    def test_bearish_alignment_in_downtrend(self):
        """Downtrend geeft bearish alignment (8 < 21 < 55)."""
        prices = [300.0 - i * 2 for i in range(80)]
        result = TechnicalIndicators.calculate_ema_stack(prices)
        assert result is not None
        assert TechnicalIndicators.is_ema_bearish_aligned(result)


class TestOBV:
    """Tests voor OBV berekening."""

    def test_insufficient_data_returns_none(self):
        """Te weinig data geeft None."""
        assert TechnicalIndicators.calculate_obv([100.0], [10.0]) is None

    def test_mismatched_lengths_returns_none(self):
        """Verschillende lengtes geeft None."""
        assert TechnicalIndicators.calculate_obv([100.0, 101.0], [10.0]) is None

    def test_uptrend_positive_obv(self):
        """Uptrend met volume geeft positieve OBV."""
        prices = [100.0, 101.0, 102.0, 103.0, 104.0]
        volumes = [100.0, 200.0, 150.0, 300.0, 250.0]
        obv = TechnicalIndicators.calculate_obv(prices, volumes)
        assert obv is not None
        assert obv > 0

    def test_downtrend_negative_obv(self):
        """Downtrend met volume geeft negatieve OBV."""
        prices = [104.0, 103.0, 102.0, 101.0, 100.0]
        volumes = [100.0, 200.0, 150.0, 300.0, 250.0]
        obv = TechnicalIndicators.calculate_obv(prices, volumes)
        assert obv is not None
        assert obv < 0

    def test_flat_prices_zero_obv(self):
        """Constante prijs geeft OBV = 0."""
        prices = [100.0] * 5
        volumes = [100.0] * 5
        obv = TechnicalIndicators.calculate_obv(prices, volumes)
        assert obv is not None
        assert obv == 0.0
