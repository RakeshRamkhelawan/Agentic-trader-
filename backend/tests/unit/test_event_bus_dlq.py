"""
Unit tests for Event Bus with DLQ and Retry mechanism.
"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.events.event_bus import (
    EventBus,
    EventBusError,
    EventMetadata,
    RetryConfig,
)


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    client = AsyncMock()
    client.xadd = AsyncMock(return_value=b"123-0")
    client.xreadgroup = AsyncMock(return_value=[])
    client.xack = AsyncMock(return_value=1)
    client.xgroup_create = AsyncMock()
    client.xrange = AsyncMock(return_value=[])
    client.xdel = AsyncMock(return_value=1)
    client.pipeline = MagicMock(return_value=AsyncMock())
    client.aclose = AsyncMock()
    return client


@pytest.fixture
def event_bus(mock_redis):
    """Create an EventBus with mocked Redis."""
    bus = EventBus(
        redis_url="redis://localhost:6379",
        retry_config=RetryConfig(max_retries=3, base_delay=0.1),
        enable_dlq=True,
    )
    bus.client = mock_redis
    return bus


class TestRetryConfig:
    """Test cases for RetryConfig."""

    def test_default_config(self):
        """Test default retry configuration."""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.exponential_base == 5.0

    def test_exponential_backoff(self):
        """Test exponential backoff calculation."""
        config = RetryConfig(base_delay=1.0, exponential_base=5.0, max_delay=100.0)

        # Attempt 0: 1s
        assert config.calculate_delay(0) == 1.0
        # Attempt 1: 5s
        assert config.calculate_delay(1) == 5.0
        # Attempt 2: 25s
        assert config.calculate_delay(2) == 25.0
        # Attempt 3: 125s but capped at max_delay
        assert config.calculate_delay(3) == 100.0


class TestEventMetadata:
    """Test cases for EventMetadata."""

    def test_creation(self):
        """Test metadata creation."""
        meta = EventMetadata(
            event_id="abc123",
            timestamp="2024-01-01T00:00:00Z",
            retry_count=2,
            original_stream="events.orders",
        )

        assert meta.event_id == "abc123"
        assert meta.retry_count == 2

    def test_to_dict(self):
        """Test conversion to dictionary."""
        meta = EventMetadata(event_id="abc", timestamp="2024-01-01T00:00:00Z")
        d = meta.to_dict()

        assert d["event_id"] == "abc"
        assert d["timestamp"] == "2024-01-01T00:00:00Z"
        assert d["retry_count"] == 0

    def test_from_dict(self):
        """Test creation from dictionary."""
        d = {
            "event_id": "abc",
            "timestamp": "2024-01-01T00:00:00Z",
            "retry_count": 3,
            "original_stream": "events.orders",
        }
        meta = EventMetadata.from_dict(d)

        assert meta.event_id == "abc"
        assert meta.retry_count == 3


class TestEventBusPublish:
    """Test cases for publishing events."""

    @pytest.mark.asyncio
    async def test_publish_adds_metadata(self, event_bus, mock_redis):
        """Test that publish adds metadata to events."""
        event_data = {"symbol": "BTC-EUR", "price": 50000}

        message_id = await event_bus.publish("events.orders", event_data)

        assert message_id is not None
        # Check that xadd was called with metadata
        call_args = mock_redis.xadd.call_args
        stream, message = call_args[0]

        # Parse the metadata from the message
        meta_json = message["_metadata"]
        meta = json.loads(meta_json)

        assert "event_id" in meta
        assert "timestamp" in meta
        assert meta["retry_count"] == 0

    @pytest.mark.asyncio
    async def test_publish_batch(self, event_bus, mock_redis):
        """Test batch publishing."""
        events = [
            {"symbol": "BTC-EUR", "price": 50000},
            {"symbol": "ETH-EUR", "price": 3000},
        ]

        # Setup pipeline mock
        pipeline_mock = AsyncMock()
        pipeline_mock.execute = AsyncMock(return_value=[b"1-0", b"2-0"])
        mock_redis.pipeline = MagicMock(return_value=pipeline_mock)

        message_ids = await event_bus.publish_batch("events.orders", events)

        assert len(message_ids) == 2
        pipeline_mock.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_not_connected(self):
        """Test that publish raises error when not connected."""
        bus = EventBus(redis_url="redis://localhost")

        with pytest.raises(EventBusError, match="not connected"):
            await bus.publish("events.orders", {"test": "data"})


class TestEventBusSubscribe:
    """Test cases for subscribing to events."""

    @pytest.mark.asyncio
    async def test_subscribe_returns_messages(self, event_bus, mock_redis):
        """Test subscription returns parsed messages."""
        # Setup mock response
        mock_redis.xreadgroup = AsyncMock(
            return_value=[
                (
                    b"events.orders",
                    [
                        (
                            b"123-0",
                            {
                                b"symbol": b"BTC-EUR",
                                b"_metadata": json.dumps(
                                    {
                                        "event_id": "abc",
                                        "timestamp": "2024-01-01T00:00:00Z",
                                        "retry_count": 0,
                                    }
                                ).encode(),
                            },
                        ),
                    ],
                ),
            ]
        )

        messages = await event_bus.subscribe("events.orders", "group1", "consumer1")

        assert len(messages) == 1
        assert messages[0]["id"] == "123-0"
        assert messages[0]["data"]["symbol"] == "BTC-EUR"


class TestEventBusRetry:
    """Test cases for retry mechanism."""

    @pytest.mark.asyncio
    async def test_successful_processing_no_retry(self, event_bus, mock_redis):
        """Test that successful processing doesn't trigger retry."""
        # Setup message
        mock_redis.xreadgroup = AsyncMock(
            return_value=[
                (
                    b"events.orders",
                    [
                        (
                            b"123-0",
                            {
                                b"symbol": b"BTC-EUR",
                                b"_metadata": json.dumps(
                                    {
                                        "event_id": "abc",
                                        "timestamp": "2024-01-01T00:00:00Z",
                                        "retry_count": 0,
                                    }
                                ).encode(),
                            },
                        ),
                    ],
                ),
            ]
        )

        processor = AsyncMock(return_value="success")

        results = await event_bus.process_with_retry(
            "events.orders", "group1", "consumer1", processor
        )

        assert len(results) == 1
        assert results[0]["success"] is True
        processor.assert_called_once()

    @pytest.mark.asyncio
    async def test_failed_processing_schedules_retry(self, event_bus, mock_redis):
        """Test that failed processing schedules retry."""
        # Setup message
        mock_redis.xreadgroup = AsyncMock(
            return_value=[
                (
                    b"events.orders",
                    [
                        (
                            b"123-0",
                            {
                                b"symbol": b"BTC-EUR",
                                b"_metadata": json.dumps(
                                    {
                                        "event_id": "abc",
                                        "timestamp": "2024-01-01T00:00:00Z",
                                        "retry_count": 0,
                                    }
                                ).encode(),
                            },
                        ),
                    ],
                ),
            ]
        )

        processor = AsyncMock(side_effect=Exception("Processing failed"))

        results = await event_bus.process_with_retry(
            "events.orders", "group1", "consumer1", processor
        )

        assert len(results) == 1
        assert results[0]["success"] is False
        # Should have published to retry stream
        assert mock_redis.xadd.call_count >= 1

    @pytest.mark.asyncio
    async def test_max_retries_sends_to_dlq(self, event_bus, mock_redis):
        """Test that exhausted retries send to DLQ."""
        # Setup message with max retries reached
        mock_redis.xreadgroup = AsyncMock(
            return_value=[
                (
                    b"events.orders",
                    [
                        (
                            b"123-0",
                            {
                                b"symbol": b"BTC-EUR",
                                b"_metadata": json.dumps(
                                    {
                                        "event_id": "abc",
                                        "timestamp": "2024-01-01T00:00:00Z",
                                        "retry_count": 3,  # Max retries
                                    }
                                ).encode(),
                            },
                        ),
                    ],
                ),
            ]
        )

        processor = AsyncMock(side_effect=Exception("Processing failed"))

        results = await event_bus.process_with_retry(
            "events.orders", "group1", "consumer1", processor
        )

        assert results[0]["success"] is False
        # Should have published to DLQ
        call_args_list = mock_redis.xadd.call_args_list
        dlq_calls = [c for c in call_args_list if "dlq" in str(c)]
        assert len(dlq_calls) > 0


class TestEventBusDLQ:
    """Test cases for Dead Letter Queue."""

    @pytest.mark.asyncio
    async def test_get_dlq_messages(self, event_bus, mock_redis):
        """Test retrieving DLQ messages."""
        mock_redis.xrange = AsyncMock(
            return_value=[
                (
                    b"456-0",
                    {
                        b"symbol": b"BTC-EUR",
                        b"_metadata": json.dumps(
                            {
                                "event_id": "failed-abc",
                                "error_info": "Processing error",
                                "original_stream": "events.orders",
                            }
                        ).encode(),
                    },
                ),
            ]
        )

        messages = await event_bus.get_dlq_messages("events.orders")

        assert len(messages) == 1
        assert messages[0]["data"]["symbol"] == "BTC-EUR"

    @pytest.mark.asyncio
    async def test_replay_from_dlq(self, event_bus, mock_redis):
        """Test replaying messages from DLQ."""
        mock_redis.xrange = AsyncMock(
            return_value=[
                (
                    b"456-0",
                    {
                        b"symbol": b"BTC-EUR",
                        b"_metadata": json.dumps(
                            {
                                "event_id": "failed-abc",
                                "error_info": "Processing error",
                                "original_stream": "events.orders",
                                "retry_count": 3,
                            }
                        ).encode(),
                    },
                ),
            ]
        )

        result = await event_bus.replay_from_dlq("events.orders")

        assert result is True
        # Should have published to original stream
        call_args_list = mock_redis.xadd.call_args_list
        original_calls = [
            c
            for c in call_args_list
            if "events.orders" in str(c) and "dlq" not in str(c)
        ]
        assert len(original_calls) > 0


class TestEventBusConsumerGroup:
    """Test cases for consumer group management."""

    @pytest.mark.asyncio
    async def test_create_consumer_group(self, event_bus, mock_redis):
        """Test creating consumer group."""
        await event_bus.create_consumer_group("events.orders", "group1")

        mock_redis.xgroup_create.assert_called_once_with(
            "events.orders", "group1", id="0", mkstream=True
        )

    @pytest.mark.asyncio
    async def test_create_consumer_group_already_exists(self, event_bus, mock_redis):
        """Test handling already existing consumer group."""
        from redis.exceptions import ResponseError

        mock_redis.xgroup_create = AsyncMock(
            side_effect=ResponseError("Consumer group already exists")
        )

        # Should not raise
        await event_bus.create_consumer_group("events.orders", "group1")


class TestEventBusAck:
    """Test cases for acknowledging messages."""

    @pytest.mark.asyncio
    async def test_acknowledge_message(self, event_bus, mock_redis):
        """Test acknowledging a message."""
        result = await event_bus.ack("events.orders", "group1", "123-0")

        assert result == 1
        mock_redis.xack.assert_called_once_with("events.orders", "group1", "123-0")
