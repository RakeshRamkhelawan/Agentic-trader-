"""
Competitions Module for Agentic Trader Platform.

Provides gamification features:
- League system (Bronze/Silver/Gold/Diamond)
- Weekly tournaments
- Leaderboards
- Strategy sharing
"""

from .leaderboard import LeaderboardService
from .league_system import LeagueSystem, LeagueTier
from .models.tournament import TournamentStatus
from .rewards import BadgeRarity, BadgeType, RewardsSystem
from .strategy_share import StrategySharingService
from .tournament_engine import TournamentEngine

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
