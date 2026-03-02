"""Competitor model for trading competitions."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class LeagueTier(Enum):
    """League tiers from beginner to expert."""

    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    DIAMOND = "diamond"


@dataclass
class CompetitorStats:
    """Statistics for a competitor."""

    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    best_trade_pnl: float = 0.0
    worst_trade_pnl: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    avg_trade_pnl: float = 0.0
    competitions_entered: int = 0
    competitions_won: int = 0
    strategies_shared: int = 0
    strategies_forked: int = 0
    followers: int = 0
    reputation_score: float = 0.0


@dataclass
class Competitor:
    """A competitor in the trading competitions."""

    id: str
    name: str
    email: str
    tier: LeagueTier = LeagueTier.BRONZE
    points: int = 0
    rank: int = 0
    stats: CompetitorStats = field(default_factory=CompetitorStats)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_active: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True

    def calculate_win_rate(self) -> float:
        """Calculate win rate percentage."""
        if self.stats.total_trades == 0:
            return 0.0
        return (self.stats.winning_trades / self.stats.total_trades) * 100

    def add_points(self, points: int) -> None:
        """Add points to competitor."""
        self.points += points
        self.last_active = datetime.utcnow()

    def update_stats(self, pnl: float, is_win: bool) -> None:
        """Update statistics after a trade."""
        self.stats.total_trades += 1
        self.stats.total_pnl += pnl

        if is_win:
            self.stats.winning_trades += 1
            if pnl > self.stats.best_trade_pnl:
                self.stats.best_trade_pnl = pnl
        else:
            self.stats.losing_trades += 1
            if pnl < self.stats.worst_trade_pnl:
                self.stats.worst_trade_pnl = pnl

        self.stats.win_rate = self.calculate_win_rate()
        self.stats.avg_trade_pnl = self.stats.total_pnl / self.stats.total_trades

        # Update reputation score
        self.stats.reputation_score = (
            self.stats.total_pnl * 0.4
            + self.stats.win_rate * 100 * 0.3
            + self.stats.sharpe_ratio * 10 * 0.2
            + self.stats.followers * 10 * 0.1
        )

        self.last_active = datetime.utcnow()
