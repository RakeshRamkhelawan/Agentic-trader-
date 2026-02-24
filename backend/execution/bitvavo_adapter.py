"""
Bitvavo Exchange Adapter for Agentic Trader Platform.

Bitvavo is a Dutch cryptocurrency exchange ideal for EUR trading pairs.
API Documentation: https://docs.bitvavo.com/

Features:
- EUR trading pairs (BTC-EUR, ETH-EUR, etc.)
- iDEAL/Bancontact deposits (for Dutch users)
- Competitive fees (0.25% taker, 0.15% maker)
- Dutch regulatory compliance

Environment Variables:
    BITVAVO_API_KEY - Your API key from Bitvavo
    BITVAVO_API_SECRET - Your API secret from Bitvavo
    BITVAVO_SANDBOX - Set to "true" for testing
"""

import logging
from typing import Any

import ccxt.async_support as ccxt

from backend.core.config.settings import settings
from backend.core.market_data.circuit_breaker import CircuitBreaker
from backend.execution._paper_guard import paper_guard

logger = logging.getLogger(__name__)


class BitvavoAdapter:
    """
    Bitvavo Exchange Adapter using CCXT.

    This adapter provides:
    - Market data (ticker, orderbook, OHLCV)
    - Account management (balance, orders)
    - Trading operations (create/cancel orders)
    - EUR-based trading pairs
    """

    def __init__(self):
        self.exchange_id = "bitvavo"
        self.api_key = settings.BITVAVO_API_KEY
        self.api_secret = settings.BITVAVO_API_SECRET
        self.sandbox = settings.BITVAVO_SANDBOX

        self.exchange: ccxt.bitvavo | None = None
        self.circuit_breaker = CircuitBreaker(name="exchange_bitvavo")

    async def initialize(self):
        """Initialize Bitvavo exchange connection."""
        if not self.api_key or not self.api_secret:
            logger.warning("Bitvavo API credentials not configured")
            logger.info("Get your API keys at: https://account.bitvavo.com/user/api-keys")
            return False

        try:
            config = {
                "apiKey": self.api_key,
                "secret": self.api_secret,
                "enableRateLimit": True,
            }

            if self.sandbox:
                config["sandbox"] = True
                logger.info("Bitvavo initialized in SANDBOX mode")

            self.exchange = ccxt.bitvavo(config)
            await self.exchange.load_markets()

            logger.info(f"✅ Connected to Bitvavo ({'sandbox' if self.sandbox else 'live'})")
            logger.info(f"   Available markets: {len(self.exchange.markets)}")

            # Log available EUR pairs
            eur_pairs = [s for s in self.exchange.markets if s.endswith("/EUR")]
            logger.info(f"   EUR trading pairs: {len(eur_pairs)}")

            return True

        except Exception as e:
            logger.error(f"Failed to initialize Bitvavo: {e}")
            return False

    async def close(self):
        """Close exchange connection."""
        if self.exchange:
            await self.exchange.close()
            logger.info("Bitvavo connection closed")

    def _check_credentials(self) -> bool:
        """Check if API credentials are configured."""
        if not self.api_key or not self.api_secret:
            logger.error("Bitvavo API credentials not set. Add to .env:")
            logger.error("   BITVAVO_API_KEY=your_key")
            logger.error("   BITVAVO_API_SECRET=your_secret")
            return False
        return True

    # =========================================================================
    # Market Data Methods
    # =========================================================================

    async def fetch_ticker(self, symbol: str) -> dict[str, Any] | None:
        """Fetch current ticker data for a symbol (e.g., 'BTC/EUR')."""
        if not self.exchange or not self._check_credentials():
            return None

        if not self.circuit_breaker.allow_request():
            logger.warning("Bitvavo circuit breaker is OPEN")
            return None

        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            await self.circuit_breaker.record_success()
            return ticker
        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
            await self.circuit_breaker.record_failure()
            return None

    async def fetch_ohlcv(
        self, symbol: str, timeframe: str = "1h", limit: int = 100
    ) -> list[list[float]] | None:
        """
        Fetch OHLCV (candlestick) data.

        Args:
            symbol: Trading pair (e.g., 'BTC/EUR')
            timeframe: '1m', '5m', '15m', '1h', '4h', '1d'
            limit: Number of candles (max 1000)
        """
        if not self.exchange or not self._check_credentials():
            return None

        if not self.circuit_breaker.allow_request():
            return None

        try:
            ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            await self.circuit_breaker.record_success()
            return ohlcv
        except Exception as e:
            logger.error(f"Error fetching OHLCV for {symbol}: {e}")
            await self.circuit_breaker.record_failure()
            return None

    async def fetch_order_book(self, symbol: str, limit: int = 20) -> dict[str, Any] | None:
        """Fetch order book for a symbol."""
        if not self.exchange or not self._check_credentials():
            return None

        if not self.circuit_breaker.allow_request():
            return None

        try:
            orderbook = await self.exchange.fetch_order_book(symbol, limit)
            await self.circuit_breaker.record_success()
            return orderbook
        except Exception as e:
            logger.error(f"Error fetching order book for {symbol}: {e}")
            await self.circuit_breaker.record_failure()
            return None

    # =========================================================================
    # Account Methods
    # =========================================================================

    async def fetch_balance(self) -> dict[str, Any] | None:
        """Fetch account balance."""
        if not self.exchange or not self._check_credentials():
            return None

        if not self.circuit_breaker.allow_request():
            return None

        try:
            balance = await self.exchange.fetch_balance()
            await self.circuit_breaker.record_success()

            # Log EUR balance
            eur_balance = balance.get("EUR", {})
            if eur_balance:
                logger.info(
                    f"EUR Balance: Free={eur_balance.get('free', 0)}, Used={eur_balance.get('used', 0)}"
                )

            return balance
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            await self.circuit_breaker.record_failure()
            return None

    # =========================================================================
    # Trading Methods
    # =========================================================================

    @paper_guard
    async def create_limit_order(
        self,
        symbol: str,
        side: str,  # 'buy' or 'sell'
        amount: float,
        price: float,
    ) -> dict[str, Any] | None:
        """
        Create a limit order.

        🔒 PAPER MODE: Deze methode wordt geblokkeerd door @paper_guard
        decorator als TRADING_MODE=paper. Gebruik ShadowPortfolioManager
        voor paper trading.

        Args:
            symbol: Trading pair (e.g., 'BTC/EUR')
            side: 'buy' or 'sell'
            amount: Amount to buy/sell
            price: Limit price
        """
        if not self.exchange or not self._check_credentials():
            return None

        if not self.circuit_breaker.allow_request():
            return None

        try:
            order = (
                await self.exchange.create_limit_buy_order(symbol, amount, price)
                if side == "buy"
                else await self.exchange.create_limit_sell_order(symbol, amount, price)
            )

            await self.circuit_breaker.record_success()
            logger.info(f"Created {side} limit order: {amount} {symbol} @ {price}")
            return order

        except Exception as e:
            logger.error(f"Error creating {side} order: {e}")
            await self.circuit_breaker.record_failure()
            return None

    @paper_guard
    async def create_market_order(
        self,
        symbol: str,
        side: str,
        amount: float,
    ) -> dict[str, Any] | None:
        """
        Create a market order.

        🔒 PAPER MODE: Deze methode wordt geblokkeerd door @paper_guard
        decorator als TRADING_MODE=paper. Gebruik ShadowPortfolioManager
        voor paper trading.
        """
        if not self.exchange or not self._check_credentials():
            return None

        if not self.circuit_breaker.allow_request():
            return None

        try:
            order = (
                await self.exchange.create_market_buy_order(symbol, amount)
                if side == "buy"
                else await self.exchange.create_market_sell_order(symbol, amount)
            )

            await self.circuit_breaker.record_success()
            logger.info(f"Created {side} market order: {amount} {symbol}")
            return order

        except Exception as e:
            logger.error(f"Error creating market order: {e}")
            await self.circuit_breaker.record_failure()
            return None

    @paper_guard
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """
        Cancel an existing order.

        🔒 PAPER MODE: Geblokkeerd door @paper_guard in paper mode.
        """
        if not self.exchange or not self._check_credentials():
            return False

        try:
            await self.exchange.cancel_order(order_id, symbol)
            logger.info(f"Cancelled order {order_id}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return False

    @paper_guard
    async def fetch_open_orders(self, symbol: str | None = None) -> list[dict[str, Any]]:
        """
        Fetch all open orders.

        🔒 PAPER MODE: Geblokkeerd door @paper_guard in paper mode.
        """
        if not self.exchange or not self._check_credentials():
            return []

        try:
            orders = await self.exchange.fetch_open_orders(symbol)
            return orders
        except Exception as e:
            logger.error(f"Error fetching open orders: {e}")
            return []

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def get_eur_pairs(self) -> list[str]:
        """Get all available EUR trading pairs."""
        if not self.exchange:
            return []
        return [s for s in self.exchange.markets if s.endswith("/EUR")]

    def get_crypto_pairs(self, quote: str = "EUR") -> list[str]:
        """Get all trading pairs for a quote currency."""
        if not self.exchange:
            return []
        suffix = f"/{quote}"
        return [s for s in self.exchange.markets if s.endswith(suffix)]


# Factory function for easy instantiation
async def create_bitvavo_adapter() -> BitvavoAdapter | None:
    """
    Create and initialize a Bitvavo adapter.

    Returns:
        Connected BitvavoAdapter or None if initialization failed
    """
    adapter = BitvavoAdapter()
    success = await adapter.initialize()
    return adapter if success else None
