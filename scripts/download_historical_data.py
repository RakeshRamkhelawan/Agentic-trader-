#!/usr/bin/env python3
"""
Historical Crypto Data Downloader

Downloads gratis OHLCV data van CryptoDataDownload.com
Geschikt voor backtesting in Agentic Trader Platform

Usage:
    python scripts/download_historical_data.py --symbol BTC-EUR --timeframe 1h
    python scripts/download_historical_data.py --symbol ETH-EUR --timeframe 1d --days 1825
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime, timedelta
from io import StringIO
from pathlib import Path
from typing import Optional
from urllib.request import urlopen

import pandas as pd

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CryptoDataDownloader:
    """
    Download historical crypto data from free sources.
    Primary: CryptoDataDownload.com
    Fallback: CCXT (Bitvavo/Binance)
    """

    def __init__(self, data_dir: str = "data/historical"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def download_cryptodatadownload(
        self, symbol: str, exchange: str = "Bitvavo", timeframe: str = "1h"
    ) -> Optional[pd.DataFrame]:
        """
        Download data from CryptoDataDownload.com

        Args:
            symbol: Trading pair (e.g., 'BTC-EUR')
            exchange: Exchange name (e.g., 'Bitvavo', 'Binance')
            timeframe: '1d', '1h', or '1m'
        """
        # Convert symbol format
        base, quote = symbol.replace("-", "/").split("/")

        # Map timeframes
        tf_map = {"1d": "d", "1h": "h", "1m": "m"}
        tf_code = tf_map.get(timeframe, "h")

        # Build URL
        url = f"https://www.cryptodatadownload.com/cdd/{exchange}_{base}{quote}_{tf_code}.csv"

        logger.info(f"Downloading from: {url}")

        try:
            # Download with user-agent header
            req = urlopen(url)
            data = req.read().decode("utf-8")

            # Parse CSV (skip first row which is usually headers/info)
            lines = data.strip().split("\n")

            # Find the actual header row (usually starts with date)
            header_idx = 0
            for i, line in enumerate(lines[:5]):
                if "date" in line.lower() or "time" in line.lower():
                    header_idx = i
                    break

            # Parse CSV
            df = pd.read_csv(StringIO("\n".join(lines[header_idx:])))

            # Standardize column names
            df.columns = [c.lower().strip() for c in df.columns]

            # Rename common columns
            col_mapping = {
                "date": "timestamp",
                "time": "timestamp",
                "datetime": "timestamp",
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "volume": "volume",
                "vol": "volume",
                "symbol": "symbol",
            }

            df = df.rename(
                columns={k: v for k, v in col_mapping.items() if k in df.columns}
            )

            # Parse timestamp
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
                df = df.sort_values("timestamp")

            # Add symbol column if missing
            if "symbol" not in df.columns:
                df["symbol"] = symbol

            logger.info(f"✓ Downloaded {len(df)} rows")
            return df

        except Exception as e:
            logger.error(f"✗ Failed to download from CryptoDataDownload: {e}")
            return None

    async def download_ccxt(
        self,
        symbol: str,
        exchange_id: str = "bitvavo",
        timeframe: str = "1h",
        since_days: int = 365,
    ) -> Optional[pd.DataFrame]:
        """
        Download data using CCXT (fallback method)

        Args:
            symbol: Trading pair (e.g., 'BTC-EUR')
            exchange_id: 'bitvavo', 'kraken', 'binance'
            timeframe: '1d', '1h', '15m', '5m', '1m'
            since_days: How many days back to fetch
        """
        try:
            import ccxt.async_support as ccxt

            # Initialize exchange
            exchange_class = getattr(ccxt, exchange_id)
            exchange = exchange_class(
                {
                    "enableRateLimit": True,
                }
            )

            await exchange.load_markets()

            # Check if symbol exists
            if (
                symbol.replace("-", "/") not in exchange.symbols
                and symbol.replace("-", "") not in exchange.symbols
            ):
                logger.warning(f"Symbol {symbol} not found on {exchange_id}")
                await exchange.close()
                return None

            # Calculate start timestamp
            since = int(
                (datetime.now() - timedelta(days=since_days)).timestamp() * 1000
            )

            logger.info(
                f"Fetching {symbol} {timeframe} data from {exchange_id} (last {since_days} days)..."
            )

            all_ohlcv = []
            while since < datetime.now().timestamp() * 1000:
                try:
                    ohlcv = await exchange.fetch_ohlcv(
                        symbol.replace("-", "/"), timeframe, since, limit=1000
                    )
                    if not ohlcv:
                        break

                    all_ohlcv.extend(ohlcv)
                    since = ohlcv[-1][0] + 1  # Next timestamp

                    logger.info(f"  Fetched {len(all_ohlcv)} candles...")

                    # Rate limit
                    await asyncio.sleep(exchange.rateLimit / 1000)

                except Exception as e:
                    logger.warning(f"  Fetch error: {e}")
                    break

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

            logger.info(f"✓ Downloaded {len(df)} rows via CCXT")
            return df

        except Exception as e:
            logger.error(f"✗ CCXT download failed: {e}")
            return None

    def save_data(self, df: pd.DataFrame, symbol: str, timeframe: str, source: str):
        """Save DataFrame to CSV and Parquet."""
        if df is None or df.empty:
            return

        # Clean symbol for filename
        clean_symbol = symbol.replace("/", "-").replace("\\", "-")

        # Save to CSV
        csv_path = self.data_dir / f"{clean_symbol}_{timeframe}_{source}.csv"
        df.to_csv(csv_path, index=False)
        logger.info(f"✓ Saved CSV: {csv_path}")

        # Save to Parquet (better for large datasets)
        parquet_path = self.data_dir / f"{clean_symbol}_{timeframe}_{source}.parquet"
        df.to_parquet(parquet_path, index=False)
        logger.info(f"✓ Saved Parquet: {parquet_path}")

        return csv_path, parquet_path

    def get_data_summary(self, df: pd.DataFrame) -> dict:
        """Get summary statistics of downloaded data."""
        if df is None or df.empty:
            return {}

        return {
            "total_rows": len(df),
            "start_date": df["timestamp"].min() if "timestamp" in df.columns else None,
            "end_date": df["timestamp"].max() if "timestamp" in df.columns else None,
            "avg_price": df["close"].mean() if "close" in df.columns else None,
            "min_price": df["low"].min() if "low" in df.columns else None,
            "max_price": df["high"].max() if "high" in df.columns else None,
            "avg_volume": df["volume"].mean() if "volume" in df.columns else None,
        }


async def main():
    parser = argparse.ArgumentParser(
        description="Download historical crypto data for backtesting",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download BTC-EUR hourly data (last ~2 years)
  python scripts/download_historical_data.py --symbol BTC-EUR --timeframe 1h
  
  # Download ETH-EUR daily data
  python scripts/download_historical_data.py --symbol ETH-EUR --timeframe 1d
  
  # Download via CCXT (Bitvavo)
  python scripts/download_historical_data.py --symbol BTC-EUR --source ccxt --days 365
  
  # Download multiple symbols
  python scripts/download_historical_data.py --symbols BTC-EUR,ETH-EUR,SOL-EUR --timeframe 1h
        """,
    )

    parser.add_argument(
        "--symbol", default="BTC-EUR", help="Trading pair (e.g., BTC-EUR)"
    )
    parser.add_argument(
        "--symbols", help="Multiple symbols comma-separated (e.g., BTC-EUR,ETH-EUR)"
    )
    parser.add_argument(
        "--timeframe",
        default="1h",
        choices=["1d", "1h", "15m", "5m", "1m"],
        help="Data granularity (default: 1h)",
    )
    parser.add_argument(
        "--source",
        default="cryptodatadownload",
        choices=["cryptodatadownload", "ccxt"],
        help="Data source (default: cryptodatadownload)",
    )
    parser.add_argument(
        "--exchange",
        default="Bitvavo",
        help="Exchange for CryptoDataDownload (default: Bitvavo)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=365,
        help="Days of history to fetch via CCXT (default: 365)",
    )
    parser.add_argument(
        "--output-dir",
        default="data/historical",
        help="Output directory (default: data/historical)",
    )

    args = parser.parse_args()

    # Initialize downloader
    downloader = CryptoDataDownloader(data_dir=args.output_dir)

    # Determine symbols to download
    symbols = args.symbols.split(",") if args.symbols else [args.symbol]

    print("=" * 70)
    print("HISTORICAL CRYPTO DATA DOWNLOADER")
    print("=" * 70)
    print(f"Source:    {args.source}")
    print(f"Timeframe: {args.timeframe}")
    print(f"Symbols:   {', '.join(symbols)}")
    print(f"Output:    {args.output_dir}")
    print("=" * 70)

    results = []

    for symbol in symbols:
        symbol = symbol.strip()
        print(f"\n📊 Processing {symbol}...")

        # Download based on source
        if args.source == "cryptodatadownload":
            df = downloader.download_cryptodatadownload(
                symbol=symbol, exchange=args.exchange, timeframe=args.timeframe
            )
        else:  # ccxt
            df = await downloader.download_ccxt(
                symbol=symbol, timeframe=args.timeframe, since_days=args.days
            )

        if df is not None and not df.empty:
            # Save data
            paths = downloader.save_data(df, symbol, args.timeframe, args.source)

            # Get summary
            summary = downloader.get_data_summary(df)

            print(f"\n✓ Downloaded {symbol}:")
            print(f"  Rows:      {summary['total_rows']:,}")
            print(f"  Period:    {summary['start_date']} to {summary['end_date']}")
            print(
                f"  Price:     €{summary['min_price']:.2f} - €{summary['max_price']:.2f}"
            )
            print(f"  Avg Price: €{summary['avg_price']:.2f}")
            print(f"  Avg Vol:   {summary['avg_volume']:,.0f}")

            results.append(
                {
                    "symbol": symbol,
                    "success": True,
                    "rows": summary["total_rows"],
                    "paths": paths,
                }
            )
        else:
            print(f"\n✗ Failed to download {symbol}")
            results.append(
                {"symbol": symbol, "success": False, "rows": 0, "paths": None}
            )

    # Summary
    print("\n" + "=" * 70)
    print("DOWNLOAD SUMMARY")
    print("=" * 70)

    successful = sum(1 for r in results if r["success"])
    total_rows = sum(r["rows"] for r in results)

    print(f"Successful: {successful}/{len(results)}")
    print(f"Total rows: {total_rows:,}")
    print(f"\nFiles saved to: {args.output_dir}")
    print("=" * 70)

    return 0 if successful == len(results) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
