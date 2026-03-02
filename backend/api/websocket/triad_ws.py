"""
Triad WebSocket Endpoint

Real-time WebSocket endpoint voor Triad updates.
Verbindt Redis Streams met frontend WebSocket clients.
"""

import asyncio
import json
import logging

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from backend.events.triad_event_bus import TriadEventBus, get_event_bus

logger = logging.getLogger(__name__)


class TriadWebSocketManager:
    """Manager voor WebSocket verbindingen."""

    def __init__(self):
        self.active_connections: set[WebSocket] = set()
        self.event_bus: TriadEventBus = get_event_bus()
        self._broadcast_task = None
        self._running = False

    async def connect(self, websocket: WebSocket):
        """Accepteer nieuwe WebSocket verbinding."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")

        if self._broadcast_task is None or self._broadcast_task.done():
            self._running = True
            self._broadcast_task = asyncio.create_task(self._broadcast_loop())

    def disconnect(self, websocket: WebSocket):
        """Verwijder WebSocket verbinding."""
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

        if not self.active_connections and self._running:
            self._running = False

    async def broadcast(self, message: dict):
        """Broadcast bericht naar alle verbonden clients."""
        if not self.active_connections:
            return

        disconnected = set()

        for connection in self.active_connections:
            try:
                if connection.client_state == WebSocketState.CONNECTED:
                    await connection.send_json(message)
            except Exception as e:
                logger.error(f"Broadcast error: {e}")
                disconnected.add(connection)

        for conn in disconnected:
            self.disconnect(conn)

    async def _broadcast_loop(self):
        """Background task die events van Redis leest en broadcast."""
        try:
            streams = [
                self.event_bus.STREAM_DELIBERATIONS,
                self.event_bus.STREAM_DECISIONS,
                self.event_bus.STREAM_EXECUTIONS
            ]

            tasks = [
                asyncio.create_task(self._subscribe_and_broadcast(stream))
                for stream in streams
            ]

            await asyncio.gather(*tasks)

        except asyncio.CancelledError:
            logger.info("Broadcast loop cancelled")
        except Exception as e:
            logger.error(f"Broadcast loop error: {e}")

    async def _subscribe_and_broadcast(self, stream: str):
        """Subscribe to stream and broadcast events."""
        try:
            async for event in self.event_bus.subscribe(stream, block_ms=1000):
                if not self._running:
                    break

                await self.broadcast({
                    "type": stream.replace("triad.", ""),
                    "data": event
                })

        except Exception as e:
            logger.error(f"Subscription error for {stream}: {e}")


# Singleton
_ws_manager = None


def get_websocket_manager() -> TriadWebSocketManager:
    """Get WebSocket manager singleton."""
    global _ws_manager
    if _ws_manager is None:
        _ws_manager = TriadWebSocketManager()
    return _ws_manager


# FastAPI WebSocket endpoint
async def triad_websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint voor Triad real-time updates.

    Usage:
        const ws = new WebSocket('ws://localhost:8000/ws/triad');
        ws.onmessage = (event) => console.log(JSON.parse(event.data));
    """
    manager = get_websocket_manager()
    await manager.connect(websocket)

    try:
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to Triad WebSocket",
            "connections": len(manager.active_connections)
        })

        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("action") == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)
