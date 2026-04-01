import uuid

import pytest

from backend.core.zero_copy_bridge import TradingIntent, ZeroCopyBridge


class TestZeroCopyBridge:

    @pytest.fixture
    def bridge(self):
        # Create bridge as creator with unique name
        unique_name = f"test_shm_{uuid.uuid4().hex}"
        bridge = ZeroCopyBridge(max_symbols=10, create=True, shm_name=unique_name)
        yield bridge
        bridge.close()

    def test_initialization(self, bridge):
        assert bridge.shm is not None
        assert bridge.intents is not None
        assert len(bridge.intents) == 10
        assert bridge.INTENT_DTYPE.itemsize == 64

    def test_write_read_intent(self, bridge):
        symbol = "BTC/USD"
        intent = TradingIntent(
            action=1,
            size=0.5,
            confidence=0.9,
            stop_loss=49000.0,
            take_profit=51000.0,
            max_hold_ms=60000,
            entry_price=50000.0,
            timestamp_ns=0,  # Will be overwritten
        )

        # Write
        bridge.write_intent(symbol, intent)

        # Read
        read_intent = bridge.read_intent(symbol)

        assert read_intent is not None
        assert read_intent.action == 1
        assert read_intent.size == pytest.approx(0.5)
        assert read_intent.confidence == pytest.approx(0.9)
        assert read_intent.stop_loss == pytest.approx(49000.0)
        assert read_intent.take_profit == pytest.approx(51000.0)
        assert read_intent.max_hold_ms == 60000
        assert read_intent.entry_price == pytest.approx(50000.0)
        assert read_intent.timestamp_ns > 0

    def test_reader_access(self, bridge):
        # Create a second bridge instance attached to same memory
        reader_bridge = ZeroCopyBridge(
            max_symbols=10, create=False, shm_name=bridge.shm_name
        )

        symbol = "ETH/USD"
        intent = TradingIntent(
            action=-1,
            size=10.0,
            confidence=0.8,
            stop_loss=3100.0,
            take_profit=2900.0,
            max_hold_ms=30000,
            entry_price=3000.0,
            timestamp_ns=0,
        )

        # Write via creator
        bridge.write_intent(symbol, intent)

        # Read via reader
        read_intent = reader_bridge.read_intent(symbol)

        assert read_intent is not None
        assert read_intent.action == -1
        assert read_intent.size == 10.0

        reader_bridge.close()

    def test_no_intent(self, bridge):
        intent = bridge.read_intent("UNKNOWN")
        assert intent is None
