
import asyncio
import logging
import msgpack
from typing import Optional, Dict, Any
from backend.api.websocket_manager import WebSocketManager
from backend.market_data.models import EventType

logger = logging.getLogger(__name__)

class RedisSubscriber:
    """
    Consumes market events from Redis Stream and pushes to WebSocketManager.
    Connects the Market Data Pipeline (Redis) to the Frontend (WebSocket).
    """
    def __init__(self, redis_client, ws_manager: WebSocketManager, stream_key: str = "market_events"):
        self.redis = redis_client
        self.ws_manager = ws_manager
        self.stream_key = stream_key
        self.running = False

    async def run(self):
        """
        Main consumption loop.
        Reads from the end of the stream ($).
        """
        self.running = True
        last_id = "$" 
        logger.info(f"RedisSubscriber started on stream: {self.stream_key}")
        
        while self.running:
            try:
                # Block for 1000ms, wait for new messages
                # xread returns [[stream_name, [(message_id, data)]]]
                streams = await self.redis.xread({self.stream_key: last_id}, count=100, block=1000)
                
                if not streams:
                    continue
                    
                for stream_name, messages in streams:
                    for message_id, data in messages:
                        last_id = message_id
                        # data is a dict of {b'key': b'value'} usually, or however we stored it.
                        # In RedisPublisher, we stored: {"data": msgpack.packb(event.to_dict())}
                        
                        payload = data.get(b"data") or data.get("data")
                        if payload:
                            try:
                                event_dict = msgpack.unpackb(payload, raw=False) # raw=False for string decoding
                                await self._process_event(event_dict)
                            except Exception as e:
                                logger.error(f"Failed to decode message {message_id}: {e}")
                                
            except asyncio.CancelledError:
                logger.info("RedisSubscriber cancelled.")
                break
            except Exception as e:
                logger.error(f"RedisSubscriber error in loop: {e}")
                await asyncio.sleep(5) # Backoff on error

    async def _process_event(self, event: Dict[str, Any]):
        """
        Process a decoded event dict and broadcast via WebSocketManager.
        """
        try:
            event_type = event.get("event_type")
            symbol = event.get("symbol")
            
            if not event_type or not symbol:
                logger.warning(f"Skipping malformed event: {event}")
                return


            if event_type == EventType.TICKER:
                bid = event.get("bid")
                ask = event.get("ask")
                # Ensure bid/ask are present (can be 0.0 but must be in dict)
                # Actually, simple validation: if bid/ask are None, maybe skip?
                # But get() returns None if missing.
                if bid is None or ask is None:
                    logger.warning(f"Skipping incomplete Ticker event: {event}")
                    return

                await self.ws_manager.broadcast_ticker(
                    symbol=symbol,
                    bid=float(bid),
                    ask=float(ask),
                    last=0.0,
                    volume_24h=0.0,
                    change_24h=0.0,
                    change_percent_24h=0.0,
                    high_24h=0.0,
                    low_24h=0.0
                )
                
            elif event_type == EventType.TRADE:
                price = event.get("price")
                if price is None:
                    logger.warning(f"Skipping incomplete Trade event: {event}")
                    return
                    
                await self.ws_manager.broadcast_ticker(
                    symbol=symbol,
                    bid=0.0, 
                    ask=0.0,
                    last=float(price),
                    volume_24h=0.0,
                    change_24h=0.0,
                    change_percent_24h=0.0,
                    high_24h=0.0,
                    low_24h=0.0
                )
                
            elif event_type == EventType.ORDERBOOK_SNAPSHOT:
                bids = event.get("bids")
                asks = event.get("asks")
                if bids is None or asks is None:
                     return

                await self.ws_manager.broadcast_orderbook(
                    symbol=symbol,
                    bids=bids,
                    asks=asks,
                    is_snapshot=True
                )
                
            elif event_type == EventType.ORDERBOOK_DELTA:
                bids = event.get("bids")
                asks = event.get("asks")
                if bids is None and asks is None: # Delta might have one or other
                     return

                await self.ws_manager.broadcast_orderbook(
                    symbol=symbol,
                    bids=bids or [],
                    asks=asks or [],
                    is_snapshot=False
                )

            elif event_type == "SIGNAL":
                # Generic Signal Broadcast
                signal_data = event.get("data")
                if signal_data:
                    # Broadcast to general signals channel
                    await self.ws_manager.broadcast_to_channel(
                        channel="signals",
                        message=signal_data,
                        message_type="signal"
                    )
                    # Agent specific
                    agent_id = signal_data.get("agent_id")
                    if agent_id:
                        await self.ws_manager.broadcast_to_channel(
                            channel=f"signals.{agent_id}",
                            message=signal_data,
                            message_type="signal"
                        )
                
            else:
                pass 
                # logger.debug(f"Unhandled event type: {event_type}")

        except Exception as e:
            logger.error(f"Error processing event: {e}")
