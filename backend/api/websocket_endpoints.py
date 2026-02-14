"""
WebSocket endpoints for real-time trading data.

Endpoints:
- /ws: Main WebSocket endpoint for trading data
"""

import asyncio
import uuid
import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from backend.api.websocket_manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = Query(None)):
    """
    Main WebSocket endpoint for real-time trading data.

    Query Parameters:
        token: JWT token for authentication (optional in dev mode)

    Message Protocol:
        Client -> Server:
            {"type": "subscribe", "channel": "orderbook.BTC-EUR"}
            {"type": "unsubscribe", "channel": "orderbook.BTC-EUR"}
            {"type": "ping"}

        Server -> Client:
            {"channel": "orderbook.BTC-EUR", "type": "snapshot", "data": {...}}
            {"channel": "orderbook.BTC-EUR", "type": "delta", "data": {...}}
            {"type": "pong"}
    """
    # Generate connection ID
    connection_id = str(uuid.uuid4())

    # TODO: Validate JWT token and extract tenant/account
    # For now, use demo credentials
    tenant_id = "demo-tenant"
    account_id = "demo-account"

    if token:
        # In production, validate token here
        # payload = jwt_manager.verify_token(token)
        # tenant_id = payload.get("tenant_id")
        # account_id = payload.get("account_id")
        pass

    try:
        # Accept connection
        await ws_manager.connect(
            websocket=websocket,
            connection_id=connection_id,
            tenant_id=tenant_id,
            account_id=account_id,
        )

        # Message handling loop
        while True:
            try:
                # Receive message with timeout for heartbeat
                data = await asyncio.wait_for(websocket.receive_json(), timeout=60.0)

                # Handle the message
                await ws_manager.handle_client_message(connection_id, data)

            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await ws_manager.send_message(connection_id, {"type": "ping"})

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {connection_id}: {e}")
    finally:
        await ws_manager.disconnect(connection_id)


@router.get("/ws/stats")
async def websocket_stats():
    """Get WebSocket connection statistics."""
    return ws_manager.get_stats()
