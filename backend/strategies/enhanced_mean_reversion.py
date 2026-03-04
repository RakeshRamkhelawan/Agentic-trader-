"""
Enhanced Mean Reversion Strategy - Multi-indicator mean reversion.

Uses 4 indicators for signal consensus:
1. Bollinger Bands position (price vs bands)
2. RSI divergence (RSI oversold at lower band = strong buy signal)
3. Volume spike detection at band-touching
4. BB squeeze detection (narrow bands = upcoming breakout, avoid entry)

Avoids entries during BB squeezes to prevent false mean-reversion trades
in breakout situations.
"""

import logging
from typing import Any, Optional

from backend.core.indicators.technical import TechnicalIndicators
from backend.core.market_data.models import UnifiedMarketEvent
from backend.strategies.base import BaseStrategy

logger = logging.getLogger(__name__)


class EnhancedMeanReversionStrategy(BaseStrategy):
    """
    Enhanced Mean Reversion Strategy with Bollinger + RSI + Volume analysis.

    Config:
        bb_period (int): Bollinger Bands period. Default 20.
        bb_std_dev (float): Number of standard deviations. Default 2.0.
        rsi_period (int): RSI period. Default 14.
        rsi_oversold (int): RSI oversold threshold for buy confirmation. Default 35.
        rsi_overbought (int): RSI overbought threshold for sell confirmation. Default 65.
        volume_spike_multiplier (float): Volume vs avg for confirmation. Default 1.5.
        squeeze_threshold (float): BB width below this = squeeze (no entry). Default 1.5.
        cooldown_ticks (int): Minimum ticks between signals. Default 10.
        max_history (int): Max ticks to keep in memory. Default 300.
    """

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.bb_period = config.get("bb_period", 20)
        self.bb_std_dev = config.get("bb_std_dev", 2.0)
        self.rsi_period = config.get("rsi_period", 14)
        self.rsi_oversold = config.get("rsi_oversold", 35)
        self.rsi_overbought = config.get("rsi_overbought", 65)
        self.volume_spike_multiplier = config.get("volume_spike_multiplier", 1.5)
        self.squeeze_threshold = config.get("squeeze_threshold", 1.5)
        self.cooldown_ticks = config.get("cooldown_ticks", 10)
        self.max_history = config.get("max_history", 300)

        # Per-symbol state
        self._price_history: dict[str, list[float]] = {}
        self._volume_history: dict[str, list[float]] = {}
        self._ticks_since_signal: dict[str, int] = {}

    async def on_tick(self, tick: UnifiedMarketEvent) -> Optional[dict[str, Any]]:
        if not tick.price or tick.price <= 0:
            return None

        symbol = tick.symbol
        price = float(tick.price)
        volume = float(tick.volume) if tick.volume else 0.0

        # Initialize
        if symbol not in self._price_history:
            self._price_history[symbol] = []
            self._volume_history[symbol] = []
            self._ticks_since_signal[symbol] = self.cooldown_ticks

        prices = self._price_history[symbol]
        volumes = self._volume_history[symbol]
        prices.append(price)
        volumes.append(volume)

        # Trim
        if len(prices) > self.max_history:
            prices.pop(0)
        if len(volumes) > self.max_history:
            volumes.pop(0)

        # Cooldown
        self._ticks_since_signal[symbol] += 1
        if self._ticks_since_signal[symbol] < self.cooldown_ticks:
            return None

        # Need enough data
        min_required = max(self.bb_period, self.rsi_period + 1)
        if len(prices) < min_required:
            return None

        try:
            return self._evaluate_signals(symbol, prices, volumes, price)
        except Exception as e:
            logger.error("Error in EnhancedMeanReversion for %s: %s", symbol, e)
            return None

    def _evaluate_signals(
        self,
        symbol: str,
        prices: list[float],
        volumes: list[float],
        current_price: float,
    ) -> Optional[dict[str, Any]]:
        """Evaluate Bollinger + RSI + Volume for mean reversion signals."""
        metrics: dict[str, Any] = {}

        # 1. Bollinger Bands
        bb = TechnicalIndicators.calculate_bollinger_bands(
            prices, period=self.bb_period, std_dev=self.bb_std_dev
        )
        if bb is None:
            return None

        metrics["bb_upper"] = round(bb.upper, 2)
        metrics["bb_lower"] = round(bb.lower, 2)
        metrics["bb_middle"] = round(bb.middle, 2)
        metrics["bb_width"] = round(bb.width, 2)
        metrics["bb_percent_b"] = round(bb.percent_b, 4)

        # Squeeze detection: narrow bands = breakout imminent, avoid entry
        if bb.width < self.squeeze_threshold:
            return None  # No mean reversion during squeeze

        # 2. RSI
        rsi = TechnicalIndicators.calculate_rsi(prices, self.rsi_period)
        if rsi is None:
            return None

        metrics["rsi"] = round(rsi, 2)

        # 3. Volume analysis
        volume_confirmed = False
        if len(volumes) >= self.bb_period:
            avg_volume = sum(volumes[-self.bb_period:]) / self.bb_period
            if avg_volume > 0:
                volume_ratio = volumes[-1] / avg_volume
                metrics["volume_ratio"] = round(volume_ratio, 2)
                volume_confirmed = volume_ratio >= self.volume_spike_multiplier

        # Signal logic: price at band extreme + RSI confirms + volume
        direction = None
        signal_strength = 0

        # BULLISH: Price below lower band + RSI oversold
        if current_price <= bb.lower:
            signal_strength += 1  # At lower band
            if rsi < self.rsi_oversold:
                signal_strength += 1  # RSI confirms oversold
            if volume_confirmed:
                signal_strength += 1  # Volume spike at extreme
            if signal_strength >= 2:
                direction = "BULLISH"

        # BEARISH: Price above upper band + RSI overbought
        elif current_price >= bb.upper:
            signal_strength += 1  # At upper band
            if rsi > self.rsi_overbought:
                signal_strength += 1  # RSI confirms overbought
            if volume_confirmed:
                signal_strength += 1  # Volume spike at extreme
            if signal_strength >= 2:
                direction = "BEARISH"

        if direction:
            self._ticks_since_signal[symbol] = 0  # Reset cooldown

            confidence = min(signal_strength / 3.0, 1.0)

            return {
                "signal": "%s_MEAN_REVERSION" % direction,
                "symbol": symbol,
                "price": current_price,
                "confidence": round(confidence, 2),
                "metrics": metrics,
                "strategy": "enhanced_mean_reversion",
                "metadata": {
                    "signal_strength": signal_strength,
                    "squeeze_detected": False,
                    "bb_period": self.bb_period,
                    "rsi_period": self.rsi_period,
                },
            }

        return None
