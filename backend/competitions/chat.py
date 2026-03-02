"""Tournament chat system."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ChatMessageType(Enum):
    """Types of chat messages."""

    TEXT = "text"
    TRADE = "trade"
    SYSTEM = "system"
    BADGE = "badge"


@dataclass
class ChatMessage:
    """A chat message."""

    id: str
    tournament_id: str
    competitor_id: str
    competitor_name: str
    message: str
    type: ChatMessageType = ChatMessageType.TEXT
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tournament_id": self.tournament_id,
            "competitor_id": self.competitor_id,
            "competitor_name": self.competitor_name,
            "message": self.message,
            "type": self.type.value,
            "created_at": self.created_at.isoformat(),
        }


class TournamentChat:
    """
    Chat system for tournaments.

    Features:
    - Public chat for all participants
    - Trade notifications
    - System announcements
    - Message history
    """

    def __init__(self, tournament_id: str, max_history: int = 500):
        self.tournament_id = tournament_id
        self.messages: list[ChatMessage] = []
        self.max_history = max_history
        self._muted_users: set = set()
        self._message_count = 0

    def send_message(
        self,
        competitor_id: str,
        competitor_name: str,
        message: str,
        msg_type: ChatMessageType = ChatMessageType.TEXT,
    ) -> ChatMessage:
        """Send a chat message."""
        if competitor_id in self._muted_users:
            raise ValueError("User is muted")

        self._message_count += 1
        msg_id = f"{self.tournament_id}_{self._message_count}"

        chat_msg = ChatMessage(
            id=msg_id,
            tournament_id=self.tournament_id,
            competitor_id=competitor_id,
            competitor_name=competitor_name,
            message=message,
            type=msg_type,
        )

        self.messages.append(chat_msg)

        # Trim history if needed
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history :]

        return chat_msg

    def send_trade_notification(
        self,
        competitor_id: str,
        competitor_name: str,
        symbol: str,
        side: str,
        pnl: float | None,
    ) -> ChatMessage:
        """Send trade notification."""
        pnl_str = f" (+{pnl:.2f} EUR)" if pnl and pnl > 0 else f" ({pnl:.2f} EUR)" if pnl else ""
        message = f"{side.upper()} {symbol}{pnl_str}"

        return self.send_message(
            competitor_id=competitor_id,
            competitor_name=competitor_name,
            message=message,
            msg_type=ChatMessageType.TRADE,
        )

    def send_system_message(self, message: str) -> ChatMessage:
        """Send system announcement."""
        return self.send_message(
            competitor_id="system",
            competitor_name="System",
            message=message,
            msg_type=ChatMessageType.SYSTEM,
        )

    def send_badge_notification(
        self,
        competitor_id: str,
        competitor_name: str,
        badge_name: str,
    ) -> ChatMessage:
        """Send badge earned notification."""
        message = f"earned the {badge_name} badge!"

        return self.send_message(
            competitor_id=competitor_id,
            competitor_name=competitor_name,
            message=message,
            msg_type=ChatMessageType.BADGE,
        )

    def get_messages(
        self,
        limit: int = 50,
        before_id: str | None = None,
    ) -> list[ChatMessage]:
        """Get chat messages."""
        messages = self.messages

        if before_id:
            # Find index of before_id
            try:
                idx = next(i for i, m in enumerate(messages) if m.id == before_id)
                messages = messages[:idx]
            except StopIteration:
                pass

        return messages[-limit:]

    def mute_user(self, competitor_id: str) -> None:
        """Mute a user."""
        self._muted_users.add(competitor_id)

    def unmute_user(self, competitor_id: str) -> None:
        """Unmute a user."""
        self._muted_users.discard(competitor_id)

    def is_muted(self, competitor_id: str) -> bool:
        """Check if user is muted."""
        return competitor_id in self._muted_users

    def clear_chat(self) -> None:
        """Clear all messages."""
        self.messages = []


class ChatManager:
    """Manager for all tournament chats."""

    def __init__(self):
        self._chats: dict[str, TournamentChat] = {}

    def get_or_create_chat(self, tournament_id: str) -> TournamentChat:
        """Get existing chat or create new one."""
        if tournament_id not in self._chats:
            self._chats[tournament_id] = TournamentChat(tournament_id)
        return self._chats[tournament_id]

    def get_chat(self, tournament_id: str) -> TournamentChat | None:
        """Get chat for tournament."""
        return self._chats.get(tournament_id)

    def delete_chat(self, tournament_id: str) -> bool:
        """Delete chat for tournament."""
        if tournament_id in self._chats:
            del self._chats[tournament_id]
            return True
        return False

    def cleanup_empty_chats(self) -> int:
        """Remove chats with no recent activity."""
        # In real implementation, check last message timestamp
        # For now, keep all chats
        return 0


# Global chat manager
chat_manager = ChatManager()
