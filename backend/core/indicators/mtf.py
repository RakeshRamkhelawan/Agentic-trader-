"""
Multi-Timeframe (MTF) Analyzer.

Analyzes price data across multiple timeframes to determine macro trend alignment.
Assigns higher weights to higher timeframes to filter out short-term noise.
"""

import logging
from typing import ClassVar

from backend.core.indicators.technical import TechnicalIndicators

logger = logging.getLogger(__name__)


class MultiTimeframeAnalyzer:
    """
    Analyzes trend direction across multiple timeframes to produce a composite macro trend score.
    """

    # Supported timeframes and their relative weights (sum to 1.0)
    TIMEFRAME_WEIGHTS: ClassVar[dict[str, float]] = {
        "5m": 0.05,
        "15m": 0.10,
        "1h": 0.20,
        "4h": 0.30,
        "1d": 0.35,
    }

    @classmethod
    def analyze_macro_trend(cls, timeframe_data: dict[str, list[float]]) -> float:
        """
        Calculate a composite macro trend score (-1.0 to 1.0).

        Args:
            timeframe_data: Dictionary mapping timeframe string (e.g., "1h") to a list
                          of historical closing prices (oldest to newest).

        Returns:
            Float between -1.0 (strong macro downtrend) and 1.0 (strong macro uptrend).
            Returns 0.0 if insufficient data or mixed trends.
        """
        if not timeframe_data:
            return 0.0

        total_score = 0.0
        applied_weight = 0.0

        for tf, weight in cls.TIMEFRAME_WEIGHTS.items():
            prices = timeframe_data.get(tf)
            if not prices or len(prices) < 55:  # Need at least 55 for EMA stack
                logger.debug("Insufficient data for timeframe %s, skipping.", tf)
                continue

            # Calculate direction for this timeframe (-1.0, 0.0, or 1.0)
            tf_direction = cls._calculate_timeframe_direction(prices)

            total_score += tf_direction * weight
            applied_weight += weight

        # Normalize score if some timeframes were missing data
        if applied_weight == 0.0:
            return 0.0

        normalized_score = total_score / applied_weight
        return round(normalized_score, 4)

    @classmethod
    def _calculate_timeframe_direction(cls, prices: list[float]) -> float:
        """
        Calculate trend direction (-1.0 to 1.0) for a single timeframe.
        Uses EMA Stack alignment and RSI.
        """
        ema_stack = TechnicalIndicators.calculate_ema_stack(prices)
        if not ema_stack:
            return 0.0

        rsi = TechnicalIndicators.calculate_rsi(prices, period=14)
        if rsi is None:
            return 0.0

        direction = 0.0

        # Bullish criteria: EMAs are bullish aligned AND RSI > 50
        if TechnicalIndicators.is_ema_bullish_aligned(ema_stack):
            if rsi >= 50:
                direction = 1.0
            else:
                direction = 0.5  # Weaker bullish signal if RSI lags

        # Bearish criteria: EMAs are bearish aligned AND RSI < 50
        elif TechnicalIndicators.is_ema_bearish_aligned(ema_stack):
            if rsi <= 50:
                direction = -1.0
            else:
                direction = -0.5  # Weaker bearish signal if RSI lags

        return direction
