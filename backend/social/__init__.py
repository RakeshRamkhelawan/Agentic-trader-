"""
Social features for competitions.

Features:
- Follow competitors
- User profiles with stats
- Activity feeds
- Direct messaging
"""

from .activity_feed import ActivityFeed, ActivityType, activity_feed
from .follow_system import FollowSystem, follow_system
from .profile_manager import ProfileManager, UserProfile, profile_manager

__all__ = [
    "FollowSystem",
    "follow_system",
    "ProfileManager",
    "UserProfile",
    "profile_manager",
    "ActivityFeed",
    "ActivityType",
    "activity_feed",
]
