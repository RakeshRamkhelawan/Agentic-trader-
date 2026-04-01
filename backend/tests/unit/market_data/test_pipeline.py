"""
TDD Tests for Market Data Pipeline.

NOTE: These tests are skipped because the interfaces/models modules were never implemented.
These are placeholder tests for a future Fase 4.1 implementation.
"""

import asyncio

import pytest

# Skip all tests if required modules don't exist
pytest.importorskip("backend.market_data.interfaces")
pytest.importorskip("backend.market_data.models")

from backend.market_data.interfaces import EventSink, ExchangeProvider

# Expect ImportError
try:
    from backend.market_data.pipeline import MarketDataPipeline
except ImportError:
    MarketDataPipeline = None


class MockProvider(ExchangeProvider):
    def __init__(self, name, out_queue, events=None):
        super().__init__(name, out_queue)
        self.events = events or []
        self._stopped = asyncio.Event()

    async def run_forever(self):
        for raw in self.events:
            if self._stopped.is_set():
                break
            await self.out_queue.put((self.name, raw))
            await asyncio.sleep(0.01)
        # Keep running to simulate provider task
        while not self._stopped.is_set():
            await asyncio.sleep(0.1)

    def stop(self):
        self._stopped.set()


class MockSink(EventSink):
    def __init__(self):
        self.events = []

    async def publish(self, event):
        self.events.append(event)


@pytest.mark.skipif(
    MarketDataPipeline is None, reason="MarketDataPipeline not implemented"
)
class TestMarketDataPipeline:
    """Test suite for MarketDataPipeline."""

    @pytest.mark.asyncio
    async def test_pipeline_single_provider_single_sink(self):
        """Happy path: One provider feeding one sink."""
        out_queue = asyncio.Queue()
        provider = MockProvider(
            "bybit",
            out_queue,
            events=[{"type": "trade", "price": 50000.0}],
        )
        sink = MockSink()

        pipeline = MarketDataPipeline([provider], [sink], out_queue)

        # Run pipeline briefly
        task = asyncio.create_task(pipeline.start())
        await asyncio.sleep(0.1)
        pipeline.stop()
        await task

        # Sink should have received normalized event
        assert len(sink.events) >= 1

    @pytest.mark.asyncio
    async def test_pipeline_multiple_providers(self):
        """Multiple providers feeding one sink."""
        out_queue = asyncio.Queue()
        provider1 = MockProvider(
            "bybit", out_queue, events=[{"type": "trade", "price": 50000.0}]
        )
        provider2 = MockProvider(
            "kraken", out_queue, events=[{"type": "ticker", "bid": 49990.0}]
        )

        sink = MockSink()
        pipeline = MarketDataPipeline([provider1, provider2], [sink], out_queue)

        task = asyncio.create_task(pipeline.start())
        await asyncio.sleep(0.2)
        pipeline.stop()
        await task

        # Should have events from both providers
        assert len(sink.events) >= 2

    @pytest.mark.asyncio
    async def test_pipeline_multiple_sinks(self):
        """One provider feeding multiple sinks."""
        out_queue = asyncio.Queue()
        provider = MockProvider(
            "bybit", out_queue, events=[{"type": "trade", "price": 50000.0}]
        )

        sink1 = MockSink()
        sink2 = MockSink()
        pipeline = MarketDataPipeline([provider], [sink1, sink2], out_queue)

        task = asyncio.create_task(pipeline.start())
        await asyncio.sleep(0.1)
        pipeline.stop()
        await task

        # Both sinks should receive the event
        assert len(sink1.events) >= 1
        assert len(sink2.events) >= 1
