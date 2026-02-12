
import asyncio
import logging
import time
from typing import List, Dict, Any, Optional

try:
    import ccxt.pro as ccxt  # Use CCXT Pro for WebSockets
except ImportError:
    import ccxt.async_support as ccxt # Fallback to REST if Pro not available (though we expect Pro)

from backend.market_data.providers.base import BaseExchangeProvider
from backend.market_data.models import UnifiedMarketEvent, EventType

logger = logging.getLogger(__name__)

class BybitProvider(BaseExchangeProvider):
    """
    Bybit WebSocket Provider using CCXT Pro.
    Streams Tickers and Trades for specified symbols.
    """
    def __init__(self, name: str, out_queue: Optional[asyncio.Queue] = None, symbols: List[str] = None):
        super().__init__(name, out_queue)
        # Bybit symbols are typically "BTC/USDT" or "BTC/USD"
        self.symbols = symbols or ["BTC/USDT", "ETH/USDT"]
        self.exchange = None

    async def _connect_and_stream(self):
        """
        Connect to Bybit via CCXT Pro and stream data.
        """
        try:
            self.exchange = ccxt.bybit({
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot', # Or 'swap' 'future' depending on need
                }
            })
            
            logger.info(f"BybitProvider: Connecting to {self.exchange.urls['api']['ws']} for {self.symbols}...")

            while not self._stopped.is_set():
                try:
                    await asyncio.gather(
                        self._watch_tickers_loop(),
                        self._watch_trades_loop()
                    )
                    
                except ccxt.NetworkError as e:
                    logger.warning(f"BybitProvider Network Error: {e}")
                    raise # Trigger backoff in base class
                except Exception as e:
                    logger.error(f"BybitProvider Error: {e}")
                    raise
                    
        finally:
            if self.exchange:
                await self.exchange.close()
                logger.info("BybitProvider: Exchange connection closed.")

    async def _watch_tickers_loop(self):
        """Loop for watching tickers."""
        while not self._stopped.is_set():
            try:
                # CCXT Unified watch_tickers
                tickers = await self.exchange.watch_tickers(self.symbols)
                
                req_time = time.time()
                
                for symbol, ticker in tickers.items():
                    # Check timestamp
                    ts_exchange = ticker.get('timestamp', req_time * 1000) / 1000.0
                    
                    event = UnifiedMarketEvent(
                        event_type=EventType.TICKER,
                        venue="bybit",
                        symbol=symbol,
                        ts_exchange=ts_exchange,
                        ts_received=req_time,
                        price=ticker.get('last'),
                        bid=ticker.get('bid'),
                        ask=ticker.get('ask'),
                        size=ticker.get('baseVolume'), 
                    )
                    
                    if self.out_queue:
                        await self.out_queue.put(event.to_dict())
                        
            except Exception as e:
                logger.debug(f"Ticker loop error: {e}")
                raise

    async def _watch_trades_loop(self):
        """Loop for watching trades."""
        # Bybit via CCXT Pro supports watching multiple symbols for trades in loop
        # But safest pattern is task per symbol or generic loop if supported.
        # CCXT Pro Bybit `watch_trades` supports list of symbols? 
        # CCXT docs say watchTrades(symbol) usually. 
        # But watchTradesForSymbols is available in some.
        # To be safe and consistent with Kraken provider:
        tasks = [self._watch_trades_single(s) for s in self.symbols]
        await asyncio.gather(*tasks)

    async def _watch_trades_single(self, symbol: str):
        while not self._stopped.is_set():
            try:
                trades = await self.exchange.watch_trades(symbol)
                req_time = time.time()
                
                for trade in trades:
                    event = UnifiedMarketEvent(
                        event_type=EventType.TRADE,
                        venue="bybit",
                        symbol=symbol,
                        ts_exchange=trade.get('timestamp', req_time * 1000) / 1000.0,
                        ts_received=req_time,
                        price=trade.get('price'),
                        size=trade.get('amount'),
                        side=trade.get('side'), 
                    )
                    
                    if self.out_queue:
                        await self.out_queue.put(event.to_dict())
                        
            except Exception as e:
                # logger.debug(f"Trade loop error for {symbol}: {e}")
                raise
