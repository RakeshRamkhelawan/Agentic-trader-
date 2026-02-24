"""
WebSocket endpoints for Live Paper Trading
"""

import asyncio
import logging
import uuid

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from backend.api.websocket_manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/paper-trading")
async def paper_trading_websocket(websocket: WebSocket, token: str | None = Query(None)):
    """
    WebSocket endpoint for live paper trading updates.

    Broadcasts:
    - Real-time trades
    - Price updates
    - Portfolio value
    - Agent decisions
    - Statistics

    Query Parameters:
        token: JWT token (optional in dev)

    Client -> Server:
        {"type": "subscribe", "channel": "paper_trading.live"}
        {"type": "subscribe", "channel": "paper_trading.stats"}
        {"type": "subscribe", "channel": "paper_trading.agents"}

    Server -> Client:
        {"channel": "paper_trading.live", "type": "trade", "data": {...}}
        {"channel": "paper_trading.live", "type": "price", "data": {...}}
        {"channel": "paper_trading.stats", "type": "stats", "data": {...}}
    """
    connection_id = str(uuid.uuid4())
    tenant_id = "paper_trading"
    account_id = "live_session"

    try:
        await ws_manager.connect(
            websocket=websocket,
            connection_id=connection_id,
            tenant_id=tenant_id,
            account_id=account_id,
        )

        # Auto-subscribe to paper trading channels
        await ws_manager.subscribe(connection_id, "paper_trading.live")
        await ws_manager.subscribe(connection_id, "paper_trading.stats")
        await ws_manager.subscribe(connection_id, "paper_trading.agents")

        logger.info(f"Paper trading client connected: {connection_id}")

        # Message loop
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=60.0)
                await ws_manager.handle_client_message(connection_id, data)
            except TimeoutError:
                await ws_manager.send_message(connection_id, {"type": "ping"})

    except WebSocketDisconnect:
        logger.info(f"Paper trading client disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"Paper trading WS error: {e}")
    finally:
        await ws_manager.disconnect(connection_id)
