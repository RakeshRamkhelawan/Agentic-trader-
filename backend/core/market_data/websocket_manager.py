import asyncio
import json
import logging
from typing import Callable, Dict, List, Optional, Any

import websockets

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages real-time WebSocket connections to crypto exchanges.
    Currently defaults to Kraken public WS API.
    """

    def __init__(self, url: str = "wss://ws.kraken.com"):
        self.url = url
        self.connection = None
        self.subscriptions: List[str] = []
        self.callbacks: List[Callable[[Dict[str, Any]], None]] = []
        self.is_running = False
        self.reconnect_delay = 5.0

    async def connect(self):
        """Establish WebSocket connection."""
        try:
            self.connection = await websockets.connect(self.url)
            self.is_running = True
            logger.info(f"Connected to WebSocket: {self.url}")
            
            # Resubscribe if we have pending subscriptions
            if self.subscriptions:
                await self.subscribe(self.subscriptions)
                
            asyncio.create_task(self._listen())
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            await self._reconnect()

    async def _reconnect(self):
        """Handle reconnection logic."""
        self.is_running = False
        logger.info(f"Reconnecting in {self.reconnect_delay} seconds...")
        await asyncio.sleep(self.reconnect_delay)
        await self.connect()

    async def subscribe(self, symbols: List[str]):
        """
        Subscribe to ticker updates for symbols.
        Format varies by exchange. Using Kraken format for default.
        """
        if not self.connection:
            self.subscriptions = list(set(self.subscriptions + symbols))
            return

        # Kraken subscription message
        # Convert symbols to Kraken format (e.g., BTC/USD -> XBT/USD) if needed
        # For simplicity, assuming input is compatible or we use a mapper later.
        msg = {
            "event": "subscribe",
            "pair": symbols,
            "subscription": {"name": "ticker"}
        }
        
        try:
            await self.connection.send(json.dumps(msg))
            self.subscriptions = list(set(self.subscriptions + symbols))
            logger.info(f"Subscribed to: {symbols}")
        except Exception as e:
            logger.error(f"Failed to subscribe: {e}")

    def add_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Add a callback function to handle incoming messages."""
        self.callbacks.append(callback)

    async def _listen(self):
        """Listen loop for incoming messages."""
        while self.is_running and self.connection:
            try:
                message = await self.connection.recv()
                data = json.loads(message)
                
                # Filter out heartbeats or system events if needed
                # For now, pass everything to callbacks
                for callback in self.callbacks:
                    try:
                        callback(data)
                    except Exception as cb_err:
                        logger.error(f"Callback error: {cb_err}")
                        
            except websockets.ConnectionClosed:
                logger.warning("WebSocket connection closed")
                await self._reconnect()
                break
            except Exception as e:
                logger.error(f"Error in listen loop: {e}")
                await self._reconnect()
                break

    async def close(self):
        """Close connection gracefully."""
        self.is_running = False
        if self.connection:
            await self.connection.close()
