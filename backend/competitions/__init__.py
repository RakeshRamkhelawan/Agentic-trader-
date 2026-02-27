"""
Competitions Module for Agentic Trader Platform.

Provides gamification features:
- League system (Bronze/Silver/Gold/Diamond)
- Weekly tournaments
- Leaderboards
- Strategy sharing
"""

from .league_system import LeagueSystem, LeagueTier
from .tournament_engine import TournamentEngine
from .models.tournament import TournamentStatus
from .leaderboard import LeaderboardService
from .strategy_share import StrategySharingService
from .rewards import RewardsSystem, BadgeType, BadgeRarity

__all__ = [
    "LeagueSystem",
    "LeagueTier",
    "TournamentEngine",
    "TournamentStatus",
    "LeaderboardService",
    "StrategySharingService",
    "RewardsSystem",
    "BadgeType",
    "BadgeRarity",
]
