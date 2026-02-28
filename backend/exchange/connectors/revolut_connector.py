"""
Revolut Exchange Connector ⚠️ DEPRECATED

⚠️ DEPRECATED: This module is deprecated and will be removed in Week 8.
Use RevolutXAdapter from backend.execution.revolut_x_adapter instead.

See: docs/adr/ADR-008-unified-execution-schema.md
.

Implements the BaseExchange interface for Revolut X crypto trading.

Features:
- Crypto trading via Revolut X platform
- JWT-based authentication
- Spot trading only (no futures)
- EUR/USD trading pairs
"""

from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

from backend.core.config.settings import settings
from backend.exchange.base_exchange import (
    OHLCV,
    Balance,
    BaseExchange,
    ExchangeCapabilities,
    Order,
    OrderRequest,
    OrderStatus,
    Symbol,
    Ticker,
    TimeInForce,
)

logger = logging.getLogger(__name__)


class RevolutConnector(BaseExchange):
    """
    Revolut X exchange connector.

    Uses the existing RevolutXClient from backend.integrations.

    Example:
        >>> connector = RevolutConnector(exchange_id="revolut_main")
        >>> await connector.connect()
        >>>
        >>> # Get balance
        >>> balance = await connector.get_balance("BTC")
        >>> print(f"BTC: {balance.free}")
        >>>
        >>> # Place order
        >>> request = OrderRequest(
        ...     symbol=Symbol("BTC", "USD"),
        ...     side=OrderSide.BUY,
        ...     order_type=OrderType.MARKET,
        ...     amount=Decimal("0.01")
        ... )
        >>> order = await connector.create_order(request)
    """

    def __init__(self, exchange_id: str = "revolut", config: dict[str, Any] | None = None):
        """
        Initialize Revolut connector.

        Args:
            exchange_id: Unique identifier for this instance
            config: Configuration with keys:
                - api_key: Revolut API key
                - private_key_path: Path to Ed25519 private key
                - sandbox: Use sandbox mode
        """
        super().__init__(exchange_id, config)

        # Get credentials from config or settings
        self.api_key = config.get("api_key") if config else None
        self.private_key_path = config.get("private_key_path") if config else None
        self.sandbox = config.get("sandbox", False) if config else False

        # Fallback to settings
        if not self.api_key:
            self.api_key = settings.REVOLUT_API_KEY
        if not self.private_key_path:
            self.private_key_path = settings.REVOLUT_PRIVATE_KEY_PATH
        if not self.sandbox:
            self.sandbox = settings.REVOLUT_SANDBOX

        self._client = None
        self._account_info: dict | None = None

        logger.info(f"[{self.exchange_id}] Revolut connector initialized (sandbox={self.sandbox})")

    # -------------------------------------------------------------------------
    # Connection Management
    # -------------------------------------------------------------------------

    async def connect(self) -> bool:
        """Connect to Revolut X API."""
        if not self.api_key:
            logger.warning(f"[{self.exchange_id}] Revolut API key not configured")
            return False

        try:
            # Import here to avoid circular imports
            from backend.integrations.revolut_x_client import RevolutXClient

            self._client = RevolutXClient(
                api_key=self.api_key,
                private_key_path=self.private_key_path,
                sandbox=self.sandbox
            )

            connected = await self._client.connect()

            if connected:
                self._connected = True
                logger.info(f"[{self.exchange_id}] Connected to Revolut X")

                # Get account info
                self._account_info = await self._client.get_account_info()
                if self._account_info:
                    logger.info(f"[{self.exchange_id}] Account: {self._account_info.get('id', 'Unknown')}")

                return True
            else:
                logger.error(f"[{self.exchange_id}] Failed to connect to Revolut X")
                return False

        except Exception as e:
            logger.error(f"[{self.exchange_id}] Connection error: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from Revolut X API."""
        if self._client:
            await self._client.disconnect()
            self._client = None

        self._connected = False
        logger.info(f"[{self.exchange_id}] Disconnected from Revolut X")

    async def is_connected(self) -> bool:
        """Check connection status."""
        return self._connected and self._client is not None

    # -------------------------------------------------------------------------
    # Market Data
    # -------------------------------------------------------------------------

    async def get_ticker(self, symbol: Symbol) -> Ticker | None:
        """Get current ticker data."""
        if not self._client:
            return None

        try:
            # Revolut uses BTC-USD format
            revolut_symbol = self.format_symbol(symbol)
            ticker_data = await self._client.get_ticker(revolut_symbol)

            return Ticker(
                symbol=symbol,
                timestamp=datetime.utcnow(),
                bid=Decimal(str(ticker_data.get("bid", 0))),
                ask=Decimal(str(ticker_data.get("ask", 0))),
                last=Decimal(str(ticker_data.get("last", 0))),
                volume_24h=Decimal(str(ticker_data.get("volume", 0))),
            )
        except Exception as e:
            logger.error(f"[{self.exchange_id}] Error fetching ticker: {e}")
            return None

    async def get_ohlcv(
        self,
        symbol: Symbol,
        timeframe: str = "1h",
        limit: int = 100,
        since: datetime | None = None
    ) -> list[OHLCV]:
        """Get OHLCV data."""
        # Revolut X doesn't provide OHLCV via basic API
        # Would need to implement or use alternative data source
        logger.warning(f"[{self.exchange_id}] OHLCV not directly available via Revolut X API")
        return []

    async def get_orderbook(
        self,
        symbol: Symbol,
        limit: int = 20
    ) -> dict[str, list[tuple]]:
        """Get order book."""
        if not self._client:
            return {"bids": [], "asks": []}

        try:
            revolut_symbol = self.format_symbol(symbol)
            orderbook = await self._client.get_orderbook(revolut_symbol, depth=limit)

            return {
                "bids": [(Decimal(str(p)), Decimal(str(a))) for p, a in orderbook.get("bids", [])[:limit]],
                "asks": [(Decimal(str(p)), Decimal(str(a))) for p, a in orderbook.get("asks", [])[:limit]],
            }
        except Exception as e:
            logger.error(f"[{self.exchange_id}] Error fetching orderbook: {e}")
            return {"bids": [], "asks": []}

    # -------------------------------------------------------------------------
    # Account Data
    # -------------------------------------------------------------------------

    async def get_balance(self, asset: str | None = None) -> Balance | None | dict[str, Balance]:
        """Get account balance."""
        if not self._client:
            return None if asset else {}

        try:
            if asset:
                # Get specific asset balance
                crypto_balance = await self._client.get_crypto_balance(asset)
                if crypto_balance:
                    return Balance(
                        asset=asset,
                        free=Decimal(str(crypto_balance.amount - crypto_balance.locked)),
                        used=Decimal(str(crypto_balance.locked)),
                        total=Decimal(str(crypto_balance.amount))
                    )
                return None
            else:
                # Get all balances
                portfolio = await self._client.get_portfolio()
                balances = {}

                if portfolio:
                    for symbol, crypto_balance in portfolio.items():
                        balances[symbol] = Balance(
                            asset=symbol,
                            free=Decimal(str(crypto_balance.amount - crypto_balance.locked)),
                            used=Decimal(str(crypto_balance.locked)),
                            total=Decimal(str(crypto_balance.amount))
                        )

                return balances

        except Exception as e:
            logger.error(f"[{self.exchange_id}] Error fetching balance: {e}")
            return None if asset else {}

    # -------------------------------------------------------------------------
    # Trading Operations
    # -------------------------------------------------------------------------

    async def create_order(self, request: OrderRequest) -> Order | None:
        """Create a new order."""
        if not self._client:
            return None

        try:
            from backend.integrations.revolut_x_client import OrderSide, OrderType

            revolut_symbol = self.format_symbol(request.symbol)

            # Map side
            side = OrderSide.BUY if request.side == OrderSide.BUY else OrderSide.SELL

            # Map order type
            if request.order_type == OrderType.MARKET:
                order_type = OrderType.MARKET
            else:
                order_type = OrderType.LIMIT

            # Place order
            revolut_order = await self._client.place_order(
                symbol=revolut_symbol,
                side=side,
                quantity=float(request.amount),
                price=float(request.price) if request.price else None,
                order_type=order_type
            )

            if revolut_order:
                return self._parse_revolut_order(revolut_order)

            return None

        except Exception as e:
            logger.error(f"[{self.exchange_id}] Error creating order: {e}")
            return None

    async def cancel_order(self, order_id: str, symbol: Symbol | None = None) -> bool:
        """Cancel an existing order."""
        if not self._client:
            return False

        try:
            success = await self._client.cancel_order(order_id)
            if success:
                logger.info(f"[{self.exchange_id}] Cancelled order: {order_id}")
            return success
        except Exception as e:
            logger.error(f"[{self.exchange_id}] Error cancelling order: {e}")
            return False

    async def get_order(self, order_id: str, symbol: Symbol | None = None) -> Order | None:
        """Get order information."""
        if not self._client:
            return None

        try:
            revolut_order = await self._client.get_order_status(order_id)
            if revolut_order:
                return self._parse_revolut_order(revolut_order)
            return None
        except Exception as e:
            logger.error(f"[{self.exchange_id}] Error fetching order: {e}")
            return None

    async def get_open_orders(self, symbol: Symbol | None = None) -> list[Order]:
        """Get all open orders."""
        if not self._client:
            return []

        try:
            # Revolut X client doesn't have direct get_open_orders
            # Would need to implement or track locally
            logger.warning(f"[{self.exchange_id}] get_open_orders not directly available")
            return []
        except Exception as e:
            logger.error(f"[{self.exchange_id}] Error fetching open orders: {e}")
            return []

    # -------------------------------------------------------------------------
    # Exchange Information
    # -------------------------------------------------------------------------

    def get_capabilities(self) -> ExchangeCapabilities:
        """Get exchange capabilities."""
        return ExchangeCapabilities(
            name="Revolut X",
            supports_spot=True,
            supports_margin=False,
            supports_futures=False,
            supports_options=False,
            supports_websocket=False,
            supports_testnet=True,
            fee_maker=Decimal("0.0025"),  # Approximate
            fee_taker=Decimal("0.0025"),  # Approximate
        )

    async def get_trading_fees(self, symbol: Symbol | None = None) -> dict[str, Decimal]:
        """Get trading fees."""
        # Revolut X fees vary by plan (Standard/Plus/Premium/Metal)
        # These are approximate
        return {
            "maker": Decimal("0.0025"),  # 0.25%
            "taker": Decimal("0.0025"),  # 0.25%
        }

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def format_symbol(self, symbol: Symbol) -> str:
        """Format symbol for Revolut (BTC-USD)."""
        return f"{symbol.base}-{symbol.quote}"

    def _parse_revolut_order(self, revolut_order) -> Order:
        """Parse Revolut order to Order object."""
        from backend.integrations.revolut_x_client import OrderSide, OrderType

        # Map status
        status_map = {
            "PENDING": OrderStatus.PENDING,
            "OPEN": OrderStatus.OPEN,
            "FILLED": OrderStatus.FILLED,
            "CANCELLED": OrderStatus.CANCELLED,
            "REJECTED": OrderStatus.REJECTED,
        }

        status = status_map.get(revolut_order.status, OrderStatus.OPEN)

        # Map side
        side = OrderSide.BUY if revolut_order.side == OrderSide.BUY else OrderSide.SELL

        # Map order type
        order_type = OrderType.MARKET if revolut_order.order_type == OrderType.MARKET else OrderType.LIMIT

        # Parse symbol
        symbol_str = revolut_order.symbol.replace("-", "/")
        symbol = Symbol.from_string(symbol_str)

        return Order(
            order_id=revolut_order.order_id,
            client_order_id=None,
            symbol=symbol,
            side=side,
            order_type=order_type,
            status=status,
            amount=Decimal(str(revolut_order.quantity)),
            filled=Decimal(str(revolut_order.filled_qty)),
            remaining=Decimal(str(revolut_order.quantity - revolut_order.filled_qty)),
            price=Decimal(str(revolut_order.price)) if revolut_order.price else None,
            average_price=Decimal(str(revolut_order.average_price)) if revolut_order.average_price else None,
            stop_price=None,
            time_in_force=TimeInForce.GTC,
            created_at=revolut_order.timestamp,
            updated_at=revolut_order.updated_at,
            exchange_id=self.exchange_id,
        )
