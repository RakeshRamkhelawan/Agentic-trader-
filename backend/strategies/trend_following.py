"""
Trend Following Strategy - Dual Moving Average Crossover + RSI + Volume.

Uses configurable short/long MA crossover with RSI momentum confirmation
and volume spike filter to identify high-probability trend entries.

Entry Long:  Short MA > Long MA + RSI > 50 + Volume > multiplier * avg
Entry Short: Short MA < Long MA + RSI < 50
"""

import logging
from typing import Any

import pandas as pd

from backend.core.market_data.models import UnifiedMarketEvent
from backend.strategies.base import BaseStrategy

logger = logging.getLogger(__name__)


class TrendFollowingStrategy(BaseStrategy):
    """
    Trend Following Strategy based on MA Crossover + RSI + Volume.

    Config:
        short_window (int): Period for fast MA. Default 50.
        long_window (int): Period for slow MA. Default 200.
        rsi_period (int): Period for RSI calculation. Default 14.
        rsi_threshold (int): RSI threshold for momentum confirmation. Default 50.
        volume_multiplier (float): Required volume vs average for confirmation. Default 1.5.
        max_history (int): Max ticks to keep in memory. Default 500.
    """

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.short_window = config.get("short_window", 50)
        self.long_window = config.get("long_window", 200)
        self.rsi_period = config.get("rsi_period", 14)
        self.rsi_threshold = config.get("rsi_threshold", 50)
        self.volume_multiplier = config.get("volume_multiplier", 1.5)
        self.max_history = config.get("max_history", 500)

        self._price_history: dict[str, list[float]] = {}
        self._volume_history: dict[str, list[float]] = {}
        self._prev_crossover: dict[str, str | None] = {}

    async def on_tick(self, tick: UnifiedMarketEvent) -> dict[str, Any] | None:
        if not tick.price or tick.price <= 0:
            return None

        symbol = tick.symbol
        price = float(tick.price)
        volume = float(tick.volume) if tick.volume else 0.0

        # Initialize histories
        if symbol not in self._price_history:
            self._price_history[symbol] = []
            self._volume_history[symbol] = []
            self._prev_crossover[symbol] = None

        prices = self._price_history[symbol]
        volumes = self._volume_history[symbol]
        prices.append(price)
        volumes.append(volume)

        # Trim histories
        if len(prices) > self.max_history:
            prices.pop(0)
        if len(volumes) > self.max_history:
            volumes.pop(0)

        # Need enough data for long MA + RSI
        min_required = max(self.long_window, self.rsi_period + 1)
        if len(prices) < min_required:
            return None

        try:
            # Calculate Moving Averages
            series = pd.Series(prices)
            short_ma = series.rolling(window=self.short_window).mean().iloc[-1]
            long_ma = series.rolling(window=self.long_window).mean().iloc[-1]

            if pd.isna(short_ma) or pd.isna(long_ma):
                return None

            # Calculate RSI
            rsi = self._calculate_rsi(prices)
            if rsi is None:
                return None

            # Determine crossover state
            if short_ma > long_ma:
                current_cross = "GOLDEN"
            else:
                current_cross = "DEATH"

            prev = self._prev_crossover[symbol]
            self._prev_crossover[symbol] = current_cross

            # Only signal on actual crossover (state change)
            if prev is None or prev == current_cross:
                return None

            # Volume confirmation
            volume_confirmed = True
            if len(volumes) >= self.short_window and self.volume_multiplier > 0:
                avg_volume = sum(volumes[-self.short_window :]) / self.short_window
                if avg_volume > 0:
                    volume_confirmed = volume >= (avg_volume * self.volume_multiplier)

            # Generate signals
            direction = None
            if current_cross == "GOLDEN" and rsi > self.rsi_threshold and volume_confirmed:
                direction = "BULLISH"
            elif current_cross == "DEATH" and rsi < self.rsi_threshold:
                direction = "BEARISH"

            if direction:
                return {
                    "signal": "%s_TREND" % direction,
                    "symbol": symbol,
                    "price": price,
                    "metrics": {
                        "short_ma": round(short_ma, 2),
                        "long_ma": round(long_ma, 2),
                        "rsi": round(rsi, 2),
                        "volume": volume,
                        "volume_confirmed": volume_confirmed,
                    },
                    "strategy": "trend_following_ma_rsi",
                    "metadata": {
                        "short_window": self.short_window,
                        "long_window": self.long_window,
                        "rsi_period": self.rsi_period,
                        "crossover": current_cross,
                    },
                }

        except Exception as e:
            logger.error("Error in TrendFollowing for %s: %s", symbol, e)
            return None

        return None

    def _calculate_rsi(self, prices: list[float]) -> float | None:
        """Calculate RSI using Wilder's smoothing via pandas."""
        if len(prices) < self.rsi_period + 1:
            return None

        series = pd.Series(prices)
        delta = series.diff()

        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(window=self.rsi_period, min_periods=self.rsi_period).mean()
        avg_loss = loss.rolling(window=self.rsi_period, min_periods=self.rsi_period).mean()

        curr_gain = avg_gain.iloc[-1]
        curr_loss = avg_loss.iloc[-1]

        if pd.isna(curr_gain) or pd.isna(curr_loss):
            return None

        if curr_loss == 0:
            return 100.0 if curr_gain > 0 else 50.0

        rs = curr_gain / curr_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
