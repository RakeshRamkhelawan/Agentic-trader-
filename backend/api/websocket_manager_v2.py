"""
WebSocket Manager v2 - Improved Reliability & Observability

Implements ADR-003: WebSocket Reliability & Backpressure
- Heartbeat with timeout detection
- Per-connection bounded queues for backpressure
- Prometheus metrics integration
- Message prioritization
- Automatic reconnect signaling

Author: Architecture Team
Date: 2026-02-20
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Set

from fastapi import WebSocket

# Import metrics if available
try:
    from backend.observability.ws_metrics import ws_metrics

    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    ws_metrics = None

logger = logging.getLogger(__name__)


@dataclass
class ConnectionState:
    """Enhanced connection state with queue and metrics."""

    websocket: WebSocket
    connection_id: str
    tenant_id: str
    account_id: str
    user_id: Optional[str] = None

    # Subscriptions
    subscriptions: Set[str] = field(default_factory=set)

    # Timing
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_pong: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)

    # Backpressure: bounded queue per connection
    # (priority, message) - high priority = 0, low priority = 1
    message_queue: asyncio.Queue = field(
        default_factory=lambda: asyncio.Queue(maxsize=1000)
    )

    # Sequence tracking per stream
    stream_sequences: Dict[str, int] = field(default_factory=dict)

    # Metrics
    messages_sent: int = 0
    messages_dropped: int = 0

    @property
    def is_stale(self, timeout_seconds: float = 90.0) -> bool:
        """Check if connection hasn't responded to pings."""
        return (time.time() - self.last_pong) > timeout_seconds

    @property
    def queue_depth(self) -> int:
        """Current queue size."""
        return self.message_queue.qsize()


class WebSocketManagerV2:
    """
    Enhanced WebSocket Manager with reliability features.

    Features:
    - Heartbeat with automatic stale connection cleanup
    - Per-connection bounded queues (backpressure)
    - Message prioritization (high/low)
    - Prometheus metrics integration
    - Sequence numbers for ordering detection
    - Automatic resync signaling
    """

    def __init__(self, heartbeat_interval: float = 30.0, stale_timeout: float = 90.0):
        self.connections: Dict[str, ConnectionState] = {}
        self.channel_subscribers: Dict[str, Set[str]] = {}
        self._lock = asyncio.Lock()

        # Configuration
        self.heartbeat_interval = heartbeat_interval
        self.stale_timeout = stale_timeout
        self.max_queue_size = 1000

        # Tasks
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._processor_tasks: Set[asyncio.Task] = set()

        # Global sequence counters per stream
        self._stream_sequences: Dict[str, int] = {}

        # Metrics
        self._metrics_enabled = METRICS_AVAILABLE and ws_metrics is not None

        logger.info(
            f"WebSocketManagerV2 initialized (metrics={'enabled' if self._metrics_enabled else 'disabled'})"
        )

    async def connect(
        self,
        websocket: WebSocket,
        tenant_id: str = "default",
        account_id: str = "default",
        user_id: Optional[str] = None,
    ) -> str:
        """
        Accept a new WebSocket connection with full initialization.

        Args:
            websocket: FastAPI WebSocket object
            tenant_id: Tenant identifier for multi-tenancy
            account_id: Account identifier
            user_id: Optional user identifier

        Returns:
            connection_id: Unique connection identifier
        """
        connection_id = str(uuid.uuid4())

        await websocket.accept()

        async with self._lock:
            conn = ConnectionState(
                websocket=websocket,
                connection_id=connection_id,
                tenant_id=tenant_id,
                account_id=account_id,
                user_id=user_id,
            )
            self.connections[connection_id] = conn

        # Start message processor for this connection
        processor_task = asyncio.create_task(
            self._process_connection_messages(connection_id),
            name=f"ws_processor_{connection_id}",
        )
        self._processor_tasks.add(processor_task)
        processor_task.add_done_callback(self._processor_tasks.discard)

        # Record metrics
        if self._metrics_enabled:
            ws_metrics.connections.inc()
            ws_metrics.connect_rate.labels(status="success").inc()

        logger.info(
            f"WebSocket connected: {connection_id} "
            f"(tenant={tenant_id}, account={account_id}, user={user_id})"
        )

        # Send connection confirmation with protocol version
        await self._send_immediate(
            connection_id,
            {
                "type": "connected",
                "connection_id": connection_id,
                "protocol_version": "2.0",
                "timestamp": datetime.utcnow().isoformat(),
                "capabilities": ["heartbeat", "backpressure", "priorities", "resync"],
            },
        )

        return connection_id

    async def disconnect(
        self, connection_id: str, reason: str = "client_disconnect"
    ) -> None:
        """Disconnect a connection with cleanup."""
        async with self._lock:
            if connection_id not in self.connections:
                return

            conn = self.connections[connection_id]

            # Unsubscribe from all channels
            for channel in list(conn.subscriptions):
                await self._unsubscribe_internal(connection_id, channel)

            # Remove connection
            del self.connections[connection_id]

        # Record metrics
        if self._metrics_enabled:
            ws_metrics.connections.dec()
            ws_metrics.disconnect_reason.labels(reason=reason).inc()

        logger.info(f"WebSocket disconnected: {connection_id} (reason={reason})")

    async def subscribe(self, connection_id: str, channel: str) -> bool:
        """Subscribe a connection to a channel."""
        async with self._lock:
            if connection_id not in self.connections:
                return False

            conn = self.connections[connection_id]

            # Apply tenant isolation for sensitive channels
            if channel == "orders":
                channel = f"orders.{conn.account_id}"
            elif channel.startswith("portfolio"):
                channel = f"portfolio.{conn.account_id}"

            conn.subscriptions.add(channel)

            if channel not in self.channel_subscribers:
                self.channel_subscribers[channel] = set()
            self.channel_subscribers[channel].add(connection_id)

        logger.debug(f"Connection {connection_id} subscribed to {channel}")

        # Send confirmation
        await self._send_immediate(
            connection_id,
            {
                "type": "subscribed",
                "channel": channel,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

        return True

    async def unsubscribe(self, connection_id: str, channel: str) -> bool:
        """Unsubscribe a connection from a channel."""
        async with self._lock:
            return await self._unsubscribe_internal(connection_id, channel)

    async def _unsubscribe_internal(self, connection_id: str, channel: str) -> bool:
        """Internal unsubscribe without lock."""
        if connection_id not in self.connections:
            return False

        conn = self.connections[connection_id]

        # Handle isolated channels
        if channel == "orders":
            channel = f"orders.{conn.account_id}"
        elif channel.startswith("portfolio"):
            channel = f"portfolio.{conn.account_id}"

        conn.subscriptions.discard(channel)

        if channel in self.channel_subscribers:
            self.channel_subscribers[channel].discard(connection_id)
            if not self.channel_subscribers[channel]:
                del self.channel_subscribers[channel]

        logger.debug(f"Connection {connection_id} unsubscribed from {channel}")
        return True

    async def broadcast(
        self,
        stream: str,
        data: Dict[str, Any],
        priority: str = "low",
        message_type: str = "update",
    ) -> Dict[str, int]:
        """
        Broadcast a message to all subscribers of a stream.

        Args:
            stream: Channel/stream name
            data: Message payload
            priority: "high" (fills, errors) or "low" (ticks)
            message_type: Event type

        Returns:
            Stats: {"sent": int, "dropped": int, "queued": int}
        """
        stats = {"sent": 0, "dropped": 0, "queued": 0}

        # Generate sequence number for this stream
        seq = self._get_next_sequence(stream)

        # Build message envelope
        message = {
            "type": message_type,
            "stream": stream,
            "ts": datetime.utcnow().isoformat(),
            "seq": seq,
            "priority": priority,
            "data": data,
        }

        # Priority: high=0, low=1
        priority_val = 0 if priority == "high" else 1

        async with self._lock:
            subscribers = list(self.channel_subscribers.get(stream, set()))

        for connection_id in subscribers:
            queued = await self._queue_message(connection_id, priority_val, message)
            if queued:
                stats["queued"] += 1
            else:
                stats["dropped"] += 1
                if priority == "high":
                    # Signal resync for dropped high-priority messages
                    asyncio.create_task(self._signal_resync(connection_id))

        # Record metrics
        if self._metrics_enabled:
            ws_metrics.messages_sent.labels(stream=stream, priority=priority).inc(
                stats["queued"]
            )
            ws_metrics.messages_dropped.labels(stream=stream).inc(stats["dropped"])

        return stats

    async def _queue_message(
        self, connection_id: str, priority: int, message: Dict
    ) -> bool:
        """Queue a message for a connection (with backpressure)."""
        if connection_id not in self.connections:
            return False

        conn = self.connections[connection_id]

        try:
            conn.message_queue.put_nowait((priority, message))
            return True
        except asyncio.QueueFull:
            conn.messages_dropped += 1
            logger.warning(
                f"Queue full for {connection_id} (depth={conn.queue_depth}), "
                f"dropping {message['type']} message"
            )
            return False

    async def _process_connection_messages(self, connection_id: str) -> None:
        """Process queued messages for a single connection."""
        while True:
            try:
                if connection_id not in self.connections:
                    break

                conn = self.connections[connection_id]

                # Wait for message with timeout
                try:
                    priority, message = await asyncio.wait_for(
                        conn.message_queue.get(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                # Send message
                try:
                    await conn.websocket.send_json(message)
                    conn.messages_sent += 1
                    conn.last_activity = time.time()
                except Exception as e:
                    logger.warning(f"Failed to send to {connection_id}: {e}")
                    await self.disconnect(connection_id, reason="send_error")
                    break

            except Exception as e:
                logger.error(f"Message processor error for {connection_id}: {e}")
                break

    async def _send_immediate(
        self, connection_id: str, message: Dict[str, Any]
    ) -> bool:
        """Send a message immediately (bypass queue for control messages)."""
        if connection_id not in self.connections:
            return False

        try:
            await self.connections[connection_id].websocket.send_json(message)
            return True
        except Exception as e:
            logger.warning(f"Failed to send immediate message to {connection_id}: {e}")
            return False

    async def handle_client_message(
        self, connection_id: str, message: Dict[str, Any]
    ) -> None:
        """Handle incoming message from client."""
        if connection_id not in self.connections:
            return

        conn = self.connections[connection_id]
        msg_type = message.get("type")

        # Update activity timestamp
        conn.last_activity = time.time()

        if msg_type == "subscribe":
            streams = message.get("streams", [message.get("channel")])
            for stream in streams:
                if stream:
                    await self.subscribe(connection_id, stream)

        elif msg_type == "unsubscribe":
            streams = message.get("streams", [message.get("channel")])
            for stream in streams:
                if stream:
                    await self.unsubscribe(connection_id, stream)

        elif msg_type == "pong":
            # Client responded to our ping
            conn.last_pong = time.time()
            logger.debug(f"Received pong from {connection_id}")

        elif msg_type == "ping":
            # Client pinged us
            await self._send_immediate(
                connection_id, {"type": "pong", "ts": datetime.utcnow().isoformat()}
            )

    async def start_heartbeat(self) -> None:
        """Start the heartbeat monitoring task."""
        if self._heartbeat_task is not None:
            return

        async def heartbeat_loop():
            while True:
                await asyncio.sleep(self.heartbeat_interval)
                await self._send_pings()
                await self._check_stale_connections()

        self._heartbeat_task = asyncio.create_task(
            heartbeat_loop(), name="ws_heartbeat"
        )
        logger.info(f"Heartbeat started (interval={self.heartbeat_interval}s)")

    async def stop_heartbeat(self) -> None:
        """Stop the heartbeat task."""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None
            logger.info("Heartbeat stopped")

    async def _send_pings(self) -> None:
        """Send ping messages to all connections."""
        ping_message = {"type": "ping", "ts": datetime.utcnow().isoformat()}

        for connection_id in list(self.connections.keys()):
            await self._send_immediate(connection_id, ping_message)

    async def _check_stale_connections(self) -> None:
        """Disconnect connections that haven't responded to pings."""
        stale_connections = []

        for conn_id, conn in self.connections.items():
            if conn.is_stale(self.stale_timeout):
                stale_connections.append(conn_id)

        for conn_id in stale_connections:
            logger.warning(f"Stale connection detected: {conn_id}")
            await self.disconnect(conn_id, reason="heartbeat_timeout")

    async def _signal_resync(self, connection_id: str) -> None:
        """Signal client that resync is required."""
        await self._send_immediate(
            connection_id,
            {
                "type": "resync_required",
                "reason": "high_priority_drop",
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    def _get_next_sequence(self, stream: str) -> int:
        """Get next sequence number for a stream."""
        seq = self._stream_sequences.get(stream, 0) + 1
        self._stream_sequences[stream] = seq
        return seq

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        total_queued = sum(conn.queue_depth for conn in self.connections.values())
        total_dropped = sum(conn.messages_dropped for conn in self.connections.values())
        total_sent = sum(conn.messages_sent for conn in self.connections.values())

        return {
            "total_connections": len(self.connections),
            "total_channels": len(self.channel_subscribers),
            "total_queued_messages": total_queued,
            "total_messages_sent": total_sent,
            "total_messages_dropped": total_dropped,
            "connections": {
                conn_id: {
                    "tenant_id": conn.tenant_id,
                    "account_id": conn.account_id,
                    "subscriptions": list(conn.subscriptions),
                    "queue_depth": conn.queue_depth,
                    "connected_at": conn.connected_at.isoformat(),
                    "last_pong": conn.last_pong,
                    "messages_sent": conn.messages_sent,
                    "messages_dropped": conn.messages_dropped,
                    "is_stale": conn.is_stale(self.stale_timeout),
                }
                for conn_id, conn in self.connections.items()
            },
            "channels": {
                channel: len(subscribers)
                for channel, subscribers in self.channel_subscribers.items()
            },
        }


# Global instance
ws_manager_v2 = WebSocketManagerV2()
