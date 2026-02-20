"""
Live Paper Trading Service with WebSocket Broadcasting

Broadcasts real-time paper trading events to connected frontend clients.
"""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any, Dict, Optional

from backend.api.websocket_manager import ws_manager

logger = logging.getLogger(__name__)


class PaperTradingLiveBroadcaster:
    """Broadcasts paper trading events to WebSocket clients."""
    
    def __init__(self):
        self.channel = "paper_trading.live"
        self.stats_channel = "paper_trading.stats"
        self.agents_channel = "paper_trading.agents"
        
    async def broadcast_trade(self, trade_data: Dict[str, Any]):
        """Broadcast a new trade execution."""
        message = {
            "type": "trade_executed",
            "data": {
                **trade_data,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        }
        await ws_manager.broadcast_to_channel(self.channel, message, "trade")
        logger.debug(f"Broadcasted trade: {trade_data.get('symbol')}")
    
    async def broadcast_price_update(self, symbol: str, price: float, exchange: str):
        """Broadcast price update for a symbol."""
        message = {
            "type": "price_update",
            "data": {
                "symbol": symbol,
                "price": price,
                "exchange": exchange,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        }
        await ws_manager.broadcast_to_channel(self.channel, message, "price")
    
    async def broadcast_portfolio_update(self, portfolio_data: Dict[str, Any]):
        """Broadcast portfolio value update."""
        message = {
            "type": "portfolio_update",
            "data": {
                **portfolio_data,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        }
        await ws_manager.broadcast_to_channel(self.channel, message, "portfolio")
    
    async def broadcast_agent_decision(self, agent_name: str, decision: Dict[str, Any]):
        """Broadcast agent trading decision."""
        message = {
            "type": "agent_decision",
            "data": {
                "agent": agent_name,
                "decision": decision,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        }
        await ws_manager.broadcast_to_channel(self.agents_channel, message, "decision")
    
    async def broadcast_stats(self, stats: Dict[str, Any]):
        """Broadcast trading statistics."""
        message = {
            "type": "stats_update",
            "data": {
                **stats,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        }
        await ws_manager.broadcast_to_channel(self.stats_channel, message, "stats")
    
    async def broadcast_session_start(self, session_info: Dict[str, Any]):
        """Broadcast session start event."""
        message = {
            "type": "session_start",
            "data": {
                **session_info,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        }
        await ws_manager.broadcast_to_channel(self.channel, message, "session")
        logger.info("Broadcasted session start")
    
    async def broadcast_session_end(self, final_stats: Dict[str, Any]):
        """Broadcast session end event."""
        message = {
            "type": "session_end",
            "data": {
                **final_stats,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        }
        await ws_manager.broadcast_to_channel(self.channel, message, "session")
        logger.info("Broadcasted session end")


# Global broadcaster instance
paper_trading_broadcaster = PaperTradingLiveBroadcaster()
