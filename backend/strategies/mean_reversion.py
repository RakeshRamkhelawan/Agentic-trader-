
from typing import Optional, Dict, List, Any
import pandas as pd
import logging
from backend.strategies.base import BaseStrategy
from backend.market_data.models import UnifiedMarketEvent

logger = logging.getLogger(__name__)

class MeanReversionStrategy(BaseStrategy):
    """
    Mean Reversion Strategy based on Bollinger Bands.
    
    Config:
        window (int): Period for SMA and StdDev. Default 20.
        std_dev (float): Number of standard deviations for bands. Default 2.0.
        max_history (int): Max ticks to keep in memory. Default 200.
    """
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.window = config.get("window", 20)
        self.std_dev_multiplier = config.get("std_dev", 2.0)
        self.max_history = config.get("max_history", 200)
        
        self._price_history: Dict[str, List[float]] = {}
        
    async def on_tick(self, tick: UnifiedMarketEvent) -> Optional[Dict[str, Any]]:
        if not tick.price or tick.price <= 0:
            return None
            
        symbol = tick.symbol
        price = float(tick.price)
        
        if symbol not in self._price_history:
            self._price_history[symbol] = []
            
        history = self._price_history[symbol]
        history.append(price)
        
        if len(history) > self.max_history:
            history.pop(0)
            
        # Need enough data
        if len(history) < self.window:
            return None
            
        try:
            # Pandas calculation
            series = pd.Series(history)
            rolling = series.rolling(window=self.window)
            sma = rolling.mean().iloc[-1]
            std = rolling.std().iloc[-1]
            
            if pd.isna(sma) or pd.isna(std):
                return None
                
            upper_band = sma + (std * self.std_dev_multiplier)
            lower_band = sma - (std * self.std_dev_multiplier)
            
            direction = None
            if price < lower_band:
                direction = "BULLISH" # Price below lower band -> Oversold -> Buy
            elif price > upper_band:
                direction = "BEARISH" # Price above upper band -> Overbought -> Sell
                
            if direction:
                return {
                    "signal": f"{direction}_BOLLINGER",
                    "symbol": symbol,
                    "price": price,
                    "metrics": {
                        "sma": round(sma, 2),
                        "upper": round(upper_band, 2),
                        "lower": round(lower_band, 2)
                    },
                    "strategy": "mean_reversion_bb",
                    "metadata": {
                        "window": self.window,
                        "std_dev": self.std_dev_multiplier
                    }
                }
                
        except Exception as e:
            logger.error(f"Error calculating Bollinger Bands for {symbol}: {e}")
            return None
            
        return None
