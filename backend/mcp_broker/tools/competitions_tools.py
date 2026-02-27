"""Competition tools for MCP broker."""

from typing import Any, Optional
from datetime import datetime

from backend.competitions.league_system import LeagueSystem, LeagueTier
from backend.competitions.tournament_engine import TournamentEngine
from backend.competitions.leaderboard import LeaderboardService
from backend.competitions.strategy_share import StrategySharingService
from backend.competitions.rewards import RewardsSystem, BadgeType, BadgeRarity


# Global instances
_league_system: Optional[LeagueSystem] = None
_tournament_engine: Optional[TournamentEngine] = None
_leaderboard_service: Optional[LeaderboardService] = None
_strategy_service: Optional[StrategySharingService] = None
_rewards_system: Optional[RewardsSystem] = None


def _get_league_system() -> LeagueSystem:
    """Get or create league system instance."""
    global _league_system
    if _league_system is None:
        _league_system = LeagueSystem()
    return _league_system


def _get_tournament_engine() -> TournamentEngine:
    """Get or create tournament engine instance."""
    global _tournament_engine
    if _tournament_engine is None:
        _tournament_engine = TournamentEngine()
    return _tournament_engine


def _get_leaderboard_service() -> LeaderboardService:
    """Get or create leaderboard service instance."""
    global _leaderboard_service
    if _leaderboard_service is None:
        _leaderboard_service = LeaderboardService()
    return _leaderboard_service


def _get_strategy_service() -> StrategySharingService:
    """Get or create strategy service instance."""
    global _strategy_service
    if _strategy_service is None:
        _strategy_service = StrategySharingService()
    return _strategy_service


def _get_rewards_system() -> RewardsSystem:
    """Get or create rewards system instance."""
    global _rewards_system
    if _rewards_system is None:
        _rewards_system = RewardsSystem()
    return _rewards_system


async def competitions_register_competitor(
    name: str,
    email: str,
    ctx: Any,
) -> dict[str, Any]:
    """Register a new competitor in the league system."""
    try:
        league = _get_league_system()
        competitor = league.register_competitor(name, email)
        
        # Also register with leaderboard
        leaderboard = _get_leaderboard_service()
        leaderboard.register_competitor(competitor)
        
        return {
            "success": True,
            "competitor_id": competitor.id,
            "name": competitor.name,
            "tier": competitor.tier.value,
            "points": competitor.points,
            "message": f"Welcome to {competitor.tier.value.upper()} League!",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


async def competitions_get_leaderboard(
    tier: Optional[str] = None,
    limit: int = 20,
    ctx: Any = None,
) -> dict[str, Any]:
    """Get competition leaderboard."""
    try:
        leaderboard = _get_leaderboard_service()
        
        if tier:
            try:
                tier_enum = LeagueTier(tier.lower())
                return leaderboard.get_league_leaderboard(tier_enum, limit)
            except ValueError:
                return {"error": f"Invalid tier: {tier}"}
        else:
            return leaderboard.get_global_leaderboard(limit)
    except Exception as e:
        return {"error": str(e)}


async def competitions_enter_tournament(
    competitor_id: str,
    tournament_id: str,
    ctx: Any = None,
) -> dict[str, Any]:
    """Enter a competitor into a tournament."""
    try:
        league = _get_league_system()
        tournament = _get_tournament_engine()
        
        competitor = league.get_competitor(competitor_id)
        if not competitor:
            return {"success": False, "error": "Competitor not found"}
        
        result = tournament.enter_tournament(tournament_id, competitor)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


async def competitions_get_tournaments(
    status: str = "active",
    ctx: Any = None,
) -> dict[str, Any]:
    """Get available tournaments."""
    try:
        tournament = _get_tournament_engine()
        
        if status == "active":
            tournaments = tournament.get_active_tournaments()
        elif status == "upcoming":
            tournaments = tournament.get_upcoming_tournaments()
        else:
            return {"error": f"Invalid status: {status}"}
        
        return {
            "tournaments": tournaments,
            "count": len(tournaments),
        }
    except Exception as e:
        return {"error": str(e)}


async def competitions_share_strategy(
    competitor_id: str,
    name: str,
    description: str,
    code: str,
    language: str = "python",
    visibility: str = "public",
    tags: Optional[list] = None,
    ctx: Any = None,
) -> dict[str, Any]:
    """Share a trading strategy with the community."""
    try:
        league = _get_league_system()
        strategy = _get_strategy_service()
        
        competitor = league.get_competitor(competitor_id)
        if not competitor:
            return {"success": False, "error": "Competitor not found"}
        
        from backend.competitions.models.strategy import (
            StrategyLanguage, StrategyVisibility
        )
        
        # Parse enums
        try:
            lang_enum = StrategyLanguage(language.lower())
        except ValueError:
            lang_enum = StrategyLanguage.PYTHON
        
        try:
            vis_enum = StrategyVisibility(visibility.lower())
        except ValueError:
            vis_enum = StrategyVisibility.PUBLIC
        
        result = strategy.share_strategy(
            author=competitor,
            name=name,
            description=description,
            code=code,
            language=lang_enum,
            visibility=vis_enum,
            tags=tags or [],
        )
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


async def competitions_search_strategies(
    query: Optional[str] = None,
    tags: Optional[list] = None,
    sort_by: str = "score",
    limit: int = 20,
    ctx: Any = None,
) -> dict[str, Any]:
    """Search for shared strategies."""
    try:
        strategy = _get_strategy_service()
        
        result = strategy.search_strategies(
            query=query,
            tags=tags,
            sort_by=sort_by,
            limit=limit,
        )
        return result
    except Exception as e:
        return {"error": str(e)}


async def competitions_get_league_info(
    ctx: Any = None,
) -> dict[str, Any]:
    """Get information about all leagues."""
    try:
        league = _get_league_system()
        return league.get_all_leagues_info()
    except Exception as e:
        return {"error": str(e)}


async def competitions_get_badges(
    competitor_id: str,
    ctx: Any = None,
) -> dict[str, Any]:
    """Get badges earned by a competitor."""
    try:
        rewards = _get_rewards_system()
        badges = rewards.get_competitor_badges(competitor_id)
        return {
            "competitor_id": competitor_id,
            "badges": badges,
            "total_badges": len(badges),
        }
    except Exception as e:
        return {"error": str(e)}


async def competitions_get_available_badges(
    ctx: Any = None,
) -> dict[str, Any]:
    """Get all available badges that can be earned."""
    try:
        rewards = _get_rewards_system()
        badges = rewards.get_all_badges()
        return {
            "badges": badges,
            "total": len(badges),
        }
    except Exception as e:
        return {"error": str(e)}
