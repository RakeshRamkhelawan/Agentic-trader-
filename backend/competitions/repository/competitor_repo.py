"""Competitor repository for database operations."""

from datetime import datetime
from typing import Any

from backend.competitions.models.competitor import Competitor, CompetitorStats, LeagueTier


class CompetitorRepository:
    """
    Repository for competitor data persistence.

    Abstracts database operations for competitor CRUD.
    Can be implemented with PostgreSQL, Redis, or other backends.
    """

    def __init__(self):
        # In-memory storage for now - replace with actual DB
        self._competitors: dict[str, Competitor] = {}
        self._email_index: dict[str, str] = {}  # email -> id

    async def create(self, competitor: Competitor) -> Competitor:
        """Create new competitor."""
        self._competitors[competitor.id] = competitor
        self._email_index[competitor.email] = competitor.id
        return competitor

    async def get_by_id(self, competitor_id: str) -> Competitor | None:
        """Get competitor by ID."""
        return self._competitors.get(competitor_id)

    async def get_by_email(self, email: str) -> Competitor | None:
        """Get competitor by email."""
        competitor_id = self._email_index.get(email)
        if competitor_id:
            return self._competitors.get(competitor_id)
        return None

    async def update(self, competitor: Competitor) -> Competitor:
        """Update competitor."""
        competitor.last_active = datetime.utcnow()
        self._competitors[competitor.id] = competitor
        return competitor

    async def delete(self, competitor_id: str) -> bool:
        """Delete competitor."""
        competitor = self._competitors.get(competitor_id)
        if competitor:
            del self._competitors[competitor_id]
            if competitor.email in self._email_index:
                del self._email_index[competitor.email]
            return True
        return False

    async def get_all(self, limit: int = 100, offset: int = 0) -> list[Competitor]:
        """Get all competitors with pagination."""
        competitors = list(self._competitors.values())
        return competitors[offset : offset + limit]

    async def get_by_tier(self, tier: LeagueTier) -> list[Competitor]:
        """Get competitors by tier."""
        return [c for c in self._competitors.values() if c.tier == tier]

    async def get_leaderboard(self, limit: int = 50) -> list[Competitor]:
        """Get top competitors by points."""
        competitors = sorted(
            self._competitors.values(),
            key=lambda c: c.points,
            reverse=True,
        )
        return competitors[:limit]

    async def update_stats(self, competitor_id: str, stats: CompetitorStats) -> bool:
        """Update competitor stats."""
        competitor = self._competitors.get(competitor_id)
        if competitor:
            competitor.stats = stats
            competitor.last_active = datetime.utcnow()
            return True
        return False

    async def update_points(self, competitor_id: str, points_delta: int) -> bool:
        """Update competitor points."""
        competitor = self._competitors.get(competitor_id)
        if competitor:
            competitor.points += points_delta
            competitor.last_active = datetime.utcnow()
            return True
        return False

    async def update_tier(self, competitor_id: str, tier: LeagueTier) -> bool:
        """Update competitor tier."""
        competitor = self._competitors.get(competitor_id)
        if competitor:
            competitor.tier = tier
            competitor.last_active = datetime.utcnow()
            return True
        return False

    async def get_count(self) -> int:
        """Get total competitor count."""
        return len(self._competitors)

    async def get_count_by_tier(self) -> dict[str, int]:
        """Get competitor counts per tier."""
        counts = {}
        for tier in LeagueTier:
            counts[tier.value] = len([c for c in self._competitors.values() if c.tier == tier])
        return counts

    # SQL Schema for PostgreSQL implementation
    @staticmethod
    def get_create_table_sql() -> str:
        """Get SQL to create competitors table."""
        return """
        CREATE TABLE IF NOT EXISTS competitors (
            id UUID PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            tier VARCHAR(20) DEFAULT 'bronze',
            points INTEGER DEFAULT 0,
            rank INTEGER DEFAULT 0,
            stats JSONB DEFAULT '{}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            last_active TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            is_active BOOLEAN DEFAULT TRUE
        );

        CREATE INDEX IF NOT EXISTS idx_competitors_points ON competitors(points DESC);
        CREATE INDEX IF NOT EXISTS idx_competitors_tier ON competitors(tier);
        CREATE INDEX IF NOT EXISTS idx_competitors_email ON competitors(email);
        """

    @staticmethod
    def competitor_to_dict(competitor: Competitor) -> dict[str, Any]:
        """Convert competitor to dictionary for DB storage."""
        return {
            "id": competitor.id,
            "name": competitor.name,
            "email": competitor.email,
            "tier": competitor.tier.value,
            "points": competitor.points,
            "rank": competitor.rank,
            "stats": {
                "total_trades": competitor.stats.total_trades,
                "winning_trades": competitor.stats.winning_trades,
                "losing_trades": competitor.stats.losing_trades,
                "total_pnl": competitor.stats.total_pnl,
                "best_trade_pnl": competitor.stats.best_trade_pnl,
                "worst_trade_pnl": competitor.stats.worst_trade_pnl,
                "sharpe_ratio": competitor.stats.sharpe_ratio,
                "max_drawdown": competitor.stats.max_drawdown,
                "win_rate": competitor.stats.win_rate,
                "competitions_entered": competitor.stats.competitions_entered,
                "competitions_won": competitor.stats.competitions_won,
                "strategies_shared": competitor.stats.strategies_shared,
                "strategies_forked": competitor.stats.strategies_forked,
                "followers": competitor.stats.followers,
                "reputation_score": competitor.stats.reputation_score,
            },
            "created_at": competitor.created_at.isoformat(),
            "last_active": competitor.last_active.isoformat(),
            "is_active": competitor.is_active,
        }

    @staticmethod
    def dict_to_competitor(data: dict[str, Any]) -> Competitor:
        """Convert dictionary to competitor."""
        stats_data = data.get("stats", {})
        stats = CompetitorStats(
            total_trades=stats_data.get("total_trades", 0),
            winning_trades=stats_data.get("winning_trades", 0),
            losing_trades=stats_data.get("losing_trades", 0),
            total_pnl=stats_data.get("total_pnl", 0.0),
            best_trade_pnl=stats_data.get("best_trade_pnl", 0.0),
            worst_trade_pnl=stats_data.get("worst_trade_pnl", 0.0),
            sharpe_ratio=stats_data.get("sharpe_ratio", 0.0),
            max_drawdown=stats_data.get("max_drawdown", 0.0),
            win_rate=stats_data.get("win_rate", 0.0),
            competitions_entered=stats_data.get("competitions_entered", 0),
            competitions_won=stats_data.get("competitions_won", 0),
            strategies_shared=stats_data.get("strategies_shared", 0),
            strategies_forked=stats_data.get("strategies_forked", 0),
            followers=stats_data.get("followers", 0),
            reputation_score=stats_data.get("reputation_score", 0.0),
        )

        return Competitor(
            id=data["id"],
            name=data["name"],
            email=data["email"],
            tier=LeagueTier(data.get("tier", "bronze")),
            points=data.get("points", 0),
            rank=data.get("rank", 0),
            stats=stats,
            created_at=datetime.fromisoformat(data["created_at"]),
            last_active=datetime.fromisoformat(data["last_active"]),
            is_active=data.get("is_active", True),
        )
