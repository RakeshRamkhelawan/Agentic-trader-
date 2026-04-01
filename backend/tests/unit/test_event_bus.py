"""
Tests for Event Bus using Redis Streams.

TDD Test Suite - Write tests FIRST before implementation.
"""

from unittest.mock import AsyncMock, patch

import pytest
import redis.asyncio as redis

from backend.events.event_bus import EventBus


@pytest.mark.unit
def test_event_bus_exists():
    """RED: EventBus class should exist."""
    assert EventBus is not None


@pytest.mark.unit
def test_event_bus_init():
    """RED: EventBus should initialize with Redis client."""
    bus = EventBus(redis_url="redis://localhost:6381")
    assert bus is not None
    assert hasattr(bus, "redis_url")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_event_bus_connect():
    """RED: EventBus should have async connect method."""
    bus = EventBus(redis_url="redis://localhost:6381")

    mock_client = AsyncMock()
    with patch("redis.asyncio.from_url", return_value=mock_client) as mock_redis:
        await bus.connect()
        mock_redis.assert_called_once_with("redis://localhost:6381")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_event_bus_disconnect():
    """RED: EventBus should cleanup connections."""
    bus = EventBus(redis_url="redis://localhost:6381")
    mock_client = AsyncMock()
    bus.client = mock_client

    await bus.disconnect()
    mock_client.aclose.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_event_bus_publish():
    """RED: EventBus should publish events to Redis stream."""
    bus = EventBus(redis_url="redis://localhost:6381")
    mock_client = AsyncMock()
    mock_client.xadd = AsyncMock(return_value=b"1234567890-0")
    bus.client = mock_client

    event_data = {"type": "test", "value": 42}
    message_id = await bus.publish("test_stream", event_data)

    assert message_id is not None
    mock_client.xadd.assert_called_once_with("test_stream", event_data)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_event_bus_subscribe():
    """RED: EventBus should subscribe to Redis stream with consumer group."""
    bus = EventBus(redis_url="redis://localhost:6381")
    mock_client = AsyncMock()

    # Mock stream response
    mock_response = [
        [b"test_stream", [(b"1234567890-0", {b"type": b"test", b"value": b"42"})]]
    ]
    mock_client.xreadgroup = AsyncMock(return_value=mock_response)
    bus.client = mock_client

    messages = await bus.subscribe(
        stream="test_stream",
        group="test_group",
        consumer="test_consumer",
        count=1,
        block=100,
    )

    assert len(messages) == 1
    assert messages[0]["id"] == "1234567890-0"
    assert messages[0]["data"]["type"] == "test"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_event_bus_create_consumer_group():
    """RED: EventBus should create consumer groups."""
    bus = EventBus(redis_url="redis://localhost:6381")
    mock_client = AsyncMock()
    mock_client.xgroup_create = AsyncMock()
    bus.client = mock_client

    await bus.create_consumer_group("test_stream", "test_group")

    mock_client.xgroup_create.assert_called_once_with(
        "test_stream", "test_group", id="0", mkstream=True
    )


@pytest.mark.unit
@pytest.mark.asyncio
async def test_event_bus_ack():
    """RED: EventBus should acknowledge processed messages."""
    bus = EventBus(redis_url="redis://localhost:6381")
    mock_client = AsyncMock()
    mock_client.xack = AsyncMock(return_value=1)
    bus.client = mock_client

    ack_count = await bus.ack("test_stream", "test_group", "1234567890-0")

    assert ack_count == 1
    mock_client.xack.assert_called_once_with(
        "test_stream", "test_group", "1234567890-0"
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_event_bus_full_integration():
    """Integration test with real Redis (requires Docker)."""
    bus = EventBus(redis_url="redis://localhost:6381")

    try:
        await bus.connect()

        # Create consumer group
        stream = "integration_test_stream"
        group = "integration_group"
        consumer = "test_consumer"

        try:
            await bus.create_consumer_group(stream, group)
        except Exception:
            pass  # Group might already exist

        # Publish event
        event = {"type": "integration_test", "value": 123}
        msg_id = await bus.publish(stream, event)
        assert msg_id is not None

        # Subscribe and read
        messages = await bus.subscribe(stream, group, consumer, count=1, block=1000)
        assert len(messages) > 0
        assert messages[0]["data"]["type"] == "integration_test"

        # Acknowledge
        ack_count = await bus.ack(stream, group, messages[0]["id"])
        assert ack_count == 1

    finally:
        await bus.disconnect()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_event_bus_handles_redis_errors():
    """RED: EventBus should handle Redis connection errors gracefully."""
    bus = EventBus(redis_url="redis://localhost:9999")  # Wrong port

    # Mock to raise connection error
    with patch(
        "redis.asyncio.from_url", side_effect=redis.ConnectionError("Cannot connect")
    ):
        with pytest.raises((redis.ConnectionError, Exception)):
            await bus.connect()
