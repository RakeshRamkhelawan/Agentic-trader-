#!/usr/bin/env python3
"""
Download 6 Years of Historical Crypto Data (2020-2026)

This script downloads comprehensive OHLCV data for serious backtesting.
Data sources: CryptoDataDownload, Binance, Bitvavo via CCXT

Usage:
    python scripts/download_6year_data.py --symbol BTC-EUR
    python scripts/download_6year_data.py --symbols BTC-EUR,ETH-EUR,SOL-EUR,ADA-EUR
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import pandas as pd

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class SixYearDataDownloader:
    """
    Download and process 6 years of historical crypto data (2020-2026).
    """

    def __init__(self, data_dir: str = "data/historical_6year"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Target date range
        self.start_date = datetime(2020, 1, 1)
        self.end_date = datetime(2026, 2, 19)  # Current date

    def download_cryptodatadownload_yearly(
        self, symbol: str, exchange: str = "Binance", timeframe: str = "1h"
    ) -> Optional[pd.DataFrame]:
        """
        Try to download from CryptoDataDownload (often has multi-year data).
        """
        from io import StringIO

        import requests

        base, quote = (
            symbol.replace("-", "").replace("/", "")[:3],
            symbol.replace("-", "").replace("/", "")[3:],
        )

        # Try different URL patterns
        urls_to_try = [
            f"https://www.cryptodatadownload.com/cdd/{exchange}_{base}{quote}_{timeframe}.csv",
            f"https://www.cryptodatadownload.com/cdd/{exchange}_{base}{quote}_{timeframe.lower()}.csv",
            f"https://www.cryptodatadownload.com/cdd/Binance_{base}{quote}_{timeframe}.csv",
            f"https://www.cryptodatadownload.com/cdd/Coinbase_{base}{quote}_{timeframe}.csv",
        ]

        for url in urls_to_try:
            try:
                logger.info(f"Trying: {url}")
                response = requests.get(url, timeout=30)

                if response.status_code == 200 and len(response.content) > 1000:
                    # Parse CSV
                    lines = response.text.strip().split("\n")

                    # Find header row
                    header_idx = 0
                    for i, line in enumerate(lines[:10]):
                        if any(
                            col in line.lower()
                            for col in ["date", "time", "open", "close"]
                        ):
                            header_idx = i
                            break

                    df = pd.read_csv(StringIO("\n".join(lines[header_idx:])))

                    # Standardize
                    df.columns = [c.lower().strip() for c in df.columns]

                    # Map columns
                    col_map = {}
                    for col in df.columns:
                        if "date" in col or "time" in col:
                            col_map[col] = "timestamp"
                        elif col in ["open", "high", "low", "close", "volume"]:
                            col_map[col] = col

                    df = df.rename(columns=col_map)

                    # Parse timestamp
                    if "timestamp" in df.columns:
                        df["timestamp"] = pd.to_datetime(df["timestamp"])
                        df = df.sort_values("timestamp")

                        # Filter to 2020-2026
                        df = df[
                            (df["timestamp"] >= self.start_date)
                            & (df["timestamp"] <= self.end_date)
                        ]

                    df["symbol"] = symbol

                    logger.info(f"✓ Downloaded {len(df):,} rows from {url}")
                    return df

            except Exception as e:
                logger.debug(f"Failed {url}: {e}")
                continue

        return None

    async def download_ccxt_chunked(
        self, symbol: str, exchange_id: str = "binance", timeframe: str = "1h"
    ) -> Optional[pd.DataFrame]:
        """
        Download data via CCXT in chunks to handle 6 years.
        """
        try:
            import ccxt.async_support as ccxt

            exchange_class = getattr(ccxt, exchange_id)
            exchange = exchange_class({"enableRateLimit": True})

            await exchange.load_markets()

            # Check symbol format
            ccxt_symbol = symbol.replace("-", "/")
            if ccxt_symbol not in exchange.symbols:
                # Try without dash
                ccxt_symbol = symbol.replace("-", "")
                if ccxt_symbol not in exchange.symbols:
                    logger.warning(f"Symbol {symbol} not found on {exchange_id}")
                    await exchange.close()
                    return None

            all_ohlcv = []

            # Download in 3-month chunks to avoid rate limits
            current_date = self.start_date
            chunk_size = timedelta(days=90)  # 3 months

            while current_date < self.end_date:
                chunk_end = min(current_date + chunk_size, self.end_date)

                since = int(current_date.timestamp() * 1000)

                logger.info(f"Fetching {current_date.date()} to {chunk_end.date()}...")

                try:
                    # Fetch with retry
                    for attempt in range(3):
                        try:
                            ohlcv = await exchange.fetch_ohlcv(
                                ccxt_symbol, timeframe, since=since, limit=1000
                            )
                            break
                        except Exception as e:
                            if attempt == 2:
                                raise
                            logger.warning(f"Retry {attempt + 1}: {e}")
                            await asyncio.sleep(2)

                    if ohlcv:
                        all_ohlcv.extend(ohlcv)
                        logger.info(
                            f"  Got {len(ohlcv)} candles (total: {len(all_ohlcv)})"
                        )

                    # Move to next chunk
                    if ohlcv:
                        last_ts = pd.to_datetime(ohlcv[-1][0], unit="ms")
                        current_date = last_ts + timedelta(hours=1)
                    else:
                        current_date = chunk_end

                    # Rate limit
                    await asyncio.sleep(exchange.rateLimit / 1000)

                except Exception as e:
                    logger.error(f"Error fetching chunk: {e}")
                    current_date = chunk_end
                    continue

            await exchange.close()

            if not all_ohlcv:
                return None

            # Convert to DataFrame
            df = pd.DataFrame(
                all_ohlcv,
                columns=["timestamp", "open", "high", "low", "close", "volume"],
            )
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df["symbol"] = symbol

            # Remove duplicates
            df = df.drop_duplicates(subset=["timestamp"])
            df = df.sort_values("timestamp")

            logger.info(f"✓ Downloaded {len(df):,} total rows via CCXT")
            return df

        except Exception as e:
            logger.error(f"CCXT download failed: {e}")
            return None

    def save_optimized(
        self, df: pd.DataFrame, symbol: str, timeframe: str, source: str
    ):
        """Save data in multiple optimized formats."""
        if df is None or df.empty:
            return None

        clean_symbol = symbol.replace("/", "-")
        base_name = f"{clean_symbol}_{timeframe}_{self.start_date.year}-{self.end_date.year}_{source}"

        # 1. Parquet (best for analysis) - skip if pyarrow not available
        try:
            parquet_path = self.data_dir / f"{base_name}.parquet"
            df.to_parquet(parquet_path, compression="zstd", index=False)
            logger.info(
                f"✓ Saved Parquet: {parquet_path} ({parquet_path.stat().st_size / 1024 / 1024:.1f} MB)"
            )
        except ImportError:
            logger.warning("PyArrow not available, skipping Parquet export")
            parquet_path = None

        # 2. Pickle (Python native, fast)
        pickle_path = self.data_dir / f"{base_name}.pkl"
        df.to_pickle(pickle_path)
        logger.info(f"✓ Saved Pickle: {pickle_path}")

        # 3. CSV sample (first 10k rows for inspection)
        if len(df) > 10000:
            csv_sample_path = self.data_dir / f"{base_name}_sample.csv"
            df.head(10000).to_csv(csv_sample_path, index=False)
            logger.info(f"✓ Saved CSV sample: {csv_sample_path}")

        # 4. Metadata
        meta = {
            "symbol": symbol,
            "timeframe": timeframe,
            "source": source,
            "rows": len(df),
            "start_date": df["timestamp"].min().isoformat(),
            "end_date": df["timestamp"].max().isoformat(),
            "columns": list(df.columns),
            "file_size_mb": csv_path.stat().st_size / 1024 / 1024,
        }

        import json

        meta_path = self.data_dir / f"{base_name}_metadata.json"
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)

        return csv_path

    async def download_symbol(self, symbol: str, timeframe: str = "1h") -> bool:
        """Download complete 6-year history for a symbol."""
        logger.info("=" * 70)
        logger.info(f"Downloading 6-year data for {symbol}")
        logger.info(f"Period: {self.start_date.date()} to {self.end_date.date()}")
        logger.info("=" * 70)

        df = None
        source = "unknown"

        # Try 1: CryptoDataDownload (fastest, often has years of data)
        logger.info("\n[1/3] Trying CryptoDataDownload...")
        df = self.download_cryptodatadownload_yearly(symbol, timeframe=timeframe)
        if df is not None and len(df) > 10000:
            source = "cryptodatadownload"

        # Try 2: CCXT + Binance (reliable, good history)
        if df is None or len(df) < 10000:
            logger.info("\n[2/3] Trying CCXT + Binance...")
            df_binance = await self.download_ccxt_chunked(symbol, "binance", timeframe)
            if df_binance is not None and len(df_binance) > (
                len(df) if df is not None else 0
            ):
                df = df_binance
                source = "binance"

        # Try 3: CCXT + Bitvavo (for EUR pairs)
        if df is None or len(df) < 10000:
            logger.info("\n[3/3] Trying CCXT + Bitvavo...")
            df_bitvavo = await self.download_ccxt_chunked(symbol, "bitvavo", timeframe)
            if df_bitvavo is not None and len(df_bitvavo) > (
                len(df) if df is not None else 0
            ):
                df = df_bitvavo
                source = "bitvavo"

        if df is None or df.empty:
            logger.error(f"✗ Failed to download data for {symbol}")
            return False

        # Save
        logger.info(f"\n[SAVING] {len(df):,} rows from {source}")
        path = self.save_optimized(df, symbol, timeframe, source)

        if path:
            logger.info(f"\n✓ SUCCESS: {symbol}")
            logger.info(f"  File: {path}")
            logger.info(f"  Rows: {len(df):,}")
            logger.info(f"  Period: {df['timestamp'].min()} to {df['timestamp'].max()}")
            logger.info(
                f"  Trading days: {(df['timestamp'].max() - df['timestamp'].min()).days}"
            )
            return True

        return False

    async def download_multiple(self, symbols: List[str], timeframe: str = "1h"):
        """Download data for multiple symbols."""
        logger.info("\n" + "=" * 70)
        logger.info("6-YEAR HISTORICAL DATA DOWNLOAD")
        logger.info("=" * 70)
        logger.info(f"Symbols: {', '.join(symbols)}")
        logger.info(f"Timeframe: {timeframe}")
        logger.info(f"Output: {self.data_dir}")
        logger.info("=" * 70)

        results = []

        for i, symbol in enumerate(symbols, 1):
            logger.info(f"\n[{i}/{len(symbols)}] Processing {symbol}...")
            success = await self.download_symbol(symbol, timeframe)
            results.append({"symbol": symbol, "success": success})

            # Small delay between symbols
            if i < len(symbols):
                await asyncio.sleep(2)

        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("DOWNLOAD SUMMARY")
        logger.info("=" * 70)

        successful = sum(1 for r in results if r["success"])
        for r in results:
            status = "✓" if r["success"] else "✗"
            logger.info(f"  {status} {r['symbol']}")

        logger.info(f"\nTotal: {successful}/{len(symbols)} successful")
        logger.info(f"Files saved to: {self.data_dir}")
        logger.info("=" * 70)

        return results


async def main():
    parser = argparse.ArgumentParser(
        description="Download 6 years of historical crypto data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download BTC-EUR 6-year history
  python scripts/download_6year_data.py --symbol BTC-EUR

  # Download multiple symbols
  python scripts/download_6year_data.py --symbols BTC-EUR,ETH-EUR,SOL-EUR,XRP-EUR

  # Daily timeframe (faster, smaller files)
  python scripts/download_6year_data.py --symbols BTC-EUR,ETH-EUR --timeframe 1d
        """,
    )

    parser.add_argument("--symbol", default="BTC-EUR", help="Single symbol to download")
    parser.add_argument("--symbols", help="Multiple symbols comma-separated")
    parser.add_argument(
        "--timeframe",
        default="1h",
        choices=["1d", "1h", "15m"],
        help="Data granularity (default: 1h)",
    )
    parser.add_argument(
        "--output-dir", default="data/historical_6year", help="Output directory"
    )

    args = parser.parse_args()

    # Determine symbols
    symbols = args.symbols.split(",") if args.symbols else [args.symbol]

    # Warn about data size
    estimated_candles = 6 * 365 * 24 if args.timeframe == "1h" else 6 * 365
    estimated_mb = len(symbols) * estimated_candles * 50 / 1024  # ~50 bytes per candle

    print("\n" + "!" * 70)
    print("WARNING: LARGE DOWNLOAD")
    print("!" * 70)
    print("This will download approximately:")
    print(f"  - {len(symbols)} symbol(s)")
    print(f"  - {estimated_candles:,} candles per symbol ({args.timeframe})")
    print(f"  - ~{estimated_mb:.1f} MB total data")
    print("\nThis may take 10-30 minutes depending on your connection.")
    print("!" * 70)

    # Auto-confirm for non-interactive use
    print("\nAuto-continuing (non-interactive mode)...")
    import time

    time.sleep(2)

    # Run download
    downloader = SixYearDataDownloader(data_dir=args.output_dir)

    try:
        results = await downloader.download_multiple(symbols, args.timeframe)
        successful = sum(1 for r in results if r["success"])
        return 0 if successful == len(symbols) else 1

    except KeyboardInterrupt:
        logger.info("\n\nDownload interrupted by user.")
        return 130
    except Exception as e:
        logger.error(f"\n\nError: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
