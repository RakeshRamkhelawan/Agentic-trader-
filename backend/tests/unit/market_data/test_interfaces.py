"""
TDD Tests for Market Data Interfaces.

NOTE: These tests are skipped because the interfaces module was never implemented.
These are placeholder tests for a future Fase 4.1 implementation.
"""

import asyncio

import pytest

# Skip all tests if interfaces module doesn't exist
pytest.importorskip("backend.market_data.interfaces")
pytest.importorskip("backend.market_data.models")

from backend.market_data.interfaces import DataNormalizer, EventSink, ExchangeProvider
from backend.market_data.models import EventType, UnifiedMarketEvent


class MockProvider(ExchangeProvider):
    """Mock implementation of ExchangeProvider."""

    def __init__(self, name: str, out_queue: asyncio.Queue):
        super().__init__(name, out_queue)
        self.stopped = False

    async def run_forever(self):
        # Allow stopping logic to be tested
        while not self.stopped:
            await asyncio.sleep(0.1)

    def stop(self):
        self.stopped = True


class MockNormalizer(DataNormalizer):
    """Mock implementation of DataNormalizer."""

    def normalize(self, venue: str, raw: dict) -> UnifiedMarketEvent:
        return UnifiedMarketEvent(
            event_type=EventType.TRADE,
            venue=venue,
            symbol="BTC/USDT",
            ts_exchange=1700000000.0,
            ts_received=1700000000.1,
            price=100.0,
            size=1.0,
            side="buy",
        )


class InMemorySink(EventSink):
    """Mock Sink that stores events in a list."""

    def __init__(self):
        self.events: list[UnifiedMarketEvent] = []

    async def publish(self, event: UnifiedMarketEvent):
        self.events.append(event)


@pytest.mark.asyncio
async def test_provider_interface():
    """Test that ExchangeProvider enforces interface."""
    queue = asyncio.Queue()
    provider = MockProvider("mock", queue)
    assert provider.name == "mock"
    assert provider.out_queue == queue

    # Test stop mechanism
    task = asyncio.create_task(provider.run_forever())
    await asyncio.sleep(0.05)
    provider.stop()
    await task
    assert provider.stopped


@pytest.mark.asyncio
async def test_normalizer_interface():
    """Test that DataNormalizer enforces interface."""
    normalizer = MockNormalizer({})
    event = normalizer.normalize("bybit", {"type": "trade"})
    assert isinstance(event, UnifiedMarketEvent)
    assert event.venue == "bybit"


@pytest.mark.asyncio
async def test_sink_interface():
    """Test that EventSink enforces interface."""
    sink = InMemorySink()
    event = UnifiedMarketEvent(
        event_type=EventType.TRADE,
        venue="bybit",
        symbol="BTC/USDT",
        ts_exchange=1700000000.0,
        ts_received=1700000000.1,
        price=100.0,
        size=1.0,
        side="buy",
    )
    await sink.publish(event)
    assert len(sink.events) == 1
    assert sink.events[0] == event
