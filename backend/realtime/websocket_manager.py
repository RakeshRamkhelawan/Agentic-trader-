"""WebSocket manager for real-time competition updates."""

from datetime import datetime
from typing import Any

from fastapi import WebSocket


class TournamentStream:
    """Manages WebSocket connections for a single tournament."""

    def __init__(self, tournament_id: str):
        self.tournament_id = tournament_id
        self.connections: set[WebSocket] = set()
        self.message_history: list[dict] = []
        self.max_history = 100

    async def connect(self, websocket: WebSocket) -> None:
        """Accept new WebSocket connection."""
        await websocket.accept()
        self.connections.add(websocket)

        # Send recent history
        if self.message_history:
            await websocket.send_json({
                "type": "history",
                "data": self.message_history[-20:],  # Last 20 messages
            })

    def disconnect(self, websocket: WebSocket) -> None:
        """Remove WebSocket connection."""
        self.connections.discard(websocket)

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast message to all connected clients."""
        # Add timestamp
        message["timestamp"] = datetime.utcnow().isoformat()

        # Store in history
        self.message_history.append(message)
        if len(self.message_history) > self.max_history:
            self.message_history = self.message_history[-self.max_history:]

        # Broadcast to all connections
        disconnected = set()
        for conn in self.connections:
            try:
                await conn.send_json(message)
            except Exception:
                disconnected.add(conn)

        # Clean up disconnected
        for conn in disconnected:
            self.connections.discard(conn)

    async def send_leaderboard_update(self, leaderboard: list[dict]) -> None:
        """Send leaderboard update."""
        await self.broadcast({
            "type": "leaderboard_update",
            "tournament_id": self.tournament_id,
            "leaderboard": leaderboard,
        })

    async def send_trade_notification(self, competitor_id: str, trade: dict) -> None:
        """Send trade notification."""
        await self.broadcast({
            "type": "trade",
            "tournament_id": self.tournament_id,
            "competitor_id": competitor_id,
            "trade": trade,
        })

    async def send_chat_message(self, competitor_id: str, name: str, message: str) -> None:
        """Send chat message."""
        await self.broadcast({
            "type": "chat",
            "tournament_id": self.tournament_id,
            "competitor_id": competitor_id,
            "name": name,
            "message": message,
        })

    async def send_price_tick(self, symbol: str, price: float, change: float) -> None:
        """Send price tick update."""
        await self.broadcast({
            "type": "price_tick",
            "tournament_id": self.tournament_id,
            "symbol": symbol,
            "price": price,
            "change": change,
        })

    async def send_system_message(self, message: str) -> None:
        """Send system announcement."""
        await self.broadcast({
            "type": "system",
            "tournament_id": self.tournament_id,
            "message": message,
        })

    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.connections)


class WebSocketManager:
    """
    Central WebSocket manager for all tournament streams.

    Routes:
    - /ws/tournament/{id} - Tournament live updates
    - /ws/global - Global leaderboard updates
    - /ws/user/{id} - Personal notifications
    """

    def __init__(self):
        self._tournament_streams: dict[str, TournamentStream] = {}
        self._global_connections: set[WebSocket] = set()
        self._user_connections: dict[str, WebSocket] = {}

    def get_or_create_stream(self, tournament_id: str) -> TournamentStream:
        """Get existing stream or create new one."""
        if tournament_id not in self._tournament_streams:
            self._tournament_streams[tournament_id] = TournamentStream(tournament_id)
        return self._tournament_streams[tournament_id]

    async def connect_tournament(self, websocket: WebSocket, tournament_id: str) -> None:
        """Connect to tournament stream."""
        stream = self.get_or_create_stream(tournament_id)
        await stream.connect(websocket)

    def disconnect_tournament(self, websocket: WebSocket, tournament_id: str) -> None:
        """Disconnect from tournament stream."""
        if tournament_id in self._tournament_streams:
            self._tournament_streams[tournament_id].disconnect(websocket)

    async def connect_global(self, websocket: WebSocket) -> None:
        """Connect to global updates."""
        await websocket.accept()
        self._global_connections.add(websocket)

    def disconnect_global(self, websocket: WebSocket) -> None:
        """Disconnect from global updates."""
        self._global_connections.discard(websocket)

    async def connect_user(self, websocket: WebSocket, user_id: str) -> None:
        """Connect to personal notifications."""
        await websocket.accept()
        self._user_connections[user_id] = websocket

    def disconnect_user(self, user_id: str) -> None:
        """Disconnect user notifications."""
        if user_id in self._user_connections:
            del self._user_connections[user_id]

    async def broadcast_leaderboard_update(
        self,
        tournament_id: str,
        leaderboard: list[dict],
    ) -> None:
        """Broadcast leaderboard update to tournament viewers."""
        stream = self._tournament_streams.get(tournament_id)
        if stream:
            await stream.send_leaderboard_update(leaderboard)

    async def broadcast_trade(
        self,
        tournament_id: str,
        competitor_id: str,
        trade: dict,
    ) -> None:
        """Broadcast trade to tournament viewers."""
        stream = self._tournament_streams.get(tournament_id)
        if stream:
            await stream.send_trade_notification(competitor_id, trade)

    async def broadcast_chat(
        self,
        tournament_id: str,
        competitor_id: str,
        name: str,
        message: str,
    ) -> None:
        """Broadcast chat message."""
        stream = self._tournament_streams.get(tournament_id)
        if stream:
            await stream.send_chat_message(competitor_id, name, message)

    async def broadcast_global_leaderboard(self, leaderboard: list[dict]) -> None:
        """Broadcast global leaderboard update."""
        message = {
            "type": "global_leaderboard_update",
            "leaderboard": leaderboard,
            "timestamp": datetime.utcnow().isoformat(),
        }

        disconnected = set()
        for conn in self._global_connections:
            try:
                await conn.send_json(message)
            except Exception:
                disconnected.add(conn)

        for conn in disconnected:
            self._global_connections.discard(conn)

    async def send_notification(self, user_id: str, notification: dict) -> None:
        """Send personal notification."""
        conn = self._user_connections.get(user_id)
        if conn:
            try:
                await conn.send_json({
                    "type": "notification",
                    "data": notification,
                    "timestamp": datetime.utcnow().isoformat(),
                })
            except Exception:
                self.disconnect_user(user_id)

    async def broadcast_system_message(self, tournament_id: str, message: str) -> None:
        """Send system message to tournament."""
        stream = self._tournament_streams.get(tournament_id)
        if stream:
            await stream.send_system_message(message)

    def get_active_streams(self) -> dict[str, int]:
        """Get count of active connections per tournament."""
        return {
            tid: stream.get_connection_count()
            for tid, stream in self._tournament_streams.items()
        }

    def cleanup_inactive_streams(self) -> None:
        """Remove streams with no connections."""
        inactive = [
            tid for tid, stream in self._tournament_streams.items()
            if stream.get_connection_count() == 0
        ]
        for tid in inactive:
            del self._tournament_streams[tid]


# Global WebSocket manager instance
websocket_manager = WebSocketManager()
