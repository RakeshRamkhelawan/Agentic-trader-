
import asyncio
import logging
from abc import abstractmethod
from typing import Optional
from backend.market_data.interfaces import ExchangeProvider

logger = logging.getLogger(__name__)

class BaseExchangeProvider(ExchangeProvider):
    """
    Base implementation for Exchange Providers with auto-reconnect.
    """
    def __init__(self, name: str, out_queue: Optional[asyncio.Queue] = None, initial_backoff: float = 1.0):
        super().__init__(name, out_queue)
        self._stopped = asyncio.Event()
        self.initial_backoff = initial_backoff

    @abstractmethod
    async def _connect_and_stream(self):
        """
        Connect to WS, subscribe, and stream messages to out_queue.
        Should raise exception on connection failure/loss.
        """
        pass

    async def run_forever(self):
        """
        Main loop with exponential backoff.
        """
        backoff = self.initial_backoff
        while not self._stopped.is_set():
            try:
                await self._connect_and_stream()
                # If returns normally, reset backoff
                backoff = self.initial_backoff 
            except asyncio.CancelledError:
                logger.info(f"Provider {self.name} cancelled.")
                raise
            except Exception as e:
                if self._stopped.is_set():
                    break
                logger.error(f"Provider {self.name} failed: {e}. Retrying in {backoff}s...")
                try:
                    await asyncio.sleep(backoff)
                except asyncio.CancelledError:
                    raise
                backoff = min(backoff * 2, 30)

    def stop(self):
        """Signal to stop."""
        logger.info(f"Stopping provider {self.name}...")
        self._stopped.set()
