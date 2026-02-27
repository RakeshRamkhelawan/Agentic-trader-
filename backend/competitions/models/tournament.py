"""Tournament model for weekly competitions."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class TournamentStatus(Enum):
    """Tournament status states."""
    PENDING = "pending"
    ACTIVE = "active"
    ENDED = "ended"
    CANCELLED = "cancelled"


class TournamentType(Enum):
    """Types of tournaments."""
    WEEKLY = "weekly"
    SPECIAL = "special"
    SEASONAL = "seasonal"


@dataclass
class PrizeDistribution:
    """Prize distribution for tournament winners."""
    position: int
    points: int
    badge: str | None = None
    title: str | None = None


@dataclass
class TournamentEntry:
    """A competitor's entry in a tournament."""
    competitor_id: str
    tournament_id: str
    starting_balance: float = 10000.0
    current_balance: float = 10000.0
    pnl: float = 0.0
    pnl_percentage: float = 0.0
    trades_count: int = 0
    rank: int = 0
    joined_at: datetime = field(default_factory=datetime.utcnow)

    def update_pnl(self, new_balance: float) -> None:
        """Update PnL based on new balance."""
        self.current_balance = new_balance
        self.pnl = new_balance - self.starting_balance
        self.pnl_percentage = (self.pnl / self.starting_balance) * 100

    def record_trade(self) -> None:
        """Record a trade for this entry."""
        self.trades_count += 1


@dataclass
class Tournament:
    """A trading tournament."""
    id: str
    name: str
    description: str
    type: TournamentType
    status: TournamentStatus
    tier_requirement: str | None = None  # Minimum tier to enter
    starting_balance: float = 10000.0
    max_participants: int = 100
    entry_fee_points: int = 0

    # Timing
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(days=7))

    # Entries and prizes
    entries: list[TournamentEntry] = field(default_factory=list)
    prizes: list[PrizeDistribution] = field(default_factory=list)

    created_at: datetime = field(default_factory=datetime.utcnow)

    def is_active(self) -> bool:
        """Check if tournament is currently active."""
        now = datetime.utcnow()
        return (
            self.status == TournamentStatus.ACTIVE and
            self.start_time <= now <= self.end_time
        )

    def can_enter(self, competitor_tier: str) -> bool:
        """Check if competitor can enter tournament."""
        if self.status != TournamentStatus.PENDING:
            return False
        if len(self.entries) >= self.max_participants:
            return False
        if self.tier_requirement and competitor_tier != self.tier_requirement:
            return False
        return True

    def add_entry(self, entry: TournamentEntry) -> bool:
        """Add entry to tournament."""
        if len(self.entries) >= self.max_participants:
            return False
        self.entries.append(entry)
        return True

    def update_rankings(self) -> None:
        """Update rankings based on PnL."""
        # Sort by PnL percentage (descending)
        sorted_entries = sorted(
            self.entries,
            key=lambda e: e.pnl_percentage,
            reverse=True
        )

        # Update ranks
        for rank, entry in enumerate(sorted_entries, 1):
            entry.rank = rank

        self.entries = sorted_entries

    def get_leaderboard(self, limit: int = 10) -> list[TournamentEntry]:
        """Get top N competitors."""
        self.update_rankings()
        return self.entries[:limit]

    def get_prize_for_position(self, position: int) -> PrizeDistribution | None:
        """Get prize for a specific position."""
        for prize in self.prizes:
            if prize.position == position:
                return prize
        return None
