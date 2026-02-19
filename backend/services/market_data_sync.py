"""
Market Data Sync Service with Tiered Intervals, Rate Limiting, and Backoff.
"""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

import backoff
from aiolimiter import AsyncLimiter

from backend.core.cache_layer import get_cache
from backend.core.config.settings import settings

logger = logging.getLogger(__name__)


class MarketDataSync:
    """
    Continuous market data synchronization service.
    Implements tiered intervals:
    - Tier 1 (WATCHED): 1s
    - Tier 2 (POOLED): 30s
    - Tier 3 (ACTIVE): 300s
    """

    def __init__(self, sync_interval: int = 1):
        self.sync_interval = sync_interval
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self.cache = get_cache()

        # Internal limiters for exchange APIs
        self.limiters = {
            "bitvavo": AsyncLimiter(10, 1),  # 10 req/s
            "kraken": AsyncLimiter(5, 1),
            "revolut": AsyncLimiter(10, 1),
        }

        # Foundation symbols
        self.target_symbols = [
            "BTC/EUR",
            "ETH/EUR",
            "SOL/EUR",
            "ADA/EUR",
            "DOT/EUR",
            "XRP/EUR",
            "LINK/EUR",
            "DOGE/EUR",
            "LTC/EUR",
            "XLM/EUR",
        ]

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._sync_loop())
        logger.info("MarketDataSync started with Tiered Refresh Patterns")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("MarketDataSync stopped")

    async def _sync_loop(self):
        iteration = 0
        while self._running:
            try:
                # Tier 1: Every 1s (WATCHED assets)
                await self._fetch_and_cache_tier(tier=1)

                # Tier 2: Every 30 iterations (30s approx)
                if iteration % 30 == 0:
                    await self._fetch_and_cache_tier(tier=2)

                # Tier 3: Every 300 iterations (300s approx)
                if iteration % 300 == 0:
                    await self._fetch_and_cache_tier(tier=3)

            except Exception as e:
                logger.error(f"Sync loop error: {e}")

            iteration += 1
            await asyncio.sleep(self.sync_interval)

    async def _fetch_and_cache_tier(self, tier: int):
        """Fetch and cache markets for a specific tier."""
        # Fetch from multiple exchanges and aggregate
        all_markets = []
        seen_symbols = set()

        # Try multiple exchanges in order of preference
        for exchange_id in ["revolut", "bitvavo", "kraken"]:
            async with self.limiters.get(exchange_id, self.limiters["bitvavo"]):
                try:
                    if exchange_id == "bitvavo":
                        markets = await self._fetch_bitvavo()
                    elif exchange_id == "revolut":
                        markets = await self._fetch_revolut()
                    elif exchange_id == "kraken":
                        markets = await self._fetch_kraken()
                    else:
                        continue

                    if markets:
                        # Store in exchange-specific cache
                        await self.cache.set(f"markets:{exchange_id}", markets, ttl=300)

                        # Add to aggregate list (avoiding duplicates)
                        for m in markets:
                            symbol = m.get("symbol", "")
                            if symbol and symbol not in seen_symbols:
                                all_markets.append(m)
                                seen_symbols.add(symbol)

                        logger.debug(
                            f"Fetched {len(markets)} markets from {exchange_id}"
                        )

                except Exception as e:
                    logger.warning(f"Failed to fetch from {exchange_id}: {e}")

        # Store aggregate in tier-specific cache
        if all_markets:
            await self.cache.set(f"markets:tier{tier}", all_markets, ttl=600)
            await self.cache.set("markets:all", all_markets, ttl=300)
            logger.info(f"Tier {tier} sync complete: {len(all_markets)} markets")
        else:
            logger.warning(f"Tier {tier} sync: no markets fetched")

    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    async def _fetch_bitvavo(self) -> List[Dict[str, Any]]:
        """Fetch markets from Bitvavo."""
        import ccxt.async_support as ccxt

        if not settings.BITVAVO_API_KEY:
            logger.debug("No Bitvavo API key, skipping")
            return []
        exchange = ccxt.bitvavo(
            {"apiKey": settings.BITVAVO_API_KEY, "secret": settings.BITVAVO_API_SECRET}
        )
        try:
            await exchange.load_markets()
            tickers = await exchange.fetch_tickers(self.target_symbols)
            return self._format_tickers(tickers, "bitvavo")
        finally:
            await exchange.close()

    async def _fetch_revolut(self) -> List[Dict[str, Any]]:
        """Fetch markets from Revolut X using the exchange adapter."""
        try:
            from backend.execution.exchange_adapter import ExchangeAdapter

            if not settings.REVOLUT_API_KEY or not settings.REVOLUT_PRIVATE_KEY:
                logger.debug("No Revolut credentials configured")
                return []

            adapter = ExchangeAdapter(
                api_key=settings.REVOLUT_API_KEY,
                private_key_pem=settings.REVOLUT_PRIVATE_KEY,
                base_url="https://revx.revolut.com",
            )

            # Fetch markets using the adapter's get_instruments method
            instruments = await adapter.get_instruments()

            if not instruments:
                logger.debug("No instruments returned from Revolut")
                return []

            markets = []
            target_set = set(self.target_symbols)

            for inst in instruments:
                symbol = inst.get("symbol", "")
                # Convert to our format and check if it's in our target list
                std_symbol = symbol.replace("-", "/")
                if std_symbol in target_set or symbol in [
                    s.replace("/", "-") for s in self.target_symbols
                ]:
                    # Get ticker for this symbol
                    try:
                        ticker = await adapter.get_ticker(symbol)
                        if ticker:
                            markets.append(
                                {
                                    "symbol": symbol,
                                    "price": float(
                                        ticker.get("last", ticker.get("price", 0))
                                    ),
                                    "bid": float(ticker.get("bid", 0)),
                                    "ask": float(ticker.get("ask", 0)),
                                    "volume": float(ticker.get("volume", 0)),
                                    "change_24h": float(
                                        ticker.get(
                                            "change", ticker.get("change_24h", 0)
                                        )
                                    ),
                                    "exchange": "revolut",
                                    "timestamp": datetime.now(UTC).isoformat(),
                                }
                            )
                    except Exception as e:
                        logger.debug(f"Failed to fetch ticker for {symbol}: {e}")

            logger.info(f"Revolut: fetched {len(markets)} markets")
            return markets

        except Exception as e:
            logger.warning(f"Revolut fetch failed: {e}")
            return []

    async def _fetch_kraken(self) -> List[Dict[str, Any]]:
        """Fetch markets from Kraken (public API - no key needed)."""
        import ccxt.async_support as ccxt

        try:
            exchange = ccxt.kraken()
            await exchange.load_markets()

            # Filter for EUR pairs
            kraken_pairs = []
            for symbol in self.target_symbols:
                base, quote = symbol.split("/")
                # Kraken uses XBT/EUR format
                kraken_symbol = f"{base}/{quote}"
                if kraken_symbol in exchange.symbols:
                    kraken_pairs.append(kraken_symbol)

            if not kraken_pairs:
                logger.debug("No matching pairs on Kraken")
                return []

            tickers = await exchange.fetch_tickers(kraken_pairs)
            markets = self._format_tickers(tickers, "kraken")
            await exchange.close()
            return markets

        except Exception as e:
            logger.warning(f"Kraken fetch failed: {e}")
            return []

    def _format_tickers(self, tickers: Dict, exchange_id: str) -> List[Dict[str, Any]]:
        """Format CCXT tickers to our market format."""
        markets = []
        for symbol, ticker in tickers.items():
            markets.append(
                {
                    "symbol": symbol.replace("/", "-"),
                    "price": float(ticker.get("last", 0)),
                    "bid": float(ticker.get("bid", 0)),
                    "ask": float(ticker.get("ask", 0)),
                    "volume": float(ticker.get("baseVolume", ticker.get("volume", 0))),
                    "change_24h": float(ticker.get("percentage", 0)),
                    "high_24h": float(ticker.get("high", 0)),
                    "low_24h": float(ticker.get("low", 0)),
                    "exchange": exchange_id,
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )
        return markets


# Global instance for module-level functions
_market_data_sync_instance: Optional[MarketDataSync] = None


async def start_market_sync() -> None:
    """Start the market data sync service."""
    global _market_data_sync_instance
    _market_data_sync_instance = MarketDataSync()
    await _market_data_sync_instance.start()


async def stop_market_sync() -> None:
    """Stop the market data sync service."""
    global _market_data_sync_instance
    if _market_data_sync_instance:
        await _market_data_sync_instance.stop()
        _market_data_sync_instance = None
