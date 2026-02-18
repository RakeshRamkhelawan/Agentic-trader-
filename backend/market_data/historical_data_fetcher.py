"""
Historical Crypto Data Fetcher using CCXT.

Downloads OHLCV data from exchanges for backtesting.
Supports: Binance, Bybit, Kraken, Coinbase, etc.

Features:
- Bulk historical data download
- Multiple timeframe support (1m, 5m, 15m, 1h, 4h, 1d)
- Automatic rate limiting
- Resume interrupted downloads
- CSV export for backtest engine

Usage:
    python -m backend.market_data.historical_data_fetcher \
        --exchange binance \
        --symbol BTC/USDT \
        --timeframe 1h \
        --start 2023-01-01 \
        --end 2024-01-01 \
        --output data/historical/
"""

import argparse
import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class FetchConfig:
    """Configuration for historical data fetching."""

    exchange_id: str = "binance"
    symbol: str = "BTC/USDT"
    timeframe: str = "1h"
    start_date: datetime = None
    end_date: datetime = None
    output_dir: str = "data/historical"
    batch_size: int = 1000  # CCXT limit per request
    rate_limit_delay: float = 0.5  # Seconds between requests


class HistoricalDataFetcher:
    """
    Fetch historical OHLCV data from crypto exchanges using CCXT.

    Supports resumable downloads and automatic rate limiting.
    """

    TIMEFRAME_MINUTES = {
        "1m": 1,
        "5m": 5,
        "15m": 15,
        "30m": 30,
        "1h": 60,
        "2h": 120,
        "4h": 240,
        "6h": 360,
        "8h": 480,
        "12h": 720,
        "1d": 1440,
        "3d": 4320,
        "1w": 10080,
    }

    def __init__(self, config: FetchConfig):
        self.config = config
        self.exchange = None
        self._fetched_count = 0

    async def initialize(self):
        """Initialize CCXT exchange."""
        try:
            import ccxt.async_support as ccxt

            exchange_class = getattr(ccxt, self.config.exchange_id)
            self.exchange = exchange_class(
                {
                    "enableRateLimit": True,
                    "options": {
                        "defaultType": "spot",  # or "future" for futures
                    },
                }
            )

            await self.exchange.load_markets()

            # Validate symbol
            if self.config.symbol not in self.exchange.markets:
                available = list(self.exchange.markets.keys())[:10]
                raise ValueError(
                    f"Symbol {self.config.symbol} not available. "
                    f"Examples: {available}"
                )

            logger.info(f"✓ Connected to {self.config.exchange_id}")
            logger.info(f"  Symbol: {self.config.symbol}")
            logger.info(f"  Timeframe: {self.config.timeframe}")

        except Exception as e:
            logger.error(f"Failed to initialize exchange: {e}")
            raise

    async def close(self):
        """Close exchange connection."""
        if self.exchange:
            await self.exchange.close()

    def _get_output_path(self) -> Path:
        """Generate output file path."""
        # Create directory structure: output_dir/exchange/symbol_timeframe.csv
        safe_symbol = self.config.symbol.replace("/", "_")
        filename = f"{safe_symbol}_{self.config.timeframe}.csv"

        output_path = Path(self.config.output_dir) / self.config.exchange_id / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        return output_path

    def _ms_to_datetime(self, ms: int) -> datetime:
        """Convert milliseconds to datetime."""
        return datetime.fromtimestamp(ms / 1000)

    def _datetime_to_ms(self, dt: datetime) -> int:
        """Convert datetime to milliseconds."""
        return int(dt.timestamp() * 1000)

    async def fetch_range(self, start_ms: int, end_ms: int) -> List[List[Any]]:
        """
        Fetch OHLCV data for a specific time range.

        Returns:
            List of [timestamp, open, high, low, close, volume]
        """
        all_candles = []
        current_since = start_ms

        while current_since < end_ms:
            try:
                candles = await self.exchange.fetch_ohlcv(
                    self.config.symbol,
                    self.config.timeframe,
                    since=current_since,
                    limit=self.config.batch_size,
                )

                if not candles:
                    logger.warning(f"No data returned for range {current_since}")
                    break

                all_candles.extend(candles)
                self._fetched_count += len(candles)

                # Get timestamp of last candle
                last_timestamp = candles[-1][0]

                # If we got fewer candles than limit, we've reached the end
                if len(candles) < self.config.batch_size:
                    break

                # Move to next batch (add 1ms to avoid duplicates)
                current_since = last_timestamp + 1

                # Progress logging
                if self._fetched_count % 5000 == 0:
                    progress_pct = (
                        (current_since - start_ms) / (end_ms - start_ms) * 100
                    )
                    logger.info(
                        f"  Fetched {self._fetched_count} candles ({progress_pct:.1f}%)"
                    )

                # Rate limiting
                await asyncio.sleep(self.config.rate_limit_delay)

            except Exception as e:
                logger.error(f"Error fetching data: {e}")
                await asyncio.sleep(5)  # Wait longer on error
                continue

        return all_candles

    async def download(self, resume: bool = True) -> pd.DataFrame:
        """
        Download historical data for the configured range.

        Args:
            resume: If True, resume from existing file

        Returns:
            DataFrame with OHLCV data
        """
        output_path = self._get_output_path()

        # Check for existing data if resuming
        existing_df = None
        if resume and output_path.exists():
            logger.info(f"Found existing file: {output_path}")
            existing_df = pd.read_csv(output_path)
            existing_df["datetime"] = pd.to_datetime(existing_df["datetime"])
            logger.info(f"  Loaded {len(existing_df)} existing candles")

        # Determine time range
        start_ms = self._datetime_to_ms(self.config.start_date)
        end_ms = self._datetime_to_ms(self.config.end_date)

        # Adjust start if resuming
        if existing_df is not None and not existing_df.empty:
            last_timestamp = existing_df["datetime"].max()
            start_ms = max(start_ms, self._datetime_to_ms(last_timestamp))
            logger.info(f"Resuming from {last_timestamp}")

        # Fetch data
        logger.info(
            f"Fetching data from {self.config.start_date} to {self.config.end_date}"
        )
        candles = await self.fetch_range(start_ms, end_ms)

        if not candles:
            if existing_df is not None:
                return existing_df
            raise ValueError("No data fetched")

        # Convert to DataFrame
        df = pd.DataFrame(
            candles, columns=["timestamp", "open", "high", "low", "close", "volume"]
        )

        # Convert timestamp to datetime
        df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms")

        # Merge with existing if resuming
        if existing_df is not None:
            df = pd.concat([existing_df, df], ignore_index=True)
            df = df.drop_duplicates(subset=["timestamp"], keep="first")
            df = df.sort_values("datetime")

        # Save to CSV
        df.to_csv(output_path, index=False)
        logger.info(f"✓ Saved {len(df)} candles to {output_path}")

        return df

    def get_data_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate summary statistics for fetched data."""
        if df.empty:
            return {"error": "Empty dataset"}

        return {
            "total_candles": len(df),
            "start_date": df["datetime"].min().isoformat(),
            "end_date": df["datetime"].max().isoformat(),
            "timeframe": self.config.timeframe,
            "symbol": self.config.symbol,
            "exchange": self.config.exchange_id,
            "avg_price": df["close"].mean(),
            "price_range": {
                "min": df["low"].min(),
                "max": df["high"].max(),
            },
            "avg_volume": df["volume"].mean(),
        }


class MultiSymbolFetcher:
    """Fetch data for multiple symbols concurrently."""

    def __init__(self, output_dir: str = "data/historical"):
        self.output_dir = output_dir
        self.results: Dict[str, pd.DataFrame] = {}

    async def fetch_multiple(
        self, configs: List[FetchConfig], max_concurrent: int = 3
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch data for multiple symbols with concurrency limit.

        Args:
            configs: List of fetch configurations
            max_concurrent: Maximum concurrent downloads

        Returns:
            Dictionary mapping symbol to DataFrame
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def fetch_one(config: FetchConfig) -> tuple:
            async with semaphore:
                fetcher = HistoricalDataFetcher(config)
                await fetcher.initialize()
                try:
                    df = await fetcher.download()
                    summary = fetcher.get_data_summary(df)
                    logger.info(f"\nSummary for {config.symbol}:")
                    for key, value in summary.items():
                        logger.info(f"  {key}: {value}")
                    return config.symbol, df
                finally:
                    await fetcher.close()

        tasks = [fetch_one(cfg) for cfg in configs]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Fetch failed: {result}")
            else:
                symbol, df = result
                self.results[symbol] = df

        return self.results


# ============================================================================
# CLI Interface
# ============================================================================


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Fetch historical crypto data for backtesting"
    )

    parser.add_argument(
        "--exchange",
        "-e",
        default="binance",
        help="Exchange ID (binance, bybit, kraken, coinbase, etc.)",
    )
    parser.add_argument(
        "--symbol",
        "-s",
        default="BTC/USDT",
        help="Trading pair (e.g., BTC/USDT, ETH/USDT)",
    )
    parser.add_argument(
        "--timeframe",
        "-t",
        default="1h",
        choices=["1m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d"],
        help="Candle timeframe",
    )
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument(
        "--output", "-o", default="data/historical", help="Output directory"
    )
    parser.add_argument(
        "--batch-size", type=int, default=1000, help="Candles per request"
    )
    parser.add_argument(
        "--no-resume", action="store_true", help="Don't resume from existing file"
    )

    return parser.parse_args()


async def main():
    """Main entry point."""
    args = parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Parse dates
    start_date = datetime.strptime(args.start, "%Y-%m-%d")
    end_date = datetime.strptime(args.end, "%Y-%m-%d")

    # Create config
    config = FetchConfig(
        exchange_id=args.exchange,
        symbol=args.symbol,
        timeframe=args.timeframe,
        start_date=start_date,
        end_date=end_date,
        output_dir=args.output,
        batch_size=args.batch_size,
    )

    # Fetch data
    fetcher = HistoricalDataFetcher(config)
    await fetcher.initialize()

    try:
        df = await fetcher.download(resume=not args.no_resume)

        # Print summary
        summary = fetcher.get_data_summary(df)
        print("\n" + "=" * 60)
        print("DOWNLOAD COMPLETE")
        print("=" * 60)
        for key, value in summary.items():
            print(f"{key:20}: {value}")

    finally:
        await fetcher.close()


if __name__ == "__main__":
    asyncio.run(main())
