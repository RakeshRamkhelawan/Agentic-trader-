"""Event publisher for real-time competition events."""

from datetime import datetime
from enum import Enum
from typing import Any

from .websocket_manager import websocket_manager


class EventType(Enum):
    """Types of real-time events."""
    TOURNAMENT_STARTED = "tournament_started"
    TOURNAMENT_ENDED = "tournament_ended"
    LEADERBOARD_UPDATE = "leaderboard_update"
    TRADE_EXECUTED = "trade_executed"
    POSITION_CHANGED = "position_changed"
    COMPETITOR_JOINED = "competitor_joined"
    COMPETITOR_LEFT = "competitor_left"
    CHAT_MESSAGE = "chat_message"
    PRICE_ALERT = "price_alert"
    BADGE_EARNED = "badge_earned"
    TIER_PROMOTION = "tier_promotion"


class EventPublisher:
    """
    Publishes events to WebSocket streams and other subscribers.

    Decouples competition logic from real-time delivery.
    """

    def __init__(self):
        self._subscribers: dict[EventType, list] = {}

    def subscribe(self, event_type: EventType, callback) -> None:
        """Subscribe to event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: EventType, callback) -> None:
        """Unsubscribe from event type."""
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                cb for cb in self._subscribers[event_type]
                if cb != callback
            ]

    async def publish(self, event_type: EventType, data: dict[str, Any]) -> None:
        """Publish event to all subscribers."""
        event = {
            "type": event_type.value,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Call registered subscribers
        callbacks = self._subscribers.get(event_type, [])
        for callback in callbacks:
            try:
                await callback(event)
            except Exception:
                pass  # Log error but don't stop other subscribers

    async def publish_tournament_started(self, tournament_id: str, name: str) -> None:
        """Publish tournament started event."""
        await self.publish(EventType.TOURNAMENT_STARTED, {
            "tournament_id": tournament_id,
            "name": name,
        })

        # Also send via WebSocket
        await websocket_manager.broadcast_system_message(
            tournament_id,
            f"Tournament '{name}' has started! Good luck!"
        )

    async def publish_tournament_ended(
        self,
        tournament_id: str,
        name: str,
        winners: list,
    ) -> None:
        """Publish tournament ended event."""
        await self.publish(EventType.TOURNAMENT_ENDED, {
            "tournament_id": tournament_id,
            "name": name,
            "winners": winners,
        })

        # WebSocket announcement
        winner_names = ", ".join([w.get("name", "Unknown") for w in winners[:3]])
        await websocket_manager.broadcast_system_message(
            tournament_id,
            f"Tournament ended! Winners: {winner_names}"
        )

    async def publish_leaderboard_update(
        self,
        tournament_id: str,
        leaderboard: list,
    ) -> None:
        """Publish leaderboard update."""
        await self.publish(EventType.LEADERBOARD_UPDATE, {
            "tournament_id": tournament_id,
            "leaderboard": leaderboard,
        })

        # WebSocket broadcast
        await websocket_manager.broadcast_leaderboard_update(
            tournament_id,
            leaderboard,
        )

    async def publish_trade(
        self,
        tournament_id: str,
        competitor_id: str,
        competitor_name: str,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        pnl: float | None = None,
    ) -> None:
        """Publish trade execution."""
        trade_data = {
            "tournament_id": tournament_id,
            "competitor_id": competitor_id,
            "competitor_name": competitor_name,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": price,
            "pnl": pnl,
        }

        await self.publish(EventType.TRADE_EXECUTED, trade_data)
        await websocket_manager.broadcast_trade(tournament_id, competitor_id, trade_data)

    async def publish_chat(
        self,
        tournament_id: str,
        competitor_id: str,
        competitor_name: str,
        message: str,
    ) -> None:
        """Publish chat message."""
        await self.publish(EventType.CHAT_MESSAGE, {
            "tournament_id": tournament_id,
            "competitor_id": competitor_id,
            "competitor_name": competitor_name,
            "message": message,
        })

        await websocket_manager.broadcast_chat(
            tournament_id,
            competitor_id,
            competitor_name,
            message,
        )

    async def publish_badge_earned(
        self,
        user_id: str,
        badge_name: str,
        badge_icon: str,
    ) -> None:
        """Publish badge earned notification."""
        notification = {
            "title": "Badge Earned!",
            "message": f"You earned the {badge_name} badge!",
            "icon": badge_icon,
            "type": "badge",
        }

        await self.publish(EventType.BADGE_EARNED, {
            "user_id": user_id,
            "badge_name": badge_name,
        })

        await websocket_manager.send_notification(user_id, notification)

    async def publish_tier_promotion(
        self,
        user_id: str,
        old_tier: str,
        new_tier: str,
    ) -> None:
        """Publish tier promotion."""
        notification = {
            "title": "Promotion!",
            "message": f"Promoted from {old_tier} to {new_tier}!",
            "icon": "trending_up",
            "type": "promotion",
        }

        await self.publish(EventType.TIER_PROMOTION, {
            "user_id": user_id,
            "old_tier": old_tier,
            "new_tier": new_tier,
        })

        await websocket_manager.send_notification(user_id, notification)


# Global event publisher instance
event_publisher = EventPublisher()
