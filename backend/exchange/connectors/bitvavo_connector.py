"""
Bitvavo Exchange Connector.

⚠️ DEPRECATED: This module is deprecated and will be removed in Week 8.
Use BitvavoAdapter from backend.execution.bitvavo_adapter instead.

See: docs/adr/ADR-008-unified-execution-schema.md

Implements the BaseExchange interface for Bitvavo, a Dutch
cryptocurrency exchange focused on EUR trading pairs.

Features:
- EUR trading pairs (BTC-EUR, ETH-EUR, etc.)
- iDEAL/Bancontact deposits
- Competitive fees (0.25% taker, 0.15% maker)
- Dutch regulatory compliance (DNB registration)
"""

from __future__ import annotations

import logging
import warnings
from datetime import datetime
from decimal import Decimal
from typing import Any

import ccxt.async_support as ccxt

# Deprecation warning
warnings.warn(
    "BitvavoConnector is deprecated. Use BitvavoAdapter from "
    "backend.execution.bitvavo_adapter instead. "
    "See ADR-008 for migration guide.",
    DeprecationWarning,
    stacklevel=2
)

from backend.core.config.settings import settings
from backend.exchange.base_exchange import (
    OHLCV,
    Balance,
    BaseExchange,
    ExchangeCapabilities,
    Order,
    OrderRequest,
    OrderSide,
    OrderStatus,
    OrderType,
    Symbol,
    Ticker,
    TimeInForce,
)

logger = logging.getLogger(__name__)


class BitvavoConnector(BaseExchange):
    """
    Bitvavo exchange connector.

    Example:
        >>> connector = BitvavoConnector(exchange_id="bitvavo_main")
        >>> await connector.connect()
        >>>
        >>> # Get balance
        >>> balance = await connector.get_balance("EUR")
        >>> print(f"EUR: {balance.free}")
        >>>
        >>> # Place order
        >>> request = OrderRequest(
        ...     symbol=Symbol("BTC", "EUR"),
        ...     side=OrderSide.BUY,
        ...     order_type=OrderType.LIMIT,
        ...     amount=Decimal("0.1"),
        ...     price=Decimal("45000")
        ... )
        >>> order = await connector.create_order(request)
    """

    def __init__(self, exchange_id: str = "bitvavo", config: dict[str, Any] | None = None):
        """
        Initialize Bitvavo connector.

        Args:
            exchange_id: Unique identifier for this instance
            config: Configuration with keys:
                - api_key: Bitvavo API key
                - api_secret: Bitvavo API secret
                - sandbox: Use sandbox mode
        """
        super().__init__(exchange_id, config)

        # Get credentials from config or settings
        self.api_key = config.get("api_key") if config else None
        self.api_secret = config.get("api_secret") if config else None
        self.sandbox = config.get("sandbox", False) if config else False

        # Fallback to settings
        if not self.api_key:
            self.api_key = settings.BITVAVO_API_KEY
        if not self.api_secret:
            self.api_secret = settings.BITVAVO_API_SECRET
        if not self.sandbox:
            self.sandbox = settings.BITVAVO_SANDBOX

        self.exchange: ccxt.bitvavo | None = None
        self._markets: dict[str, Any] = {}

        logger.info(f"[{self.exchange_id}] Bitvavo connector initialized (sandbox={self.sandbox})")

    # -------------------------------------------------------------------------
    # Connection Management
    # -------------------------------------------------------------------------

    async def connect(self) -> bool:
        """Connect to Bitvavo API."""
        if not self.api_key or not self.api_secret:
            logger.warning(f"[{self.exchange_id}] Bitvavo API credentials not configured")
            return False

        try:
            config = {
                "apiKey": self.api_key,
                "secret": self.api_secret,
                "enableRateLimit": True,
                "options": {
                    "defaultType": "spot",
                }
            }

            if self.sandbox:
                config["sandbox"] = True

            self.exchange = ccxt.bitvavo(config)
            await self.exchange.load_markets()

            self._markets = self.exchange.markets
            self._connected = True

            # Log available markets
            eur_pairs = [s for s in self._markets if s.endswith("/EUR")]
            logger.info(f"[{self.exchange_id}] Connected to Bitvavo")
            logger.info(f"[{self.exchange_id}] Available markets: {len(self._markets)}")
            logger.info(f"[{self.exchange_id}] EUR pairs: {len(eur_pairs)}")

            return True

        except Exception as e:
            logger.error(f"[{self.exchange_id}] Failed to connect: {e}")
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Disconnect from Bitvavo API."""
        if self.exchange:
            await self.exchange.close()
            self.exchange = None

        self._connected = False
        logger.info(f"[{self.exchange_id}] Disconnected from Bitvavo")

    async def is_connected(self) -> bool:
        """Check connection status."""
        return self._connected and self.exchange is not None

    # -------------------------------------------------------------------------
    # Market Data
    # -------------------------------------------------------------------------

    async def get_ticker(self, symbol: Symbol) -> Ticker | None:
        """Get current ticker data."""
        if not self.exchange:
            return None

        try:
            ccxt_symbol = self.format_symbol(symbol)
            ticker_data = await self.exchange.fetch_ticker(ccxt_symbol)

            return Ticker(
                symbol=symbol,
                timestamp=datetime.utcnow(),
                bid=Decimal(str(ticker_data["bid"])),
                ask=Decimal(str(ticker_data["ask"])),
                last=Decimal(str(ticker_data["last"])),
                volume_24h=Decimal(str(ticker_data.get("quoteVolume", 0))),
                high_24h=Decimal(str(ticker_data.get("high", 0))),
                low_24h=Decimal(str(ticker_data.get("low", 0))),
                change_24h=Decimal(str(ticker_data.get("change", 0))),
                change_pct_24h=Decimal(str(ticker_data.get("percentage", 0))),
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
        """Get OHLCV candlestick data."""
        if not self.exchange:
            return []

        try:
            ccxt_symbol = self.format_symbol(symbol)

            # Convert timeframe to CCXT format
            tf_map = {
                "1m": "1m", "5m": "5m", "15m": "15m",
                "1h": "1h", "4h": "4h", "1d": "1d"
            }
            ccxt_tf = tf_map.get(timeframe, "1h")

            since_ms = int(since.timestamp() * 1000) if since else None

            ohlcv_data = await self.exchange.fetch_ohlcv(
                ccxt_symbol, ccxt_tf, since=since_ms, limit=limit
            )

            return [
                OHLCV(
                    timestamp=datetime.utcfromtimestamp(candle[0] / 1000),
                    open=Decimal(str(candle[1])),
                    high=Decimal(str(candle[2])),
                    low=Decimal(str(candle[3])),
                    close=Decimal(str(candle[4])),
                    volume=Decimal(str(candle[5])),
                )
                for candle in ohlcv_data
            ]
        except Exception as e:
            logger.error(f"[{self.exchange_id}] Error fetching OHLCV: {e}")
            return []

    async def get_orderbook(
        self,
        symbol: Symbol,
        limit: int = 20
    ) -> dict[str, list[tuple]]:
        """Get order book."""
        if not self.exchange:
            return {"bids": [], "asks": []}

        try:
            ccxt_symbol = self.format_symbol(symbol)
            orderbook = await self.exchange.fetch_order_book(ccxt_symbol, limit)

            return {
                "bids": [(Decimal(str(p)), Decimal(str(a))) for p, a in orderbook["bids"][:limit]],
                "asks": [(Decimal(str(p)), Decimal(str(a))) for p, a in orderbook["asks"][:limit]],
            }
        except Exception as e:
            logger.error(f"[{self.exchange_id}] Error fetching orderbook: {e}")
            return {"bids": [], "asks": []}

    # -------------------------------------------------------------------------
    # Account Data
    # -------------------------------------------------------------------------

    async def get_balance(self, asset: str | None = None) -> Balance | None | dict[str, Balance]:
        """Get account balance."""
        if not self.exchange:
            return None if asset else {}

        try:
            balance_data = await self.exchange.fetch_balance()

            balances = {}
            for currency, data in balance_data.items():
                if isinstance(data, dict) and "total" in data:
                    total = Decimal(str(data.get("total", 0)))
                    free = Decimal(str(data.get("free", 0)))
                    used = Decimal(str(data.get("used", 0)))

                    if total > 0 or currency in ["EUR", "USD", "USDT", "BTC", "ETH"]:
                        balances[currency] = Balance(
                            asset=currency,
                            free=free,
                            used=used,
                            total=total
                        )

            if asset:
                return balances.get(asset)
            return balances

        except Exception as e:
            logger.error(f"[{self.exchange_id}] Error fetching balance: {e}")
            return None if asset else {}

    # -------------------------------------------------------------------------
    # Trading Operations
    # -------------------------------------------------------------------------

    async def create_order(self, request: OrderRequest) -> Order | None:
        """Create a new order."""
        if not self.exchange:
            return None

        try:
            ccxt_symbol = self.format_symbol(request.symbol)
            side = request.side.value
            order_type = request.order_type.value
            amount = float(request.amount)

            params = {}

            # Handle time in force
            if request.time_in_force == TimeInForce.POST_ONLY:
                params["postOnly"] = True

            # Create order
            if request.order_type == OrderType.MARKET:
                if request.side == OrderSide.BUY:
                    order_data = await self.exchange.create_market_buy_order(ccxt_symbol, amount)
                else:
                    order_data = await self.exchange.create_market_sell_order(ccxt_symbol, amount)
            else:  # LIMIT
                price = float(request.price)
                if request.side == OrderSide.BUY:
                    order_data = await self.exchange.create_limit_buy_order(ccxt_symbol, amount, price, params)
                else:
                    order_data = await self.exchange.create_limit_sell_order(ccxt_symbol, amount, price, params)

            return self._parse_order(order_data, request.symbol)

        except Exception as e:
            logger.error(f"[{self.exchange_id}] Error creating order: {e}")
            return None

    async def cancel_order(self, order_id: str, symbol: Symbol | None = None) -> bool:
        """Cancel an existing order."""
        if not self.exchange:
            return False

        try:
            ccxt_symbol = self.format_symbol(symbol) if symbol else None
            await self.exchange.cancel_order(order_id, ccxt_symbol)
            logger.info(f"[{self.exchange_id}] Cancelled order: {order_id}")
            return True
        except Exception as e:
            logger.error(f"[{self.exchange_id}] Error cancelling order: {e}")
            return False

    async def get_order(self, order_id: str, symbol: Symbol | None = None) -> Order | None:
        """Get order information."""
        if not self.exchange:
            return None

        try:
            ccxt_symbol = self.format_symbol(symbol) if symbol else None
            order_data = await self.exchange.fetch_order(order_id, ccxt_symbol)
            return self._parse_order(order_data, symbol)
        except Exception as e:
            logger.error(f"[{self.exchange_id}] Error fetching order: {e}")
            return None

    async def get_open_orders(self, symbol: Symbol | None = None) -> list[Order]:
        """Get all open orders."""
        if not self.exchange:
            return []

        try:
            ccxt_symbol = self.format_symbol(symbol) if symbol else None
            orders_data = await self.exchange.fetch_open_orders(ccxt_symbol)
            return [self._parse_order(o, symbol) for o in orders_data]
        except Exception as e:
            logger.error(f"[{self.exchange_id}] Error fetching open orders: {e}")
            return []

    # -------------------------------------------------------------------------
    # Exchange Information
    # -------------------------------------------------------------------------

    def get_capabilities(self) -> ExchangeCapabilities:
        """Get exchange capabilities."""
        return ExchangeCapabilities(
            name="Bitvavo",
            supports_spot=True,
            supports_margin=False,
            supports_futures=False,
            supports_options=False,
            supports_websocket=True,
            supports_testnet=True,
            fee_maker=Decimal("0.0015"),  # 0.15%
            fee_taker=Decimal("0.0025"),  # 0.25%
        )

    async def get_trading_fees(self, symbol: Symbol | None = None) -> dict[str, Decimal]:
        """Get trading fees."""
        if not self.exchange:
            return {"maker": Decimal("0.0015"), "taker": Decimal("0.0025")}

        try:
            fees = await self.exchange.fetch_trading_fees()
            return {
                "maker": Decimal(str(fees.get("maker", 0.0015))),
                "taker": Decimal(str(fees.get("taker", 0.0025))),
            }
        except Exception:
            return {"maker": Decimal("0.0015"), "taker": Decimal("0.0025")}

    async def get_symbol_info(self, symbol: Symbol) -> dict[str, Any]:
        """Get symbol information."""
        ccxt_symbol = self.format_symbol(symbol)
        market = self._markets.get(ccxt_symbol, {})

        limits = market.get("limits", {})
        precision = market.get("precision", {})

        return {
            "symbol": str(symbol),
            "min_amount": Decimal(str(limits.get("amount", {}).get("min", 0))),
            "max_amount": limits.get("amount", {}).get("max"),
            "min_price": Decimal(str(limits.get("price", {}).get("min", 0))),
            "amount_precision": precision.get("amount", 8),
            "price_precision": precision.get("price", 2),
        }

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    def format_symbol(self, symbol: Symbol) -> str:
        """Format symbol for Bitvavo (BTC/EUR)."""
        return f"{symbol.base}/{symbol.quote}"

    def _parse_order(self, data: dict[str, Any], symbol: Symbol | None = None) -> Order:
        """Parse CCXT order data to Order object."""
        # Extract symbol
        if not symbol:
            symbol_str = data.get("symbol", "")
            symbol = Symbol.from_string(symbol_str)

        # Map status
        status_map = {
            "open": OrderStatus.OPEN,
            "closed": OrderStatus.FILLED,
            "canceled": OrderStatus.CANCELLED,
            "cancelled": OrderStatus.CANCELLED,
            "pending": OrderStatus.PENDING,
            "rejected": OrderStatus.REJECTED,
        }

        ccxt_status = data.get("status", "open")
        status = status_map.get(ccxt_status, OrderStatus.OPEN)

        # Determine if partially filled
        filled = Decimal(str(data.get("filled", 0)))
        amount = Decimal(str(data.get("amount", 0)))

        if filled > 0 and filled < amount:
            status = OrderStatus.PARTIALLY_FILLED

        return Order(
            order_id=data.get("id", ""),
            client_order_id=data.get("clientOrderId"),
            symbol=symbol,
            side=OrderSide(data.get("side", "buy")),
            order_type=OrderType(data.get("type", "limit")),
            status=status,
            amount=amount,
            filled=filled,
            remaining=Decimal(str(data.get("remaining", 0))),
            price=Decimal(str(data.get("price"))) if data.get("price") else None,
            average_price=Decimal(str(data.get("average"))) if data.get("average") else None,
            stop_price=None,
            time_in_force=TimeInForce.GTC,
            created_at=datetime.utcfromtimestamp(data.get("timestamp", 0) / 1000),
            updated_at=datetime.utcnow(),
            exchange_id=self.exchange_id,
            metadata=data,
        )
