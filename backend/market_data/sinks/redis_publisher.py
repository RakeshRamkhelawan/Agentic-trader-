
import asyncio
import logging
import msgpack
from typing import Optional, Any
from backend.market_data.interfaces import EventSink
from backend.market_data.models import UnifiedMarketEvent

logger = logging.getLogger(__name__)

class RedisPublisher(EventSink):
    """
    Publishes UnifiedMarketEvents to Redis Streams.
    """
    def __init__(self, redis_client, stream_key: str, maxlen: Optional[int] = None):
        self.redis = redis_client
        self.stream_key = stream_key
        self.maxlen = maxlen

    async def publish(self, event: Any):
        """
        Serialize event to MsgPack and publish to Redis Stream.
        Accepts UnifiedMarketEvent or dict.
        """
        try:
            # Serialize to dict -> msgpack bytes
            if hasattr(event, "to_dict"):
                data = event.to_dict()
            elif isinstance(event, dict):
                data = event
            else:
                data = str(event) # Fallback

            # Remove None values to save space? Or keep for schema?
            # to_dict keeps them.
            
            payload = msgpack.packb(data, use_bin_type=True)
            
            # Publish to stream
            # xadd(name, fields, id='*', maxlen=None)
            # fields is a dict of bytes/strings
            fields = {"data": payload}
            
            await self.redis.xadd(self.stream_key, fields, maxlen=self.maxlen)
            
        except Exception as e:
            logger.error(f"Failed to publish to Redis stream {self.stream_key}: {e}")
            raise
