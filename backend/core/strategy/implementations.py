import time
from typing import Any, Dict

from backend.core.zero_copy_bridge import TradingIntent


class TrendFollowingStrategy:
    """
    Aggressive strategy for BULL/BEAR regimes.
    Follows the trend direction (SMA alignment).
    """

    name = "TrendFollowing"

    async def analyze(
        self, market_data: Dict[str, Any], soul_context: Dict[str, Any]
    ) -> TradingIntent:
        price = market_data.get("price", 0.0)
        metrics = soul_context.get("market_metrics", {})
        sma_50 = metrics.get("sma_50", 0.0)
        sma_200 = metrics.get("sma_200", 0.0)

        # Default Hold
        action = 0
        size = 0.0
        confidence = 0.0

        # Bull Trend
        if price > sma_50 > sma_200:
            action = 1  # BUY
            size = 1.0  # Aggressive
            confidence = 0.8
        # Bear Trend
        elif price < sma_50 < sma_200:
            action = 2  # SELL
            size = 1.0  # Aggressive
            confidence = 0.8

        return TradingIntent(
            action=action,
            size=size,
            confidence=confidence,
            stop_loss=0.0,  # Strategy doesn't set SL/TP, Execution/Risk does
            take_profit=0.0,
            max_hold_ms=60000,  # 1 min
            entry_price=price,
            timestamp_ns=time.time_ns(),
        )


class MeanReversionStrategy:
    """
    Strategy for SIDEWAYS regimes.
    Buys at lower band, Sells at upper band (bollinger-like logic).
    For now, uses simple deviation from SMA 50.
    """

    name = "MeanReversion"

    async def analyze(
        self, market_data: Dict[str, Any], soul_context: Dict[str, Any]
    ) -> TradingIntent:
        price = market_data.get("price", 0.0)
        metrics = soul_context.get("market_metrics", {})
        sma_50 = metrics.get("sma_50", price)

        action = 0
        size = 0.0
        confidence = 0.0

        # Calculate deviation
        if sma_50 == 0:
            sma_50 = price if price > 0 else 1.0
        deviation = (price - sma_50) / sma_50

        # If price is 1% below SMA50 -> Buy (Revert to mean)
        if deviation < -0.01:
            action = 1  # BUY
            size = 0.5  # Moderate
            confidence = 0.6
        # If price is 1% above SMA50 -> Sell
        elif deviation > 0.01:
            action = 2  # SELL
            size = 0.5  # Moderate
            confidence = 0.6

        return TradingIntent(
            action=action,
            size=size,
            confidence=confidence,
            stop_loss=0.0,
            take_profit=0.0,
            max_hold_ms=120000,  # 2 mins (slower)
            entry_price=price,
            timestamp_ns=time.time_ns(),
        )


class DefensiveStrategy:
    """
    Protective strategy for VOLATILE regimes or RAHU KALA.
    Does NOT trade. Exits positions if implementation allowed (currently just Hold).
    """

    name = "Defensive"

    async def analyze(
        self, market_data: Dict[str, Any], soul_context: Dict[str, Any]
    ) -> TradingIntent:
        # Always return HOLD (Action 0)
        # Size 0.0 enforces closure if logic supported it, but here it just means "Do Nothing"
        return TradingIntent(
            action=0,
            size=0.0,
            confidence=0.0,
            stop_loss=0.0,
            take_profit=0.0,
            max_hold_ms=0,
            entry_price=0.0,
            timestamp_ns=time.time_ns(),
        )
