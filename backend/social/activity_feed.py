"""Activity feed for social features."""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ActivityType(Enum):
    """Types of activities."""
    # Trading activities
    TRADE_EXECUTED = "trade_executed"
    POSITION_CLOSED = "position_closed"

    # Competition activities
    TOURNAMENT_ENTERED = "tournament_entered"
    TOURNAMENT_WON = "tournament_won"
    RANK_ACHIEVED = "rank_achieved"

    # Social activities
    STRATEGY_SHARED = "strategy_shared"
    STRATEGY_FORKED = "strategy_forked"
    USER_FOLLOWED = "user_followed"

    # Achievement activities
    BADGE_EARNED = "badge_earned"
    TIER_PROMOTED = "tier_promoted"

    # System activities
    PROFILE_UPDATED = "profile_updated"


@dataclass
class Activity:
    """An activity entry."""
    id: str
    user_id: str
    type: ActivityType
    data: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_public: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type.value,
            "data": self.data,
            "created_at": self.created_at.isoformat(),
        }


class ActivityFeed:
    """
    Activity feed for social features.

    Provides:
    - Personal activity feed
    - Following activity feed
    - Global activity feed
    - Activity aggregation
    """

    def __init__(self):
        self._activities: dict[str, list[Activity]] = defaultdict(list)  # user_id -> activities
        self._global_activities: list[Activity] = []
        self._max_per_user = 100
        self._max_global = 1000
        self._counter = 0

    def _generate_id(self) -> str:
        """Generate unique activity ID."""
        self._counter += 1
        return f"activity_{self._counter}_{datetime.utcnow().timestamp()}"

    def add_activity(
        self,
        user_id: str,
        activity_type: ActivityType,
        data: dict[str, Any],
        is_public: bool = True,
    ) -> Activity:
        """Add an activity to a user's feed."""
        activity = Activity(
            id=self._generate_id(),
            user_id=user_id,
            type=activity_type,
            data=data,
            is_public=is_public,
        )

        # Add to user feed
        self._activities[user_id].append(activity)

        # Trim user feed
        if len(self._activities[user_id]) > self._max_per_user:
            self._activities[user_id] = self._activities[user_id][-self._max_per_user:]

        # Add to global feed if public
        if is_public:
            self._global_activities.append(activity)

            # Trim global feed
            if len(self._global_activities) > self._max_global:
                self._global_activities = self._global_activities[-self._max_global:]

        return activity

    def get_user_feed(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Activity]:
        """Get a user's personal activity feed."""
        activities = self._activities.get(user_id, [])

        # Sort by created_at desc
        activities = sorted(activities, key=lambda a: a.created_at, reverse=True)

        return activities[offset:offset + limit]

    def get_following_feed(
        self,
        user_id: str,
        follow_system,
        limit: int = 50,
    ) -> list[Activity]:
        """Get activity feed for users that user_id follows."""
        following = follow_system.get_following(user_id)

        # Collect activities from followed users
        all_activities = []
        for followed_id in following:
            activities = self._activities.get(followed_id, [])
            all_activities.extend([a for a in activities if a.is_public])

        # Sort by created_at desc
        all_activities.sort(key=lambda a: a.created_at, reverse=True)

        return all_activities[:limit]

    def get_global_feed(self, limit: int = 50) -> list[Activity]:
        """Get global activity feed."""
        # Sort by created_at desc
        activities = sorted(
            self._global_activities,
            key=lambda a: a.created_at,
            reverse=True,
        )

        return activities[:limit]

    def get_feed_by_type(
        self,
        activity_type: ActivityType,
        limit: int = 50,
    ) -> list[Activity]:
        """Get activities of a specific type."""
        activities = [
            a for a in self._global_activities
            if a.type == activity_type
        ]

        # Sort by created_at desc
        activities.sort(key=lambda a: a.created_at, reverse=True)

        return activities[:limit]

    # Convenience methods for common activities
    def add_trade_activity(
        self,
        user_id: str,
        symbol: str,
        side: str,
        pnl: float,
    ) -> Activity:
        """Add trade executed activity."""
        return self.add_activity(
            user_id=user_id,
            activity_type=ActivityType.TRADE_EXECUTED,
            data={
                "symbol": symbol,
                "side": side,
                "pnl": pnl,
            },
        )

    def add_tournament_won_activity(
        self,
        user_id: str,
        tournament_name: str,
        rank: int,
        prize: int,
    ) -> Activity:
        """Add tournament won activity."""
        return self.add_activity(
            user_id=user_id,
            activity_type=ActivityType.TOURNAMENT_WON,
            data={
                "tournament_name": tournament_name,
                "rank": rank,
                "prize": prize,
            },
        )

    def add_badge_earned_activity(
        self,
        user_id: str,
        badge_name: str,
        badge_icon: str,
    ) -> Activity:
        """Add badge earned activity."""
        return self.add_activity(
            user_id=user_id,
            activity_type=ActivityType.BADGE_EARNED,
            data={
                "badge_name": badge_name,
                "badge_icon": badge_icon,
            },
        )

    def add_strategy_shared_activity(
        self,
        user_id: str,
        strategy_name: str,
        strategy_id: str,
    ) -> Activity:
        """Add strategy shared activity."""
        return self.add_activity(
            user_id=user_id,
            activity_type=ActivityType.STRATEGY_SHARED,
            data={
                "strategy_name": strategy_name,
                "strategy_id": strategy_id,
            },
        )

    def add_follow_activity(
        self,
        user_id: str,
        followed_user_id: str,
        followed_user_name: str,
    ) -> Activity:
        """Add user followed activity."""
        return self.add_activity(
            user_id=user_id,
            activity_type=ActivityType.USER_FOLLOWED,
            data={
                "followed_user_id": followed_user_id,
                "followed_user_name": followed_user_name,
            },
        )

    def add_tier_promotion_activity(
        self,
        user_id: str,
        old_tier: str,
        new_tier: str,
    ) -> Activity:
        """Add tier promotion activity."""
        return self.add_activity(
            user_id=user_id,
            activity_type=ActivityType.TIER_PROMOTED,
            data={
                "old_tier": old_tier,
                "new_tier": new_tier,
            },
        )

    def delete_old_activities(self, days: int = 30) -> int:
        """Delete activities older than specified days."""
        cutoff = datetime.utcnow() - timedelta(days=days)

        deleted_count = 0

        # Clean user activities
        for user_id in self._activities:
            original_count = len(self._activities[user_id])
            self._activities[user_id] = [
                a for a in self._activities[user_id]
                if a.created_at > cutoff
            ]
            deleted_count += original_count - len(self._activities[user_id])

        # Clean global activities
        original_count = len(self._global_activities)
        self._global_activities = [
            a for a in self._global_activities
            if a.created_at > cutoff
        ]
        deleted_count += original_count - len(self._global_activities)

        return deleted_count

    def get_stats(self) -> dict[str, Any]:
        """Get activity feed statistics."""
        return {
            "total_users": len(self._activities),
            "total_global_activities": len(self._global_activities),
            "by_type": self._count_by_type(),
        }

    def _count_by_type(self) -> dict[str, int]:
        """Count activities by type."""
        counts = defaultdict(int)
        for activity in self._global_activities:
            counts[activity.type.value] += 1
        return dict(counts)


from datetime import timedelta

# Global activity feed
activity_feed = ActivityFeed()
