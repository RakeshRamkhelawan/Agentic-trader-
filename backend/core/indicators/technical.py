"""
Technical Indicators Library - Shared calculations for agents and strategies.

Provides stateless, pure-function indicator calculations using numpy and pandas.
All methods are static and operate on price/volume arrays.

Indicators:
- RSI (Relative Strength Index) with Wilder's smoothing
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- ADX (Average Directional Index)
- EMA (Exponential Moving Average)
- OBV (On-Balance Volume)
"""

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class MACDResult:
    """MACD calculation result."""

    macd_line: float
    signal_line: float
    histogram: float


@dataclass
class BollingerResult:
    """Bollinger Bands calculation result."""

    upper: float
    middle: float
    lower: float
    width: float  # Band width as percentage of middle
    percent_b: float  # Where price is relative to bands (0=lower, 1=upper)


class TechnicalIndicators:
    """
    Stateless technical indicator calculations.

    All methods accept price/volume arrays and return computed values.
    Designed to be shared across agents and strategies.
    """

    @staticmethod
    def calculate_rsi(
        prices: list[float],
        period: int = 14,
    ) -> Optional[float]:
        """
        Calculate RSI using Wilder's Smoothing (EMA-based).

        Args:
            prices: List of closing prices (oldest first).
            period: RSI period (default 14).

        Returns:
            RSI value [0, 100] or None if insufficient data.
        """
        if len(prices) < period + 1:
            return None

        series = pd.Series(prices, dtype=float)
        delta = series.diff()

        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)

        # Wilder's smoothing (EMA with alpha = 1/period)
        avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

        curr_gain = avg_gain.iloc[-1]
        curr_loss = avg_loss.iloc[-1]

        if pd.isna(curr_gain) or pd.isna(curr_loss):
            return None

        if curr_loss == 0:
            return 100.0 if curr_gain > 0 else 50.0

        rs = curr_gain / curr_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))

        return float(rsi)

    @staticmethod
    def calculate_macd(
        prices: list[float],
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> Optional[MACDResult]:
        """
        Calculate MACD (Moving Average Convergence Divergence).

        Args:
            prices: List of closing prices (oldest first).
            fast_period: Fast EMA period (default 12).
            slow_period: Slow EMA period (default 26).
            signal_period: Signal line EMA period (default 9).

        Returns:
            MACDResult or None if insufficient data.
        """
        min_required = slow_period + signal_period
        if len(prices) < min_required:
            return None

        series = pd.Series(prices, dtype=float)

        fast_ema = series.ewm(span=fast_period, adjust=False).mean()
        slow_ema = series.ewm(span=slow_period, adjust=False).mean()

        macd_line = fast_ema - slow_ema
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        histogram = macd_line - signal_line

        macd_val = macd_line.iloc[-1]
        signal_val = signal_line.iloc[-1]
        hist_val = histogram.iloc[-1]

        if pd.isna(macd_val) or pd.isna(signal_val):
            return None

        return MACDResult(
            macd_line=float(macd_val),
            signal_line=float(signal_val),
            histogram=float(hist_val),
        )

    @staticmethod
    def calculate_bollinger_bands(
        prices: list[float],
        period: int = 20,
        std_dev: float = 2.0,
    ) -> Optional[BollingerResult]:
        """
        Calculate Bollinger Bands.

        Args:
            prices: List of closing prices (oldest first).
            period: SMA period (default 20).
            std_dev: Number of standard deviations (default 2.0).

        Returns:
            BollingerResult or None if insufficient data.
        """
        if len(prices) < period:
            return None

        series = pd.Series(prices, dtype=float)
        rolling = series.rolling(window=period)

        sma = rolling.mean().iloc[-1]
        std = rolling.std().iloc[-1]

        if pd.isna(sma) or pd.isna(std):
            return None

        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)

        # Band width as percentage of middle
        width = ((upper - lower) / sma * 100.0) if sma > 0 else 0.0

        # Percent B: where current price is relative to bands
        current_price = prices[-1]
        band_range = upper - lower
        if band_range > 0:
            percent_b = (current_price - lower) / band_range
        else:
            percent_b = 0.5

        return BollingerResult(
            upper=float(upper),
            middle=float(sma),
            lower=float(lower),
            width=float(width),
            percent_b=float(percent_b),
        )

    @staticmethod
    def calculate_adx(
        highs: list[float],
        lows: list[float],
        closes: list[float],
        period: int = 14,
    ) -> Optional[float]:
        """
        Calculate ADX (Average Directional Index).

        Measures trend strength regardless of direction.
        ADX > 25 = strong trend, ADX < 20 = weak/no trend.

        Args:
            highs: List of high prices.
            lows: List of low prices.
            closes: List of closing prices.
            period: ADX period (default 14).

        Returns:
            ADX value [0, 100] or None if insufficient data.
        """
        min_required = period * 2 + 1
        if len(closes) < min_required or len(highs) < min_required or len(lows) < min_required:
            return None

        high = np.array(highs, dtype=float)
        low = np.array(lows, dtype=float)
        close = np.array(closes, dtype=float)

        # True Range
        tr1 = high[1:] - low[1:]
        tr2 = np.abs(high[1:] - close[:-1])
        tr3 = np.abs(low[1:] - close[:-1])
        tr = np.maximum(tr1, np.maximum(tr2, tr3))

        # Directional Movement
        up_move = high[1:] - high[:-1]
        down_move = low[:-1] - low[1:]

        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)

        # Wilder's smoothing via pandas EMA
        alpha = 1.0 / period

        atr = pd.Series(tr).ewm(alpha=alpha, adjust=False).mean()
        plus_di_smooth = pd.Series(plus_dm).ewm(alpha=alpha, adjust=False).mean()
        minus_di_smooth = pd.Series(minus_dm).ewm(alpha=alpha, adjust=False).mean()

        # Directional Indicators
        atr_vals = atr.values
        safe_atr = np.where(atr_vals > 0, atr_vals, 1.0)
        plus_di = 100.0 * plus_di_smooth.values / safe_atr
        minus_di = 100.0 * minus_di_smooth.values / safe_atr

        # DX and ADX
        di_sum = plus_di + minus_di
        safe_di_sum = np.where(di_sum > 0, di_sum, 1.0)
        dx = 100.0 * np.abs(plus_di - minus_di) / safe_di_sum

        adx = pd.Series(dx).ewm(alpha=alpha, adjust=False).mean()

        result = adx.iloc[-1]
        if pd.isna(result):
            return None

        return float(result)

    @staticmethod
    def calculate_ema(
        prices: list[float],
        period: int,
    ) -> Optional[float]:
        """
        Calculate Exponential Moving Average.

        Args:
            prices: List of closing prices (oldest first).
            period: EMA period.

        Returns:
            EMA value or None if insufficient data.
        """
        if len(prices) < period:
            return None

        series = pd.Series(prices, dtype=float)
        ema = series.ewm(span=period, adjust=False).mean()

        result = ema.iloc[-1]
        if pd.isna(result):
            return None

        return float(result)

    @staticmethod
    def calculate_ema_stack(
        prices: list[float],
        periods: tuple[int, ...] = (8, 21, 55),
    ) -> Optional[dict[int, float]]:
        """
        Calculate multiple EMAs for stack alignment analysis.

        Bullish alignment: short EMA > medium EMA > long EMA
        Bearish alignment: short EMA < medium EMA < long EMA

        Args:
            prices: List of closing prices (oldest first).
            periods: Tuple of EMA periods (default 8, 21, 55).

        Returns:
            Dict mapping period to EMA value, or None if insufficient data.
        """
        max_period = max(periods)
        if len(prices) < max_period:
            return None

        result = {}
        for period in periods:
            ema = TechnicalIndicators.calculate_ema(prices, period)
            if ema is None:
                return None
            result[period] = ema

        return result

    @staticmethod
    def is_ema_bullish_aligned(ema_stack: dict[int, float]) -> bool:
        """Check if EMAs are in bullish alignment (short > medium > long)."""
        periods = sorted(ema_stack.keys())
        if len(periods) < 2:
            return False
        return all(ema_stack[periods[i]] > ema_stack[periods[i + 1]] for i in range(len(periods) - 1))

    @staticmethod
    def is_ema_bearish_aligned(ema_stack: dict[int, float]) -> bool:
        """Check if EMAs are in bearish alignment (short < medium < long)."""
        periods = sorted(ema_stack.keys())
        if len(periods) < 2:
            return False
        return all(ema_stack[periods[i]] < ema_stack[periods[i + 1]] for i in range(len(periods) - 1))

    @staticmethod
    def calculate_obv(
        prices: list[float],
        volumes: list[float],
    ) -> Optional[float]:
        """
        Calculate On-Balance Volume.

        OBV tracks cumulative buying/selling pressure via volume.
        Rising OBV confirms uptrend, falling OBV confirms downtrend.

        Args:
            prices: List of closing prices (oldest first).
            volumes: List of volume values (same length as prices).

        Returns:
            Current OBV value or None if insufficient data.
        """
        if len(prices) < 2 or len(volumes) < 2 or len(prices) != len(volumes):
            return None

        obv = 0.0
        for i in range(1, len(prices)):
            if prices[i] > prices[i - 1]:
                obv += volumes[i]
            elif prices[i] < prices[i - 1]:
                obv -= volumes[i]
            # Equal prices: OBV unchanged

        return obv

    @staticmethod
    def calculate_obv_ema(
        prices: list[float],
        volumes: list[float],
        period: int = 20,
    ) -> Optional[float]:
        """
        Calculate OBV EMA for trend confirmation.

        Returns the ratio of current OBV to its EMA.
        > 1.0 = bullish volume trend, < 1.0 = bearish volume trend.

        Args:
            prices: List of closing prices.
            volumes: List of volumes.
            period: EMA period for OBV smoothing.

        Returns:
            OBV/EMA ratio or None if insufficient data.
        """
        if len(prices) < period + 1 or len(volumes) < period + 1:
            return None

        # Calculate OBV series
        obv_series = [0.0]
        for i in range(1, len(prices)):
            if prices[i] > prices[i - 1]:
                obv_series.append(obv_series[-1] + volumes[i])
            elif prices[i] < prices[i - 1]:
                obv_series.append(obv_series[-1] - volumes[i])
            else:
                obv_series.append(obv_series[-1])

        obv_pd = pd.Series(obv_series, dtype=float)
        obv_ema = obv_pd.ewm(span=period, adjust=False).mean().iloc[-1]

        if pd.isna(obv_ema) or obv_ema == 0:
            return 1.0  # Neutral

        return float(obv_pd.iloc[-1] / obv_ema)
