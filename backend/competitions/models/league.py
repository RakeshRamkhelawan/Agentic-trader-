"""League models for tiered competitions."""

from dataclasses import dataclass, field
from datetime import datetime

from .competitor import LeagueTier


@dataclass
class LeaguePromotion:
    """Promotion/demotion rules and history."""
    competitor_id: str
    from_tier: LeagueTier
    to_tier: LeagueTier
    promoted_at: datetime = field(default_factory=datetime.utcnow)
    reason: str = ""  # "performance", "season_end", "manual"
    pnl_at_promotion: float = 0.0
    rank_at_promotion: int = 0


@dataclass
class League:
    """A competition league tier."""
    tier: LeagueTier
    name: str
    description: str

    # Tier thresholds
    min_points: int = 0
    max_points: int = 0

    # Promotion/demotion rules
    promotion_threshold: int = 1000  # Points needed to promote
    demotion_threshold: int = -500   # Points for demotion

    # Members
    competitor_ids: list[str] = field(default_factory=list)
    max_members: int = 1000

    # Statistics
    total_pnl: float = 0.0
    avg_pnl: float = 0.0
    best_performer_id: str | None = None

    # Metadata
    season_number: int = 1
    season_start: datetime = field(default_factory=datetime.utcnow)
    season_end: datetime | None = None

    def add_competitor(self, competitor_id: str) -> bool:
        """Add competitor to league."""
        if len(self.competitor_ids) >= self.max_members:
            return False
        if competitor_id not in self.competitor_ids:
            self.competitor_ids.append(competitor_id)
            return True
        return False

    def remove_competitor(self, competitor_id: str) -> bool:
        """Remove competitor from league."""
        if competitor_id in self.competitor_ids:
            self.competitor_ids.remove(competitor_id)
            return True
        return False

    def update_stats(self, competitor_pnls: dict[str, float]) -> None:
        """Update league statistics."""
        if not competitor_pnls:
            return

        self.total_pnl = sum(competitor_pnls.values())
        self.avg_pnl = self.total_pnl / len(competitor_pnls)

        # Find best performer
        if competitor_pnls:
            self.best_performer_id = max(
                competitor_pnls,
                key=competitor_pnls.get
            )

    def get_tier_requirements(self) -> dict[str, any]:
        """Get tier requirements info."""
        return {
            "tier": self.tier.value,
            "name": self.name,
            "min_points": self.min_points,
            "max_points": self.max_points,
            "promotion_threshold": self.promotion_threshold,
            "demotion_threshold": self.demotion_threshold,
            "current_members": len(self.competitor_ids),
            "max_members": self.max_members,
        }

    @staticmethod
    def get_tier_bounds(tier: LeagueTier) -> tuple:
        """Get point bounds for a tier."""
        bounds = {
            LeagueTier.BRONZE: (0, 1000),
            LeagueTier.SILVER: (1000, 10000),
            LeagueTier.GOLD: (10000, 50000),
            LeagueTier.DIAMOND: (50000, float('inf')),
        }
        return bounds.get(tier, (0, 0))

    @staticmethod
    def get_next_tier(current: LeagueTier) -> LeagueTier | None:
        """Get next tier for promotion."""
        progression = [
            LeagueTier.BRONZE,
            LeagueTier.SILVER,
            LeagueTier.GOLD,
            LeagueTier.DIAMOND,
        ]

        try:
            idx = progression.index(current)
            if idx < len(progression) - 1:
                return progression[idx + 1]
        except ValueError:
            pass
        return None

    @staticmethod
    def get_previous_tier(current: LeagueTier) -> LeagueTier | None:
        """Get previous tier for demotion."""
        progression = [
            LeagueTier.BRONZE,
            LeagueTier.SILVER,
            LeagueTier.GOLD,
            LeagueTier.DIAMOND,
        ]

        try:
            idx = progression.index(current)
            if idx > 0:
                return progression[idx - 1]
        except ValueError:
            pass
        return None
