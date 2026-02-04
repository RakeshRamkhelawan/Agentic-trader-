"""
Unhappy Path Tests for EventBus.

Tests error conditions, edge cases, and failure scenarios.
"""

import pytest
import redis.asyncio as redis
from unittest.mock import AsyncMock, MagicMock, patch
from backend.events.event_bus import EventBus


@pytest.mark.unit
@pytest.mark.asyncio
async def test_event_bus_publish_without_connection():
    """Unhappy: Publishing without connection should raise error."""
    bus = EventBus(redis_url="redis://localhost:6381")
    
    with pytest.raises(RuntimeError, match="not connected"):
        await bus.publish("test_stream", {"data": "test"})


@pytest.mark.unit
@pytest.mark.asyncio
async def test_event_bus_subscribe_without_connection():
    """Unhappy: Subscribing without connection should raise error."""
    bus = EventBus(redis_url="redis://localhost:6381")
    
    with pytest.raises(RuntimeError, match="not connected"):
        await bus.subscribe("test", "group", "consumer")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_event_bus_invalid_redis_url():
    """Unhappy: Invalid Redis URL should fail connection."""
    bus = EventBus(redis_url="invalid://url")
    
    with pytest.raises(Exception):
        await bus.connect()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_event_bus_connection_timeout():
    """Unhappy: Connection timeout should be handled."""
    bus = EventBus(redis_url="redis://192.0.2.1:6379")  # Non-routable IP
    
    with patch("redis.asyncio.from_url", side_effect=redis.TimeoutError("Connection timeout")):
        with pytest.raises(redis.TimeoutError):
            await bus.connect()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_event_bus_publish_serialization_error():
    """Unhappy: Publishing non-serializable data should fail."""
    bus = EventBus(redis_url="redis://localhost:6381")
    mock_client = AsyncMock()
    mock_client.xadd = AsyncMock(side_effect=TypeError("Cannot serialize"))
    bus.client = mock_client
    
    with pytest.raises(TypeError):
        await bus.publish("test", {"data": object()})


@pytest.mark.unit
@pytest.mark.asyncio
async def test_event_bus_subscribe_no_messages():
    """Unhappy: Subscribe with no messages should return empty list."""
    bus = EventBus(redis_url="redis://localhost:6381")
    mock_client = AsyncMock()
    mock_client.xreadgroup = AsyncMock(return_value=[])
    bus.client = mock_client
    
    messages = await bus.subscribe("test", "group", "consumer", count=1, block=100)
    
    assert messages == []


@pytest.mark.unit
@pytest.mark.asyncio
async def test_event_bus_create_group_already_exists():
    """Unhappy: Creating existing group should raise error."""
    bus = EventBus(redis_url="redis://localhost:6381")
    mock_client = AsyncMock()
    mock_client.xgroup_create = AsyncMock(
        side_effect=redis.ResponseError("BUSYGROUP Consumer Group name already exists")
    )
    bus.client = mock_client
    
    with pytest.raises(redis.ResponseError, match="BUSYGROUP"):
        await bus.create_consumer_group("test", "existing_group")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_event_bus_ack_nonexistent_message():
    """Unhappy: Acknowledging non-existent message should return 0."""
    bus = EventBus(redis_url="redis://localhost:6381")
    mock_client = AsyncMock()
    mock_client.xack = AsyncMock(return_value=0)
    bus.client = mock_client
    
    ack_count = await bus.ack("test", "group", "999999-0")
    
    assert ack_count == 0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_event_bus_disconnect_without_connection():
    """Unhappy: Disconnecting without connection should not raise error."""
    bus = EventBus(redis_url="redis://localhost:6381")
    
    # Should not raise
    await bus.disconnect()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_event_bus_publish_empty_data():
    """Unhappy: Publishing empty dict should still work."""
    bus = EventBus(redis_url="redis://localhost:6381")
    mock_client = AsyncMock()
    mock_client.xadd = AsyncMock(return_value=b"1234567890-0")
    bus.client = mock_client
    
    message_id = await bus.publish("test", {})
    
    assert message_id is not None
    mock_client.xadd.assert_called_once_with("test", {})


@pytest.mark.unit
@pytest.mark.asyncio
async def test_event_bus_subscribe_redis_error():
    """Unhappy: Redis errors during subscribe should propagate."""
    bus = EventBus(redis_url="redis://localhost:6381")
    mock_client = AsyncMock()
    mock_client.xreadgroup = AsyncMock(
        side_effect=redis.ConnectionError("Connection lost")
    )
    bus.client = mock_client
    
    with pytest.raises(redis.ConnectionError):
        await bus.subscribe("test", "group", "consumer")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_event_bus_publish_connection_lost():
    """Unhappy: Connection loss during publish should raise error."""
    bus = EventBus(redis_url="redis://localhost:6381")
    mock_client = AsyncMock()
    mock_client.xadd = AsyncMock(
        side_effect=redis.ConnectionError("Connection closed")
    )
    bus.client = mock_client
    
    with pytest.raises(redis.ConnectionError):
        await bus.publish("test", {"data": "test"})


@pytest.mark.unit
@pytest.mark.asyncio
async def test_event_bus_create_group_invalid_stream():
    """Unhappy: Creating group on invalid stream name should fail."""
    bus = EventBus(redis_url="redis://localhost:6381")
    mock_client = AsyncMock()
    mock_client.xgroup_create = AsyncMock(
        side_effect=redis.ResponseError("Invalid stream")
    )
    bus.client = mock_client
    
    with pytest.raises(redis.ResponseError):
        await bus.create_consumer_group("", "group")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_event_bus_multiple_disconnect_calls():
    """Unhappy: Multiple disconnect calls should be safe."""
    bus = EventBus(redis_url="redis://localhost:6381")
    mock_client = AsyncMock()
    bus.client = mock_client
    
    await bus.disconnect()
    await bus.disconnect()
    await bus.disconnect()
    
    # Should be called only once or handle multiple calls gracefully
    assert mock_client.aclose.call_count >= 1
