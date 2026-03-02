import time
import uuid

import numpy as np
import pytest

from backend.core.zero_copy_bridge import ZeroCopyBridge


class TestMarketDataBridge:
    @pytest.fixture
    def unique_shm_name(self):
        """Generate a unique shared memory name for each test."""
        return f"test_market_shm_{uuid.uuid4().hex}"

    def test_market_data_write_read(self, unique_shm_name):
        # 1. Create Writer
        writer = ZeroCopyBridge(
            max_symbols=5, create=True, shm_name=unique_shm_name, dtype_name="market"
        )

        # 2. Create Reader
        reader = ZeroCopyBridge(
            max_symbols=5, create=False, shm_name=unique_shm_name, dtype_name="market"
        )

        symbol = "BTC/USD"

        # 3. Write Data
        writer.write_market_data(
            symbol=symbol, bid=50000.0, ask=50010.0, last=50005.0, bid_size=1.5, ask_size=2.0
        )

        # 4. Read Data
        data = reader.read_market_data(symbol)

        assert data is not None
        assert data["bid"] == 50000.0
        assert data["ask"] == 50010.0
        assert data["last"] == 50005.0
        assert data["timestamp_ns"] > 0

        # Cleanup
        reader.close()
        writer.close()

    def test_market_data_update(self, unique_shm_name):
        writer = ZeroCopyBridge(
            max_symbols=5, create=True, shm_name=unique_shm_name, dtype_name="market"
        )
        reader = ZeroCopyBridge(
            max_symbols=5, create=False, shm_name=unique_shm_name, dtype_name="market"
        )

        symbol = "ETH/USD"

        # Write initial
        writer.write_market_data(symbol, 2000.0, 2001.0, 2000.5)
        data1 = reader.read_market_data(symbol)
        ts1 = data1["timestamp_ns"]

        time.sleep(0.001)  # Ensure timestamp change

        # Update
        writer.write_market_data(symbol, 2005.0, 2006.0, 2005.5)
        data2 = reader.read_market_data(symbol)
        ts2 = data2["timestamp_ns"]

        assert data2["last"] == 2005.5
        assert ts2 > ts1

        # Cleanup
        reader.close()
        writer.close()
