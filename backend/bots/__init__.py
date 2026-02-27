"""
AI Trading Bots for solo practice competitions.

Provides algorithmic competitors with different strategies:
- TrendFollowerBot: Follows moving average trends
- MeanReversionBot: Trades mean reversion
- MomentumBot: Rides momentum waves
- RandomBot: Random entries for baseline
"""

from .base_bot import BaseTradingBot, BotConfig, BotDifficulty, BotPersonality, TradeDecision
from .trend_bot import TrendFollowerBot
from .mean_reversion_bot import MeanReversionBot
from .momentum_bot import MomentumBot
from .random_bot import RandomBot
from .bot_manager import BotManager

__all__ = [
    "BaseTradingBot",
    "BotConfig",
    "BotDifficulty",
    "BotPersonality",
    "TradeDecision",
    "TrendFollowerBot",
    "MeanReversionBot",
    "MomentumBot",
    "RandomBot",
    "BotManager",
]
