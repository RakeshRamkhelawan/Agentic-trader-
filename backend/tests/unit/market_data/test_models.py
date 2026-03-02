"""
TDD Tests for Market Data Models.

NOTE: These tests are skipped because the models module was never implemented.
These are placeholder tests for a future Fase 4.1 implementation.
"""

import pytest

# Skip all tests if models module doesn't exist
pytest.importorskip("backend.market_data.models")

from backend.market_data.models import EventType, UnifiedMarketEvent


def test_unified_market_event_happy_path_trade():
    """Test creating a valid TRADE event."""
    event = UnifiedMarketEvent(
        event_type=EventType.TRADE,
        venue="bybit",
        symbol="BTC/USDT",
        ts_exchange=1700000000.0,
        ts_received=1700000000.1,
        price=50000.0,
        size=0.1,
        side="buy",
    )
    event.validate()
    assert event.venue == "bybit"
    assert event.price == 50000.0


def test_unified_market_event_happy_path_ticker():
    """Test creating a valid TICKER event."""
    event = UnifiedMarketEvent(
        event_type=EventType.TICKER,
        venue="kraken",
        symbol="ETH/USD",
        ts_exchange=1700000000.0,
        ts_received=1700000000.2,
        bid=2000.0,
        ask=2001.0,
    )
    event.validate()
    assert event.bid == 2000.0


def test_unified_market_event_orderbook_snapshot():
    """Test creating a valid ORDERBOOK_SNAPSHOT event."""
    event = UnifiedMarketEvent(
        event_type=EventType.ORDERBOOK_SNAPSHOT,
        venue="bybit",
        symbol="BTC/USDT",
        ts_exchange=1700000000.0,
        ts_received=1700000000.3,
        bids=[(49999.0, 1.0), (49998.0, 0.5)],
        asks=[(50000.0, 0.5), (50001.0, 1.0)],
    )
    event.validate()
    assert len(event.bids) == 2


def test_validation_negative_price():
    """Test that negative price raises ValueError."""
    event = UnifiedMarketEvent(
        event_type=EventType.TRADE,
        venue="bybit",
        symbol="BTC/USDT",
        ts_exchange=1700000000.0,
        ts_received=1700000000.1,
        price=-100.0,  # Invalid
        size=1.0,
        side="buy",
    )
    with pytest.raises(ValueError, match="Price must be positive"):
        event.validate()


def test_validation_negative_size():
    """Test that negative size raises ValueError."""
    event = UnifiedMarketEvent(
        event_type=EventType.TRADE,
        venue="bybit",
        symbol="BTC/USDT",
        ts_exchange=1700000000.0,
        ts_received=1700000000.1,
        price=50000.0,
        size=-1.0,  # Invalid
        side="buy",
    )
    with pytest.raises(ValueError, match="Size must be positive"):
        event.validate()


def test_validation_invalid_side():
    """Test that invalid side raises ValueError."""
    event = UnifiedMarketEvent(
        event_type=EventType.TRADE,
        venue="bybit",
        symbol="BTC/USDT",
        ts_exchange=1700000000.0,
        ts_received=1700000000.1,
        price=50000.0,
        size=1.0,
        side="invalid_side",  # Invalid
    )
    with pytest.raises(ValueError, match="Side must be 'buy' or 'sell'"):
        event.validate()
