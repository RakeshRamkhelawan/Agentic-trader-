"""
Signal Bridge - Connects AI Agents to Frontend via WebSocket.

This bridge listens to agent signals and broadcasts them to
subscribed frontend clients in real-time.

Channels:
- signals: All trading signals from agents
- signals.{agent_id}: Signals from a specific agent
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SignalType(str, Enum):
    """Types of trading signals."""

    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    ALERT = "alert"
    INFO = "info"


class SignalConfidence(str, Enum):
    """Confidence levels for signals."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class TradingSignal:
    """A trading signal from an AI agent."""

    signal_id: str
    agent_id: str
    agent_name: str
    symbol: str
    signal_type: SignalType
    confidence: SignalConfidence
    message: str
    reasoning: Optional[str] = None
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "signal_id": self.signal_id,
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "symbol": self.symbol,
            "signal_type": self.signal_type.value,
            "confidence": self.confidence.value,
            "message": self.message,
            "reasoning": self.reasoning,
            "target_price": self.target_price,
            "stop_loss": self.stop_loss,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


class SignalBridge:
    """
    Bridge between AI Agents and WebSocket clients.

    Collects signals from the CognitiveOrchestrator and broadcasts
    them to subscribed frontend clients.
    """

    def __init__(self):
        # Reference to WebSocket manager (set externally)
        self.ws_manager = None
        self.redis_publisher = None
        # Signal history for late-joining clients
        self.signal_history: List[TradingSignal] = []
        self.max_history_size = 50
        # Lock for thread-safe signal processing
        self._lock = asyncio.Lock()

    def set_redis_publisher(self, redis_publisher) -> None:
        """Set the Redis publisher for backend-to-frontend broadcasting."""
        self.redis_publisher = redis_publisher
        logger.info("SignalBridge connected to Redis publisher")

    async def emit_signal(self, signal: TradingSignal) -> int:
        """
        Emit a trading signal to all subscribed clients.

        Returns the number of clients that received the signal.
        """
        async with self._lock:
            # Add to history
            self.signal_history.append(signal)
            if len(self.signal_history) > self.max_history_size:
                self.signal_history.pop(0)

        # 1. Publish to Redis (for Frontend Broadcast)
        if hasattr(self, "redis_publisher") and self.redis_publisher:
            try:
                # We publish to the configured stream (e.g. market_events or signal_events)
                # Ideally, we should wrap this in a structure that the consumer expects.
                # But typically RedisPublisher.publish handles wrapping.
                # However, if stream key is "market_events", consumer expects "event_type".
                # TradingSignal has "signal_type".
                # To prevent confusion, maybe we should NOT publish to market_events if format differs.
                # But assuming the architecture intends this:
                await self.redis_publisher.publish(signal.to_dict())
            except Exception as e:
                logger.error(f"SignalBridge: Failed to publish to Redis: {e}")

        # 2. Publish to WebSocket Manager (if in same process)
        if hasattr(self, "ws_manager") and self.ws_manager:
            signal_data = signal.to_dict()

            # Broadcast to general signals channel
            sent_count = await self.ws_manager.broadcast_to_channel(
                channel="signals", message=signal_data, message_type="signal"
            )

            # Also broadcast to agent-specific channel
            await self.ws_manager.broadcast_to_channel(
                channel=f"signals.{signal.agent_id}",
                message=signal_data,
                message_type="signal",
            )

            logger.info(
                f"Signal emitted: {signal.signal_type.value} {signal.symbol} "
                f"from {signal.agent_name} (sent to {sent_count} clients)"
            )
            return sent_count

        return 0

    async def emit_from_agent_message(
        self, agent_id: str, agent_name: str, message_type: str, payload: Dict[str, Any]
    ) -> Optional[TradingSignal]:
        """
        Create and emit a signal from an agent message.

        Parses the payload to extract signal information.
        Returns the created signal or None if not applicable.
        """
        import uuid

        # Determine signal type from message
        signal_type = SignalType.INFO
        if message_type in ["BUY_SIGNAL", "LONG_SIGNAL"]:
            signal_type = SignalType.BUY
        elif message_type in ["SELL_SIGNAL", "SHORT_SIGNAL"]:
            signal_type = SignalType.SELL
        elif message_type in ["HOLD_SIGNAL", "NEUTRAL"]:
            signal_type = SignalType.HOLD
        elif message_type in ["ALERT", "WARNING", "RISK_ALERT"]:
            signal_type = SignalType.ALERT

        # Extract symbol
        symbol = payload.get("symbol", payload.get("asset", "UNKNOWN"))

        # Extract confidence
        conf_str = payload.get("confidence", "medium").lower()
        if conf_str in ["high", "strong"]:
            confidence = SignalConfidence.HIGH
        elif conf_str in ["low", "weak"]:
            confidence = SignalConfidence.LOW
        else:
            confidence = SignalConfidence.MEDIUM

        # Build message
        message = payload.get(
            "message",
            payload.get("summary", f"{signal_type.value.upper()} signal for {symbol}"),
        )

        # Create signal
        signal = TradingSignal(
            signal_id=str(uuid.uuid4()),
            agent_id=agent_id,
            agent_name=agent_name,
            symbol=symbol,
            signal_type=signal_type,
            confidence=confidence,
            message=message,
            reasoning=payload.get("reasoning", payload.get("analysis")),
            target_price=payload.get("target_price"),
            stop_loss=payload.get("stop_loss"),
            metadata={
                "original_type": message_type,
                "guna_vibration": payload.get("guna_vibration"),
                "sentiment_score": payload.get("sentiment_score"),
                "market_regime": payload.get("market_regime"),
            },
        )

        await self.emit_signal(signal)
        return signal

    async def get_recent_signals(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent signals from history."""
        async with self._lock:
            signals = self.signal_history[-limit:]
            return [s.to_dict() for s in reversed(signals)]

    async def send_snapshot_to_client(self, connection_id: str) -> None:
        """Send signal history snapshot to a newly connected client."""
        if not self.ws_manager:
            return

        recent_signals = await self.get_recent_signals(20)

        await self.ws_manager.send_message(
            connection_id,
            {
                "channel": "signals",
                "type": "snapshot",
                "data": recent_signals,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


# Global signal bridge singleton
signal_bridge = SignalBridge()
