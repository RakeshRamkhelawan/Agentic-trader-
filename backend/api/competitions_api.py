"""
Competitions REST API - Trading competitions, tournaments, and leaderboards.

Endpoints:
- GET /api/v1/competitions/tournaments - List tournaments
- GET /api/v1/competitions/league-info - Get league information
- POST /api/v1/competitions/enter - Enter a tournament
- GET /api/v1/competitions/leaderboard - Get leaderboard
- GET /api/v1/competitions/badges/{competitor_id} - Get user badges
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.competitions.leaderboard import LeaderboardService
from backend.competitions.league_system import LeagueSystem, LeagueTier
from backend.competitions.rewards import RewardsSystem
from backend.competitions.strategy_share import StrategySharingService
from backend.competitions.tournament_engine import TournamentEngine

router = APIRouter()

# Global instances (lazy initialization)
_league_system: LeagueSystem | None = None
_tournament_engine: TournamentEngine | None = None
_leaderboard_service: LeaderboardService | None = None
_strategy_service: StrategySharingService | None = None
_rewards_system: RewardsSystem | None = None


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


def _get_rewards_system() -> RewardsSystem:
    """Get or create rewards system instance."""
    global _rewards_system
    if _rewards_system is None:
        _rewards_system = RewardsSystem()
    return _rewards_system


# ============================================================================
# Request/Response Schemas
# ============================================================================


class EnterTournamentRequest(BaseModel):
    """Request to enter a tournament."""

    competitor_id: str
    tournament_id: str


class TournamentResponse(BaseModel):
    """Tournament response."""

    id: str
    name: str
    description: str
    type: str
    participants: int
    max_participants: int
    ends_at: str
    time_remaining: str
    entry_fee: float
    prize_pool: float


class LeagueInfoResponse(BaseModel):
    """League information response."""

    tier: str
    name: str
    min_points: int
    max_points: int
    current_members: int
    max_members: int


class LeaderboardEntryResponse(BaseModel):
    """Leaderboard entry."""

    rank: int
    competitor_id: str
    name: str
    tier: str
    points: int
    win_rate: float
    total_pnl: float


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/tournaments")
async def get_tournaments(
    status: str = Query(default="active", description="Tournament status: active or upcoming"),
) -> dict[str, Any]:
    """
    Get available tournaments.

    Args:
        status: Filter by status - "active" or "upcoming"

    Returns:
        List of tournaments with count
    """
    try:
        tournament = _get_tournament_engine()

        if status == "active":
            tournaments = tournament.get_active_tournaments()
        elif status == "upcoming":
            tournaments = tournament.get_upcoming_tournaments()
        else:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

        # Format tournaments for frontend
        formatted_tournaments = []
        for t in tournaments:
            formatted_tournaments.append(
                {
                    "id": t.get("id", ""),
                    "name": t.get("name", ""),
                    "description": t.get("description", ""),
                    "type": t.get("type", "standard"),
                    "participants": t.get("participants", 0),
                    "max_participants": t.get("max_participants", 100),
                    "ends_at": t.get("ends_at", ""),
                    "time_remaining": t.get("time_remaining", ""),
                    "entry_fee": t.get("entry_fee", 0),
                    "prize_pool": t.get("prize_pool", 0),
                }
            )

        return {
            "tournaments": formatted_tournaments,
            "count": len(formatted_tournaments),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/league-info")
async def get_league_info() -> dict[str, Any]:
    """
    Get information about all leagues.

    Returns:
        Dictionary of league tier -> league info
    """
    try:
        league = _get_league_system()
        info = league.get_all_leagues_info()

        # Format for frontend
        formatted_info = {}
        for tier, data in info.items():
            formatted_info[tier] = {
                "tier": tier,
                "name": data.get("name", tier.capitalize()),
                "min_points": data.get("min_points", 0),
                "max_points": data.get("max_points", 0),
                "current_members": data.get("current_members", 0),
                "max_members": data.get("max_members", 1000),
            }

        return formatted_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enter")
async def enter_tournament(request: EnterTournamentRequest) -> dict[str, Any]:
    """
    Enter a competitor into a tournament.

    Args:
        request: Contains competitor_id and tournament_id

    Returns:
        Success status and message
    """
    try:
        league = _get_league_system()
        tournament = _get_tournament_engine()

        competitor = league.get_competitor(request.competitor_id)
        if not competitor:
            raise HTTPException(status_code=404, detail="Competitor not found")

        result = tournament.enter_tournament(request.tournament_id, competitor)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leaderboard")
async def get_leaderboard(
    tier: str | None = Query(default=None, description="Filter by league tier"),
    limit: int = Query(default=20, ge=1, le=100, description="Number of entries to return"),
) -> dict[str, Any]:
    """
    Get competition leaderboard.

    Args:
        tier: Optional league tier filter (bronze, silver, gold, platinum, diamond)
        limit: Maximum number of entries

    Returns:
        Leaderboard entries and total count
    """
    try:
        leaderboard = _get_leaderboard_service()

        if tier:
            try:
                tier_enum = LeagueTier(tier.lower())
                result = leaderboard.get_league_leaderboard(tier_enum, limit)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid tier: {tier}")
        else:
            result = leaderboard.get_global_leaderboard(limit)

        # Format entries
        entries = []
        for entry in result.get("entries", []):
            entries.append(
                {
                    "rank": entry.get("rank", 0),
                    "competitor_id": entry.get("competitor_id", ""),
                    "name": entry.get("name", ""),
                    "tier": entry.get("tier", ""),
                    "points": entry.get("points", 0),
                    "win_rate": entry.get("win_rate", 0.0),
                    "total_pnl": entry.get("total_pnl", 0.0),
                }
            )

        return {
            "entries": entries,
            "total": result.get("total", len(entries)),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/badges/{competitor_id}")
async def get_badges(competitor_id: str) -> dict[str, Any]:
    """
    Get badges earned by a competitor.

    Args:
        competitor_id: ID of the competitor

    Returns:
        List of badges and total count
    """
    try:
        rewards = _get_rewards_system()
        badges = rewards.get_competitor_badges(competitor_id)

        return {
            "competitor_id": competitor_id,
            "badges": badges,
            "total_badges": len(badges),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available-badges")
async def get_available_badges() -> dict[str, Any]:
    """
    Get all available badges that can be earned.

    Returns:
        List of all badge definitions
    """
    try:
        rewards = _get_rewards_system()
        badges = rewards.get_all_badges()

        return {
            "badges": badges,
            "total": len(badges),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
