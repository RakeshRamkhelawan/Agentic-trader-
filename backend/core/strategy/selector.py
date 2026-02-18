from typing import Dict

from backend.core.risk.guna_sizing import GunaType
from backend.core.schemas.ooda_types import MarketRegime
from backend.core.strategy.implementations import (DefensiveStrategy,
                                                   MeanReversionStrategy,
                                                   TrendFollowingStrategy)
from backend.core.strategy.interface import TradingStrategy


class StrategySelector:
    """
    Selects the optimal strategy based on Market Regime and Guna Dominance.
    """

    def __init__(self):
        self.strategies: Dict[str, TradingStrategy] = {
            "trend": TrendFollowingStrategy(),
            "mean_reversion": MeanReversionStrategy(),
            "defensive": DefensiveStrategy(),
        }

    def get_strategy(self, regime: str, guna: str) -> TradingStrategy:
        """
        Returns the appropriate strategy instance.
        """
        # 1. Defensive Overrides
        # If High Volatility OR Tamas (Inertia/Darkness) -> Defensive
        if regime == MarketRegime.VOLATILE.value or guna == GunaType.TAMAS.value:
            return self.strategies["defensive"]

        # 2. Bull/Bear -> Trend Following
        if regime in [MarketRegime.BULL.value, MarketRegime.BEAR.value]:
            return self.strategies["trend"]

        # 3. Sideways -> Mean Reversion
        if regime == MarketRegime.SIDEWAYS.value:
            return self.strategies["mean_reversion"]

        # Default fallback
        return self.strategies["defensive"]
