from typing import Optional, Dict, List, Any
import pandas as pd
import logging
from backend.strategies.base import BaseStrategy
from backend.market_data.models import UnifiedMarketEvent

logger = logging.getLogger(__name__)


class MomentumStrategy(BaseStrategy):
    """
    Momentum Strategy based on RSI (Relative Strength Index).

    Config:
        rsi_period (int): Period for RSI calculation. Default 14.
        overbought (int): Threshold for overbought (sell signal). Default 70.
        oversold (int): Threshold for oversold (buy signal). Default 30.
        max_history (int): Max ticks to keep in memory. Default 200.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.rsi_period = config.get("rsi_period", 14)
        self.overbought = config.get("overbought", 70)
        self.oversold = config.get("oversold", 30)
        self.max_history = config.get("max_history", 200)

        # In-memory state: {symbol: [price1, price2, ...]}
        self._price_history: Dict[str, List[float]] = {}
        # To avoid spamming signals, we can track last signal state or cool-down
        # For MVP, we'll just emit on every tick in the zone (Orchestrator can filter)

    async def on_tick(self, tick: UnifiedMarketEvent) -> Optional[Dict[str, Any]]:
        if not tick.price or tick.price <= 0:
            return None

        symbol = tick.symbol
        price = float(tick.price)

        # Initialize history
        if symbol not in self._price_history:
            self._price_history[symbol] = []

        history = self._price_history[symbol]
        history.append(price)

        # Trim history
        if len(history) > self.max_history:
            history.pop(0)

        # Need enough data for RSI
        # RSI needs index + period. Ideally > period + 1
        if len(history) <= self.rsi_period:
            return None

        # Calculate RSI
        try:
            rsi = self._calculate_rsi(history)
            if rsi is None:
                return None

            # Check thresholds
            direction = None
            if rsi < self.oversold:
                direction = "BULLISH"  # Oversold -> Buy
            elif rsi > self.overbought:
                direction = "BEARISH"  # Overbought -> Sell

            if direction:
                return {
                    "signal": f"{direction}_RSI",
                    "symbol": symbol,
                    "price": price,
                    "metrics": {"rsi": round(rsi, 2)},
                    "strategy": "momentum_rsi",
                    "metadata": {
                        "period": self.rsi_period,
                        "threshold": (
                            self.oversold if direction == "BULLISH" else self.overbought
                        ),
                    },
                }

        except Exception as e:
            logger.error(f"Error calculating RSI for {symbol}: {e}")
            return None

        return None

    def _calculate_rsi(self, prices: List[float]) -> Optional[float]:
        """
        Calculate RSI using pandas.
        """
        if len(prices) < self.rsi_period + 1:
            return None

        series = pd.Series(prices)
        delta = series.diff()

        # Gain and Loss
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        # Calculate RS using Wilder's Smoothing (standard RSI) or Simple MA
        # Here we use Simple MA (Rolling) for speed/simplicity effectively "RSI-SMA"
        # Standard RSI usually uses EWMA (com=period-1)

        avg_gain = gain.rolling(
            window=self.rsi_period, min_periods=self.rsi_period
        ).mean()
        avg_loss = loss.rolling(
            window=self.rsi_period, min_periods=self.rsi_period
        ).mean()

        # Get last values
        curr_gain = avg_gain.iloc[-1]
        curr_loss = avg_loss.iloc[-1]

        if pd.isna(curr_gain) or pd.isna(curr_loss):
            return None

        if curr_loss == 0:
            return 100.0 if curr_gain > 0 else 50.0  # Edge case

        rs = curr_gain / curr_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi
