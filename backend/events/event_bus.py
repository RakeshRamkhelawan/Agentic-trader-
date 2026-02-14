"""
EventBus using Redis Streams.

Provides publish/subscribe capabilities using Redis Streams with consumer groups.
"""

import redis.asyncio as redis
from typing import Any, Dict, List, Optional


class EventBus:
    """Redis Streams-based event bus for event-driven architecture."""

    def __init__(self, redis_url: str):
        """
        Initialize EventBus.

        Args:
            redis_url: Redis connection URL (e.g., "redis://localhost:6381")
        """
        self.redis_url = redis_url
        self.client: Optional[redis.Redis] = None

    async def connect(self) -> None:
        """Establish connection to Redis."""
        self.client = redis.from_url(self.redis_url)

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self.client:
            await self.client.aclose()

    async def publish(self, stream: str, event_data: Dict[str, Any]) -> str:
        """
        Publish event to Redis stream.

        Args:
            stream: Stream name
            event_data: Event payload as dictionary

        Returns:
            Message ID from Redis
        """
        if not self.client:
            raise RuntimeError("EventBus not connected. Call connect() first.")

        message_id = await self.client.xadd(stream, event_data)
        return message_id.decode()

    async def subscribe(
        self, stream: str, group: str, consumer: str, count: int = 10, block: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Subscribe to stream using consumer group.

        Args:
            stream: Stream name
            group: Consumer group name
            consumer: Consumer name
            count: Max messages to fetch
            block: Blocking timeout in milliseconds

        Returns:
            List of messages with id and data
        """
        if not self.client:
            raise RuntimeError("EventBus not connected. Call connect() first.")

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
                    messages.append(
                        {
                            "id": message_id.decode(),
                            "data": {
                                k.decode(): v.decode() for k, v in message_data.items()
                            },
                        }
                    )

        return messages

    async def create_consumer_group(
        self, stream: str, group: str, id: str = "0"
    ) -> None:
        """
        Create consumer group for stream.

        Args:
            stream: Stream name
            group: Consumer group name
            id: Starting message ID (default "0" = from beginning)
        """
        if not self.client:
            raise RuntimeError("EventBus not connected. Call connect() first.")

        await self.client.xgroup_create(stream, group, id=id, mkstream=True)

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
            raise RuntimeError("EventBus not connected. Call connect() first.")

        return await self.client.xack(stream, group, message_id)
