from enum import Enum
from typing import List, Tuple

import numpy as np


class MarketRegime(str, Enum):
    BULL = "BULL"
    BEAR = "BEAR"
    SIDEWAYS = "SIDEWAYS"
    VOLATILE = "VOLATILE"


class RegimeDetector:
    """
    Classifies the current market state to adjust strategy parameters.
    Uses numpy for efficient calculation of technical indicators.
    """

    def calculate_indicators(self, prices: List[float]) -> Tuple[float, float, float]:
        """
        Calculates SMA50, SMA200, and Volatility (StdDev of last 20 periods).
        Assumes prices are ordered from oldest to newest.
        """
        if len(prices) < 200:
            # Not enough data, return safe defaults
            # Use last price for SMAs to simulate flat trend, and 0 vol
            last_price = prices[-1] if prices else 0.0
            return last_price, last_price, 0.0

        np_prices = np.array(prices)

        sma_50 = np.mean(np_prices[-50:])
        sma_200 = np.mean(np_prices[-200:])

        # Volatility: Standard Deviation of returns over last 20 periods
        # Log returns are better, but simple returns ok for now
        # We'll just use price std dev relative to price for simplicity in this cycle
        # Or ATR approximation. Let's use StdDev of last 20 prices normalized by mean
        recent_prices = np_prices[-20:]
        std_dev = np.std(recent_prices)
        mean_price = np.mean(recent_prices)
        volatility = std_dev / mean_price if mean_price > 0 else 0.0

        return sma_50, sma_200, volatility

    def detect(
        self, price: float, sma_50: float, sma_200: float, volatility: float
    ) -> MarketRegime:
        """
        Determines the market regime based on indicators.
        """
        # High Volatility Override
        # If volatility (std dev / price) > 2% (0.02), we consider it volatile for this timeframe
        if volatility > 0.02:
            return MarketRegime.VOLATILE

        # Bull Trend: Price > SMA50 > SMA200
        if price > sma_50 and sma_50 > sma_200:
            return MarketRegime.BULL

        # Bear Trend: Price < SMA50 < SMA200
        if price < sma_50 and sma_50 < sma_200:
            return MarketRegime.BEAR

        # Default to Sideways (Choppy or Consolidating)
        return MarketRegime.SIDEWAYS
