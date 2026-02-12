
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

class KrakenProvider(BaseExchangeProvider):
    """
    Kraken WebSocket Provider using CCXT Pro.
    Streams Tickers and Trades for specified symbols.
    """
    def __init__(self, name: str, out_queue: Optional[asyncio.Queue] = None, symbols: List[str] = None):
        super().__init__(name, out_queue)
        self.symbols = symbols or ["BTC/USD", "ETH/USD"]
        self.exchange = None

    async def _connect_and_stream(self):
        """
        Connect to Kraken via CCXT Pro and stream data.
        """
        try:
            self.exchange = ccxt.kraken({
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot',
                }
            })
            
            logger.info(f"KrakenProvider: Connecting to {self.exchange.urls['api']['ws']} for {self.symbols}...")

            # Create tasks for tickers and trades
            # CCXT watch_tickers supports multiple symbols
            # watch_trades might need a loop or multiple tasks depending on exchange, 
            # but usually handled via loop.
            
            while not self._stopped.is_set():
                try:
                    # We use asyncio.gather to wait for either ticker or trade updates
                    # But ccxt watch methods block until an update arrives. 
                    # To handle multiple streams, we need concurrent tasks.
                    
                    # Since this method is called inside a loop in BaseExchangeProvider,
                    # we should probably run the specialized loops here.
                    
                    await asyncio.gather(
                        self._watch_tickers_loop(),
                        self._watch_trades_loop()
                    )
                    
                except ccxt.NetworkError as e:
                    logger.warning(f"KrakenProvider Network Error: {e}")
                    raise # Trigger backoff in base class
                except Exception as e:
                    logger.error(f"KrakenProvider Error: {e}")
                    raise
                    
        finally:
            if self.exchange:
                await self.exchange.close()
                logger.info("KrakenProvider: Exchange connection closed.")

    async def _watch_tickers_loop(self):
        """Loop for watching tickers."""
        # Convert symbols to CCXT format if needed (usually auto-handled)
        while not self._stopped.is_set():
            try:
                # Watch multiple tickers
                tickers = await self.exchange.watch_tickers(self.symbols)
                
                # 'tickers' is a dict {symbol: ticker_structure}
                # CCXT usually returns the whole dict on update, but check specifics.
                # Actually watch_tickers returns the changed tickers or all.
                
                req_time = time.time()
                
                for symbol, ticker in tickers.items():
                    # Check timestamp
                    ts_exchange = ticker.get('timestamp', req_time * 1000) / 1000.0
                    
                    event = UnifiedMarketEvent(
                        event_type=EventType.TICKER,
                        venue="kraken",
                        symbol=symbol,
                        ts_exchange=ts_exchange,
                        ts_received=req_time,
                        price=ticker.get('last'),
                        bid=ticker.get('bid'),
                        ask=ticker.get('ask'),
                        size=ticker.get('baseVolume'), # 24h volume usually
                    )
                    
                    if self.out_queue:
                        await self.out_queue.put(event.to_dict())
                        
            except Exception as e:
                logger.debug(f"Ticker loop error: {e}")
                raise

    async def _watch_trades_loop(self):
        """Loop for watching trades."""
        # watch_trades usually wants a single symbol or list.
        # Check ccxt capability. Kraken supports multi.
        # But CCXT unified API often loops per symbol. 
        # For simplicity in this step, we might just spawn sub-tasks if needed.
        # But watch_trades_for_symbols is supported by some.
        
        # If not supported, we might just iterate. 
        # Let's try watching symbol by symbol in separate tasks if needed, 
        # or just pick the first one for MVP if multi not supported.
        # verifiable: await exchange.watch_trades(symbol)
        
        # For robustness, let's create a task per symbol.
        tasks = [self._watch_trades_single(s) for s in self.symbols]
        await asyncio.gather(*tasks)

    async def _watch_trades_single(self, symbol: str):
        while not self._stopped.is_set():
            try:
                trades = await self.exchange.watch_trades(symbol)
                # Returns list of trades
                req_time = time.time()
                
                for trade in trades:
                    # trade structure
                    event = UnifiedMarketEvent(
                        event_type=EventType.TRADE,
                        venue="kraken",
                        symbol=symbol,
                        ts_exchange=trade.get('timestamp', req_time * 1000) / 1000.0,
                        ts_received=req_time,
                        price=trade.get('price'),
                        size=trade.get('amount'),
                        side=trade.get('side'), # 'buy' or 'sell'
                    )
                    
                    if self.out_queue:
                        await self.out_queue.put(event.to_dict())
                        
            except Exception as e:
                # logger.debug(f"Trade loop error for {symbol}: {e}")
                raise
