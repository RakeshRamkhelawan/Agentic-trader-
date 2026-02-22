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
        self.vedic_channel = "paper_trading.vedic"  # NIEUW: Vedic context channel
        
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
    
    # ========== VEDIC CONTEXT CHANNEL (paper_trading.vedic) ==========
    
    async def broadcast_soul_update(self, soul_context: Dict[str, Any]):
        """Broadcast Soul context update (Rahu Kala, Market Regime, etc.)."""
        message = {
            "channel": "paper_trading.vedic",
            "type": "soul_update",
            "data": {
                "rahu_kala": soul_context.get("rahu_kala_active", False),
                "market_regime": soul_context.get("market_regime", "neutral"),
                "vedic_time": soul_context.get("vedic_time", "Unknown"),
                "navagraha_dominant": soul_context.get("navagraha_dominant", "Unknown"),
                "consciousness_level": soul_context.get("consciousness_level", 0.5),
                "trading_gate_open": soul_context.get("trading_gate_open", True),
                "timestamp": datetime.now(UTC).isoformat(),
            }
        }
        await ws_manager.broadcast_to_channel(self.vedic_channel, message, "soul")
        logger.debug(f"Broadcasted soul update: regime={soul_context.get('market_regime')}")
    
    async def broadcast_prana_update(self, prana_levels: Dict[str, float]):
        """Broadcast Prana levels for all elemental agents."""
        message = {
            "channel": "paper_trading.vedic",
            "type": "prana_update",
            "data": {
                **prana_levels,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        }
        await ws_manager.broadcast_to_channel(self.vedic_channel, message, "prana")
        logger.debug(f"Broadcasted prana update: {prana_levels}")
    
    async def broadcast_harmony_update(self, harmony_score: float, synthesis: Dict[str, Any]):
        """Broadcast Harmony score from Ether Orchestrator."""
        message = {
            "channel": "paper_trading.vedic",
            "type": "harmony_update",
            "data": {
                "harmony_score": harmony_score,
                "dominant_element": synthesis.get("focus_element", "unknown"),
                "action": synthesis.get("action", "hold"),
                "confidence": synthesis.get("confidence", 0.0),
                "timestamp": datetime.now(UTC).isoformat(),
            }
        }
        await ws_manager.broadcast_to_channel(self.vedic_channel, message, "harmony")
        logger.debug(f"Broadcasted harmony update: score={harmony_score:.2f}")
    
    async def broadcast_cosmic_block(self, reason: str, blocked_at: str, resumes_at: str):
        """Broadcast cosmic block event (Rahu Kala, etc.)."""
        message = {
            "channel": "paper_trading.vedic",
            "type": "cosmic_block",
            "data": {
                "reason": reason,
                "blocked_at": blocked_at,
                "resumes_at": resumes_at,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        }
        await ws_manager.broadcast_to_channel(self.vedic_channel, message, "cosmic")
        logger.info(f"Broadcasted cosmic block: {reason}")


# Global broadcaster instance
paper_trading_broadcaster = PaperTradingLiveBroadcaster()
