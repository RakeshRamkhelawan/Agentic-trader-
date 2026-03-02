from unittest.mock import MagicMock

import pytest

# Expect ImportError initially
try:
    from backend.market_data.providers.bybit_provider import BybitProvider
except ImportError:
    BybitProvider = None

# Sample Data based on Bybit V5 Websocket Docs
SAMPLE_TRADE_MSG = {
    "topic": "publicTrade.BTCUSDT",
    "type": "snapshot",
    "ts": 1672304486868,
    "data": [
        {
            "T": 1672304486865,
            "s": "BTCUSDT",
            "S": "Buy",
            "v": "0.001",
            "p": "16578.50",
            "L": "PlusTick",
            "i": "20f43950-d8dd-5b31-9112-a1ce8b0c8d50",
            "BT": False,
        }
    ],
}

SAMPLE_TICKER_MSG = {
    "topic": "tickers.BTCUSDT",
    "type": "snapshot",
    "cs": 24987956059,
    "ts": 1672304486868,
    "data": {
        "symbol": "BTCUSDT",
        "tickDirection": "PlusTick",
        "price24hPcnt": "0.0123",
        "lastPrice": "16578.50",
        "prevPrice24h": "16376.50",
        "highPrice24h": "16698.00",
        "lowPrice24h": "16375.00",
        "turnover24h": "24987.5",
        "volume24h": "1.5",
        "usdIndexPrice": "16578.50",
        "bid1Price": "16578.00",
        "bid1Size": "1.5",
        "ask1Price": "16578.50",
        "ask1Size": "0.5",
    },
}


class TestBybitProvider:
    def setup_method(self):
        if BybitProvider is None:
            pytest.fail("BybitProvider not implemented")
        self.provider = BybitProvider("bybit", MagicMock())

    def test_parse_trade(self):
        """Test parsing of trade message."""
        raw_events = self.provider._parse_raw(SAMPLE_TRADE_MSG)
        assert len(raw_events) == 1
        event = raw_events[0]

        # Check normalized raw structure
        assert event["type"] == "trade"
        assert event["symbol"] == "BTCUSDT"
        assert event["price"] == 16578.50
        assert event["size"] == 0.001
        assert event["side"] == "buy"  # "Buy" -> "buy"
        assert event["ts"] == 1672304486.865  # T field (ms to s)

    def test_parse_ticker(self):
        """Test parsing of ticker message."""
        raw_events = self.provider._parse_raw(SAMPLE_TICKER_MSG)
        # Ticker might return 1 event
        assert len(raw_events) >= 1
        event = raw_events[0]

        assert event["type"] == "ticker"
        assert event["symbol"] == "BTCUSDT"
        assert event["bid"] == 16578.00
        assert event["ask"] == 16578.50
        assert event["ts"] == 1672304486.868  # ts field

    def test_parse_unknown_topic(self):
        """Test ignoring unknown topics."""
        msg = {"topic": "unknown", "data": {}}
        raw_events = self.provider._parse_raw(msg)
        assert len(raw_events) == 0

    def test_parse_empty_data(self):
        """Test handling empty data list (heartbeats?)."""
        msg = {"topic": "publicTrade.BTCUSDT", "ts": 123, "type": "snapshot", "data": []}
        raw_events = self.provider._parse_raw(msg)
        assert len(raw_events) == 0
