import asyncio
from unittest.mock import MagicMock

import pytest

from backend.market_data.interfaces import EventSink
from backend.market_data.normalizer import StandardNormalizer
from backend.market_data.pipeline import MarketDataPipeline
from backend.market_data.providers.base import BaseExchangeProvider


class MockInjectableProvider(BaseExchangeProvider):
    def __init__(self, name, out_queue=None):
        super().__init__(name, out_queue)
        # BaseExchangeProvider sets self._stopped

    async def _connect_and_stream(self):
        # We don't stream automatically. Data is injected manually into out_queue
        # But run_forever calls this.
        # We just sleep to keep the loop alive.
        await asyncio.sleep(0.1)

    async def inject(self, raw_data):
        await self.out_queue.put((self.name, raw_data))


class MockRedisSink(EventSink):
    def __init__(self):
        self.published = []

    async def publish(self, event):
        self.published.append(event)


@pytest.mark.asyncio
async def test_end_to_end_flow_in_memory():
    """
    Verify: Inject Raw -> Normalize -> Redis Publish -> ClickHouse Enqueue.
    """
    # 1. Setup Validation Components
    redis_sink = MockRedisSink()

    ch_client = MagicMock()
    # ClickHouseWriter
    from backend.market_data.sinks.clickhouse_writer import ClickHouseWriter

    # Use small batch / interval for test
    ch_writer = ClickHouseWriter(ch_client, batch_size=2, flush_interval=0.5)

    # Normalizer
    symbol_map = {("mock", "BTC_RAW"): "BTC/USDT"}
    normalizer = StandardNormalizer(symbol_map)

    # Provider
    provider = MockInjectableProvider("mock")

    # Pipeline
    pipeline = MarketDataPipeline(
        providers=[provider],
        normalizer=normalizer,
        redis_publisher=redis_sink,
        clickhouse_writer=ch_writer,
    )

    # 2. Start Pipeline
    start_task = asyncio.create_task(pipeline.start())

    # Give it a moment to initialize queues
    await asyncio.sleep(0.1)

    # 3. Inject Data
    raw_trade_1 = {
        "type": "trade",
        "symbol": "BTC_RAW",
        "price": 100.0,
        "size": 1.0,
        "side": "buy",
        "ts": 1234567890,
    }
    raw_trade_2 = {
        "type": "trade",
        "symbol": "BTC_RAW",
        "price": 101.0,
        "size": 0.5,
        "side": "sell",
        "ts": 1234567891,
    }

    await provider.inject(raw_trade_1)
    await provider.inject(raw_trade_2)

    # 4. Wait for processing (Redis is async immediate, CH is batched)
    await asyncio.sleep(0.2)

    # Verify Redis (Real-time)
    assert len(redis_sink.published) == 2
    assert redis_sink.published[0].price == 100.0
    assert redis_sink.published[1].price == 101.0
    assert redis_sink.published[0].symbol == "BTC/USDT"

    # Verify ClickHouse (Batched)
    # Batch size is 2. Should have flushed by now?
    # Writer loop checks every flush_interval or when item arrives?
    # My writer loop checks conditions.
    # It might need a bit more time or batch size trigger.

    # Wait for flush interval if needed
    await asyncio.sleep(0.5)

    assert ch_client.insert.called
    args, _ = ch_client.insert.call_args
    # First arg table, second batch
    assert len(args[1]) == 2
    assert args[1][0]["price"] == 100.0

    # 5. Stop
    await pipeline.stop()
    try:
        await start_task
    except asyncio.CancelledError:
        pass
