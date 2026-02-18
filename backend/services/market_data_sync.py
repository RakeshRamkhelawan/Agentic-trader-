"""
Market Data Sync Service

Background service that continuously fetches real-time market data
from configured exchanges (Kraken, Revolut, Bitvavo) and stores
in Redis cache for fast frontend access.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.core.cache_layer import get_cache
from backend.core.config.settings import settings

logger = logging.getLogger(__name__)


class MarketDataSync:
    """
    Continuous market data synchronization service.

    Runs in background, fetching tickers from exchanges every X seconds
    and updating the Redis cache for frontend consumption.
    """

    def __init__(self, sync_interval: int = 10):
        """
        Initialize the sync service.

        Args:
            sync_interval: Seconds between sync cycles (default: 10s)
        """
        self.sync_interval = sync_interval
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self.cache = get_cache()

        # Target symbols (EUR pairs) - Only major pairs supported by most exchanges
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

        logger.info(f"MarketDataSync initialized (interval: {sync_interval}s)")

    async def start(self):
        """Start the background sync loop."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._sync_loop())
        logger.info("MarketDataSync started")

    async def stop(self):
        """Stop the background sync loop."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("MarketDataSync stopped")

    async def _sync_loop(self):
        """Main sync loop."""
        while self._running:
            try:
                await self._fetch_and_cache_all()
            except Exception as e:
                logger.error(f"Market sync error: {e}")

            await asyncio.sleep(self.sync_interval)

    async def _fetch_and_cache_all(self):
        """Fetch data from all configured exchanges and cache."""
        # Try multiple exchanges in order of preference
        exchanges = []

        # Check which exchanges are configured
        if settings.REVOLUT_API_KEY:
            exchanges.append(("revolut", self._fetch_revolut))

        if settings.BITVAVO_API_KEY:
            exchanges.append(("bitvavo", self._fetch_bitvavo))

        # Always fallback to Kraken public API
        exchanges.append(("kraken", self._fetch_kraken_public))

        all_markets = []

        for exchange_id, fetch_func in exchanges:
            try:
                markets = await fetch_func()
                if markets:
                    logger.debug(f"Fetched {len(markets)} markets from {exchange_id}")
                    all_markets.extend(markets)

                    # Cache per exchange
                    await self.cache.set(f"markets:{exchange_id}", markets, ttl=60)

                    # If we got good data, we can stop
                    if len(markets) >= 4:
                        break

            except Exception as e:
                logger.warning(f"Failed to fetch from {exchange_id}: {e}")
                continue

        if all_markets:
            # Deduplicate by symbol
            seen = set()
            unique_markets = []
            for m in all_markets:
                if m["symbol"] not in seen:
                    seen.add(m["symbol"])
                    unique_markets.append(m)

            # Update aggregate cache
            await self.cache.set("markets:all", unique_markets, ttl=60)
            await self.cache.set(
                "markets:last_update", datetime.utcnow().isoformat(), ttl=60
            )

            logger.info(f"Cached {len(unique_markets)} unique markets")

    async def _fetch_kraken_public(self) -> List[Dict[str, Any]]:
        """Fetch public tickers from Kraken."""
        import ccxt.async_support as ccxt

        exchange = ccxt.kraken()
        try:
            await exchange.load_markets()
            tickers = await exchange.fetch_tickers(self.target_symbols)

            markets = []
            for symbol, ticker in tickers.items():
                if not ticker:
                    continue

                base = symbol.split("/")[0] if "/" in symbol else symbol.split("-")[0]
                change = ticker.get("percentage", ticker.get("change", 0))

                markets.append(
                    {
                        "symbol": symbol.replace("/", "-"),
                        "name": base,
                        "price": float(ticker.get("last", 0)),
                        "change": float(change) if change else 0,
                        "change_24h": float(change) if change else 0,
                        "volume": self._format_volume(
                            float(ticker.get("baseVolume", 0))
                        ),
                        "volume_24h": float(ticker.get("baseVolume", 0)),
                        "favorite": False,
                        "exchange": "kraken",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

            return markets
        finally:
            await exchange.close()

    async def _fetch_revolut(self) -> List[Dict[str, Any]]:
        """Fetch tickers from Revolut X using bulk API."""
        from backend.execution.exchange_adapter import ExchangeAdapter

        adapter = ExchangeAdapter(
            api_key=settings.REVOLUT_API_KEY,
            private_key_pem=settings.REVOLUT_PRIVATE_KEY,
            base_url="https://revx.revolut.com"
            if not settings.REVOLUT_SANDBOX
            else "https://sandbox-revx.revolut.com",
        )

        markets = []
        # Revolut symbols are in format BTC-EUR
        revolut_symbols = [s.replace("/", "-") for s in self.target_symbols]

        try:
            # Use bulk API (get_tickers) instead of single (get_ticker) - more reliable
            tickers = await adapter.get_tickers(revolut_symbols)

            for symbol_norm, ticker in tickers.items():
                # symbol_norm is BTC/EUR, convert back to BTC-EUR for display
                symbol_display = symbol_norm.replace("/", "-")
                base = symbol_display.split("-")[0]

                markets.append(
                    {
                        "symbol": symbol_display,
                        "name": base,
                        "price": float(ticker.get("last", 0)),
                        "change": float(ticker.get("change_24h", 0)),
                        "change_24h": float(ticker.get("change_24h", 0)),
                        "volume": self._format_volume(
                            float(ticker.get("volume_24h", 0))
                        ),
                        "volume_24h": float(ticker.get("volume_24h", 0)),
                        "favorite": False,
                        "exchange": "revolut",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )
        except Exception as e:
            logger.warning(f"Revolut bulk fetch error: {e}")

        return markets

    async def _fetch_bitvavo(self) -> List[Dict[str, Any]]:
        """Fetch tickers from Bitvavo."""
        import ccxt.async_support as ccxt

        if not settings.BITVAVO_API_KEY or not settings.BITVAVO_API_SECRET:
            return []

        exchange = ccxt.bitvavo(
            {
                "apiKey": settings.BITVAVO_API_KEY,
                "secret": settings.BITVAVO_API_SECRET,
            }
        )

        try:
            await exchange.load_markets()
            tickers = await exchange.fetch_tickers(self.target_symbols)

            markets = []
            for symbol, ticker in tickers.items():
                if not ticker:
                    continue

                base = symbol.split("/")[0] if "/" in symbol else symbol.split("-")[0]
                change = ticker.get("percentage", ticker.get("change", 0))

                markets.append(
                    {
                        "symbol": symbol.replace("/", "-"),
                        "name": base,
                        "price": float(ticker.get("last", 0)),
                        "change": float(change) if change else 0,
                        "change_24h": float(change) if change else 0,
                        "volume": self._format_volume(
                            float(ticker.get("baseVolume", 0))
                        ),
                        "volume_24h": float(ticker.get("baseVolume", 0)),
                        "favorite": False,
                        "exchange": "bitvavo",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

            return markets
        finally:
            await exchange.close()

    def _format_volume(self, volume: float) -> str:
        """Format volume for display."""
        if volume >= 1_000_000_000:
            return f"{volume / 1_000_000_000:.1f}B"
        if volume >= 1_000_000:
            return f"{volume / 1_000_000:.1f}M"
        if volume >= 1_000:
            return f"{volume / 1_000:.1f}K"
        return str(round(volume, 2))


# Global singleton instance
_market_sync: Optional[MarketDataSync] = None


def get_market_sync() -> MarketDataSync:
    """Get or create the global MarketDataSync instance."""
    global _market_sync
    if _market_sync is None:
        _market_sync = MarketDataSync()
    return _market_sync


async def start_market_sync():
    """Start the global market sync service."""
    sync = get_market_sync()
    await sync.start()


async def stop_market_sync():
    """Stop the global market sync service."""
    global _market_sync
    if _market_sync:
        await _market_sync.stop()
        _market_sync = None
