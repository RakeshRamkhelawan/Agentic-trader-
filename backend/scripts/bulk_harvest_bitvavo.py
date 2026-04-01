"""
Bulk Harvest Bitvavo - Fetching all available symbols (8 years).

This script identifies all /EUR and /USDT pairs and fetches their
full historical 1d OHLCV data in parallel with rate limiting.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import List

import ccxt.async_support as ccxt
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class BulkHarvester:
    def __init__(self, output_dir: str = "data/historical/bitvavo/full_catalog"):
        self.output_dir = output_dir
        self.exchange = ccxt.bitvavo({"enableRateLimit": True, "options": {"defaultType": "spot"}})
        os.makedirs(self.output_dir, exist_ok=True)

    async def fetch_ohlcv(self, symbol: str, base_start_date: str):
        """Fetch full OHLCV for a symbol with resilient start date lookups."""
        years_to_try = ["2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025"]
        all_ohlcv = []
        since = None

        # Try finding the earliest possible start year
        for year in years_to_try:
            if year < base_start_date[:4]:
                continue

            try:
                candidate_since = self.exchange.parse8601(f"{year}-01-01T00:00:00Z")
                ohlcv = await self.exchange.fetch_ohlcv(
                    symbol, timeframe="1d", since=candidate_since, limit=1
                )
                if ohlcv:
                    since = candidate_since
                    logger.info(f"  Found start date for {symbol}: {year}")
                    break
            except Exception:
                continue

        if since is None:
            logger.warning(f"  No historical data found for {symbol} after trying all years.")
            return

        try:
            while since < self.exchange.milliseconds():
                ohlcv = await self.exchange.fetch_ohlcv(
                    symbol, timeframe="1d", since=since, limit=1000
                )
                if not ohlcv:
                    break
                all_ohlcv.extend(ohlcv)
                since = ohlcv[-1][0] + 86400000  # Jump to next day

                if len(ohlcv) < 1000:
                    break

            if not all_ohlcv:
                logger.warning(f"No data found for {symbol}")
                return

            # Convert to DataFrame
            df = pd.DataFrame(
                all_ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
            )
            df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms")

            # Save CSV
            safe_symbol = symbol.replace("/", "_")
            file_path = os.path.join(self.output_dir, f"{safe_symbol}_1d.csv")
            df.to_csv(file_path, index=False)
            logger.info(f"✓ Saved {len(df)} candles for {symbol}")

        except Exception as e:
            logger.error(f"Error fetching {symbol}: {e}")

    async def run(self, start_date: str = "2018-01-01"):
        """Run the bulk harvest."""
        logger.info("Initializing markets...")
        await self.exchange.load_markets()

        # Filter symbols: /EUR or /USDT
        symbols = [s for s in self.exchange.symbols if s.endswith("/EUR") or s.endswith("/USDT")]
        logger.info(f"Targeting {len(symbols)} symbols for harvest.")

        # Semaphore to limit concurrency (staying safe with rate limits)
        semaphore = asyncio.Semaphore(10)

        async def sem_fetch(symbol):
            async with semaphore:
                await self.fetch_ohlcv(symbol, start_date)

        tasks = [sem_fetch(s) for s in symbols]
        await asyncio.gather(*tasks)

        await self.exchange.close()
        logger.info("Bulk Harvest Complete.")


if __name__ == "__main__":
    harvester = BulkHarvester()
    asyncio.run(harvester.run())
