"""
Triad Event Bus - Redis Streams Implementation

Provides sub-500ms latency between market data and UI updates.
Replaces 3s polling with real-time event streaming.
"""

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

import redis.asyncio as redis

logger = logging.getLogger(__name__)


@dataclass
class CouncilDeliberation:
    """Event: Council heeft een perspectief gedeeld."""

    council_type: str  # "guna", "elemental", "mind", "body", "graha"
    perspective: str  # "bullish", "bearish", "neutral"
    confidence: float  # 0.0 - 1.0
    reasoning: str
    metadata: dict[str, Any]
    timestamp: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "CouncilDeliberation":
        return cls(**data)


@dataclass
class BuddhiDecision:
    """Event: Buddhi heeft een finale beslissing genomen."""

    action: str  # "buy", "sell", "hold"
    confidence: float  # 0.0 - 1.0
    coherence: float  # Agreement tussen councils
    rationale: str
    council_views: list  # Lijst van CouncilDeliberation summaries
    session_id: str
    timestamp: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ExecutionUpdate:
    """Event: Paper trading execution update."""

    symbol: str
    action: str
    quantity: float
    price: float
    pnl: float | None
    status: str  # "pending", "filled", "failed"
    timestamp: str


from backend.core.config.redis_config import REDIS_URL


class TriadEventBus:
    """
    Redis Streams gebaseerde event bus voor real-time Triad updates.

    Streams:
    - triad.deliberations: Council beslissingen
    - triad.decisions: Buddhi finale besluiten
    - triad.executions: Paper trading executions
    - triad.market: Market microstructure updates

    Usage:
        bus = TriadEventBus()

        # Publish
        await bus.publish_deliberation(council_type="guna", ...)

        # Subscribe
        async for event in bus.subscribe("triad.decisions"):
            print(event)
    """

    # Stream names
    STREAM_DELIBERATIONS = "triad.deliberations"
    STREAM_DECISIONS = "triad.decisions"
    STREAM_EXECUTIONS = "triad.executions"
    STREAM_MARKET = "triad.market"

    def __init__(self, redis_url: str = None, max_stream_length: int = 1000):
        if redis_url is None:
            redis_url = REDIS_URL  # Use configured URL
        self.redis_url = redis_url
        self.redis: redis.Redis | None = None
        self.max_stream_length = max_stream_length

    async def connect(self):
        """Connect to Redis."""
        if self.redis is None:
            try:
                self.redis = redis.from_url(self.redis_url, decode_responses=True)
                await self.redis.ping()
                logger.info(f"Connected to Redis at {self.redis_url}")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise
        return self

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
            self.redis = None
            logger.info("Disconnected from Redis")

    async def publish_deliberation(
        self,
        council_type: str,
        perspective: str,
        confidence: float,
        reasoning: str,
        metadata: dict | None = None,
    ) -> str:
        """
        Publiceer council deliberatie naar Redis Stream.

        Returns:
            str: Message ID
        """
        await self.connect()

        event = CouncilDeliberation(
            council_type=council_type,
            perspective=perspective,
            confidence=confidence,
            reasoning=reasoning,
            metadata=metadata or {},
            timestamp=datetime.utcnow().isoformat(),
        )

        message_id = await self.redis.xadd(
            self.STREAM_DELIBERATIONS,
            {"data": json.dumps(event.to_dict())},
            maxlen=self.max_stream_length,
        )

        logger.debug(f"Published deliberation: {council_type} -> {perspective}")
        return message_id

    async def publish_decision(
        self,
        action: str,
        confidence: float,
        coherence: float,
        rationale: str,
        council_views: list,
        session_id: str,
    ) -> str:
        """Publiceer Buddhi beslissing."""
        await self.connect()

        event = BuddhiDecision(
            action=action,
            confidence=confidence,
            coherence=coherence,
            rationale=rationale,
            council_views=council_views,
            session_id=session_id,
            timestamp=datetime.utcnow().isoformat(),
        )

        message_id = await self.redis.xadd(
            self.STREAM_DECISIONS,
            {"data": json.dumps(event.to_dict())},
            maxlen=self.max_stream_length // 2,  # Keep fewer decisions
        )

        logger.info(f"Published decision: {action} (confidence: {confidence:.2f})")
        return message_id

    async def publish_execution(
        self,
        symbol: str,
        action: str,
        quantity: float,
        price: float,
        pnl: float | None = None,
        status: str = "filled",
    ) -> str:
        """Publiceer execution update."""
        await self.connect()

        event = ExecutionUpdate(
            symbol=symbol,
            action=action,
            quantity=quantity,
            price=price,
            pnl=pnl,
            status=status,
            timestamp=datetime.utcnow().isoformat(),
        )

        message_id = await self.redis.xadd(
            self.STREAM_EXECUTIONS,
            {"data": json.dumps(event.__dict__)},
            maxlen=self.max_stream_length,
        )

        logger.debug(f"Published execution: {symbol} {action} @ {price}")
        return message_id

    async def subscribe(
        self, stream: str, last_id: str = "$", block_ms: int = 5000
    ) -> AsyncIterator[dict]:
        """
        Subscribe to events from een stream.

        Args:
            stream: Stream naam (bijv. "triad.decisions")
            last_id: Laatst geziene message ID ("$" = alleen nieuwe)
            block_ms: Hoe lang wachten op nieuwe messages

        Yields:
            Dict: Event data
        """
        await self.connect()

        current_id = last_id

        while True:
            try:
                # Read new messages
                messages = await self.redis.xread({stream: current_id}, block=block_ms)

                for stream_name, events in messages:
                    for message_id, data in events:
                        event_data = json.loads(data.get("data", "{}"))
                        event_data["_message_id"] = message_id
                        event_data["_stream"] = stream
                        yield event_data
                        current_id = message_id

            except asyncio.CancelledError:
                logger.info(f"Subscription to {stream} cancelled")
                break
            except Exception as e:
                logger.error(f"Error in subscription: {e}")
                await asyncio.sleep(1)

    async def get_stream_info(self, stream: str) -> dict:
        """Get info over een stream (length, etc.)."""
        await self.connect()

        info = await self.redis.xinfo_stream(stream)
        return {
            "length": info.get("length", 0),
            "radix-tree-keys": info.get("radix-tree-keys", 0),
            "groups": info.get("groups", 0),
            "last-generated-id": info.get("last-generated-id", ""),
        }

    async def trim_stream(self, stream: str, max_length: int = None):
        """Trim stream naar max length."""
        await self.connect()

        max_len = max_length or self.max_stream_length
        await self.redis.xtrim(stream, maxlen=max_len)
        logger.info(f"Trimmed {stream} to max {max_len} messages")


class TriadEventBusSync:
    """
    Synchrone wrapper voor gebruik in non-async code.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.async_bus = TriadEventBus(redis_url)
        self._loop = None

    def _get_loop(self):
        if self._loop is None:
            self._loop = asyncio.new_event_loop()
        return self._loop

    def publish_deliberation(self, **kwargs) -> str:
        """Sync wrapper voor publish_deliberation."""
        loop = self._get_loop()
        return loop.run_until_complete(self.async_bus.publish_deliberation(**kwargs))

    def publish_decision(self, **kwargs) -> str:
        """Sync wrapper voor publish_decision."""
        loop = self._get_loop()
        return loop.run_until_complete(self.async_bus.publish_decision(**kwargs))


# Singleton instances
_event_bus: TriadEventBus | None = None
_event_bus_sync: TriadEventBusSync | None = None


def get_event_bus() -> TriadEventBus:
    """Get async event bus singleton."""
    global _event_bus
    if _event_bus is None:
        _event_bus = TriadEventBus(redis_url=REDIS_URL)
    return _event_bus


def get_event_bus_sync() -> TriadEventBusSync:
    """Get sync event bus singleton."""
    global _event_bus_sync
    if _event_bus_sync is None:
        _event_bus_sync = TriadEventBusSync()
    return _event_bus_sync


# Convenience functies
async def publish_deliberation(**kwargs) -> str:
    """Publish deliberation via singleton."""
    return await get_event_bus().publish_deliberation(**kwargs)


async def publish_decision(**kwargs) -> str:
    """Publish decision via singleton."""
    return await get_event_bus().publish_decision(**kwargs)


if __name__ == "__main__":
    # Test de event bus
    logging.basicConfig(level=logging.INFO)

    async def test():
        print("=" * 60)
        print("TRIAD EVENT BUS - TEST")
        print("=" * 60)

        bus = TriadEventBus()

        try:
            await bus.connect()
            print("\n✓ Connected to Redis")

            # Publish test events
            print("\nPublishing test events...")

            msg_id = await bus.publish_deliberation(
                council_type="guna",
                perspective="bullish",
                confidence=0.82,
                reasoning="Rajas dominant, strong momentum",
                metadata={"trend": "up", "volatility": 0.025},
            )
            print(f"  Published deliberation: {msg_id}")

            msg_id = await bus.publish_decision(
                action="buy",
                confidence=0.73,
                coherence=0.68,
                rationale="Councils agree on bullish outlook",
                council_views=[
                    {"council": "guna", "perspective": "bullish", "confidence": 0.82},
                    {"council": "mind", "perspective": "neutral", "confidence": 0.55},
                ],
                session_id="test_session_001",
            )
            print(f"  Published decision: {msg_id}")

            # Check stream info
            print("\nStream info:")
            for stream in [bus.STREAM_DELIBERATIONS, bus.STREAM_DECISIONS]:
                try:
                    info = await bus.get_stream_info(stream)
                    print(f"  {stream}: {info['length']} messages")
                except Exception as e:
                    print(f"  {stream}: empty or error ({e})")

            # Subscribe test (run for 5 seconds)
            print("\nSubscribing to decisions for 5 seconds...")
            print("(Send test messages in another terminal with redis-cli)")

            async def subscribe_test():
                count = 0
                async for event in bus.subscribe(bus.STREAM_DECISIONS, block_ms=1000):
                    print(f"  Received: {event.get('action')} @ {event.get('timestamp')}")
                    count += 1
                    if count >= 3:  # Stop after 3 messages
                        break

            try:
                await asyncio.wait_for(subscribe_test(), timeout=5.0)
            except TimeoutError:
                print("  (No messages received in 5s - this is OK)")

            print("\n✓ Test complete!")

        except Exception as e:
            print(f"\n✗ Error: {e}")
            print("  (Make sure Redis is running: docker-compose up redis)")
        finally:
            await bus.disconnect()

    asyncio.run(test())
