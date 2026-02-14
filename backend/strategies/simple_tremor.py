from typing import Any, Dict, List, Optional

from backend.market_data.models import UnifiedMarketEvent
from backend.strategies.base import BaseStrategy


class SimpleTremorStrategy(BaseStrategy):
    """
    MVP Strategy: Simple Mean Reversion based on rolling window deviation.

    Config:
        window_size (int): Number of ticks to keep for average. Default 5.
        deviation_threshold (float): Percentage deviation to trigger signal. Default 0.02 (2%).
        max_history (int): Max ticks to keep in memory per symbol. Default 100.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.window_size = config.get("window_size", 5)
        self.deviation_threshold = config.get("deviation_threshold", 0.02)
        self.max_history = config.get("max_history", 100)

        # In-memory state: {symbol: [price1, price2, ...]}
        self._price_history: Dict[str, List[float]] = {}

    async def on_tick(self, tick: UnifiedMarketEvent) -> Optional[Dict[str, Any]]:
        if not tick.price or tick.price <= 0:
            return None

        symbol = tick.symbol
        price = float(tick.price)

        # Initialize history for symbol if needed
        if symbol not in self._price_history:
            self._price_history[symbol] = []

        history = self._price_history[symbol]
        history.append(price)

        # Trim history
        if len(history) > self.max_history:
            history.pop(0)

        # Check signal condition
        if len(history) >= self.window_size:
            # Calculate SMA of last N items
            # Note: We take the last window_size items
            recent_prices = history[-self.window_size :]
            avg = sum(recent_prices) / len(recent_prices)

            if avg > 0:
                deviation = (price - avg) / avg

                direction = None
                if deviation > self.deviation_threshold:
                    direction = "BULLISH"
                elif deviation < -self.deviation_threshold:
                    direction = "BEARISH"

                if direction:
                    return {
                        "signal": f"{direction}_MOMENTUM",
                        "symbol": symbol,
                        "price": price,
                        "deviation": round(deviation, 4),
                        "strategy": "simple_tremor",
                        "metadata": {
                            "avg": round(avg, 2),
                            "threshold": self.deviation_threshold,
                        },
                    }

        return None
