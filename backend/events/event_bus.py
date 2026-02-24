"""
EventBus using Redis Streams with Dead Letter Queue and Retry Mechanism.

Provides publish/subscribe capabilities using Redis Streams with consumer groups,
exponential backoff retry, and DLQ for failed messages.
"""

import hashlib
import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class EventBusError(Exception):
    """Base exception for EventBus errors."""

    pass


class RetryExhaustedError(EventBusError):
    """Raised when all retry attempts are exhausted."""

    pass


@dataclass
class RetryConfig:
    """Configuration for retry mechanism."""

    max_retries: int = 3
    base_delay: float = 1.0  # Base delay in seconds
    max_delay: float = 60.0  # Maximum delay cap
    exponential_base: float = 5.0  # Exponential multiplier

    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for a given retry attempt using exponential backoff.

        Formula: min(base_delay * (exponential_base ^ attempt), max_delay)
        """

        delay = self.base_delay * (self.exponential_base**attempt)
        return min(delay, self.max_delay)


@dataclass
class EventMetadata:
    """Metadata attached to events for tracking."""

    event_id: str
    timestamp: str
    retry_count: int = 0
    original_stream: str | None = None
    error_info: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "retry_count": self.retry_count,
            "original_stream": self.original_stream,
            "error_info": self.error_info,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EventMetadata":
        return cls(
            event_id=data.get("event_id", ""),
            timestamp=data.get("timestamp", ""),
            retry_count=data.get("retry_count", 0),
            original_stream=data.get("original_stream"),
            error_info=data.get("error_info"),
        )


class EventBus:
    """
    Redis Streams-based event bus with DLQ and retry support.

    Features:
    - Publish/subscribe with Redis Streams
    - Consumer groups for parallel processing
    - Exponential backoff retry (1s, 5s, 25s)
    - Dead Letter Queue for exhausted retries
    - Batch publishing support
    """

    DLQ_SUFFIX = ".dlq"
    RETRY_SUFFIX = ".retry"

    def __init__(
        self,
        redis_url: str,
        retry_config: RetryConfig | None = None,
        enable_dlq: bool = True,
    ):
        """
        Initialize EventBus.

        Args:
            redis_url: Redis connection URL (e.g., "redis://localhost:6381")
            retry_config: Retry configuration (default: 3 retries, 1s/5s/25s)
            enable_dlq: If True, enable Dead Letter Queue
        """
        self.redis_url = redis_url
        self.client: redis.Redis | None = None
        self.retry_config = retry_config or RetryConfig()
        self.enable_dlq = enable_dlq

        # Batch publishing buffer
        self._batch_buffer: list[tuple] = []
        self._batch_size = 100
        self._batch_flush_interval = 1.0  # seconds

    async def connect(self) -> None:
        """Establish connection to Redis."""
        self.client = redis.from_url(self.redis_url)
        logger.info("EventBus connected to Redis")

    async def disconnect(self) -> None:
        """Close Redis connection."""
        # Flush any pending batches
        if self._batch_buffer:
            await self._flush_batch()

        if self.client:
            await self.client.aclose()
            logger.info("EventBus disconnected from Redis")

    def _generate_event_id(self, event_data: dict[str, Any]) -> str:
        """Generate unique event ID based on content hash."""
        content = json.dumps(event_data, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _add_metadata(self, event_data: dict[str, Any], retry_count: int = 0) -> dict[str, Any]:
        """Add metadata to event data."""
        metadata = EventMetadata(
            event_id=self._generate_event_id(event_data),
            timestamp=datetime.now(UTC).isoformat(),
            retry_count=retry_count,
            original_stream=event_data.get("_original_stream"),
        )

        # Add metadata without modifying original data structure
        event_with_meta = event_data.copy()
        event_with_meta["_metadata"] = metadata.to_dict()
        return event_with_meta

    async def publish(self, stream: str, event_data: dict[str, Any]) -> str:
        """
        Publish event to Redis stream.

        Args:
            stream: Stream name
            event_data: Event payload as dictionary

        Returns:
            Message ID from Redis
        """
        if not self.client:
            raise EventBusError("EventBus not connected. Call connect() first.")

        # Add metadata
        event_with_meta = self._add_metadata(event_data)

        # Convert to strings for Redis
        message = {
            k: json.dumps(v, default=str) if isinstance(v, (dict, list)) else str(v)
            for k, v in event_with_meta.items()
        }

        message_id = await self.client.xadd(stream, message)
        logger.debug(f"Published event to {stream}: {message_id}")
        return message_id.decode()

    async def publish_batch(self, stream: str, events: list[dict[str, Any]]) -> list[str]:
        """
        Publish multiple events in a batch (using Redis pipeline).

        Args:
            stream: Stream name
            events: List of event payloads

        Returns:
            List of message IDs
        """
        if not self.client:
            raise EventBusError("EventBus not connected. Call connect() first.")

        pipe = self.client.pipeline()

        for event_data in events:
            event_with_meta = self._add_metadata(event_data)
            message = {
                k: json.dumps(v, default=str) if isinstance(v, (dict, list)) else str(v)
                for k, v in event_with_meta.items()
            }
            pipe.xadd(stream, message)

        message_ids = await pipe.execute()
        logger.debug(f"Published {len(events)} events to {stream}")
        return [mid.decode() for mid in message_ids]

    async def subscribe(
        self,
        stream: str,
        group: str,
        consumer: str,
        count: int = 10,
        block: int = 1000,
    ) -> list[dict[str, Any]]:
        """
        Subscribe to stream using consumer group.

        Args:
            stream: Stream name
            group: Consumer group name
            consumer: Consumer name
            count: Max messages to fetch
            block: Blocking timeout in milliseconds

        Returns:
            List of messages with id, data, and metadata
        """
        if not self.client:
            raise EventBusError("EventBus not connected. Call connect() first.")

        response = await self.client.xreadgroup(
            groupname=group,
            consumername=consumer,
            streams={stream: ">"},
            count=count,
            block=block,
        )

        messages = []
        if response:
            for stream_name, stream_messages in response:
                for message_id, message_data in stream_messages:
                    # Parse message data
                    parsed_data = {}
                    for k, v in message_data.items():
                        key = k.decode() if isinstance(k, bytes) else k
                        val = v.decode() if isinstance(v, bytes) else v
                        # Try to parse JSON
                        try:
                            val = json.loads(val)
                        except (json.JSONDecodeError, TypeError):
                            pass
                        parsed_data[key] = val

                    messages.append(
                        {
                            "id": (
                                message_id.decode() if isinstance(message_id, bytes) else message_id
                            ),
                            "data": parsed_data,
                            "stream": (
                                stream.decode() if isinstance(stream_name, bytes) else stream_name
                            ),
                        }
                    )

        return messages

    async def process_with_retry(
        self,
        stream: str,
        group: str,
        consumer: str,
        processor: Callable[[dict[str, Any]], Any],
        count: int = 10,
        block: int = 1000,
    ) -> list[dict[str, Any]]:
        """
        Subscribe and process messages with automatic retry and DLQ support.

        Args:
            stream: Stream name
            group: Consumer group name
            consumer: Consumer name
            processor: Function to process message (should raise on failure)
            count: Max messages to fetch
            block: Blocking timeout in milliseconds

        Returns:
            List of processing results
        """
        messages = await self.subscribe(stream, group, consumer, count, block)
        results = []

        for message in messages:
            try:
                # Process message
                result = await processor(message["data"])
                results.append({"message_id": message["id"], "result": result, "success": True})

                # Acknowledge successful processing
                await self.ack(stream, group, message["id"])

            except Exception as e:
                # Get retry count from metadata
                metadata = message["data"].get("_metadata", {})
                retry_count = metadata.get("retry_count", 0)

                if retry_count < self.retry_config.max_retries:
                    # Retry with exponential backoff
                    await self._schedule_retry(stream, message["data"], str(e))
                    logger.warning(
                        f"Message {message['id']} failed, scheduling retry {retry_count + 1}/"
                        f"{self.retry_config.max_retries}"
                    )
                else:
                    # Max retries exhausted - send to DLQ
                    await self._send_to_dlq(stream, message["data"], str(e))
                    logger.error(f"Message {message['id']} exhausted all retries, sent to DLQ")

                # Acknowledge original message (we've either retried or DLQ'd)
                await self.ack(stream, group, message["id"])
                results.append({"message_id": message["id"], "error": str(e), "success": False})

        return results

    async def _schedule_retry(
        self, original_stream: str, event_data: dict[str, Any], error: str
    ) -> None:
        """
        Schedule a message for retry with exponential backoff.

        Stores in a retry stream with delay calculated based on retry count.
        """
        metadata = event_data.get("_metadata", {})
        retry_count = metadata.get("retry_count", 0)

        # Increment retry count
        metadata["retry_count"] = retry_count + 1
        metadata["error_info"] = error
        metadata["original_stream"] = original_stream
        event_data["_metadata"] = metadata

        # Calculate delay
        delay = self.retry_config.calculate_delay(retry_count)

        # Publish to retry stream with scheduled time
        retry_stream = f"{original_stream}{self.RETRY_SUFFIX}"
        event_data["_scheduled_time"] = datetime.now(UTC).timestamp() + delay

        await self.publish(retry_stream, event_data)
        logger.debug(f"Scheduled retry {retry_count + 1} for {original_stream} in {delay}s")

    async def _send_to_dlq(
        self, original_stream: str, event_data: dict[str, Any], error: str
    ) -> None:
        """Send message to Dead Letter Queue."""
        if not self.enable_dlq:
            logger.error(f"DLQ disabled, dropping failed message from {original_stream}")
            return

        dlq_stream = f"{original_stream}{self.DLQ_SUFFIX}"

        # Add error info to metadata
        metadata = event_data.get("_metadata", {})
        metadata["error_info"] = error
        metadata["original_stream"] = original_stream
        metadata["dlq_timestamp"] = datetime.now(UTC).isoformat()
        event_data["_metadata"] = metadata

        await self.publish(dlq_stream, event_data)
        logger.info(f"Message sent to DLQ: {dlq_stream}")

    async def process_retries(self, original_stream: str) -> int:
        """
        Process messages from retry stream that are due for retry.

        Args:
            original_stream: Original stream name

        Returns:
            Number of messages retried
        """
        if not self.client:
            return 0

        retry_stream = f"{original_stream}{self.RETRY_SUFFIX}"
        now = datetime.now(UTC).timestamp()

        # Read pending messages from retry stream
        messages = await self.client.xrange(retry_stream, min="-", max="+")

        retried = 0
        for message_id, message_data in messages:
            # Parse message
            parsed = {}
            for k, v in message_data.items():
                key = k.decode() if isinstance(k, bytes) else k
                val = v.decode() if isinstance(v, bytes) else v
                try:
                    val = json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    pass
                parsed[key] = val

            scheduled_time = parsed.get("_scheduled_time", 0)

            if scheduled_time <= now:
                # Due for retry - republish to original stream
                metadata = parsed.get("_metadata", {})
                retry_count = metadata.get("retry_count", 0)

                # Remove scheduling metadata
                parsed.pop("_scheduled_time", None)

                await self.publish(original_stream, parsed)

                # Delete from retry stream
                await self.client.xdel(retry_stream, message_id)

                retried += 1
                logger.debug(f"Retried message to {original_stream} (attempt {retry_count})")

        return retried

    async def get_dlq_messages(
        self, original_stream: str, count: int = 100
    ) -> list[dict[str, Any]]:
        """
        Get messages from Dead Letter Queue.

        Args:
            original_stream: Original stream name
            count: Max messages to retrieve

        Returns:
            List of DLQ messages
        """
        if not self.client or not self.enable_dlq:
            return []

        dlq_stream = f"{original_stream}{self.DLQ_SUFFIX}"
        messages = await self.client.xrange(dlq_stream, min="-", max="+", count=count)

        result = []
        for message_id, message_data in messages:
            parsed = {}
            for k, v in message_data.items():
                key = k.decode() if isinstance(k, bytes) else k
                val = v.decode() if isinstance(v, bytes) else v
                try:
                    val = json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    pass
                parsed[key] = val

            result.append(
                {
                    "id": message_id.decode() if isinstance(message_id, bytes) else message_id,
                    "data": parsed,
                }
            )

        return result

    async def replay_from_dlq(self, original_stream: str, message_id: str | None = None) -> bool:
        """
        Replay a message from DLQ back to original stream.

        Args:
            original_stream: Original stream name
            message_id: Specific message ID to replay (None = replay all)

        Returns:
            True if successful
        """
        if not self.client or not self.enable_dlq:
            return False

        dlq_stream = f"{original_stream}{self.DLQ_SUFFIX}"

        if message_id:
            # Get specific message
            messages = await self.client.xrange(dlq_stream, min=message_id, max=message_id)
        else:
            # Get all messages
            messages = await self.client.xrange(dlq_stream, min="-", max="+")

        for msg_id, msg_data in messages:
            parsed = {}
            for k, v in msg_data.items():
                key = k.decode() if isinstance(k, bytes) else k
                val = v.decode() if isinstance(v, bytes) else v
                try:
                    val = json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    pass
                parsed[key] = val

            # Reset retry count for replay
            metadata = parsed.get("_metadata", {})
            metadata["retry_count"] = 0
            metadata["error_info"] = None
            parsed["_metadata"] = metadata

            # Publish to original stream
            await self.publish(original_stream, parsed)

            # Delete from DLQ
            await self.client.xdel(dlq_stream, msg_id)

        logger.info(f"Replayed {len(messages)} messages from DLQ to {original_stream}")
        return True

    async def create_consumer_group(self, stream: str, group: str, id: str = "0") -> None:
        """
        Create consumer group for stream.

        Args:
            stream: Stream name
            group: Consumer group name
            id: Starting message ID (default "0" = from beginning)
        """
        if not self.client:
            raise EventBusError("EventBus not connected. Call connect() first.")

        try:
            await self.client.xgroup_create(stream, group, id=id, mkstream=True)
            logger.info(f"Created consumer group '{group}' for stream '{stream}'")
        except redis.ResponseError as e:
            if "already exists" in str(e):
                logger.debug(f"Consumer group '{group}' already exists")
            else:
                raise

    async def ack(self, stream: str, group: str, message_id: str) -> int:
        """
        Acknowledge processed message.

        Args:
            stream: Stream name
            group: Consumer group name
            message_id: Message ID to acknowledge

        Returns:
            Number of messages acknowledged
        """
        if not self.client:
            raise EventBusError("EventBus not connected. Call connect() first.")

        return await self.client.xack(stream, group, message_id)

    async def _flush_batch(self) -> None:
        """Flush batch buffer to Redis."""
        if not self._batch_buffer or not self.client:
            return

        pipe = self.client.pipeline()

        for stream, event_data in self._batch_buffer:
            event_with_meta = self._add_metadata(event_data)
            message = {
                k: json.dumps(v, default=str) if isinstance(v, (dict, list)) else str(v)
                for k, v in event_with_meta.items()
            }
            pipe.xadd(stream, message)

        await pipe.execute()
        logger.debug(f"Flushed batch of {len(self._batch_buffer)} messages")
        self._batch_buffer.clear()

    async def add_to_batch(self, stream: str, event_data: dict[str, Any]) -> None:
        """Add event to batch buffer (manual batching)."""
        self._batch_buffer.append((stream, event_data))

        if len(self._batch_buffer) >= self._batch_size:
            await self._flush_batch()
