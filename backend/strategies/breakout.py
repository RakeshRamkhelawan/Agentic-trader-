"""
Breakout Strategy - Consolidation Range Detection + Volume Confirmation.

Detects periods of price consolidation (low range) and generates signals
when price breaks out of the range with volume confirmation.

Entry Long:  Price > range_high + volume > multiplier * avg
Entry Short: Price < range_low + volume > multiplier * avg
"""

import logging
from typing import Any

from backend.core.market_data.models import UnifiedMarketEvent
from backend.strategies.base import BaseStrategy

logger = logging.getLogger(__name__)


class BreakoutStrategy(BaseStrategy):
    """
    Breakout Strategy based on Consolidation Range + Volume Confirmation.

    Config:
        consolidation_bars (int): Bars to check for consolidation. Default 20.
        range_threshold (float): Max range as % of midpoint for consolidation. Default 0.03 (3%).
        volume_multiplier (float): Required volume vs average for confirmation. Default 2.0.
        max_history (int): Max ticks to keep in memory. Default 200.
    """

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.consolidation_bars = config.get("consolidation_bars", 20)
        self.range_threshold = config.get("range_threshold", 0.03)
        self.volume_multiplier = config.get("volume_multiplier", 2.0)
        self.max_history = config.get("max_history", 200)

        self._price_history: dict[str, list[float]] = {}
        self._volume_history: dict[str, list[float]] = {}
        self._consolidation_state: dict[str, bool] = {}

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
            self._consolidation_state[symbol] = False

        prices = self._price_history[symbol]
        volumes = self._volume_history[symbol]
        prices.append(price)
        volumes.append(volume)

        # Trim histories
        if len(prices) > self.max_history:
            prices.pop(0)
        if len(volumes) > self.max_history:
            volumes.pop(0)

        # Need enough bars for consolidation detection
        if len(prices) < self.consolidation_bars + 1:
            return None

        try:
            # Use the bars BEFORE the current one for range detection
            lookback = prices[-(self.consolidation_bars + 1) : -1]
            range_high = max(lookback)
            range_low = min(lookback)
            midpoint = (range_high + range_low) / 2.0

            if midpoint <= 0:
                return None

            # Calculate range as percentage of midpoint
            price_range = (range_high - range_low) / midpoint
            is_consolidating = price_range < self.range_threshold

            was_consolidating = self._consolidation_state[symbol]
            self._consolidation_state[symbol] = is_consolidating

            # Breakout detection: was consolidating AND price breaks out
            if not was_consolidating:
                return None

            # Volume confirmation
            volume_confirmed = True
            if len(volumes) >= self.consolidation_bars and self.volume_multiplier > 0:
                avg_volume = sum(volumes[-self.consolidation_bars :]) / self.consolidation_bars
                if avg_volume > 0:
                    volume_confirmed = volume >= (avg_volume * self.volume_multiplier)

            direction = None
            if price > range_high and volume_confirmed:
                direction = "BULLISH"
            elif price < range_low and volume_confirmed:
                direction = "BEARISH"

            if direction:
                return {
                    "signal": "%s_BREAKOUT" % direction,
                    "symbol": symbol,
                    "price": price,
                    "metrics": {
                        "range_high": round(range_high, 2),
                        "range_low": round(range_low, 2),
                        "range_pct": round(price_range, 4),
                        "volume": volume,
                        "volume_confirmed": volume_confirmed,
                    },
                    "strategy": "breakout_consolidation",
                    "metadata": {
                        "consolidation_bars": self.consolidation_bars,
                        "range_threshold": self.range_threshold,
                    },
                }

        except Exception as e:
            logger.error("Error in Breakout for %s: %s", symbol, e)
            return None

        return None
