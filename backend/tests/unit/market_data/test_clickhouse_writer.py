import asyncio
from unittest.mock import MagicMock

import pytest

# Expect ImportError
try:
    from backend.market_data.sinks.clickhouse_writer import ClickHouseWriter
except ImportError:
    ClickHouseWriter = None


class TestClickHouseWriter:

    @pytest.mark.asyncio
    async def test_batch_flush_on_size(self):
        """Test flushing when batch size is reached."""
        if not ClickHouseWriter:
            pytest.fail("ClickHouseWriter not implemented")

        mock_client = MagicMock()
        mock_client.insert = (
            MagicMock()
        )  # Sync or async? clickhouse-connect is predominantly sync, but we might wrap it.
        # Let's assume we use 'clickhouse_connect' client which is sync, so we run it in executor or if we use 'asynch' it's async.
        # The prompt says: "Async methods... run() -> while loop... insert aanroept op een async ClickHouse client"
        # Let's assume the writer handles the async nature. If using clickhouse-connect, we might wrap in to_thread.

        # We will mock the 'insert' method on the client.

        writer = ClickHouseWriter(mock_client, batch_size=2, flush_interval=10.0)

        # Enqueue 2 items
        await writer.enqueue({"a": 1})
        await writer.enqueue({"a": 2})

        # Run loop briefly
        task = asyncio.create_task(writer.run())
        await asyncio.sleep(0.1)  # Let it process

        # Verify insert called
        assert mock_client.insert.called
        # Check args
        args, _ = mock_client.insert.call_args
        # args[0] = table, args[1] = data
        assert len(args[1]) == 2

        writer.stop()
        await task

    @pytest.mark.asyncio
    async def test_batch_flush_on_interval(self):
        """Test flushing on time interval."""
        if not ClickHouseWriter:
            pytest.fail("ClickHouseWriter not implemented")

        mock_client = MagicMock()
        writer = ClickHouseWriter(mock_client, batch_size=10, flush_interval=0.1)

        await writer.enqueue({"a": 1})

        # Run loop
        task = asyncio.create_task(writer.run())

        # Wait > flush_interval
        await asyncio.sleep(0.2)

        assert mock_client.insert.called
        args, _ = mock_client.insert.call_args
        assert len(args[1]) == 1

        writer.stop()
        await task

    @pytest.mark.asyncio
    async def test_graceful_stop_flushes_remaining(self):
        """Test that stopping flushes the queue."""
        if not ClickHouseWriter:
            pytest.fail("ClickHouseWriter not implemented")

        mock_client = MagicMock()
        writer = ClickHouseWriter(mock_client, batch_size=10, flush_interval=10.0)

        await writer.enqueue({"a": 1})

        task = asyncio.create_task(writer.run())
        await asyncio.sleep(0.01)  # Enqueue processed

        assert not mock_client.insert.called  # Should not have flushed yet

        writer.stop()
        await task

        assert mock_client.insert.called  # Should flush on stop

    @pytest.mark.asyncio
    async def test_data_transformation(self):
        """Test transformation of bids, asks, checksum, and timestamps."""
        if not ClickHouseWriter:
            pytest.fail("ClickHouseWriter not implemented")

        mock_client = MagicMock()
        writer = ClickHouseWriter(mock_client, batch_size=1, flush_interval=0.1)

        from datetime import datetime

        ts = 1700000000.0
        expected_dt = datetime.fromtimestamp(ts)

        # Enqueue item
        item = {
            "symbol": "BTC/USDT",
            "ts_exchange": ts,
            "ts_received": ts,
            "price": 50000.0,
            "bids": [(49990.0, 1.0), (49980.0, 2.0)],
            "asks": [(50010.0, 0.5)],
            "checksum": 123456,
        }
        await writer.enqueue(item)

        # Run loop briefly
        task = asyncio.create_task(writer.run())
        await asyncio.sleep(0.01)  # Small sleep

        writer.stop()
        await task

        assert mock_client.insert.called
        args, kwargs = mock_client.insert.call_args

        # args[0] is table
        data = args[1]
        columns = kwargs.get("column_names")

        assert columns is not None
        assert "bids" not in columns
        assert "asks" not in columns
        assert "checksum" not in columns
        assert "bids_price" in columns
        assert "bids_size" in columns
        assert "asks_price" in columns

        # Verify data row
        row = data[0]
        # Find index of columns
        idx_bids_px = columns.index("bids_price")
        idx_bids_sz = columns.index("bids_size")
        idx_asks_px = columns.index("asks_price")
        idx_ts = columns.index("ts_exchange")

        assert row[idx_bids_px] == [49990.0, 49980.0]
        assert row[idx_bids_sz] == [1.0, 2.0]
        assert row[idx_asks_px] == [50010.0]
        assert row[idx_ts] == expected_dt
