import logging
from typing import Any

import ccxt.async_support as ccxt
from ccxt.base.errors import ExchangeError, NetworkError, RequestTimeout

from backend.core.config.settings import settings
from backend.core.market_data.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)


class ExchangeInterface:
    """
    Unified interface for crypto exchanges using CCXT.
    Wraps API calls with Circuit Breaker protection.

    Supported exchanges:
    - bitvavo (Dutch exchange, ideal for EUR pairs)
    - kraken (US/EU exchange)
    - binance (Global, via CCXT)
    """

    def __init__(self, exchange_override: Any | None = None, exchange_id: str | None = None):
        self.exchange_id = exchange_id or settings.EXCHANGE_ID
        self.api_key = settings.EXCHANGE_API_KEY
        self.secret = settings.EXCHANGE_SECRET

        # Load exchange-specific credentials
        if self.exchange_id == "bitvavo":
            self.api_key = settings.BITVAVO_API_KEY or settings.EXCHANGE_API_KEY
            self.secret = settings.BITVAVO_API_SECRET or settings.EXCHANGE_SECRET

        self.exchange = exchange_override
        self.circuit_breaker = CircuitBreaker(name=f"exchange_{self.exchange_id}")

    async def initialize(self):
        """Initialize CCXT exchange instance."""
        if self.exchange:
            return

        try:
            exchange_class = getattr(ccxt, self.exchange_id)
            self.exchange = exchange_class(
                {
                    "apiKey": self.api_key,
                    "secret": self.secret,
                    "enableRateLimit": True,
                }
            )
            await self.exchange.load_markets()
            logger.info(f"Initialized exchange: {self.exchange_id}")
        except Exception as e:
            logger.error(f"Failed to initialize exchange {self.exchange_id}: {e}")
            raise

    async def close(self):
        """Close exchange connection."""
        if self.exchange:
            await self.exchange.close()

    async def _execute_with_breaker(self, func, *args, **kwargs):
        """Execute a function with circuit breaker protection."""
        if not self.circuit_breaker.allow_request():
            logger.warning(f"Circuit {self.exchange_id} is OPEN. Request blocked.")
            return None

        try:
            result = await func(*args, **kwargs)
            await self.circuit_breaker.record_success()
            return result
        except (NetworkError, RequestTimeout) as e:
            logger.warning(f"Network error on {self.exchange_id}: {e}")
            await self.circuit_breaker.record_failure()
            return None
        except ExchangeError as e:
            logger.error(f"Exchange error on {self.exchange_id}: {e}")
            # Exchange errors (like invalid symbol) typically don't trip circuit,
            # but for 5xx they might. For now, treat as failure.
            await self.circuit_breaker.record_failure()
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            await self.circuit_breaker.record_failure()
            return None

    async def fetch_ticker(self, symbol: str) -> dict[str, Any] | None:
        if not self.exchange:
            await self.initialize()
        if not self.exchange:
            return None
        return await self._execute_with_breaker(self.exchange.fetch_ticker, symbol)

    async def fetch_ohlcv(
        self, symbol: str, timeframe: str = "1m", limit: int = 100
    ) -> list[Any] | None:
        if not self.exchange:
            await self.initialize()
        if not self.exchange:
            return None
        return await self._execute_with_breaker(
            self.exchange.fetch_ohlcv, symbol, timeframe, limit=limit
        )

    async def fetch_order_book(self, symbol: str, limit: int = 25) -> dict[str, Any] | None:
        if not self.exchange:
            await self.initialize()
        if not self.exchange:
            return None
        return await self._execute_with_breaker(self.exchange.fetch_order_book, symbol, limit=limit)

    async def fetch_balance(self) -> dict[str, Any] | None:
        if not self.exchange:
            await self.initialize()
        if not self.exchange:
            return None
        return await self._execute_with_breaker(self.exchange.fetch_balance)
