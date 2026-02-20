"""
Price Fetch Agent - WebSocket + In-Memory Cache

Features:
- Bitvavo WebSocket voor real-time prijzen
- In-memory cache met timestamps
- Max 5s staleness
- Fallback naar REST polling
- Circuit breaker pattern
"""

import asyncio
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable, Set

# Fix path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import websockets
from websockets.exceptions import ConnectionClosed, InvalidStatusCode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PriceFetchAgent")


@dataclass
class PriceData:
    """Price data with metadata."""
    symbol: str
    price: float
    timestamp: datetime
    source: str = "unknown"  # "websocket", "rest", "cache"
    volume_24h: float = 0.0
    change_24h: float = 0.0
    
    @property
    def age_ms(self) -> float:
        """Age in milliseconds."""
        return (datetime.now() - self.timestamp).total_seconds() * 1000
    
    @property
    def is_fresh(self, max_age_seconds: float = 5.0) -> bool:
        """Check if data is fresh enough."""
        return (datetime.now() - self.timestamp).total_seconds() < max_age_seconds


class PriceFetchAgent:
    """
    Fetch Agent that maintains in-memory price cache.
    
    WebSocket (primary) → REST (fallback)
    """
    
    def __init__(
        self,
        max_staleness_seconds: float = 5.0,
        rest_fallback_interval: float = 10.0,
        circuit_breaker_threshold: int = 5
    ):
        self.max_staleness = max_staleness_seconds
        self.rest_fallback_interval = rest_fallback_interval
        self.circuit_breaker_threshold = circuit_breaker_threshold
        
        # In-memory cache: symbol -> PriceData
        self._cache: Dict[str, PriceData] = {}
        self._cache_lock = asyncio.Lock()
        
        # WebSocket state
        self._ws = None
        self._ws_connected = False
        self._ws_url = "wss://ws.bitvavo.com/v2"
        
        # REST fallback state
        self._bitvavo_rest = None
        self._rest_fallback_active = False
        
        # Circuit breaker
        self._consecutive_errors = 0
        self._circuit_open = False
        self._circuit_reset_time = None
        
        # Stats
        self._stats = {
            'ws_messages': 0,
            'rest_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'updates': 0
        }
        
        # Callbacks for price updates
        self._update_callbacks: Set[Callable[[PriceData], None]] = set()
        
        self._running = False
        self._tasks = []
        
    # ============ Public API ============
    
    async def start(self):
        """Start the fetch agent."""
        self._running = True
        logger.info("=" * 80)
        logger.info("PRICE FETCH AGENT - Starting")
        logger.info(f"Max staleness: {self.max_staleness}s")
        logger.info(f"REST fallback interval: {self.rest_fallback_interval}s")
        logger.info("=" * 80)
        
        # Start WebSocket connection
        self._tasks.append(asyncio.create_task(self._websocket_loop()))
        
        # Start REST fallback monitor
        self._tasks.append(asyncio.create_task(self._rest_fallback_loop()))
        
        # Start stats reporter
        self._tasks.append(asyncio.create_task(self._stats_reporter()))
        
    async def stop(self):
        """Stop the fetch agent."""
        self._running = False
        
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        if self._ws:
            await self._ws.close()
        
        logger.info("Price Fetch Agent stopped")
    
    def register_callback(self, callback: Callable[[PriceData], None]):
        """Register callback for price updates."""
        self._update_callbacks.add(callback)
    
    def unregister_callback(self, callback: Callable[[PriceData], None]):
        """Unregister callback."""
        self._update_callbacks.discard(callback)
    
    async def get_price(self, symbol: str) -> Optional[PriceData]:
        """
        Get price for symbol from cache.
        Returns None if not found or too stale.
        """
        async with self._cache_lock:
            data = self._cache.get(symbol)
        
        if data is None:
            self._stats['cache_misses'] += 1
            return None
        
        if not data.is_fresh(self.max_staleness):
            logger.warning(f"Price for {symbol} is stale ({data.age_ms:.0f}ms old)")
            return None
        
        self._stats['cache_hits'] += 1
        return data
    
    async def get_all_prices(self, max_age: Optional[float] = None) -> Dict[str, PriceData]:
        """Get all fresh prices."""
        max_age = max_age or self.max_staleness
        
        async with self._cache_lock:
            return {
                symbol: data 
                for symbol, data in self._cache.items() 
                if data.is_fresh(max_age)
            }
    
    async def wait_for_prices(self, symbols: list, timeout: float = 30.0) -> bool:
        """Wait until all symbols have fresh prices."""
        start = time.time()
        while time.time() - start < timeout:
            async with self._cache_lock:
                all_fresh = all(
                    symbol in self._cache and self._cache[symbol].is_fresh(self.max_staleness)
                    for symbol in symbols
                )
            if all_fresh:
                return True
            await asyncio.sleep(0.1)
        return False
    
    def get_stats(self) -> dict:
        """Get current stats."""
        return {
            **self._stats,
            'cache_size': len(self._cache),
            'ws_connected': self._ws_connected,
            'rest_fallback': self._rest_fallback_active,
            'circuit_open': self._circuit_open
        }
    
    # ============ WebSocket Implementation ============
    
    async def _websocket_loop(self):
        """Main WebSocket loop with auto-reconnect."""
        while self._running:
            try:
                if self._circuit_open:
                    await self._wait_for_circuit_reset()
                
                logger.info("Connecting to Bitvavo WebSocket...")
                async with websockets.connect(
                    self._ws_url,
                    ping_interval=20,
                    ping_timeout=10
                ) as ws:
                    self._ws = ws
                    self._ws_connected = True
                    self._consecutive_errors = 0
                    logger.info("✓ WebSocket connected")
                    
                    # Subscribe to all EUR pairs
                    await self._subscribe_all(ws)
                    
                    # Handle messages
                    async for message in ws:
                        if not self._running:
                            break
                        await self._handle_ws_message(message)
                        
            except ConnectionClosed as e:
                logger.warning(f"WebSocket closed: {e}")
                self._ws_connected = False
            except InvalidStatusCode as e:
                logger.error(f"WebSocket connection failed: {e}")
                self._ws_connected = False
                self._consecutive_errors += 1
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                self._ws_connected = False
                self._consecutive_errors += 1
            
            # Check circuit breaker
            if self._consecutive_errors >= self.circuit_breaker_threshold:
                self._open_circuit()
            
            if self._running:
                logger.info("Reconnecting in 5s...")
                await asyncio.sleep(5)
    
    async def _subscribe_all(self, ws):
        """Subscribe to major EUR pairs via WebSocket."""
        # Top 50 most liquid EUR pairs on Bitvavo
        major_markets = [
            "BTC-EUR", "ETH-EUR", "SOL-EUR", "ADA-EUR", "DOT-EUR",
            "XRP-EUR", "LINK-EUR", "LTC-EUR", "BCH-EUR", "XLM-EUR",
            "DOGE-EUR", "MATIC-EUR", "AVAX-EUR", "ATOM-EUR", "ALGO-EUR",
            "VET-EUR", "FIL-EUR", "TRX-EUR", "ETC-EUR", "XMR-EUR",
            "EOS-EUR", "AAVE-EUR", "UNI-EUR", "MKR-EUR", "COMP-EUR",
            "SNX-EUR", "YFI-EUR", "BAT-EUR", "ZRX-EUR", "ENJ-EUR",
            "CHZ-EUR", "MANA-EUR", "SAND-EUR", "AXS-EUR", "LRC-EUR",
            "CRV-EUR", "BAL-EUR", "KNC-EUR", "GRT-EUR", "UMA-EUR",
            "REN-EUR", "OCEAN-EUR", "BAND-EUR", "SUSHI-EUR", "1INCH-EUR",
            "STORJ-EUR", "FET-EUR", "SKL-EUR", "CVC-EUR", "ANT-EUR"
        ]
        
        try:
            # Subscribe in batches of 25
            for i in range(0, len(major_markets), 25):
                batch = major_markets[i:i+25]
                subscribe_msg = {
                    "action": "subscribe",
                    "channels": [{"name": "ticker", "markets": batch}]
                }
                await ws.send(json.dumps(subscribe_msg))
                logger.info(f"Subscribed to {len(batch)} markets (batch {i//25 + 1})")
                await asyncio.sleep(0.3)  # Rate limit between batches
                
        except Exception as e:
            logger.error(f"Failed to subscribe: {e}")
            # Fallback: subscribe to top 5
            subscribe_msg = {
                "action": "subscribe",
                "channels": [{"name": "ticker", "markets": ["BTC-EUR", "ETH-EUR", "SOL-EUR", "ADA-EUR", "DOT-EUR"]}]
            }
            await ws.send(json.dumps(subscribe_msg))
            logger.info("Subscribed to top 5 markets (fallback)")
    
    async def _handle_ws_message(self, message: str):
        """Handle incoming WebSocket message."""
        try:
            data = json.loads(message)
            
            # Handle ticker updates
            if data.get("event") == "ticker":
                await self._process_ticker_update(data)
                self._stats['ws_messages'] += 1
            
            # Handle subscription confirmation
            elif data.get("event") == "subscribed":
                logger.info(f"✓ Subscribed: {data.get('channels', [])}")
            
            # Handle errors
            elif "error" in data:
                logger.error(f"WebSocket error message: {data['error']}")
                self._consecutive_errors += 1
                
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON: {message[:100]}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def _process_ticker_update(self, data: dict):
        """Process ticker update and update cache."""
        try:
            market = data.get("market", "")
            if not market.endswith("-EUR"):
                return  # Only EUR pairs
            
            price = float(data.get("last", 0))
            if price <= 0:
                return
            
            # Convert to PriceData
            price_data = PriceData(
                symbol=market.replace("-", "/"),
                price=price,
                timestamp=datetime.now(),
                source="websocket",
                volume_24h=float(data.get("volume", 0)),
                change_24h=float(data.get("change24h", 0))
            )
            
            # Update cache
            async with self._cache_lock:
                self._cache[price_data.symbol] = price_data
            
            self._stats['updates'] += 1
            
            # Notify callbacks
            for callback in self._update_callbacks:
                try:
                    callback(price_data)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
                    
        except Exception as e:
            logger.error(f"Error processing ticker: {e}")
    
    # ============ REST Fallback ============
    
    async def _rest_fallback_loop(self):
        """Periodic REST polling as fallback."""
        await asyncio.sleep(5)  # Wait for WebSocket to start
        
        while self._running:
            try:
                await asyncio.sleep(self.rest_fallback_interval)
                
                if not self._ws_connected:
                    logger.info("WebSocket down, activating REST fallback...")
                    self._rest_fallback_active = True
                    await self._fetch_via_rest()
                else:
                    self._rest_fallback_active = False
                    
            except Exception as e:
                logger.error(f"REST fallback error: {e}")
    
    async def _fetch_via_rest(self):
        """Fetch prices via REST API (fallback)."""
        try:
            from backend.execution.bitvavo_adapter import BitvavoAdapter
            
            if not self._bitvavo_rest:
                self._bitvavo_rest = BitvavoAdapter()
                await self._bitvavo_rest.initialize()
            
            # Fetch top markets to save API calls
            symbols = self._bitvavo_rest.get_eur_pairs()[:100]  # Top 100
            
            logger.info(f"REST fallback: fetching {len(symbols)} prices...")
            
            for symbol in symbols:
                try:
                    ticker = await self._bitvavo_rest.fetch_ticker(symbol)
                    if ticker and ticker.get('last'):
                        price_data = PriceData(
                            symbol=symbol.replace("-", "/"),
                            price=float(ticker['last']),
                            timestamp=datetime.now(),
                            source="rest",
                            volume_24h=float(ticker.get('volume', 0)),
                            change_24h=float(ticker.get('change24h', 0))
                        )
                        
                        async with self._cache_lock:
                            self._cache[price_data.symbol] = price_data
                        
                        self._stats['rest_requests'] += 1
                        
                    await asyncio.sleep(0.05)  # Rate limit
                    
                except Exception as e:
                    logger.warning(f"REST fetch failed for {symbol}: {e}")
                    
            logger.info(f"✓ REST fallback complete: {self._stats['rest_requests']} prices updated")
            
        except Exception as e:
            logger.error(f"REST fallback failed: {e}")
    
    # ============ Circuit Breaker ============
    
    def _open_circuit(self):
        """Open circuit breaker after too many errors."""
        self._circuit_open = True
        self._circuit_reset_time = datetime.now() + timedelta(minutes=1)
        logger.error(f"🚨 CIRCUIT BREAKER OPEN - Waiting 1 minute")
    
    async def _wait_for_circuit_reset(self):
        """Wait until circuit can be reset."""
        if self._circuit_reset_time and datetime.now() < self._circuit_reset_time:
            wait = (self._circuit_reset_time - datetime.now()).total_seconds()
            logger.info(f"Circuit breaker: waiting {wait:.0f}s...")
            await asyncio.sleep(wait)
        
        self._circuit_open = False
        self._consecutive_errors = 0
        logger.info("✓ Circuit breaker reset")
    
    # ============ Monitoring ============
    
    async def _stats_reporter(self):
        """Periodic stats reporting."""
        while self._running:
            await asyncio.sleep(60)
            
            stats = self.get_stats()
            cache_fresh = sum(1 for d in self._cache.values() if d.is_fresh(self.max_staleness))
            
            logger.info("=" * 60)
            logger.info("FETCH AGENT STATS")
            logger.info(f"  Cache: {stats['cache_size']} total, {cache_fresh} fresh")
            logger.info(f"  WS messages: {stats['ws_messages']} | REST: {stats['rest_requests']}")
            logger.info(f"  Cache hits/misses: {stats['cache_hits']}/{stats['cache_misses']}")
            logger.info(f"  Updates: {stats['updates']}")
            logger.info(f"  WS connected: {stats['ws_connected']} | REST fallback: {stats['rest_fallback']}")
            logger.info("=" * 60)


# Singleton instance
_fetch_agent: Optional[PriceFetchAgent] = None


async def get_fetch_agent() -> PriceFetchAgent:
    """Get or create singleton fetch agent."""
    global _fetch_agent
    if _fetch_agent is None:
        _fetch_agent = PriceFetchAgent()
    return _fetch_agent
