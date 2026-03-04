"""
Trading Strategies Package.

Contains both basic and enhanced multi-indicator trading strategies.
"""

from backend.strategies.breakout import BreakoutStrategy
from backend.strategies.enhanced_mean_reversion import EnhancedMeanReversionStrategy
from backend.strategies.enhanced_momentum import EnhancedMomentumStrategy
from backend.strategies.mean_reversion import MeanReversionStrategy
from backend.strategies.momentum import MomentumStrategy
from backend.strategies.trend_following import TrendFollowingStrategy

__all__ = [
    "MomentumStrategy",
    "MeanReversionStrategy",
    "BreakoutStrategy",
    "TrendFollowingStrategy",
    "EnhancedMomentumStrategy",
    "EnhancedMeanReversionStrategy",
]
