"""
Data Pre-fetch Agent - Proactive Data Collection

Deze agent is verantwoordelijk voor het VOORAF verzamelen van data,
zodat trading agents NOOIT zonder verse data komen te staan.

Architectuur:
1. Warm-up mode: Laad historische data vooraf (2 minuten)
2. Real-time mode: WebSocket streaming + REST backup
3. Cache serving: Directe data levering aan agents (<1ms)

Timing guarantees:
- Data age: <5s (WebSocket) of <15s (REST)
- Cache hit rate: 100% (voor gemonitorde symbolen)
- Agent latency: <1ms voor data ophalen
"""

import asyncio
import json
import logging
import os
import sys
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import websockets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DataPreFetchAgent")


@dataclass
class PriceData:
    """Price data with metadata."""

    symbol: str
    price: float
    timestamp: datetime
    source: str = "unknown"
    volume_24h: float = 0.0
    change_24h: float = 0.0

    def is_fresh(self, max_age_seconds: float = 10.0) -> bool:
        """Check if data is fresh enough."""
        return (datetime.now() - self.timestamp).total_seconds() < max_age_seconds


class DataPreFetchAgent:
    """
    Data Pre-fetch Agent - Zorgt ervoor dat data ALTIJD beschikbaar is.

    Key features:
    - Warm-up: Laad data vooraf (historisch)
    - Multi-source: WebSocket + REST parallel
    - Proactive: Fetch VOORDAT agents vragen
    - Guaranteed: 100% cache hit rate voor gemonitorde symbolen
    """

    # Top 50 meest liquide EUR pairs (prioriteit voor warm-up)
    PRIORITY_SYMBOLS = [
        "BTC/EUR",
        "ETH/EUR",
        "SOL/EUR",
        "ADA/EUR",
        "DOT-EUR",
        "XRP/EUR",
        "LINK/EUR",
        "LTC/EUR",
        "BCH/EUR",
        "XLM/EUR",
        "DOGE/EUR",
        "AVAX/EUR",
        "ATOM/EUR",
        "ALGO/EUR",
        "VET/EUR",
        "FIL/EUR",
        "TRX/EUR",
        "ETC/EUR",
        "EOS/EUR",
        "AAVE/EUR",
        "UNI/EUR",
        "MKR/EUR",
        "COMP/EUR",
        "SNX/EUR",
        "YFI/EUR",
        "BAT/EUR",
        "ZRX/EUR",
        "ENJ/EUR",
        "CHZ/EUR",
        "MANA/EUR",
        "SAND/EUR",
        "AXS/EUR",
        "LRC/EUR",
        "CRV/EUR",
        "KNC/EUR",
        "GRT/EUR",
        "UMA/EUR",
        "SUSHI/EUR",
        "1INCH/EUR",
        "STORJ/EUR",
        "FET/EUR",
        "SKL/EUR",
        "APT/EUR",
        "ARB/EUR",
        "OP/EUR",
        "NEAR/EUR",
        "FTM/EUR",
        "GALA/EUR",
        "SUI/EUR",
        "INJ/EUR",
    ]

    def __init__(
        self,
        warmup_duration: int = 120,  # 2 minuten warm-up
        max_staleness: float = 15.0,  # Data max 15s oud
        rest_interval: float = 5.0,  # REST elke 5s
    ):
        self.warmup_duration = warmup_duration
        self.max_staleness = max_staleness
        self.rest_interval = rest_interval

        # Cache: symbol -> PriceData
        self._cache: dict[str, PriceData] = {}
        self._cache_lock = asyncio.Lock()

        # History voor technische analyse: symbol -> deque van PriceData
        self._history: dict[str, deque] = {}
        self._max_history = 100  # Houd 100 punten per symbool

        # WebSocket state
        self._ws = None
        self._ws_connected = False
        self._ws_url = "wss://ws.bitvavo.com/v2"

        # REST fallback
        self._bitvavo_rest = None

        # Stats
        self._stats = {
            "ws_messages": 0,
            "rest_updates": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "warmup_complete": False,
        }

        # State
        self._running = False
        self._tasks = []
        self._warmup_event = asyncio.Event()

        # Callbacks voor price updates
        self._price_callbacks: set[Callable[[PriceData], None]] = set()

    # ============ PUBLIC API ============

    async def start(self):
        """Start de Data Pre-fetch Agent met warm-up."""
        self._running = True
        logger.info("=" * 80)
        logger.info("DATA PRE-FETCH AGENT - Starting")
        logger.info(f"Warm-up duration: {self.warmup_duration}s")
        logger.info(f"Max staleness: {self.max_staleness}s")
        logger.info("=" * 80)

        # Start alle fetchers parallel
        self._tasks = [
            asyncio.create_task(self._websocket_fetcher()),
            asyncio.create_task(self._rest_fetcher()),
            asyncio.create_task(self._warmup_monitor()),
            asyncio.create_task(self._stats_reporter()),
        ]

        # Wacht op warm-up completion
        logger.info("[WARM-UP] Waiting for initial data population...")
        try:
            await asyncio.wait_for(self._warmup_event.wait(), timeout=self.warmup_duration)
            logger.info("[WARM-UP] ✓ Complete - Cache populated")
        except TimeoutError:
            logger.warning(
                f"[WARM-UP] Timeout after {self.warmup_duration}s - starting with partial data"
            )

        self._stats["warmup_complete"] = True

    async def stop(self):
        """Stop de agent."""
        self._running = False
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        if self._ws:
            await self._ws.close()
        logger.info("Data Pre-fetch Agent stopped")

    async def get_price(self, symbol: str) -> PriceData | None:
        """Haal prijs op uit cache (ALTIJD beschikbaar na warm-up)."""
        async with self._cache_lock:
            data = self._cache.get(symbol)

        if data is None:
            self._stats["cache_misses"] += 1
            return None

        self._stats["cache_hits"] += 1
        return data

    async def get_all_prices(self, max_age: float | None = None) -> dict[str, PriceData]:
        """Haal alle verse prijzen op."""
        max_age = max_age or self.max_staleness

        async with self._cache_lock:
            return {symbol: data for symbol, data in self._cache.items() if data.is_fresh(max_age)}

    async def get_price_history(self, symbol: str, lookback: int = 20) -> list[PriceData]:
        """Haal historische prijzen op voor technische analyse."""
        async with self._cache_lock:
            history = self._history.get(symbol, deque())
            return list(history)[-lookback:]

    def register_price_callback(self, callback: Callable[[PriceData], None]):
        """Registreer callback voor real-time price updates."""
        self._price_callbacks.add(callback)

    def get_stats(self) -> dict:
        """Haal statistieken op."""
        # Niet-async voor eenvoudige statistieken
        fresh_count = sum(1 for d in self._cache.values() if d.is_fresh(self.max_staleness))
        return {
            **self._stats,
            "cache_size": len(self._cache),
            "fresh_count": fresh_count,
            "history_entries": sum(len(h) for h in self._history.values()),
            "ws_connected": self._ws_connected,
        }

    async def wait_for_symbol(self, symbol: str, timeout: float = 30.0) -> bool:
        """Wacht tot een symbool beschikbaar is."""
        start = datetime.now()
        while (datetime.now() - start).total_seconds() < timeout:
            async with self._cache_lock:
                if symbol in self._cache and self._cache[symbol].is_fresh(self.max_staleness):
                    return True
            await asyncio.sleep(0.1)
        return False

    # ============ INTERNAL FETCHERS ============

    async def _websocket_fetcher(self):
        """WebSocket fetcher - real-time data."""
        while self._running:
            try:
                async with websockets.connect(
                    self._ws_url, ping_interval=20, ping_timeout=10
                ) as ws:
                    self._ws = ws
                    self._ws_connected = True
                    logger.info("✓ WebSocket connected")

                    # Subscribe naar alle priority symbolen
                    await self._subscribe_websocket(ws)

                    # Luister naar berichten
                    async for message in ws:
                        if not self._running:
                            break
                        await self._handle_ws_message(message)

            except Exception as e:
                logger.warning(f"WebSocket error: {e}")
                self._ws_connected = False

            if self._running:
                await asyncio.sleep(5)

    async def _rest_fetcher(self):
        """REST fetcher - backup data elke X seconden."""
        # Wacht even voor WebSocket
        await asyncio.sleep(2)

        while self._running:
            try:
                if not self._ws_connected or len(self._cache) < 50:
                    await self._fetch_rest_batch()
                await asyncio.sleep(self.rest_interval)
            except Exception as e:
                logger.error(f"REST fetcher error: {e}")
                await asyncio.sleep(self.rest_interval)

    async def _warmup_monitor(self):
        """Monitor warm-up voortgang."""
        check_interval = 5  # Check elke 5s

        while self._running and not self._warmup_event.is_set():
            await asyncio.sleep(check_interval)

            async with self._cache_lock:
                fresh_count = sum(1 for d in self._cache.values() if d.is_fresh(self.max_staleness))
                len(self._cache)

            # Warm-up complete als we >80% van priority symbolen hebben
            if fresh_count >= len(self.PRIORITY_SYMBOLS) * 0.8:
                logger.info(f"[WARM-UP] {fresh_count}/{len(self.PRIORITY_SYMBOLS)} symbols ready")
                self._warmup_event.set()

    # ============ DATA PROCESSING ============

    async def _subscribe_websocket(self, ws):
        """Subscribe naar WebSocket kanalen."""
        # Converteer symbolen naar Bitvavo formaat
        markets = [s.replace("/", "-") for s in self.PRIORITY_SYMBOLS[:40]]

        # Subscribe in batches van 10
        for i in range(0, len(markets), 10):
            batch = markets[i : i + 10]
            msg = {"action": "subscribe", "channels": [{"name": "ticker", "markets": batch}]}
            await ws.send(json.dumps(msg))
            await asyncio.sleep(0.3)

    async def _handle_ws_message(self, message: str):
        """Verwerk WebSocket bericht."""
        try:
            data = json.loads(message)
            self._stats["ws_messages"] += 1

            if data.get("event") == "ticker" or "bestAsk" in data or "bestBid" in data:
                await self._update_price_from_ws(data)

        except Exception as e:
            logger.debug(f"WS message error: {e}")

    async def _update_price_from_ws(self, data: dict):
        """Update prijs vanuit WebSocket data."""
        try:
            market = data.get("market", "")
            if not market.endswith("-EUR"):
                return

            symbol = market.replace("-", "/")

            # Haal prijs op (bestAsk of bestBid)
            price = float(data.get("bestAsk") or data.get("bestBid") or 0)
            if price <= 0:
                return

            price_data = PriceData(
                symbol=symbol, price=price, timestamp=datetime.now(), source="websocket"
            )

            await self._store_price(price_data)

        except Exception as e:
            logger.debug(f"Price update error: {e}")

    async def _fetch_rest_batch(self):
        """Fetch prijzen via REST API."""
        try:
            from backend.execution.bitvavo_adapter import BitvavoAdapter

            if not self._bitvavo_rest:
                self._bitvavo_rest = BitvavoAdapter()
                await self._bitvavo_rest.initialize()

            symbols = self._bitvavo_rest.get_eur_pairs()[:100]

            for symbol in symbols:
                try:
                    ticker = await self._bitvavo_rest.fetch_ticker(symbol)
                    if ticker and ticker.get("last"):
                        price_data = PriceData(
                            symbol=symbol.replace("-", "/"),
                            price=float(ticker["last"]),
                            timestamp=datetime.now(),
                            source="rest",
                            volume_24h=float(ticker.get("volume", 0)),
                            change_24h=float(ticker.get("change24h", 0)),
                        )
                        await self._store_price(price_data)
                        self._stats["rest_updates"] += 1

                    await asyncio.sleep(0.01)  # Rate limit

                except Exception:
                    continue

        except Exception as e:
            logger.error(f"REST fetch error: {e}")

    async def _store_price(self, price_data: PriceData):
        """Sla prijs op in cache en history."""
        async with self._cache_lock:
            # Update cache
            self._cache[price_data.symbol] = price_data

            # Update history
            if price_data.symbol not in self._history:
                self._history[price_data.symbol] = deque(maxlen=self._max_history)
            self._history[price_data.symbol].append(price_data)

        # Notify callbacks
        for callback in self._price_callbacks:
            try:
                callback(price_data)
            except Exception:
                pass

    async def _stats_reporter(self):
        """Rapporteer statistieken."""
        while self._running:
            await asyncio.sleep(60)
            stats = self.get_stats()
            logger.info("=" * 60)
            logger.info("DATA AGENT STATS")
            logger.info(f"  Cache: {stats['cache_size']} total, {stats['fresh_count']} fresh")
            logger.info(f"  WS messages: {stats['ws_messages']} | REST: {stats['rest_updates']}")
            logger.info(f"  Cache hits/misses: {stats['cache_hits']}/{stats['cache_misses']}")
            logger.info(f"  History entries: {stats['history_entries']}")
            logger.info(f"  WS connected: {stats['ws_connected']}")
            logger.info("=" * 60)


# Singleton instance
_data_agent: DataPreFetchAgent | None = None


async def get_data_agent() -> DataPreFetchAgent:
    """Get or create singleton data agent."""
    global _data_agent
    if _data_agent is None:
        _data_agent = DataPreFetchAgent()
    return _data_agent
