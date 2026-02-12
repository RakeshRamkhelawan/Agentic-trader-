from enum import Enum

class MarketRegime(str, Enum):
    BULL = "BULL"
    BEAR = "BEAR"
    SIDEWAYS = "SIDEWAYS"
    VOLATILE = "VOLATILE"

class RegimeDetector:
    """
    Classifies the current market state to adjust strategy parameters.
    """
    def detect(self, price: float, sma_50: float, volatility: float) -> MarketRegime:
        # High Volatility Override
        if volatility > 0.05: # >5% vol is extreme
            return MarketRegime.VOLATILE
            
        if price > sma_50:
            return MarketRegime.BULL
        elif price < sma_50:
            return MarketRegime.BEAR
        else:
            return MarketRegime.SIDEWAYS
