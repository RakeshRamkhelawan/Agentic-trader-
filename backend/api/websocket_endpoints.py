"""
WebSocket endpoints for real-time trading data.

Endpoints:
- /ws: Main WebSocket endpoint for trading data
"""

import asyncio
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.api.websocket_manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter()


async def handle_websocket_connection(websocket: WebSocket, token: Optional[str] = None):
    """
    Handle WebSocket connection lifecycle.
    Separated from endpoint for better error handling.
    """
    # Generate connection ID
    connection_id = str(uuid.uuid4())

    # Use demo credentials for now (in production, validate token)
    tenant_id = "demo-tenant"
    account_id = "demo-account"

    # TODO: In production, validate JWT token here
    # if token:
    #     from backend.security.jwt_handler import JWTHandler
    #     handler = JWTHandler(...)
    #     payload = handler.verify_token(token)
    #     tenant_id = payload.get("tenant_id")
    #     account_id = payload.get("account_id")

    try:
        # Accept connection
        await ws_manager.connect(
            websocket=websocket,
            connection_id=connection_id,
            tenant_id=tenant_id,
            account_id=account_id,
        )

        logger.info(f"WebSocket connected: {connection_id}")

        # Message handling loop
        while True:
            try:
                # Receive message with timeout for heartbeat
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=60.0
                )

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
    await handle_websocket_connection(websocket, token)


@router.get("/ws/stats")
async def websocket_stats():
    """Get WebSocket connection statistics."""
    return ws_manager.get_stats()


# Alternative WebSocket endpoint with CORS workaround for development
@router.websocket("/ws/public")
async def websocket_public_endpoint(websocket: WebSocket):
    """
    Public WebSocket endpoint (no auth required).
    Use this for development/testing when auth is not configured.
    """
    await handle_websocket_connection(websocket, token=None)
