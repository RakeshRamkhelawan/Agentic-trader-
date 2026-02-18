#!/usr/bin/env python3
"""
Bulk Historical Data Downloader for Agentic Trader Platform.

Downloads OHLCV data for backtesting from multiple exchanges.
Pre-configured with popular trading pairs.

Examples:
    # Download BTC and ETH hourly data for 2023
    python scripts/download_historical_data.py --year 2023 --timeframe 1h
    
    # Download all configured symbols with 15m candles
    python scripts/download_historical_data.py --timeframe 15m --symbols BTC/USDT,ETH/USDT
    
    # Download from Bybit instead of Binance
    python scripts/download_historical_data.py --exchange bybit --year 2024
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.market_data.historical_data_fetcher import (FetchConfig,
                                                         MultiSymbolFetcher)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Popular trading pairs for backtesting
DEFAULT_SYMBOLS = [
    "BTC/USDT",
    "ETH/USDT",
    "SOL/USDT",
    "BNB/USDT",
    "XRP/USDT",
    "ADA/USDT",
    "DOGE/USDT",
    "DOT/USDT",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Download historical crypto data for backtesting"
    )
    parser.add_argument(
        "--exchange",
        default="binance",
        choices=["binance", "bybit", "kraken", "coinbase", "kucoin"],
        help="Exchange to fetch from",
    )
    parser.add_argument(
        "--symbols", help="Comma-separated symbols (e.g., BTC/USDT,ETH/USDT)"
    )
    parser.add_argument(
        "--timeframe",
        default="1h",
        choices=["1m", "5m", "15m", "30m", "1h", "4h", "1d"],
        help="Candle timeframe",
    )
    parser.add_argument("--year", type=int, default=2023, help="Year to download")
    parser.add_argument("--start", help="Start date (YYYY-MM-DD), overrides --year")
    parser.add_argument("--end", help="End date (YYYY-MM-DD), overrides --year")
    parser.add_argument("--output", default="data/historical", help="Output directory")
    parser.add_argument(
        "--concurrent", type=int, default=3, help="Max concurrent downloads"
    )
    parser.add_argument(
        "--test", action="store_true", help="Test mode: download only first symbol"
    )

    return parser.parse_args()


async def main():
    args = parse_args()

    # Determine date range
    if args.start and args.end:
        start_date = datetime.strptime(args.start, "%Y-%m-%d")
        end_date = datetime.strptime(args.end, "%Y-%m-%d")
    else:
        start_date = datetime(args.year, 1, 1)
        end_date = datetime(args.year, 12, 31)

    # Determine symbols
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(",")]
    else:
        symbols = DEFAULT_SYMBOLS

    if args.test:
        symbols = symbols[:1]
        logger.info("TEST MODE: Only downloading first symbol")

    logger.info("=" * 60)
    logger.info("HISTORICAL DATA DOWNLOAD")
    logger.info("=" * 60)
    logger.info(f"Exchange:   {args.exchange}")
    logger.info(f"Symbols:    {len(symbols)} pairs")
    logger.info(f"Timeframe:  {args.timeframe}")
    logger.info(f"Period:     {start_date.date()} to {end_date.date()}")
    logger.info(f"Output:     {args.output}")
    logger.info("=" * 60)

    # Create configs
    configs = [
        FetchConfig(
            exchange_id=args.exchange,
            symbol=symbol,
            timeframe=args.timeframe,
            start_date=start_date,
            end_date=end_date,
            output_dir=args.output,
        )
        for symbol in symbols
    ]

    # Fetch all
    fetcher = MultiSymbolFetcher(output_dir=args.output)
    results = await fetcher.fetch_multiple(configs, max_concurrent=args.concurrent)

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("DOWNLOAD SUMMARY")
    logger.info("=" * 60)

    total_candles = 0
    for symbol, df in results.items():
        candles = len(df)
        total_candles += candles
        logger.info(f"{symbol:15}: {candles:>8,} candles")

    logger.info("-" * 60)
    logger.info(f"{'TOTAL':15}: {total_candles:>8,} candles")
    logger.info(f"{'SYMBOLS':15}: {len(results):>8} pairs")
    logger.info("=" * 60)

    return results


if __name__ == "__main__":
    results = asyncio.run(main())
    sys.exit(0 if results else 1)
