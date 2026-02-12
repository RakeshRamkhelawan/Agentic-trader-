
import asyncio
import logging
import time
from typing import List, Optional

from backend.market_data.providers.base import BaseExchangeProvider
from backend.market_data.models import UnifiedMarketEvent, EventType
from backend.execution.exchange_adapter import ExchangeAdapter
from backend.core.config.settings import settings

logger = logging.getLogger(__name__)

class RevolutProvider(BaseExchangeProvider):
    """
    Revolut Market Data Provider.
    Uses generic REST Polling via ExchangeAdapter since WS is not publicly documented/supported in CCXT.
    """
    def __init__(self, name: str, out_queue: Optional[asyncio.Queue] = None, symbols: List[str] = None):
        super().__init__(name, out_queue)
        self.symbols = symbols or ["BTC/USD", "ETH/USD"]
        self.adapter: Optional[ExchangeAdapter] = None
        
    async def _connect_and_stream(self):
        """
        Init adapter and start polling loop.
        """
        api_key = settings.REVOLUT_API_KEY
        private_key = settings.REVOLUT_PRIVATE_KEY
        
        if not api_key:
            logger.warning("RevolutProvider: No API Key found. Market Data will be sparse/unavailable if Auth required.")
            # Some endpoints might be public, but Adapter usually requires auth.
            
        self.adapter = ExchangeAdapter(
            api_key=api_key or "dummy",
            private_key_pem=private_key or "dummy_pem", # Only needed if we sign requests
            base_url="https://sandbox-revx.revolut.com" if settings.REVOLUT_SANDBOX else "https://revx.revolut.com"
        )
        
        logger.info(f"RevolutProvider: Polling {self.symbols} interval=1s")
        
        while not self._stopped.is_set():
            try:
                # Poll Tickers
                # Revolut Adapter has get_tickers(list)
                tickers = await self.adapter.get_tickers(self.symbols)
                req_time = time.time()
                
                for symbol, data in tickers.items():
                   
                    event = UnifiedMarketEvent(
                        event_type=EventType.TICKER,
                        venue="revolut",
                        symbol=symbol,
                        ts_exchange=req_time, # REST doesn't always give TS, so use close enough
                        ts_received=req_time,
                        price=data.get('last'),
                        bid=data.get('bid'),
                        ask=data.get('ask'),
                        size=data.get('volume_24h')
                    )
                    
                    if self.out_queue:
                        await self.out_queue.put(event.to_dict())
                
                # Verify we aren't spinning too fast if no symbols or error
                await asyncio.sleep(1.0) 
                
            except Exception as e:
                logger.error(f"RevolutProvider Polling Error: {e}")
                await asyncio.sleep(5.0) # Error backoff
