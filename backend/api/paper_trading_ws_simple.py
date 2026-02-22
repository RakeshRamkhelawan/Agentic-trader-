"""
Simplified WebSocket for Live Paper Trading
"""

import asyncio
import json
import logging
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter()

# Store connected clients
connected_clients = set()


@router.websocket("/ws/paper-trading")
async def paper_trading_websocket(websocket: WebSocket):
    """Simple WebSocket endpoint for paper trading with Vedic context."""
    await websocket.accept()
    connected_clients.add(websocket)
    client_id = id(websocket)

    logger.info(f"Paper trading client connected: {client_id}")

    # Import ws_manager voor channel subscription
    from backend.api.websocket_manager import ws_manager

    # Registreer client bij alle paper trading channels
    connection_id = f"paper_{client_id}"
    await ws_manager.connect(websocket, connection_id)
    await ws_manager.subscribe(connection_id, "paper_trading.live")
    await ws_manager.subscribe(connection_id, "paper_trading.stats")
    await ws_manager.subscribe(connection_id, "paper_trading.agents")
    await ws_manager.subscribe(connection_id, "paper_trading.vedic")  # NIEUW

    try:
        # Send initial connection message
        await websocket.send_json(
            {
                "type": "connected",
                "message": "Paper trading WebSocket connected",
                "channels": [
                    "paper_trading.live",
                    "paper_trading.stats",
                    "paper_trading.agents",
                    "paper_trading.vedic",
                ],
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for messages with timeout
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)

                # Echo back for ping/pong
                try:
                    msg = json.loads(data)
                    if msg.get("type") == "ping":
                        await websocket.send_json({"type": "pong"})
                except:
                    pass

            except asyncio.TimeoutError:
                # Send keepalive
                await websocket.send_json(
                    {"type": "keepalive", "timestamp": datetime.utcnow().isoformat()}
                )

    except WebSocketDisconnect:
        logger.info(f"Client disconnected: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        connected_clients.discard(websocket)
        # Cleanup channel subscriptions
        try:
            from backend.api.websocket_manager import ws_manager

            await ws_manager.disconnect(connection_id)
        except:
            pass


async def broadcast_to_clients(message: dict):
    """Broadcast message to all connected clients."""
    disconnected = set()

    for client in connected_clients:
        try:
            await client.send_json(message)
        except:
            disconnected.add(client)

    # Clean up disconnected clients
    for client in disconnected:
        connected_clients.discard(client)
