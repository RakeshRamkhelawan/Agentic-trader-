"""Follow system for tracking competitors."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class FollowRelationship:
    """A follow relationship between users."""

    follower_id: str
    following_id: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    notifications_enabled: bool = True


class FollowSystem:
    """
    Manages follow relationships between competitors.

    Features:
    - Follow/unfollow competitors
    - Get followers/following lists
    - Check if following
    - Get follow counts
    """

    def __init__(self):
        # follower_id -> set of following_ids
        self._following: dict[str, set[str]] = {}
        # following_id -> set of follower_ids
        self._followers: dict[str, set[str]] = {}
        # (follower_id, following_id) -> FollowRelationship
        self._relationships: dict[tuple, FollowRelationship] = {}

    def follow(self, follower_id: str, following_id: str) -> bool:
        """
        Make one user follow another.

        Args:
            follower_id: User who is following
            following_id: User being followed

        Returns:
            True if successful, False if already following
        """
        if follower_id == following_id:
            return False  # Can't follow yourself

        # Check if already following
        if self.is_following(follower_id, following_id):
            return False

        # Add to following set
        if follower_id not in self._following:
            self._following[follower_id] = set()
        self._following[follower_id].add(following_id)

        # Add to followers set
        if following_id not in self._followers:
            self._followers[following_id] = set()
        self._followers[following_id].add(follower_id)

        # Create relationship
        relationship = FollowRelationship(
            follower_id=follower_id,
            following_id=following_id,
        )
        self._relationships[(follower_id, following_id)] = relationship

        return True

    def unfollow(self, follower_id: str, following_id: str) -> bool:
        """
        Make one user unfollow another.

        Returns:
            True if successful, False if not following
        """
        if not self.is_following(follower_id, following_id):
            return False

        # Remove from following set
        if follower_id in self._following:
            self._following[follower_id].discard(following_id)

        # Remove from followers set
        if following_id in self._followers:
            self._followers[following_id].discard(follower_id)

        # Remove relationship
        self._relationships.pop((follower_id, following_id), None)

        return True

    def is_following(self, follower_id: str, following_id: str) -> bool:
        """Check if follower_id is following following_id."""
        return following_id in self._following.get(follower_id, set())

    def get_following(self, user_id: str) -> list[str]:
        """Get list of users that user_id is following."""
        return list(self._following.get(user_id, set()))

    def get_followers(self, user_id: str) -> list[str]:
        """Get list of users following user_id."""
        return list(self._followers.get(user_id, set()))

    def get_following_count(self, user_id: str) -> int:
        """Get number of users that user_id is following."""
        return len(self._following.get(user_id, set()))

    def get_follower_count(self, user_id: str) -> int:
        """Get number of followers for user_id."""
        return len(self._followers.get(user_id, set()))

    def get_follow_counts(self, user_id: str) -> dict[str, int]:
        """Get both follower and following counts."""
        return {
            "following": self.get_following_count(user_id),
            "followers": self.get_follower_count(user_id),
        }

    def get_relationship(self, follower_id: str, following_id: str) -> FollowRelationship | None:
        """Get follow relationship details."""
        return self._relationships.get((follower_id, following_id))

    def enable_notifications(self, follower_id: str, following_id: str) -> bool:
        """Enable notifications for a follow relationship."""
        relationship = self._relationships.get((follower_id, following_id))
        if relationship:
            relationship.notifications_enabled = True
            return True
        return False

    def disable_notifications(self, follower_id: str, following_id: str) -> bool:
        """Disable notifications for a follow relationship."""
        relationship = self._relationships.get((follower_id, following_id))
        if relationship:
            relationship.notifications_enabled = False
            return True
        return False

    def get_follower_notifications_enabled(self, user_id: str) -> list[str]:
        """Get followers who have notifications enabled."""
        followers = self.get_followers(user_id)
        return [
            follower_id
            for follower_id in followers
            if self._relationships.get(
                (follower_id, user_id), FollowRelationship(follower_id, user_id)
            ).notifications_enabled
        ]

    def get_mutual_follows(self, user_id: str) -> list[str]:
        """Get users who follow each other (mutual follows)."""
        following = self._following.get(user_id, set())
        followers = self._followers.get(user_id, set())
        return list(following & followers)

    def suggest_users_to_follow(self, user_id: str, limit: int = 10) -> list[str]:
        """
        Suggest users to follow based on:
        - Mutual connections
        - Similar performance/tier
        - Popular traders
        """
        suggestions = set()

        # Get users followed by people user follows
        following = self._following.get(user_id, set())
        for followed_id in following:
            their_following = self._following.get(followed_id, set())
            for potential in their_following:
                if potential != user_id and not self.is_following(user_id, potential):
                    suggestions.add(potential)

        return list(suggestions)[:limit]

    def get_stats(self) -> dict:
        """Get follow system statistics."""
        total_following = sum(len(s) for s in self._following.values())
        total_users = len(set(self._following.keys()) | set(self._followers.keys()))

        return {
            "total_users": total_users,
            "total_following_relationships": total_following,
            "avg_following_per_user": (total_following / total_users if total_users > 0 else 0),
        }


# Global follow system instance
follow_system = FollowSystem()
