
"""
Market Data Sync Service with Tiered Intervals, Rate Limiting, and Backoff.
"""

import asyncio
import logging
from datetime import datetime, UTC
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
            "bitvavo": AsyncLimiter(10, 1), # 10 req/s
            "kraken": AsyncLimiter(5, 1),
            "revolut": AsyncLimiter(10, 1),
        }

        # Foundation symbols
        self.target_symbols = [
            "BTC/EUR", "ETH/EUR", "SOL/EUR", "ADA/EUR", "DOT/EUR",
            "XRP/EUR", "LINK/EUR", "DOGE/EUR", "LTC/EUR", "XLM/EUR",
        ]

    async def start(self):
        if self._running: return
        self._running = True
        self._task = asyncio.create_task(self._sync_loop())
        logger.info("MarketDataSync started with Tiered Refresh Patterns")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try: await self._task
            except asyncio.CancelledError: pass
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
        # In a real impl, this would query AssetRegistry for symbols by status mirroring tiers
        # Here we simulate with bitvavo for demonstration of the pattern
        async with self.limiters["bitvavo"]:
            try:
                markets = await self._fetch_bitvavo()
                if markets:
                    await self.cache.set(f"markets:tier{tier}", markets, ttl=600)
                    logger.debug(f"Tier {tier} sync complete")
            except Exception as e:
                logger.warning(f"Tier {tier} fetch failed: {e}")

    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    async def _fetch_bitvavo(self) -> List[Dict[str, Any]]:
        import ccxt.async_support as ccxt
        if not settings.BITVAVO_API_KEY: return []
        exchange = ccxt.bitvavo({"apiKey": settings.BITVAVO_API_KEY, "secret": settings.BITVAVO_API_SECRET})
        try:
            await exchange.load_markets()
            tickers = await exchange.fetch_tickers(self.target_symbols)
            return self._format_tickers(tickers, "bitvavo")
        finally:
            await exchange.close()

    def _format_tickers(self, tickers: Dict, exchange_id: str) -> List[Dict]:
        markets = []
        for symbol, ticker in tickers.items():
            markets.append({
                "symbol": symbol.replace("/", "-"),
                "price": float(ticker.get("last", 0)),
                "exchange": exchange_id,
                "timestamp": datetime.now(UTC).isoformat()
            })
        return markets
