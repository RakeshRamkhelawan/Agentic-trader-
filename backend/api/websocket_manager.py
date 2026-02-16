"""
WebSocket Manager for real-time trading data.

Features:
- Connection management with heartbeat
- Channel-based subscriptions (orderbook, ticker, orders)
- Multi-tenant isolation
- Broadcast to subscribers
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Set

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


@dataclass
class Connection:
    """Represents a WebSocket connection with its subscriptions."""

    websocket: WebSocket
    tenant_id: str
    account_id: str
    subscriptions: Set[str] = field(default_factory=set)
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_ping: datetime = field(default_factory=datetime.utcnow)


class WebSocketManager:
    """
    Manages WebSocket connections and message routing.

    Channels:
    - orderbook.{symbol}: Orderbook updates for a symbol
    - ticker.{symbol}: Ticker updates for a symbol
    - orders: Order updates for the connected user
    """

    def __init__(self):
        # Map of connection_id -> Connection
        self.connections: Dict[str, Connection] = {}
        # Map of channel -> set of connection_ids
        self.channel_subscribers: Dict[str, Set[str]] = {}
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
        # Heartbeat task
        self._heartbeat_task: Optional[asyncio.Task] = None

    async def connect(
        self, websocket: WebSocket, connection_id: str, tenant_id: str, account_id: str
    ) -> None:
        """Accept a new WebSocket connection."""
        await websocket.accept()

        async with self._lock:
            self.connections[connection_id] = Connection(
                websocket=websocket, tenant_id=tenant_id, account_id=account_id
            )

        logger.info(f"WebSocket connected: {connection_id} (tenant: {tenant_id})")

        # Send connection confirmation
        await self.send_message(
            connection_id,
            {
                "type": "connected",
                "connection_id": connection_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def disconnect(self, connection_id: str) -> None:
        """Remove a WebSocket connection."""
        async with self._lock:
            if connection_id in self.connections:
                conn = self.connections[connection_id]

                # Remove from all subscribed channels
                for channel in conn.subscriptions:
                    if channel in self.channel_subscribers:
                        self.channel_subscribers[channel].discard(connection_id)
                        if not self.channel_subscribers[channel]:
                            del self.channel_subscribers[channel]

                del self.connections[connection_id]
                logger.info(f"WebSocket disconnected: {connection_id}")

    async def subscribe(self, connection_id: str, channel: str) -> bool:
        """Subscribe a connection to a channel."""
        async with self._lock:
            if connection_id not in self.connections:
                return False

            conn = self.connections[connection_id]

            # Check tenant isolation for order channels
            if channel == "orders":
                # Orders channel is per-user, append account_id
                channel = f"orders.{conn.account_id}"

            conn.subscriptions.add(channel)

            if channel not in self.channel_subscribers:
                self.channel_subscribers[channel] = set()
            self.channel_subscribers[channel].add(connection_id)

            logger.debug(f"Connection {connection_id} subscribed to {channel}")
            return True

    async def unsubscribe(self, connection_id: str, channel: str) -> bool:
        """Unsubscribe a connection from a channel."""
        async with self._lock:
            if connection_id not in self.connections:
                return False

            conn = self.connections[connection_id]

            # Handle orders channel
            if channel == "orders":
                channel = f"orders.{conn.account_id}"

            conn.subscriptions.discard(channel)

            if channel in self.channel_subscribers:
                self.channel_subscribers[channel].discard(connection_id)
                if not self.channel_subscribers[channel]:
                    del self.channel_subscribers[channel]

            logger.debug(f"Connection {connection_id} unsubscribed from {channel}")
            return True

    async def send_message(self, connection_id: str, message: Dict[str, Any]) -> bool:
        """Send a message to a specific connection."""
        if connection_id not in self.connections:
            return False

        conn = self.connections[connection_id]
        try:
            await conn.websocket.send_json(message)
            return True
        except Exception as e:
            logger.warning(f"Failed to send message to {connection_id}: {e}")
            await self.disconnect(connection_id)
            return False

    async def broadcast_to_channel(
        self, channel: str, message: Dict[str, Any], message_type: str = "update"
    ) -> int:
        """Broadcast a message to all subscribers of a channel."""
        if channel not in self.channel_subscribers:
            return 0

        # Add channel and type to message
        full_message = {
            "channel": channel,
            "type": message_type,
            "data": message,
            "timestamp": datetime.utcnow().isoformat(),
        }

        subscribers = list(self.channel_subscribers.get(channel, []))
        sent_count = 0

        for connection_id in subscribers:
            if await self.send_message(connection_id, full_message):
                sent_count += 1

        return sent_count

    async def broadcast_orderbook(
        self, symbol: str, bids: list, asks: list, is_snapshot: bool = False
    ) -> int:
        """Broadcast orderbook update to subscribers."""
        channel = f"orderbook.{symbol}"
        return await self.broadcast_to_channel(
            channel,
            {"bids": bids, "asks": asks},
            message_type="snapshot" if is_snapshot else "delta",
        )

    async def broadcast_ticker(
        self,
        symbol: str,
        bid: float,
        ask: float,
        last: float,
        volume_24h: float,
        change_24h: float,
        change_percent_24h: float,
        high_24h: float,
        low_24h: float,
    ) -> int:
        """Broadcast ticker update to subscribers."""
        channel = f"ticker.{symbol}"
        return await self.broadcast_to_channel(
            channel,
            {
                "symbol": symbol,
                "bid": bid,
                "ask": ask,
                "last": last,
                "volume_24h": volume_24h,
                "change_24h": change_24h,
                "change_percent_24h": change_percent_24h,
                "high_24h": high_24h,
                "low_24h": low_24h,
                "timestamp": datetime.utcnow().isoformat(),
            },
            message_type="update",
        )

    async def broadcast_order_update(
        self, account_id: str, order_data: Dict[str, Any]
    ) -> int:
        """Broadcast order update to a specific user."""
        channel = f"orders.{account_id}"
        return await self.broadcast_to_channel(
            channel, order_data, message_type="update"
        )

    async def handle_client_message(
        self, connection_id: str, message: Dict[str, Any]
    ) -> None:
        """Handle incoming message from a client."""
        msg_type = message.get("type")

        if msg_type == "subscribe":
            channel = message.get("channel")
            if channel:
                success = await self.subscribe(connection_id, channel)

                # Send initial snapshot for orderbook channels
                if success and channel.startswith("orderbook."):
                    symbol = channel.split(".")[1]
                    # TODO: Fetch current orderbook from exchange
                    # For now, send empty snapshot
                    await self.send_message(
                        connection_id,
                        {
                            "channel": channel,
                            "type": "snapshot",
                            "data": {"bids": [], "asks": []},
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    )

        elif msg_type == "unsubscribe":
            channel = message.get("channel")
            if channel:
                await self.unsubscribe(connection_id, channel)

        elif msg_type == "ping":
            # Update last ping time
            if connection_id in self.connections:
                self.connections[connection_id].last_ping = datetime.utcnow()
            await self.send_message(connection_id, {"type": "pong"})

    async def start_heartbeat(self, interval_seconds: int = 30) -> None:
        """Start heartbeat monitoring for stale connections."""

        async def heartbeat_loop():
            while True:
                await asyncio.sleep(interval_seconds)
                await self._check_stale_connections()

        self._heartbeat_task = asyncio.create_task(heartbeat_loop())

    async def _check_stale_connections(self, timeout_seconds: int = 90) -> None:
        """Disconnect stale connections that haven't sent a ping."""
        now = datetime.utcnow()
        stale_connections = []

        for conn_id, conn in list(self.connections.items()):
            if (now - conn.last_ping).total_seconds() > timeout_seconds:
                stale_connections.append(conn_id)

        for conn_id in stale_connections:
            logger.info(f"Disconnecting stale connection: {conn_id}")
            await self.disconnect(conn_id)

    async def broadcast_navagraha_update(self, state: Dict[str, Any]) -> int:
        """Broadcast Navagraha state update."""
        return await self.broadcast_to_channel(
            "navagraha.updates",
            state,
            message_type="update",
        )

    async def broadcast_ooda_update(self, cycle_state: Dict[str, Any]) -> int:
        """Broadcast OODA Cycle state update."""
        return await self.broadcast_to_channel(
            "ooda.updates",
            cycle_state,
            message_type="update",
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket manager statistics."""
        return {
            "total_connections": len(self.connections),
            "total_channels": len(self.channel_subscribers),
            "channels": {
                channel: len(subscribers)
                for channel, subscribers in self.channel_subscribers.items()
            },
        }


# Global WebSocket manager singleton
ws_manager = WebSocketManager()
