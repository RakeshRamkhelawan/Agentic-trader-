"""Rewards and badges system for competitions."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class BadgeType(Enum):
    """Types of badges that can be earned."""

    # Performance badges
    PROFITABLE_TRADER = "profitable_trader"
    SHARPE_MASTER = "sharpe_master"
    WIN_STREAK = "win_streak"

    # Competition badges
    TOURNAMENT_WINNER = "tournament_winner"
    TOURNAMENT_TOP_3 = "tournament_top_3"
    WEEKLY_CHAMPION = "weekly_champion"

    # League badges
    BRONZE_LEAGUE = "bronze_league"
    SILVER_LEAGUE = "silver_league"
    GOLD_LEAGUE = "gold_league"
    DIAMOND_LEAGUE = "diamond_league"

    # Strategy badges
    STRATEGY_CREATOR = "strategy_creator"
    POPULAR_STRATEGY = "popular_strategy"
    STRATEGY_MASTER = "strategy_master"

    # Community badges
    HELPER = "helper"
    INFLUENCER = "influencer"
    EARLY_ADOPTER = "early_adopter"


class BadgeRarity(Enum):
    """Badge rarity levels."""

    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


@dataclass
class Badge:
    """A badge that can be earned."""

    type: BadgeType
    name: str
    description: str
    rarity: BadgeRarity
    icon: str
    points_bonus: int = 0
    requirements: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type.value,
            "name": self.name,
            "description": self.description,
            "rarity": self.rarity.value,
            "icon": self.icon,
            "points_bonus": self.points_bonus,
        }


@dataclass
class EarnedBadge:
    """A badge earned by a competitor."""

    badge_type: BadgeType
    competitor_id: str
    earned_at: datetime = field(default_factory=datetime.utcnow)
    context: str = ""  # Additional context (e.g., tournament name)


@dataclass
class Achievement:
    """An achievement with progress tracking."""

    id: str
    name: str
    description: str
    badge: Badge | None = None
    target_value: int = 1
    current_value: int = 0
    completed: bool = False
    completed_at: datetime | None = None

    def update_progress(self, value: int) -> bool:
        """Update achievement progress."""
        self.current_value = min(value, self.target_value)

        if self.current_value >= self.target_value and not self.completed:
            self.completed = True
            self.completed_at = datetime.utcnow()
            return True  # Achievement completed
        return False

    def get_progress_percent(self) -> float:
        """Get progress percentage."""
        return (self.current_value / self.target_value) * 100


class RewardsSystem:
    """
    Manages badges, achievements, and rewards.

    Badge Collections:
    - Performance: Based on trading results
    - Competition: Based on tournament performance
    - League: Based on league tier
    - Strategy: Based on strategy sharing
    - Community: Based on community engagement
    """

    def __init__(self):
        self._badges: dict[BadgeType, Badge] = {}
        self._earned_badges: dict[str, list[EarnedBadge]] = {}  # competitor_id -> badges
        self._achievements: dict[str, list[Achievement]] = {}  # competitor_id -> achievements

        self._init_badges()

    def _init_badges(self) -> None:
        """Initialize all available badges."""
        # Performance badges
        self._badges[BadgeType.PROFITABLE_TRADER] = Badge(
            type=BadgeType.PROFITABLE_TRADER,
            name="Profitable Trader",
            description="Achieve positive P&L over 10 trades",
            rarity=BadgeRarity.COMMON,
            icon="trending_up",
            points_bonus=100,
        )

        self._badges[BadgeType.SHARPE_MASTER] = Badge(
            type=BadgeType.SHARPE_MASTER,
            name="Sharpe Master",
            description="Maintain Sharpe ratio above 2.0 for a month",
            rarity=BadgeRarity.RARE,
            icon="activity",
            points_bonus=500,
        )

        self._badges[BadgeType.WIN_STREAK] = Badge(
            type=BadgeType.WIN_STREAK,
            name="Win Streak",
            description="Win 5 trades in a row",
            rarity=BadgeRarity.UNCOMMON,
            icon="zap",
            points_bonus=250,
        )

        # Competition badges
        self._badges[BadgeType.TOURNAMENT_WINNER] = Badge(
            type=BadgeType.TOURNAMENT_WINNER,
            name="Champion",
            description="Win 1st place in a tournament",
            rarity=BadgeRarity.EPIC,
            icon="trophy",
            points_bonus=1000,
        )

        self._badges[BadgeType.TOURNAMENT_TOP_3] = Badge(
            type=BadgeType.TOURNAMENT_TOP_3,
            name="Podium Finish",
            description="Finish in top 3 of a tournament",
            rarity=BadgeRarity.RARE,
            icon="award",
            points_bonus=500,
        )

        self._badges[BadgeType.WEEKLY_CHAMPION] = Badge(
            type=BadgeType.WEEKLY_CHAMPION,
            name="Weekly Champion",
            description="Win 3 weekly tournaments",
            rarity=BadgeRarity.LEGENDARY,
            icon="crown",
            points_bonus=2500,
        )

        # League badges
        self._badges[BadgeType.BRONZE_LEAGUE] = Badge(
            type=BadgeType.BRONZE_LEAGUE,
            name="Bronze Trader",
            description="Reach Bronze League",
            rarity=BadgeRarity.COMMON,
            icon="star",
            points_bonus=50,
        )

        self._badges[BadgeType.SILVER_LEAGUE] = Badge(
            type=BadgeType.SILVER_LEAGUE,
            name="Silver Trader",
            description="Reach Silver League",
            rarity=BadgeRarity.UNCOMMON,
            icon="star",
            points_bonus=200,
        )

        self._badges[BadgeType.GOLD_LEAGUE] = Badge(
            type=BadgeType.GOLD_LEAGUE,
            name="Gold Trader",
            description="Reach Gold League",
            rarity=BadgeRarity.RARE,
            icon="star",
            points_bonus=500,
        )

        self._badges[BadgeType.DIAMOND_LEAGUE] = Badge(
            type=BadgeType.DIAMOND_LEAGUE,
            name="Diamond Trader",
            description="Reach Diamond League",
            rarity=BadgeRarity.LEGENDARY,
            icon="diamond",
            points_bonus=2500,
        )

        # Strategy badges
        self._badges[BadgeType.STRATEGY_CREATOR] = Badge(
            type=BadgeType.STRATEGY_CREATOR,
            name="Strategy Creator",
            description="Share your first strategy",
            rarity=BadgeRarity.COMMON,
            icon="code",
            points_bonus=100,
        )

        self._badges[BadgeType.POPULAR_STRATEGY] = Badge(
            type=BadgeType.POPULAR_STRATEGY,
            name="Viral Strategy",
            description="Get 50 likes on a strategy",
            rarity=BadgeRarity.RARE,
            icon="heart",
            points_bonus=500,
        )

        self._badges[BadgeType.STRATEGY_MASTER] = Badge(
            type=BadgeType.STRATEGY_MASTER,
            name="Strategy Master",
            description="Have 10 strategies forked",
            rarity=BadgeRarity.EPIC,
            icon="git-branch",
            points_bonus=1000,
        )

        # Community badges
        self._badges[BadgeType.HELPER] = Badge(
            type=BadgeType.HELPER,
            name="Community Helper",
            description="Help 5 other traders improve",
            rarity=BadgeRarity.UNCOMMON,
            icon="helping_hand",
            points_bonus=200,
        )

        self._badges[BadgeType.INFLUENCER] = Badge(
            type=BadgeType.INFLUENCER,
            name="Trading Influencer",
            description="Gain 100 followers",
            rarity=BadgeRarity.EPIC,
            icon="users",
            points_bonus=1000,
        )

        self._badges[BadgeType.EARLY_ADOPTER] = Badge(
            type=BadgeType.EARLY_ADOPTER,
            name="Early Adopter",
            description="Join during beta period",
            rarity=BadgeRarity.LEGENDARY,
            icon="rocket",
            points_bonus=500,
        )

    def award_badge(
        self,
        competitor_id: str,
        badge_type: BadgeType,
        context: str = "",
    ) -> dict[str, Any]:
        """Award a badge to a competitor."""
        badge = self._badges.get(badge_type)
        if not badge:
            return {"success": False, "error": "Badge not found"}

        # Check if already earned
        existing = self._earned_badges.get(competitor_id, [])
        if any(e.badge_type == badge_type for e in existing):
            return {"success": False, "error": "Badge already earned"}

        # Award badge
        earned = EarnedBadge(
            badge_type=badge_type,
            competitor_id=competitor_id,
            context=context,
        )

        if competitor_id not in self._earned_badges:
            self._earned_badges[competitor_id] = []
        self._earned_badges[competitor_id].append(earned)

        return {
            "success": True,
            "badge": badge.to_dict(),
            "points_bonus": badge.points_bonus,
            "message": f"Congratulations! You earned the {badge.name} badge!",
        }

    def get_competitor_badges(self, competitor_id: str) -> list[dict[str, Any]]:
        """Get all badges earned by a competitor."""
        earned = self._earned_badges.get(competitor_id, [])

        return [
            {
                **self._badges[e.badge_type].to_dict(),
                "earned_at": e.earned_at.isoformat(),
                "context": e.context,
            }
            for e in earned
            if e.badge_type in self._badges
        ]

    def get_all_badges(self) -> list[dict[str, Any]]:
        """Get all available badges."""
        return [badge.to_dict() for badge in self._badges.values()]

    def create_achievement(
        self,
        competitor_id: str,
        name: str,
        description: str,
        target_value: int,
        badge_type: BadgeType | None = None,
    ) -> str:
        """Create a new achievement for a competitor."""
        achievement_id = f"{competitor_id}_{name.lower().replace(' ', '_')}"

        badge = self._badges.get(badge_type) if badge_type else None

        achievement = Achievement(
            id=achievement_id,
            name=name,
            description=description,
            badge=badge,
            target_value=target_value,
        )

        if competitor_id not in self._achievements:
            self._achievements[competitor_id] = []
        self._achievements[competitor_id].append(achievement)

        return achievement_id

    def update_achievement_progress(
        self,
        competitor_id: str,
        achievement_id: str,
        value: int,
    ) -> dict[str, Any]:
        """Update achievement progress."""
        achievements = self._achievements.get(competitor_id, [])
        achievement = next((a for a in achievements if a.id == achievement_id), None)

        if not achievement:
            return {"error": "Achievement not found"}

        completed = achievement.update_progress(value)

        result = {
            "achievement_id": achievement_id,
            "current_value": achievement.current_value,
            "target_value": achievement.target_value,
            "progress_percent": achievement.get_progress_percent(),
            "completed": achievement.completed,
        }

        if completed and achievement.badge:
            badge_result = self.award_badge(competitor_id, achievement.badge.type)
            result["badge_awarded"] = badge_result

        return result

    def get_competitor_achievements(self, competitor_id: str) -> list[dict[str, Any]]:
        """Get all achievements for a competitor."""
        achievements = self._achievements.get(competitor_id, [])

        return [
            {
                "id": a.id,
                "name": a.name,
                "description": a.description,
                "current_value": a.current_value,
                "target_value": a.target_value,
                "progress_percent": a.get_progress_percent(),
                "completed": a.completed,
                "completed_at": a.completed_at.isoformat() if a.completed_at else None,
                "badge": a.badge.to_dict() if a.badge else None,
            }
            for a in achievements
        ]

    def get_leaderboard_by_badges(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get leaderboard sorted by badge count."""
        badge_counts = [
            {
                "competitor_id": cid,
                "badge_count": len(badges),
                "legendary_badges": sum(
                    1 for e in badges if self._badges[e.badge_type].rarity == BadgeRarity.LEGENDARY
                ),
            }
            for cid, badges in self._earned_badges.items()
        ]

        # Sort by badge count, then legendary count
        badge_counts.sort(key=lambda x: (x["badge_count"], x["legendary_badges"]), reverse=True)

        return badge_counts[:limit]
