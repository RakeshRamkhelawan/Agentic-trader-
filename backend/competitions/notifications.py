"""Notification system for competitions."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
import asyncio


class NotificationType(Enum):
    """Types of notifications."""
    TOURNAMENT_START = "tournament_start"
    TOURNAMENT_END = "tournament_end"
    RANK_CHANGE = "rank_change"
    BADGE_EARNED = "badge_earned"
    TIER_PROMOTION = "tier_promotion"
    TRADE_FILLED = "trade_filled"
    STRATEGY_FORKED = "strategy_forked"
    CHAT_MENTION = "chat_mention"
    SYSTEM = "system"


class NotificationPriority(Enum):
    """Notification priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Notification:
    """A notification."""
    id: str
    user_id: str
    type: NotificationType
    title: str
    message: str
    priority: NotificationPriority = NotificationPriority.MEDIUM
    data: Dict[str, Any] = field(default_factory=dict)
    read: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "message": self.message,
            "priority": self.priority.value,
            "data": self.data,
            "read": self.read,
            "created_at": self.created_at.isoformat(),
        }


class NotificationManager:
    """
    Manages notifications for competition events.
    
    Features:
    - In-app notifications
    - Email notifications (optional)
    - Push notifications (optional)
    - Notification preferences
    """
    
    def __init__(self):
        self._notifications: Dict[str, List[Notification]] = {}  # user_id -> notifications
        self._handlers: Dict[NotificationType, List[Callable]] = {}
        self._preferences: Dict[str, Dict[NotificationType, bool]] = {}
        self._counter = 0
    
    def register_handler(
        self,
        notification_type: NotificationType,
        handler: Callable[[Notification], None],
    ) -> None:
        """Register a handler for a notification type."""
        if notification_type not in self._handlers:
            self._handlers[notification_type] = []
        self._handlers[notification_type].append(handler)
    
    def set_preferences(
        self,
        user_id: str,
        preferences: Dict[NotificationType, bool],
    ) -> None:
        """Set notification preferences for a user."""
        self._preferences[user_id] = preferences
    
    def should_notify(self, user_id: str, notification_type: NotificationType) -> bool:
        """Check if user should receive this notification type."""
        prefs = self._preferences.get(user_id, {})
        return prefs.get(notification_type, True)  # Default to enabled
    
    async def send_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        data: Optional[Dict[str, Any]] = None,
    ) -> Notification:
        """Send a notification to a user."""
        if not self.should_notify(user_id, notification_type):
            return None
        
        self._counter += 1
        notification = Notification(
            id=f"notif_{self._counter}",
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            priority=priority,
            data=data or {},
        )
        
        # Store notification
        if user_id not in self._notifications:
            self._notifications[user_id] = []
        self._notifications[user_id].append(notification)
        
        # Call handlers
        handlers = self._handlers.get(notification_type, [])
        for handler in handlers:
            try:
                await handler(notification)
            except Exception:
                pass  # Log error but continue
        
        return notification
    
    async def notify_tournament_start(
        self,
        user_id: str,
        tournament_name: str,
        tournament_id: str,
    ) -> Notification:
        """Notify user that tournament started."""
        return await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.TOURNAMENT_START,
            title="Tournament Started!",
            message=f"'{tournament_name}' has begun! Good luck!",
            priority=NotificationPriority.HIGH,
            data={"tournament_id": tournament_id, "tournament_name": tournament_name},
        )
    
    async def notify_tournament_end(
        self,
        user_id: str,
        tournament_name: str,
        rank: int,
        pnl: float,
    ) -> Notification:
        """Notify user that tournament ended."""
        result = "profit" if pnl > 0 else "loss"
        
        return await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.TOURNAMENT_END,
            title="Tournament Ended",
            message=f"'{tournament_name}' finished! You ranked #{rank} with a {result} of {abs(pnl):.2f} EUR",
            priority=NotificationPriority.HIGH,
            data={"rank": rank, "pnl": pnl},
        )
    
    async def notify_rank_change(
        self,
        user_id: str,
        old_rank: int,
        new_rank: int,
        tournament_name: str,
    ) -> Notification:
        """Notify user of rank change."""
        if new_rank < old_rank:  # Better rank (lower number)
            title = "Rank Improved!"
            message = f"You moved up from #{old_rank} to #{new_rank} in '{tournament_name}'!"
            priority = NotificationPriority.MEDIUM
        else:
            title = "Rank Update"
            message = f"Your rank changed from #{old_rank} to #{new_rank} in '{tournament_name}'"
            priority = NotificationPriority.LOW
        
        return await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.RANK_CHANGE,
            title=title,
            message=message,
            priority=priority,
            data={"old_rank": old_rank, "new_rank": new_rank},
        )
    
    async def notify_badge_earned(
        self,
        user_id: str,
        badge_name: str,
        badge_icon: str,
    ) -> Notification:
        """Notify user of badge earned."""
        return await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.BADGE_EARNED,
            title="Badge Earned!",
            message=f"Congratulations! You earned the '{badge_name}' badge!",
            priority=NotificationPriority.HIGH,
            data={"badge_name": badge_name, "badge_icon": badge_icon},
        )
    
    async def notify_tier_promotion(
        self,
        user_id: str,
        old_tier: str,
        new_tier: str,
    ) -> Notification:
        """Notify user of tier promotion."""
        return await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.TIER_PROMOTION,
            title="Promoted!",
            message=f"You've been promoted from {old_tier} to {new_tier}! Keep it up!",
            priority=NotificationPriority.URGENT,
            data={"old_tier": old_tier, "new_tier": new_tier},
        )
    
    async def notify_trade_filled(
        self,
        user_id: str,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        pnl: Optional[float] = None,
    ) -> Notification:
        """Notify user of trade fill."""
        message = f"{side.upper()} {quantity} {symbol} @ {price:.2f}"
        if pnl is not None:
            pnl_str = f"+{pnl:.2f}" if pnl > 0 else f"{pnl:.2f}"
            message += f" (P&L: {pnl_str} EUR)"
        
        return await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.TRADE_FILLED,
            title="Trade Filled",
            message=message,
            priority=NotificationPriority.MEDIUM,
            data={"symbol": symbol, "side": side, "quantity": quantity, "price": price, "pnl": pnl},
        )
    
    async def notify_strategy_forked(
        self,
        user_id: str,
        strategy_name: str,
        forker_name: str,
    ) -> Notification:
        """Notify user that their strategy was forked."""
        return await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.STRATEGY_FORKED,
            title="Strategy Forked",
            message=f"{forker_name} forked your strategy '{strategy_name}'!",
            priority=NotificationPriority.LOW,
            data={"strategy_name": strategy_name, "forker_name": forker_name},
        )
    
    def get_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50,
    ) -> List[Notification]:
        """Get notifications for a user."""
        notifications = self._notifications.get(user_id, [])
        
        if unread_only:
            notifications = [n for n in notifications if not n.read]
        
        # Sort by created_at desc
        notifications = sorted(notifications, key=lambda n: n.created_at, reverse=True)
        
        return notifications[:limit]
    
    def mark_as_read(self, user_id: str, notification_id: str) -> bool:
        """Mark notification as read."""
        notifications = self._notifications.get(user_id, [])
        for notif in notifications:
            if notif.id == notification_id:
                notif.read = True
                return True
        return False
    
    def mark_all_as_read(self, user_id: str) -> int:
        """Mark all notifications as read."""
        notifications = self._notifications.get(user_id, [])
        count = 0
        for notif in notifications:
            if not notif.read:
                notif.read = True
                count += 1
        return count
    
    def get_unread_count(self, user_id: str) -> int:
        """Get unread notification count."""
        notifications = self._notifications.get(user_id, [])
        return sum(1 for n in notifications if not n.read)
    
    def clear_old_notifications(self, days: int = 30) -> int:
        """Clear notifications older than specified days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        total_cleared = 0
        
        for user_id in self._notifications:
            original_count = len(self._notifications[user_id])
            self._notifications[user_id] = [
                n for n in self._notifications[user_id]
                if n.created_at > cutoff
            ]
            total_cleared += original_count - len(self._notifications[user_id])
        
        return total_cleared


# Global notification manager
notification_manager = NotificationManager()
