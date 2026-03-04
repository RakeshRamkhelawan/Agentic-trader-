"""
Enhanced Momentum Strategy - Multi-indicator composite momentum analysis.

Uses 5 indicators for signal consensus:
1. RSI momentum (oversold/overbought zones)
2. MACD crossover (line crosses signal)
3. ADX trend strength filter (ADX > 25 = strong trend)
4. EMA stack alignment (8 > 21 > 55 = bullish)
5. Volume confirmation (OBV trend)

Only generates signals when >= 3/5 indicators agree.
"""

import logging
import time
from typing import Any, Optional

from backend.core.indicators.technical import TechnicalIndicators
from backend.core.market_data.models import UnifiedMarketEvent
from backend.strategies.base import BaseStrategy

logger = logging.getLogger(__name__)


class EnhancedMomentumStrategy(BaseStrategy):
    """
    Enhanced Momentum Strategy with 5-indicator composite scoring.

    Config:
        rsi_period (int): RSI period. Default 14.
        rsi_overbought (int): RSI overbought threshold. Default 70.
        rsi_oversold (int): RSI oversold threshold. Default 30.
        adx_threshold (float): Minimum ADX for trend confirmation. Default 25.
        min_consensus (int): Minimum agreeing indicators for signal. Default 3.
        cooldown_ticks (int): Minimum ticks between signals. Default 10.
        max_history (int): Max ticks to keep in memory. Default 300.
    """

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.rsi_period = config.get("rsi_period", 14)
        self.rsi_overbought = config.get("rsi_overbought", 70)
        self.rsi_oversold = config.get("rsi_oversold", 30)
        self.adx_threshold = config.get("adx_threshold", 25.0)
        self.min_consensus = config.get("min_consensus", 3)
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

        # Need enough data (at least for MACD: 26+9=35)
        if len(prices) < 35:
            return None

        try:
            return self._evaluate_signals(symbol, prices, volumes, price)
        except Exception as e:
            logger.error("Error in EnhancedMomentum for %s: %s", symbol, e)
            return None

    def _evaluate_signals(
        self,
        symbol: str,
        prices: list[float],
        volumes: list[float],
        current_price: float,
    ) -> Optional[dict[str, Any]]:
        """Evaluate all 5 indicators and generate composite signal."""
        bullish_count = 0
        bearish_count = 0
        metrics: dict[str, Any] = {}

        # 1. RSI
        rsi = TechnicalIndicators.calculate_rsi(prices, self.rsi_period)
        if rsi is not None:
            metrics["rsi"] = round(rsi, 2)
            if rsi < self.rsi_oversold:
                bullish_count += 1  # Oversold = buy
            elif rsi > self.rsi_overbought:
                bearish_count += 1  # Overbought = sell

        # 2. MACD
        macd = TechnicalIndicators.calculate_macd(prices)
        if macd is not None:
            metrics["macd_histogram"] = round(macd.histogram, 4)
            if macd.histogram > 0 and macd.macd_line > macd.signal_line:
                bullish_count += 1
            elif macd.histogram < 0 and macd.macd_line < macd.signal_line:
                bearish_count += 1

        # 3. ADX (trend strength filter)
        # Use close as proxy for high/low since we only have tick data
        highs = [p * 1.002 for p in prices]
        lows = [p * 0.998 for p in prices]
        adx = TechnicalIndicators.calculate_adx(highs, lows, prices, period=14)
        if adx is not None:
            metrics["adx"] = round(adx, 2)
            # ADX acts as a filter: only trade in trending markets
            if adx < self.adx_threshold:
                return None  # No trend, no trade

        # 4. EMA Stack alignment
        ema_stack = TechnicalIndicators.calculate_ema_stack(prices)
        if ema_stack is not None:
            metrics["ema_8"] = round(ema_stack[8], 2)
            metrics["ema_21"] = round(ema_stack[21], 2)
            metrics["ema_55"] = round(ema_stack[55], 2)
            if TechnicalIndicators.is_ema_bullish_aligned(ema_stack):
                bullish_count += 1
            elif TechnicalIndicators.is_ema_bearish_aligned(ema_stack):
                bearish_count += 1

        # 5. Volume (OBV trend)
        obv_ratio = TechnicalIndicators.calculate_obv_ema(prices, volumes, period=20)
        if obv_ratio is not None:
            metrics["obv_ratio"] = round(obv_ratio, 4)
            if obv_ratio > 1.05:  # OBV above its EMA = bullish volume
                bullish_count += 1
            elif obv_ratio < 0.95:  # OBV below its EMA = bearish volume
                bearish_count += 1

        # Consensus check
        direction = None
        if bullish_count >= self.min_consensus:
            direction = "BULLISH"
        elif bearish_count >= self.min_consensus:
            direction = "BEARISH"

        if direction:
            self._ticks_since_signal[symbol] = 0  # Reset cooldown

            confidence = max(bullish_count, bearish_count) / 5.0

            return {
                "signal": "%s_MOMENTUM_COMPOSITE" % direction,
                "symbol": symbol,
                "price": current_price,
                "confidence": round(confidence, 2),
                "metrics": metrics,
                "strategy": "enhanced_momentum",
                "metadata": {
                    "bullish_indicators": bullish_count,
                    "bearish_indicators": bearish_count,
                    "min_consensus": self.min_consensus,
                    "adx_threshold": self.adx_threshold,
                },
            }

        return None
