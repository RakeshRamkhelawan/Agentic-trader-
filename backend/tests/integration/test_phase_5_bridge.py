import asyncio
from unittest.mock import AsyncMock

import pytest
import redis.asyncio as redis

from backend.market_data.models import EventType, UnifiedMarketEvent
from backend.market_data.sinks.redis_publisher import RedisPublisher
from backend.market_data.sinks.redis_subscriber import RedisSubscriber

# Configuration
REDIS_URL = "redis://localhost:6381/0"
STREAM_KEY = "market_events_test"


@pytest.fixture
async def redis_client():
    client = redis.from_url(REDIS_URL, decode_responses=False)
    await client.flushdb()  # Clean start
    yield client
    await client.close()


@pytest.fixture
def mock_ws_manager():
    return AsyncMock()


@pytest.mark.asyncio
async def test_redis_bridge_e2e(redis_client, mock_ws_manager):
    """
    E2E Test: Publisher -> Redis Stream -> Subscriber -> WebSocket Manager
    """
    # 1. Setup Publisher
    publisher = RedisPublisher(redis_client, STREAM_KEY)

    # 2. Setup Subscriber
    subscriber = RedisSubscriber(redis_client, mock_ws_manager, STREAM_KEY)

    # 3. Start Subscriber in Background Task
    subscriber_task = asyncio.create_task(subscriber.run())

    try:
        # Allow subscriber to start and poll
        await asyncio.sleep(0.5)

        # 4. Create Event
        event = UnifiedMarketEvent(
            event_type=EventType.TRADE,
            venue="bybit",
            symbol="BTC/USDT",
            price=50100.0,
            size=0.5,
            side="buy",
            ts_exchange=1600000000.0,
            ts_received=1600000001.0,
        )

        # 5. Publish Event
        await publisher.publish(event)

        # 6. Wait for processing (Subscriber polls every ~100-1000ms + processing time)
        # Our subscriber implementation blocks for 1000ms on xread, so it might take up to 1s to return if idle,
        # or immediately if data is ready?
        # Actually xread returns immediately if data is ready or waits up to block time.
        # But if it was already waiting, it returns immediately when data arrives.
        await asyncio.sleep(2.0)

        # 7. Assert WebSocket Broadcast
        # Expect 'broadcast_ticker' call because TRADE mapped to ticker update
        mock_ws_manager.broadcast_ticker.assert_called_once()
        call_args = mock_ws_manager.broadcast_ticker.call_args[1]

        assert call_args["symbol"] == "BTC/USDT"
        assert call_args["last"] == 50100.0

        print("\n[SUCCESS] Event published to Redis and received by WebSocketManager mock!")

    finally:
        # Cleanup
        subscriber_task.cancel()
        try:
            await subscriber_task
        except asyncio.CancelledError:
            pass
