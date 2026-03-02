"""User profile management."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class UserProfile:
    """Enhanced user profile with social features."""

    user_id: str
    display_name: str
    bio: str = ""
    avatar_url: str | None = None
    location: str = ""
    website: str | None = None

    # Trading stats (synced from competitor)
    tier: str = "bronze"
    points: int = 0
    rank: int = 0
    total_pnl: float = 0.0
    win_rate: float = 0.0
    total_trades: int = 0

    # Social stats
    followers_count: int = 0
    following_count: int = 0
    strategies_count: int = 0
    tournaments_won: int = 0
    badges_count: int = 0

    # Preferences
    is_public: bool = True
    show_trades: bool = True
    show_pnl: bool = True
    allow_messages: bool = True

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "display_name": self.display_name,
            "bio": self.bio,
            "avatar_url": self.avatar_url,
            "location": self.location,
            "website": self.website,
            "tier": self.tier,
            "points": self.points,
            "rank": self.rank,
            "stats": {
                "total_pnl": self.total_pnl,
                "win_rate": self.win_rate,
                "total_trades": self.total_trades,
            },
            "social": {
                "followers": self.followers_count,
                "following": self.following_count,
                "strategies": self.strategies_count,
                "tournaments_won": self.tournaments_won,
                "badges": self.badges_count,
            },
            "preferences": {
                "is_public": self.is_public,
                "show_trades": self.show_trades,
                "show_pnl": self.show_pnl,
                "allow_messages": self.allow_messages,
            },
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class ProfileManager:
    """
    Manages user profiles with social features.

    Provides:
    - Profile CRUD operations
    - Profile search/discovery
    - Stats synchronization from competitions
    """

    def __init__(self):
        self._profiles: dict[str, UserProfile] = {}
        self._display_name_index: dict[str, str] = {}  # display_name -> user_id

    def create_profile(
        self, user_id: str, display_name: str, bio: str = "", **kwargs
    ) -> UserProfile:
        """Create a new user profile."""
        # Ensure unique display name
        base_name = display_name
        counter = 1
        while display_name in self._display_name_index:
            display_name = f"{base_name}_{counter}"
            counter += 1

        profile = UserProfile(user_id=user_id, display_name=display_name, bio=bio, **kwargs)

        self._profiles[user_id] = profile
        self._display_name_index[display_name] = user_id

        return profile

    def get_profile(self, user_id: str) -> UserProfile | None:
        """Get profile by user ID."""
        return self._profiles.get(user_id)

    def get_profile_by_name(self, display_name: str) -> UserProfile | None:
        """Get profile by display name."""
        user_id = self._display_name_index.get(display_name)
        if user_id:
            return self._profiles.get(user_id)
        return None

    def update_profile(self, user_id: str, **kwargs) -> UserProfile | None:
        """Update profile fields."""
        profile = self._profiles.get(user_id)
        if not profile:
            return None

        # Handle display name change
        if "display_name" in kwargs and kwargs["display_name"] != profile.display_name:
            new_name = kwargs["display_name"]
            if new_name in self._display_name_index:
                return None  # Name already taken

            # Update index
            del self._display_name_index[profile.display_name]
            self._display_name_index[new_name] = user_id

        # Update fields
        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)

        profile.updated_at = datetime.utcnow()
        return profile

    def delete_profile(self, user_id: str) -> bool:
        """Delete a profile."""
        profile = self._profiles.get(user_id)
        if profile:
            del self._profiles[user_id]
            del self._display_name_index[profile.display_name]
            return True
        return False

    def sync_competitor_stats(
        self,
        user_id: str,
        tier: str,
        points: int,
        rank: int,
        total_pnl: float,
        win_rate: float,
        total_trades: int,
    ) -> UserProfile | None:
        """Synchronize stats from competition system."""
        profile = self._profiles.get(user_id)
        if profile:
            profile.tier = tier
            profile.points = points
            profile.rank = rank
            profile.total_pnl = total_pnl
            profile.win_rate = win_rate
            profile.total_trades = total_trades
            profile.updated_at = datetime.utcnow()
        return profile

    def update_social_stats(
        self,
        user_id: str,
        followers: int | None = None,
        following: int | None = None,
        strategies: int | None = None,
        tournaments_won: int | None = None,
        badges: int | None = None,
    ) -> UserProfile | None:
        """Update social stats."""
        profile = self._profiles.get(user_id)
        if profile:
            if followers is not None:
                profile.followers_count = followers
            if following is not None:
                profile.following_count = following
            if strategies is not None:
                profile.strategies_count = strategies
            if tournaments_won is not None:
                profile.tournaments_won = tournaments_won
            if badges is not None:
                profile.badges_count = badges
            profile.updated_at = datetime.utcnow()
        return profile

    def search_profiles(
        self,
        query: str | None = None,
        tier: str | None = None,
        min_points: int | None = None,
        limit: int = 20,
    ) -> list[UserProfile]:
        """Search profiles."""
        results = list(self._profiles.values())

        # Filter by query (display name or bio)
        if query:
            query_lower = query.lower()
            results = [
                p
                for p in results
                if query_lower in p.display_name.lower() or query_lower in p.bio.lower()
            ]

        # Filter by tier
        if tier:
            results = [p for p in results if p.tier == tier]

        # Filter by minimum points
        if min_points is not None:
            results = [p for p in results if p.points >= min_points]

        # Sort by points (descending)
        results.sort(key=lambda p: p.points, reverse=True)

        return results[:limit]

    def get_leaderboard_profiles(self, limit: int = 50) -> list[dict]:
        """Get profiles formatted for leaderboard."""
        profiles = sorted(
            self._profiles.values(),
            key=lambda p: p.points,
            reverse=True,
        )[:limit]

        return [
            {
                "rank": i + 1,
                "user_id": p.user_id,
                "display_name": p.display_name,
                "tier": p.tier,
                "points": p.points,
                "total_pnl": p.total_pnl,
                "win_rate": p.win_rate,
                "followers": p.followers_count,
            }
            for i, p in enumerate(profiles)
        ]

    def get_public_profile(self, user_id: str) -> dict | None:
        """Get public profile view (respects privacy settings)."""
        profile = self._profiles.get(user_id)
        if not profile:
            return None

        if not profile.is_public:
            return {
                "user_id": profile.user_id,
                "display_name": profile.display_name,
                "tier": profile.tier,
                "is_private": True,
            }

        data = profile.to_dict()

        # Respect privacy settings
        if not profile.show_pnl:
            data["stats"]["total_pnl"] = None
        if not profile.show_trades:
            data["stats"]["total_trades"] = None
            data["stats"]["win_rate"] = None

        return data

    def get_stats(self) -> dict:
        """Get profile system statistics."""
        return {
            "total_profiles": len(self._profiles),
            "by_tier": self._count_by_tier(),
        }

    def _count_by_tier(self) -> dict[str, int]:
        """Count profiles by tier."""
        counts = {}
        for profile in self._profiles.values():
            counts[profile.tier] = counts.get(profile.tier, 0) + 1
        return counts


# Global profile manager
profile_manager = ProfileManager()
