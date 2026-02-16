import logging
import json
from typing import Any, Dict

import redis.asyncio as redis

logger = logging.getLogger(__name__)

class RedisPublisher:
    """
    Publishes events to a Redis Stream or PubSub.
    """
    def __init__(self, client: redis.Redis, stream_key: str):
        self.client = client
        self.stream_key = stream_key

    async def publish(self, message: Dict[str, Any]):
        """Publish message to Redis Stream."""
        try:
            # Use XADD for streams
            # Redis streams require dict keys to be strings, values to be strings/bytes/numbers
            # We might need to serialize complex objects to JSON string before sending
            
            # Simple approach: JSON dump the whole payload into a 'data' field
            payload_str = json.dumps(message, default=str)
            
            await self.client.xadd(
                self.stream_key,
                {"data": payload_str}
            )
        except Exception as e:
            logger.error(f"Failed to publish to Redis stream {self.stream_key}: {e}")
