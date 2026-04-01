"""
Unit tests for Historical Data Fetcher.
"""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.market_data.historical_data_fetcher import (
    FetchConfig,
    HistoricalDataFetcher,
    MultiSymbolFetcher,
)


class TestFetchConfig:
    """Test FetchConfig dataclass."""

    def test_default_values(self):
        config = FetchConfig()
        assert config.exchange_id == "binance"
        assert config.symbol == "BTC/USDT"
        assert config.timeframe == "1h"
        assert config.batch_size == 1000

    def test_custom_values(self):
        config = FetchConfig(
            exchange_id="bybit", symbol="ETH/USDT", timeframe="15m", batch_size=500
        )
        assert config.exchange_id == "bybit"
        assert config.symbol == "ETH/USDT"
        assert config.timeframe == "15m"
        assert config.batch_size == 500


class TestHistoricalDataFetcher:
    """Test HistoricalDataFetcher class."""

    @pytest.fixture
    def config(self):
        return FetchConfig(
            exchange_id="binance",
            symbol="BTC/USDT",
            timeframe="1h",
            start_date=datetime(2023, 1, 1),
            end_date=datetime(2023, 1, 31),
            output_dir=tempfile.mkdtemp(),
        )

    @pytest.fixture
    def fetcher(self, config):
        return HistoricalDataFetcher(config)

    def test_init(self, fetcher, config):
        assert fetcher.config == config
        assert fetcher.exchange is None
        assert fetcher._fetched_count == 0

    def test_get_output_path(self, fetcher):
        path = fetcher._get_output_path()
        assert "binance" in str(path)
        assert "BTC_USDT_1h.csv" in str(path)

    def test_ms_datetime_conversion(self, fetcher):
        dt = datetime(2023, 1, 1, 0, 0, 0)
        ms = fetcher._datetime_to_ms(dt)
        back = fetcher._ms_to_datetime(ms)
        assert back == dt

    @pytest.mark.asyncio
    async def test_initialize_mock(self, fetcher):
        """Test initialization with mocked CCXT."""
        mock_exchange = MagicMock()
        mock_exchange.markets = {"BTC/USDT": {}}
        mock_exchange.load_markets = AsyncMock(return_value={"BTC/USDT": {}})

        with patch("ccxt.async_support.binance") as mock_ccxt:
            mock_ccxt.return_value = mock_exchange
            await fetcher.initialize()

        assert fetcher.exchange is not None

    @pytest.mark.asyncio
    async def test_fetch_range_mock(self, fetcher):
        """Test fetch_range with mocked exchange."""
        # Mock candles: [timestamp, open, high, low, close, volume]
        mock_candles = [
            [1609459200000, 29000.0, 29100.0, 28900.0, 29050.0, 100.0],
            [1609462800000, 29050.0, 29200.0, 29000.0, 29150.0, 150.0],
        ]

        fetcher.exchange = MagicMock()
        fetcher.exchange.fetch_ohlcv = AsyncMock(return_value=mock_candles)

        start_ms = 1609459200000
        end_ms = 1609466400000

        candles = await fetcher.fetch_range(start_ms, end_ms)

        assert len(candles) == 2
        assert candles[0][0] == 1609459200000
        fetcher.exchange.fetch_ohlcv.assert_called_once()

    @pytest.mark.asyncio
    async def test_download_with_mock(self, fetcher):
        """Test full download flow with mocks."""
        mock_candles = [
            [1609459200000, 29000.0, 29100.0, 28900.0, 29050.0, 100.0],
            [1609462800000, 29050.0, 29200.0, 29000.0, 29150.0, 150.0],
            [1609466400000, 29150.0, 29300.0, 29100.0, 29250.0, 200.0],
        ]

        fetcher.exchange = MagicMock()
        fetcher.exchange.fetch_ohlcv = AsyncMock(return_value=mock_candles)

        df = await fetcher.download(resume=False)

        assert len(df) == 3
        assert "datetime" in df.columns
        assert "open" in df.columns
        assert "close" in df.columns
        assert "volume" in df.columns

        # Check CSV was saved
        output_path = fetcher._get_output_path()
        assert output_path.exists()

    def test_get_data_summary(self, fetcher):
        """Test summary generation."""
        import pandas as pd

        df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=3, freq="h"),
                "open": [29000.0, 29100.0, 29200.0],
                "high": [29100.0, 29200.0, 29300.0],
                "low": [28900.0, 29000.0, 29100.0],
                "close": [29050.0, 29150.0, 29250.0],
                "volume": [100.0, 150.0, 200.0],
            }
        )

        summary = fetcher.get_data_summary(df)

        assert summary["total_candles"] == 3
        assert summary["symbol"] == "BTC/USDT"
        assert summary["timeframe"] == "1h"
        assert "avg_price" in summary
        assert "price_range" in summary


class TestMultiSymbolFetcher:
    """Test MultiSymbolFetcher class."""

    @pytest.mark.asyncio
    async def test_fetch_multiple(self):
        """Test fetching multiple symbols concurrently."""
        configs = [
            FetchConfig(
                exchange_id="binance",
                symbol="BTC/USDT",
                timeframe="1h",
                start_date=datetime(2023, 1, 1),
                end_date=datetime(2023, 1, 2),
                output_dir=tempfile.mkdtemp(),
            ),
            FetchConfig(
                exchange_id="binance",
                symbol="ETH/USDT",
                timeframe="1h",
                start_date=datetime(2023, 1, 1),
                end_date=datetime(2023, 1, 2),
                output_dir=tempfile.mkdtemp(),
            ),
        ]

        fetcher = MultiSymbolFetcher()

        # Mock the individual fetchers
        import pandas as pd

        mock_df = pd.DataFrame(
            {
                "datetime": pd.date_range("2023-01-01", periods=2, freq="h"),
                "open": [28900.0, 29000.0],
                "high": [29100.0, 29200.0],
                "low": [28800.0, 28900.0],
                "close": [29000.0, 29100.0],
                "volume": [100.0, 150.0],
            }
        )

        with patch.object(HistoricalDataFetcher, "initialize", new=AsyncMock()):
            with patch.object(HistoricalDataFetcher, "close", new=AsyncMock()):
                with patch.object(
                    HistoricalDataFetcher,
                    "download",
                    new=AsyncMock(return_value=mock_df),
                ):
                    results = await fetcher.fetch_multiple(configs, max_concurrent=2)

        assert len(results) == 2
        assert "BTC/USDT" in results
        assert "ETH/USDT" in results


class TestIntegration:
    """Integration tests with real data format."""

    def test_csv_format_compatibility(self):
        """Verify CSV format works with HistoricalCSVData feed."""

        from backend.backtesting.data_feed_historical import HistoricalCSVData

        # Create test CSV in expected format
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("timestamp,open,high,low,close,volume,datetime\n")
            f.write("1609459200000,29000.0,29100.0,28900.0,29050.0,100.0,2021-01-01 00:00:00\n")
            f.write("1609462800000,29050.0,29200.0,29000.0,29150.0,150.0,2021-01-01 01:00:00\n")
            csv_path = f.name

        # Load with HistoricalCSVData
        feed = HistoricalCSVData(csv_path)
        feed.load_data(
            symbols=["BTC/USDT"],
            start_date=datetime(2021, 1, 1),
            end_date=datetime(2021, 1, 2),
        )

        bar = feed.get_latest_bar("BTC/USDT")
        assert bar is not None
        assert bar["open"] == 29000.0
        assert bar["close"] == 29050.0
        assert bar["volume"] == 100.0

        # Cleanup
        Path(csv_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
