#!/usr/bin/env python3
"""
Download 6 Years of Historical Crypto Data (2020-2026)
"""

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent.parent))


class SixYearDataDownloader:
    def __init__(self, data_dir: str = "data/historical_6year"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.start_date = datetime(2020, 1, 1)
        self.end_date = datetime(2026, 2, 19)

    async def download_ccxt_chunked(
        self, symbol: str, exchange_id: str = "bitvavo", timeframe: str = "1h"
    ):
        try:
            import ccxt.async_support as ccxt

            exchange_class = getattr(ccxt, exchange_id)
            exchange = exchange_class({"enableRateLimit": True})
            await exchange.load_markets()

            ccxt_symbol = symbol.replace("-", "/")
            if ccxt_symbol not in exchange.symbols:
                ccxt_symbol = symbol.replace("-", "")
                if ccxt_symbol not in exchange.symbols:
                    logger.warning(f"Symbol {symbol} not found on {exchange_id}")
                    await exchange.close()
                    return None

            all_ohlcv = []
            current_date = self.start_date
            chunk_size = timedelta(days=90)

            while current_date < self.end_date:
                chunk_end = min(current_date + chunk_size, self.end_date)
                since = int(current_date.timestamp() * 1000)

                logger.info(f"Fetching {current_date.date()} to {chunk_end.date()}...")

                try:
                    ohlcv = await exchange.fetch_ohlcv(
                        ccxt_symbol, timeframe, since=since, limit=1000
                    )
                    if ohlcv:
                        all_ohlcv.extend(ohlcv)
                        logger.info(
                            f"  Got {len(ohlcv)} candles (total: {len(all_ohlcv)})"
                        )
                        last_ts = pd.to_datetime(ohlcv[-1][0], unit="ms")
                        current_date = last_ts + timedelta(hours=1)
                    else:
                        current_date = chunk_end

                    await asyncio.sleep(exchange.rateLimit / 1000)

                except Exception as e:
                    logger.error(f"Error: {e}")
                    current_date = chunk_end
                    continue

            await exchange.close()

            if not all_ohlcv:
                return None

            df = pd.DataFrame(
                all_ohlcv,
                columns=["timestamp", "open", "high", "low", "close", "volume"],
            )
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df["symbol"] = symbol
            df = df.drop_duplicates(subset=["timestamp"])
            df = df.sort_values("timestamp")

            logger.info(f"✓ Downloaded {len(df):,} rows via {exchange_id}")
            return df

        except Exception as e:
            logger.error(f"CCXT failed: {e}")
            return None

    def save_data(self, df: pd.DataFrame, symbol: str, timeframe: str, source: str):
        if df is None or df.empty:
            return None

        clean_symbol = symbol.replace("/", "-")
        base_name = f"{clean_symbol}_{timeframe}_{self.start_date.year}-{self.end_date.year}_{source}"

        # Save CSV (always works)
        csv_path = self.data_dir / f"{base_name}.csv"
        df.to_csv(csv_path, index=False)
        logger.info(f"✓ Saved CSV: {csv_path}")

        # Try Parquet
        try:
            parquet_path = self.data_dir / f"{base_name}.parquet"
            df.to_parquet(parquet_path, compression="zstd", index=False)
            logger.info(f"✓ Saved Parquet: {parquet_path}")
        except ImportError:
            logger.warning("PyArrow not available, skipping Parquet")

        # Save Pickle
        pickle_path = self.data_dir / f"{base_name}.pkl"
        df.to_pickle(pickle_path)
        logger.info(f"✓ Saved Pickle: {pickle_path}")

        # Metadata
        meta = {
            "symbol": symbol,
            "timeframe": timeframe,
            "source": source,
            "rows": len(df),
            "start_date": df["timestamp"].min().isoformat(),
            "end_date": df["timestamp"].max().isoformat(),
            "file_size_mb": csv_path.stat().st_size / 1024 / 1024,
        }

        meta_path = self.data_dir / f"{base_name}_metadata.json"
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2)
        logger.info(f"✓ Saved metadata: {meta_path}")

        return csv_path

    async def download_symbol(self, symbol: str, timeframe: str = "1h") -> bool:
        logger.info("=" * 70)
        logger.info(f"Downloading 6-year data for {symbol}")
        logger.info(f"Period: {self.start_date.date()} to {self.end_date.date()}")
        logger.info("=" * 70)

        df = None
        source = "unknown"

        # Try Binance first
        logger.info("\n[1/2] Trying Binance...")
        df = await self.download_ccxt_chunked(symbol, "binance", timeframe)
        if df is not None and len(df) > 1000:
            source = "binance"

        # Try Bitvavo as fallback
        if df is None or len(df) < 1000:
            logger.info("\n[2/2] Trying Bitvavo...")
            df_bitvavo = await self.download_ccxt_chunked(symbol, "bitvavo", timeframe)
            if df_bitvavo is not None and len(df_bitvavo) > (
                len(df) if df is not None else 0
            ):
                df = df_bitvavo
                source = "bitvavo"

        if df is None or df.empty:
            logger.error(f"✗ Failed to download {symbol}")
            return False

        logger.info(f"\n[SAVING] {len(df):,} rows from {source}")
        path = self.save_data(df, symbol, timeframe, source)

        if path:
            logger.info(f"\n✓ SUCCESS: {symbol}")
            return True
        return False


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="BTC-EUR")
    parser.add_argument("--symbols", help="Comma-separated")
    parser.add_argument("--timeframe", default="1h", choices=["1d", "1h", "15m"])
    parser.add_argument("--output-dir", default="data/historical_6year")
    args = parser.parse_args()

    symbols = args.symbols.split(",") if args.symbols else [args.symbol]

    print("!" * 70)
    print("6-YEAR HISTORICAL DATA DOWNLOAD")
    print("!" * 70)
    print(f"Symbols: {', '.join(symbols)}")
    print(f"This will download ~{6 * 365 * 24:,} candles per symbol")
    print("Starting in 3 seconds...")
    print("!" * 70)
    import time

    time.sleep(3)

    downloader = SixYearDataDownloader(data_dir=args.output_dir)

    for symbol in symbols:
        print(f"\n{'='*70}")
        print(f"Processing {symbol}...")
        print("=" * 70)
        success = await downloader.download_symbol(symbol, args.timeframe)
        if not success:
            print(f"✗ Failed: {symbol}")

    print("\n" + "=" * 70)
    print("DOWNLOAD COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
