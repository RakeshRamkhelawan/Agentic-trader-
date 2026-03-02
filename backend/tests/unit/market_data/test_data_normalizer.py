"""
TDD Tests for Data Normalizer.

NOTE: These tests are skipped because the interfaces/models modules were never implemented.
These are placeholder tests for a future Fase 4.1 implementation.
"""

import pytest

# Skip all tests if required modules don't exist
pytest.importorskip("backend.market_data.interfaces")
pytest.importorskip("backend.market_data.models")

from backend.market_data.models import EventType, UnifiedMarketEvent

# Expect ImportError
try:
    from backend.market_data.normalizer import StandardNormalizer
except ImportError:
    StandardNormalizer = None


class TestDataNormalizer:
    def setup_method(self):
        self.symbol_map = {("bybit", "BTCUSDT"): "BTC/USDT", ("kraken", "XBT/USDT"): "BTC/USDT"}
        if StandardNormalizer:
            self.normalizer = StandardNormalizer(self.symbol_map)

    def test_normalize_trade_bybit(self):
        """Happy path: Bybit Trade."""
        if not StandardNormalizer:
            pytest.fail("StandardNormalizer not implemented")

        raw = {
            "type": "trade",
            "symbol": "BTCUSDT",
            "price": 50000.0,
            "size": 0.1,
            "side": "buy",
            "ts": 1700000000.0,
        }
        event = self.normalizer.normalize("bybit", raw)

        assert isinstance(event, UnifiedMarketEvent)
        assert event.event_type == EventType.TRADE
        assert event.symbol == "BTC/USDT"
        assert event.venue == "bybit"
        assert event.price == 50000.0

    def test_normalize_ticker_kraken(self):
        """Happy path: Kraken Ticker."""
        if not StandardNormalizer:
            pytest.fail("StandardNormalizer not implemented")

        raw = {
            "type": "ticker",
            "symbol": "XBT/USDT",
            "bid": 49990.0,
            "ask": 50010.0,
            "ts": 1700000000.0,
        }
        event = self.normalizer.normalize("kraken", raw)

        assert event.event_type == EventType.TICKER
        assert event.symbol == "BTC/USDT"
        assert event.venue == "kraken"
        assert event.bid == 49990.0

    def test_unknown_symbol(self):
        """Unhappy path: Unknown symbol."""
        if not StandardNormalizer:
            pytest.fail("StandardNormalizer not implemented")

        raw = {
            "type": "trade",
            "symbol": "UNKNOWN",
            "price": 100,
            "size": 1,
            "side": "buy",
            "ts": 0,
        }

        # Should raise KeyError or custom error. Let's expect KeyError for simplicity.
        with pytest.raises(KeyError):
            self.normalizer.normalize("bybit", raw)

    def test_unknown_event_type(self):
        """Unhappy path: Unknown event type."""
        if not StandardNormalizer:
            pytest.fail("StandardNormalizer not implemented")

        raw = {"type": "unknown", "symbol": "BTCUSDT", "ts": 0}
        with pytest.raises(ValueError):
            self.normalizer.normalize("bybit", raw)
