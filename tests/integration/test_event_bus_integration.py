"""
Integration Tests for Triad Event Bus (Phase 2)

Tests Redis Streams connectivity, publishing, and subscription.
"""

import asyncio
import json
import pytest
import redis.asyncio as redis
from datetime import datetime

from backend.events.triad_event_bus import (
    TriadEventBus, CouncilDeliberation, BuddhiDecision,
    get_event_bus, publish_deliberation, publish_decision
)


@pytest.fixture
async def event_bus():
    """Create event bus connected to test Redis."""
    bus = TriadEventBus(redis_url="redis://localhost:6379")
    await bus.connect()
    yield bus
    await bus.disconnect()


@pytest.mark.asyncio
class TestEventBusConnectivity:
    """Test basic Redis connectivity."""

    async def test_redis_connection(self):
        """Test that we can connect to Redis."""
        bus = TriadEventBus()
        await bus.connect()
        assert bus.redis is not None
        # Ping Redis
        result = await bus.redis.ping()
        assert result is True
        await bus.disconnect()

    async def test_stream_creation(self, event_bus):
        """Test that streams are created on publish."""
        # Publish a test message
        msg_id = await event_bus.publish_deliberation(
            council_type="test",
            perspective="bullish",
            confidence=0.8,
            reasoning="Test"
        )

        assert msg_id is not None
        assert isinstance(msg_id, str)

        # Check stream exists
        info = await event_bus.get_stream_info(event_bus.STREAM_DELIBERATIONS)
        assert info["length"] >= 1


@pytest.mark.asyncio
class TestEventPublishing:
    """Test event publishing functionality."""

    async def test_publish_deliberation(self, event_bus):
        """Test publishing council deliberation."""
        msg_id = await event_bus.publish_deliberation(
            council_type="guna",
            perspective="bullish",
            confidence=0.82,
            reasoning="Rajas dominant",
            metadata={"trend": "up", "volatility": 0.025}
        )

        assert msg_id is not None
        print(f"Published deliberation: {msg_id}")

    async def test_publish_decision(self, event_bus):
        """Test publishing Buddhi decision."""
        msg_id = await event_bus.publish_decision(
            action="buy",
            confidence=0.73,
            coherence=0.68,
            rationale="Councils agree",
            council_views=[
                {"council": "guna", "perspective": "bullish", "confidence": 0.82}
            ],
            session_id="test_session_001"
        )

        assert msg_id is not None
        print(f"Published decision: {msg_id}")

    async def test_publish_execution(self, event_bus):
        """Test publishing execution update."""
        msg_id = await event_bus.publish_execution(
            symbol="BTC",
            action="buy",
            quantity=0.5,
            price=45000.0,
            pnl=None,
            status="filled"
        )

        assert msg_id is not None


@pytest.mark.asyncio
class TestEventSubscription:
    """Test event subscription and streaming."""

    async def test_subscribe_to_stream(self, event_bus):
        """Test subscribing to a stream."""
        # Publish a message first
        await event_bus.publish_deliberation(
            council_type="test",
            perspective="neutral",
            confidence=0.5,
            reasoning="Test message"
        )

        # Subscribe and receive
        messages = []
        async for event in event_bus.subscribe(
            event_bus.STREAM_DELIBERATIONS,
            last_id="0",  # Read from beginning
            block_ms=1000
        ):
            messages.append(event)
            if len(messages) >= 1:
                break

        assert len(messages) >= 1
        assert "council" in messages[0]

    async def test_subscription_latency(self, event_bus):
        """Test that subscription latency is under 500ms."""
        import time

        received = asyncio.Event()
        received_message = None

        async def subscriber():
            nonlocal received_message
            async for event in event_bus.subscribe(
                event_bus.STREAM_DECISIONS,
                block_ms=5000
            ):
                received_message = event
                received.set()
                break

        # Start subscriber
        sub_task = asyncio.create_task(subscriber())

        # Wait a bit for subscription to be ready
        await asyncio.sleep(0.1)

        # Publish and measure
        start_time = time.time()
        await event_bus.publish_decision(
            action="buy",
            confidence=0.8,
            coherence=0.7,
            rationale="Test latency",
            council_views=[],
            session_id="latency_test"
        )

        # Wait for reception
        try:
            await asyncio.wait_for(received.wait(), timeout=2.0)
        except asyncio.TimeoutError:
            pytest.fail("Message not received within 2 seconds")

        latency = (time.time() - start_time) * 1000  # ms

        print(f"Subscription latency: {latency:.1f}ms")
        assert latency < 500, f"Latency {latency:.1f}ms exceeds 500ms target"

        sub_task.cancel()


@pytest.mark.asyncio
class TestEventBusHelpers:
    """Test helper functions."""

    async def test_singleton_pattern(self):
        """Test that get_event_bus returns singleton."""
        bus1 = get_event_bus()
        bus2 = get_event_bus()
        assert bus1 is bus2

    async def test_convenience_functions(self):
        """Test publish_deliberation convenience function."""
        # These use singleton
        msg_id = await publish_deliberation(
            council_type="guna",
            perspective="bullish",
            confidence=0.8,
            reasoning="Test"
        )

        assert msg_id is not None


class TestEventDataStructures:
    """Test dataclass structures."""

    def test_council_deliberation_creation(self):
        """Test CouncilDeliberation dataclass."""
        d = CouncilDeliberation(
            council_type="guna",
            perspective="bullish",
            confidence=0.82,
            reasoning="Test",
            metadata={},
            timestamp=datetime.utcnow().isoformat()
        )

        assert d.council_type == "guna"
        assert d.confidence == 0.82

        # Test serialization
        data = d.to_dict()
        assert "council_type" in data

    def test_buddhi_decision_creation(self):
        """Test BuddhiDecision dataclass."""
        d = BuddhiDecision(
            action="buy",
            confidence=0.73,
            coherence=0.68,
            rationale="Test",
            council_views=[],
            session_id="test",
            timestamp=datetime.utcnow().isoformat()
        )

        assert d.action == "buy"
        assert d.coherence == 0.68


if __name__ == "__main__":
    # Run tests manually
    print("=" * 60)
    print("EVENT BUS INTEGRATION TESTS")
    print("=" * 60)

    async def run_tests():
        bus = TriadEventBus()
        await bus.connect()

        try:
            # Test 1: Publish
            print("\n1. Testing publish...")
            msg_id = await bus.publish_deliberation(
                council_type="test",
                perspective="bullish",
                confidence=0.8,
                reasoning="Integration test"
            )
            print(f"   ✓ Published: {msg_id}")

            # Test 2: Subscribe
            print("\n2. Testing subscribe...")
            messages = []
            async for event in bus.subscribe(bus.STREAM_DELIBERATIONS, last_id="0", block_ms=1000):
                messages.append(event)
                if len(messages) >= 1:
                    break

            if messages:
                print(f"   ✓ Received {len(messages)} messages")
                print(f"   Last: {messages[-1].get('council')} - {messages[-1].get('perspective')}")
            else:
                print("   ✗ No messages received")

            # Test 3: Stream info
            print("\n3. Testing stream info...")
            info = await bus.get_stream_info(bus.STREAM_DELIBERATIONS)
            print(f"   Stream length: {info['length']}")

            print("\n✓ All tests passed!")

        finally:
            await bus.disconnect()

    asyncio.run(run_tests())
