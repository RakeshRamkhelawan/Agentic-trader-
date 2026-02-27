"""
Multi-Exchange Price Aggregator

Combines price data from multiple exchanges for:
- Best price discovery
- Price discrepancy detection
- Arbitrage opportunity identification
- Smart order routing decisions
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ExchangePrice:
    """Price data from a single exchange."""

    exchange: str
    symbol: str
    bid: float
    ask: float
    last: float
    volume_24h: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    latency_ms: float = 0.0
    confidence: float = 1.0  # 0-1 based on data freshness

    @property
    def spread(self) -> float:
        """Bid-ask spread."""
        return self.ask - self.bid

    @property
    def spread_pct(self) -> float:
        """Bid-ask spread as percentage."""
        if self.last > 0:
            return (self.spread / self.last) * 100
        return 0.0

    @property
    def mid(self) -> float:
        """Mid price."""
        return (self.bid + self.ask) / 2

    def is_fresh(self, max_age_seconds: float = 30.0) -> bool:
        """Check if price data is fresh."""
        return (datetime.utcnow() - self.timestamp).total_seconds() < max_age_seconds


@dataclass
class AggregatedPrice:
    """Aggregated price data from multiple exchanges."""

    symbol: str
    prices: dict[str, ExchangePrice] = field(default_factory=dict)
    aggregated_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def best_bid(self) -> tuple[str, float] | None:
        """Get best (highest) bid and exchange."""
        if not self.prices:
            return None
        best = max(self.prices.items(), key=lambda x: x[1].bid)
        return best[0], best[1].bid

    @property
    def best_ask(self) -> tuple[str, float] | None:
        """Get best (lowest) ask and exchange."""
        if not self.prices:
            return None
        best = min(self.prices.items(), key=lambda x: x[1].ask)
        return best[0], best[1].ask

    @property
    def vwap(self) -> float:
        """Volume-weighted average price across exchanges."""
        total_volume = sum(p.volume_24h for p in self.prices.values())
        if total_volume == 0:
            return sum(p.last for p in self.prices.values()) / len(self.prices) if self.prices else 0.0

        weighted_sum = sum(p.last * p.volume_24h for p in self.prices.values())
        return weighted_sum / total_volume

    @property
    def price_discrepancy_pct(self) -> float:
        """Max price discrepancy between exchanges as percentage."""
        if len(self.prices) < 2:
            return 0.0

        prices_list = [p.last for p in self.prices.values()]
        min_price = min(prices_list)
        max_price = max(prices_list)

        if min_price > 0:
            return ((max_price - min_price) / min_price) * 100
        return 0.0

    @property
    def arbitrage_opportunity(self) -> dict[str, Any] | None:
        """Detect arbitrage opportunity between exchanges."""
        if len(self.prices) < 2:
            return None

        # Find best ask (lowest) and best bid (highest)
        best_ask_ex, best_ask_price = self.best_ask
        best_bid_ex, best_bid_price = self.best_bid

        if best_ask_ex == best_bid_ex:
            return None

        # Calculate potential profit
        if best_ask_price >= best_bid_price:
            return None

        profit_pct = ((best_bid_price - best_ask_price) / best_ask_price) * 100

        # Only report if profit > 0.1% (accounting for fees)
        if profit_pct < 0.1:
            return None

        return {
            "buy_exchange": best_ask_ex,
            "sell_exchange": best_bid_ex,
            "buy_price": best_ask_price,
            "sell_price": best_bid_price,
            "profit_pct": profit_pct,
            "symbol": self.symbol,
        }

    def get_exchange_ranking(self) -> list[tuple[str, float]]:
        """Rank exchanges by price competitiveness."""
        if not self.prices:
            return []

        # Rank by how close to best bid/ask
        rankings = []
        best_bid = self.best_bid[1] if self.best_bid else 0
        best_ask = self.best_ask[1] if self.best_ask else float("inf")

        for ex, price in self.prices.items():
            # Score: how close to best bid (for sellers) or best ask (for buyers)
            bid_score = price.bid / best_bid if best_bid > 0 else 0
            ask_score = best_ask / price.ask if price.ask > 0 else 0
            score = (bid_score + ask_score) / 2
            rankings.append((ex, score))

        return sorted(rankings, key=lambda x: x[1], reverse=True)


class MultiExchangeAggregator:
    """
    Aggregates price data from multiple exchanges.

    Supports:
    - Bitvavo (EUR pairs)
    - Revolut X (USD pairs)
    """

    SUPPORTED_EXCHANGES = ["bitvavo", "revolutx"]

    def __init__(self):
        self._cache: dict[str, AggregatedPrice] = {}
        self._cache_lock = asyncio.Lock()
        self._exchange_adapters: dict[str, Any] = {}
        self._running = False
        self._update_task: asyncio.Task | None = None

        # Configuration
        self.update_interval = 5.0  # Seconds between updates
        self.max_price_age = 30.0  # Maximum acceptable price age

    async def initialize(self):
        """Initialize exchange adapters."""
        logger.info("[INIT] Initializing MultiExchangeAggregator")

        # Initialize Bitvavo adapter
        try:
            from backend.execution.bitvavo_adapter import BitvavoAdapter
            self._exchange_adapters["bitvavo"] = BitvavoAdapter()
            await self._exchange_adapters["bitvavo"].initialize()
            logger.info("[INIT] Bitvavo adapter initialized")
        except Exception as e:
            logger.warning(f"[INIT] Bitvavo adapter failed: {e}")

        # Initialize Revolut X adapter
        try:
            from backend.execution.revolut_x_adapter import RevolutXAdapter
            self._exchange_adapters["revolutx"] = RevolutXAdapter()
            await self._exchange_adapters["revolutx"].connect()
            logger.info("[INIT] Revolut X adapter initialized")
        except Exception as e:
            logger.warning(f"[INIT] Revolut X adapter failed: {e}")

        logger.info(f"[INIT] {len(self._exchange_adapters)} exchanges available")

    async def start(self):
        """Start background price aggregation."""
        self._running = True
        self._update_task = asyncio.create_task(self._aggregation_loop())
        logger.info("[START] MultiExchangeAggregator started")

    async def stop(self):
        """Stop background aggregation."""
        self._running = False
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass

        # Disconnect adapters
        for name, adapter in self._exchange_adapters.items():
            try:
                if name == "revolutx":
                    await adapter.disconnect()
                logger.info(f"[STOP] Disconnected from {name}")
            except Exception as e:
                logger.warning(f"[STOP] Error disconnecting {name}: {e}")

        logger.info("[STOP] MultiExchangeAggregator stopped")

    async def _aggregation_loop(self):
        """Background loop for price aggregation."""
        while self._running:
            try:
                await self._update_all_prices()
                await asyncio.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"[LOOP] Aggregation error: {e}")
                await asyncio.sleep(self.update_interval)

    async def _update_all_prices(self):
        """Update prices from all exchanges for common symbols."""
        # Common symbols across exchanges
        common_symbols = [
            ("BTC", "BTC-EUR", "BTC-USD"),
            ("ETH", "ETH-EUR", "ETH-USD"),
            ("SOL", "SOL-EUR", "SOL-USD"),
            ("ADA", "ADA-EUR", "ADA-USD"),
            ("XRP", "XRP-EUR", "XRP-USD"),
        ]

        for base, bitvavo_sym, revolut_sym in common_symbols:
            await self._fetch_and_aggregate(base, bitvavo_sym, revolut_sym)

    async def _fetch_and_aggregate(self, base: str, bitvavo_sym: str, revolut_sym: str):
        """Fetch prices from all exchanges and aggregate."""
        prices = {}

        # Fetch from Bitvavo
        if "bitvavo" in self._exchange_adapters:
            try:
                start = datetime.utcnow()
                ticker = await self._exchange_adapters["bitvavo"].fetch_ticker(bitvavo_sym)
                latency = (datetime.utcnow() - start).total_seconds() * 1000

                prices["bitvavo"] = ExchangePrice(
                    exchange="bitvavo",
                    symbol=base,
                    bid=float(ticker.get("bid", 0)),
                    ask=float(ticker.get("ask", 0)),
                    last=float(ticker.get("last", 0)),
                    volume_24h=float(ticker.get("volume", 0)),
                    latency_ms=latency,
                )
            except Exception as e:
                logger.debug(f"[FETCH] Bitvavo {bitvavo_sym} failed: {e}")

        # Fetch from Revolut X
        if "revolutx" in self._exchange_adapters:
            try:
                start = datetime.utcnow()
                ticker = await self._exchange_adapters["revolutx"].fetch_ticker(revolut_sym)
                latency = (datetime.utcnow() - start).total_seconds() * 1000

                prices["revolutx"] = ExchangePrice(
                    exchange="revolutx",
                    symbol=base,
                    bid=float(ticker.get("bid", 0)),
                    ask=float(ticker.get("ask", 0)),
                    last=float(ticker.get("last", 0)),
                    volume_24h=float(ticker.get("volume_24h", 0)),
                    latency_ms=latency,
                )
            except Exception as e:
                logger.debug(f"[FETCH] Revolut X {revolut_sym} failed: {e}")

        # Store aggregated price
        if prices:
            async with self._cache_lock:
                self._cache[base] = AggregatedPrice(
                    symbol=base,
                    prices=prices,
                )

    async def get_aggregated_price(self, symbol: str) -> AggregatedPrice | None:
        """Get aggregated price for a symbol."""
        async with self._cache_lock:
            agg = self._cache.get(symbol)
            if agg and (datetime.utcnow() - agg.aggregated_at).total_seconds() < self.max_price_age:
                return agg

        # Fetch fresh data
        symbol_map = {
            "BTC": ("BTC-EUR", "BTC-USD"),
            "ETH": ("ETH-EUR", "ETH-USD"),
            "SOL": ("SOL-EUR", "SOL-USD"),
            "ADA": ("ADA-EUR", "ADA-USD"),
            "XRP": ("XRP-EUR", "XRP-USD"),
        }

        if symbol in symbol_map:
            await self._fetch_and_aggregate(symbol, symbol_map[symbol][0], symbol_map[symbol][1])

        async with self._cache_lock:
            return self._cache.get(symbol)

    async def get_best_price(self, symbol: str, side: str) -> dict[str, Any] | None:
        """
        Get best price for a specific side.

        Args:
            symbol: Base symbol (e.g., 'BTC')
            side: 'buy' or 'sell'

        Returns:
            Best price info with exchange
        """
        agg = await self.get_aggregated_price(symbol)
        if not agg:
            return None

        if side.lower() == "buy":
            best = agg.best_ask
            if best:
                return {
                    "exchange": best[0],
                    "price": best[1],
                    "side": "ask",
                    "symbol": symbol,
                }
        else:
            best = agg.best_bid
            if best:
                return {
                    "exchange": best[0],
                    "price": best[1],
                    "side": "bid",
                    "symbol": symbol,
                }

        return None

    async def get_arbitrage_opportunities(self) -> list[dict[str, Any]]:
        """Get all current arbitrage opportunities."""
        opportunities = []

        async with self._cache_lock:
            cached = list(self._cache.values())

        for agg in cached:
            arb = agg.arbitrage_opportunity
            if arb:
                opportunities.append(arb)

        return sorted(opportunities, key=lambda x: x["profit_pct"], reverse=True)

    async def get_price_discrepancies(self, threshold_pct: float = 0.5) -> list[dict[str, Any]]:
        """
        Get symbols with significant price discrepancies.

        Args:
            threshold_pct: Minimum discrepancy to report (%)

        Returns:
            List of discrepancies
        """
        discrepancies = []

        async with self._cache_lock:
            cached = list(self._cache.values())

        for agg in cached:
            if agg.price_discrepancy_pct >= threshold_pct:
                prices = {ex: p.last for ex, p in agg.prices.items()}
                discrepancies.append({
                    "symbol": agg.symbol,
                    "discrepancy_pct": agg.price_discrepancy_pct,
                    "prices": prices,
                    "vwap": agg.vwap,
                })

        return sorted(discrepancies, key=lambda x: x["discrepancy_pct"], reverse=True)

    def get_stats(self) -> dict[str, Any]:
        """Get aggregator statistics."""
        return {
            "cached_symbols": len(self._cache),
            "active_exchanges": list(self._exchange_adapters.keys()),
            "update_interval": self.update_interval,
            "max_price_age": self.max_price_age,
        }


# Singleton instance
_aggregator: MultiExchangeAggregator | None = None


async def get_multi_exchange_aggregator() -> MultiExchangeAggregator:
    """Get or create singleton aggregator."""
    global _aggregator
    if _aggregator is None:
        _aggregator = MultiExchangeAggregator()
        await _aggregator.initialize()
    return _aggregator
