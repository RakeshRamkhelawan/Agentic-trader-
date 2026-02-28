"""
Base Exchange Interface for Agentic Trader Platform.

This module defines the abstract base class that all exchange connectors must implement.
It provides a unified interface for trading operations across different exchanges.

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │                    BaseExchange (ABC)                       │
    │                    ─────────────────                        │
    │  • connect()           • create_order()                     │
    │  • disconnect()        • cancel_order()                     │
    │  • get_balance()       • get_order_status()                 │
    │  • get_ticker()        • get_positions()                    │
    │  • get_ohlcv()         • subscribe_ws()                     │
    └─────────────────────────────────────────────────────────────┘
                              △
            ┌─────────────────┼─────────────────┐
            │                 │                 │
    ┌───────┴──────┐ ┌────────┴────────┐ ┌─────┴──────┐
    │   Bitvavo    │ │    Revolut      │ │  Future    │
    │  Connector   │ │    Connector    │ │ Exchanges  │
    └──────────────┘ └─────────────────┘ └────────────┘
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Protocol

logger = logging.getLogger(__name__)


# =============================================================================
# Enums and Constants
# =============================================================================

class OrderSide(Enum):
    """Order side enumeration."""
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    """Order type enumeration."""
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class OrderStatus(Enum):
    """Order status enumeration."""
    PENDING = "pending"
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class TimeInForce(Enum):
    """Time in force enumeration."""
    GTC = "gtc"           # Good Till Cancelled
    IOC = "ioc"           # Immediate Or Cancel
    FOK = "fok"           # Fill Or Kill
    GTD = "gtd"           # Good Till Date
    POST_ONLY = "post_only"


class ExchangeType(Enum):
    """Exchange type enumeration."""
    SPOT = "spot"
    MARGIN = "margin"
    FUTURES = "futures"
    OPTIONS = "options"


# =============================================================================
# Data Classes
# =============================================================================

@dataclass(frozen=True)
class Symbol:
    """Trading pair symbol representation."""
    base: str           # Base asset (e.g., BTC)
    quote: str          # Quote asset (e.g., EUR)

    def __str__(self) -> str:
        return f"{self.base}/{self.quote}"

    @classmethod
    def from_string(cls, symbol_str: str) -> Symbol:
        """Create Symbol from string like 'BTC/EUR' or 'BTC-EUR'."""
        for sep in ["/", "-", "_"]:
            if sep in symbol_str:
                base, quote = symbol_str.split(sep)
                return cls(base=base.upper(), quote=quote.upper())
        raise ValueError(f"Invalid symbol format: {symbol_str}")


@dataclass
class Balance:
    """Account balance for a single asset."""
    asset: str
    free: Decimal       # Available for trading
    used: Decimal       # Locked in orders
    total: Decimal      # free + used

    def __post_init__(self):
        if self.total != self.free + self.used:
            self.total = self.free + self.used


@dataclass
class Ticker:
    """Market ticker data."""
    symbol: Symbol
    timestamp: datetime
    bid: Decimal
    ask: Decimal
    last: Decimal
    volume_24h: Decimal
    high_24h: Decimal | None = None
    low_24h: Decimal | None = None
    change_24h: Decimal | None = None
    change_pct_24h: Decimal | None = None


@dataclass
class OHLCV:
    """OHLCV candlestick data."""
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal


@dataclass
class OrderRequest:
    """Order request parameters."""
    symbol: Symbol
    side: OrderSide
    order_type: OrderType
    amount: Decimal
    price: Decimal | None = None           # For limit orders
    stop_price: Decimal | None = None      # For stop orders
    time_in_force: TimeInForce = TimeInForce.GTC
    client_order_id: str | None = None
    post_only: bool = False
    reduce_only: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        """Validate order request."""
        if self.amount <= 0:
            raise ValueError("Order amount must be positive")

        if self.order_type in (OrderType.LIMIT, OrderType.STOP_LIMIT) and self.price is None:
            raise ValueError("Limit orders require a price")

        if self.order_type in (OrderType.STOP_LOSS, OrderType.STOP_LIMIT) and self.stop_price is None:
            raise ValueError("Stop orders require a stop_price")


@dataclass
class Order:
    """Order information."""
    order_id: str
    client_order_id: str | None
    symbol: Symbol
    side: OrderSide
    order_type: OrderType
    status: OrderStatus
    amount: Decimal           # Original amount
    filled: Decimal          # Filled amount
    remaining: Decimal       # Remaining to fill
    price: Decimal | None # Order price (None for market)
    average_price: Decimal | None  # Average fill price
    stop_price: Decimal | None
    time_in_force: TimeInForce
    created_at: datetime
    updated_at: datetime
    exchange_id: str         # Exchange that owns this order
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_open(self) -> bool:
        return self.status in (OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED, OrderStatus.PENDING)

    @property
    def is_filled(self) -> bool:
        return self.status == OrderStatus.FILLED

    @property
    def fill_percentage(self) -> Decimal:
        if self.amount == 0:
            return Decimal("0")
        return (self.filled / self.amount) * 100


@dataclass
class Position:
    """Trading position."""
    symbol: Symbol
    side: OrderSide         # Overall position side
    amount: Decimal         # Position size
    entry_price: Decimal
    mark_price: Decimal | None = None
    liquidation_price: Decimal | None = None
    margin: Decimal | None = None
    unrealized_pnl: Decimal | None = None
    realized_pnl: Decimal | None = None
    leverage: Decimal = Decimal("1")
    created_at: datetime | None = None
    exchange_id: str = ""


@dataclass
class OrderBook:
    """Order book data."""
    symbol: Symbol
    timestamp: datetime
    bids: list[tuple]  # (price, amount) tuples
    asks: list[tuple]  # (price, amount) tuples

    @property
    def best_bid(self) -> Decimal | None:
        return Decimal(str(self.bids[0][0])) if self.bids else None

    @property
    def best_ask(self) -> Decimal | None:
        return Decimal(str(self.asks[0][0])) if self.asks else None

    @property
    def spread(self) -> Decimal | None:
        if self.best_bid and self.best_ask:
            return self.best_ask - self.best_bid
        return None

    @property
    def mid_price(self) -> Decimal | None:
        if self.best_bid and self.best_ask:
            return (self.best_bid + self.best_ask) / 2
        return None


@dataclass
class Trade:
    """Trade execution information."""
    trade_id: str
    order_id: str
    symbol: Symbol
    side: OrderSide
    amount: Decimal
    price: Decimal
    fee: Decimal
    fee_currency: str
    timestamp: datetime
    exchange_id: str = ""


@dataclass
class ExchangeCapabilities:
    """Exchange capabilities and features."""
    name: str
    supports_spot: bool = True
    supports_margin: bool = False
    supports_futures: bool = False
    supports_options: bool = False
    supports_websocket: bool = False
    supports_testnet: bool = False
    max_leverage: Decimal = Decimal("1")
    fee_maker: Decimal = Decimal("0")
    fee_taker: Decimal = Decimal("0")
    min_order_size: dict[str, Decimal] = field(default_factory=dict)
    price_precision: dict[str, int] = field(default_factory=dict)
    amount_precision: dict[str, int] = field(default_factory=dict)


# =============================================================================
# WebSocket Protocol
# =============================================================================

class WebSocketHandler(Protocol):
    """Protocol for WebSocket message handlers."""

    async def on_ticker(self, ticker: Ticker) -> None:
        ...

    async def on_trade(self, trade: Trade) -> None:
        ...

    async def on_orderbook(self, symbol: Symbol, bids: list[tuple], asks: list[tuple]) -> None:
        ...

    async def on_order_update(self, order: Order) -> None:
        ...


# =============================================================================
# Abstract Base Class
# =============================================================================

class BaseExchange(ABC):
    """
    Abstract base class for all exchange connectors.

    This class defines the interface that all exchange implementations must follow.
    It provides a unified API for trading operations regardless of the underlying
    exchange.

    Example:
        >>> exchange = BitvavoConnector()
        >>> await exchange.connect()
        >>>
        >>> # Get balance
        >>> balance = await exchange.get_balance("EUR")
        >>> print(f"EUR Balance: {balance.free}")
        >>>
        >>> # Place order
        >>> order_req = OrderRequest(
        ...     symbol=Symbol("BTC", "EUR"),
        ...     side=OrderSide.BUY,
        ...     order_type=OrderType.LIMIT,
        ...     amount=Decimal("0.1"),
        ...     price=Decimal("45000")
        ... )
        >>> order = await exchange.create_order(order_req)
        >>>
        >>> await exchange.disconnect()
    """

    def __init__(self, exchange_id: str, config: dict[str, Any] | None = None):
        """
        Initialize exchange connector.

        Args:
            exchange_id: Unique identifier for this exchange instance
            config: Optional configuration dictionary
        """
        self.exchange_id = exchange_id
        self.config = config or {}
        self._connected = False
        self._capabilities: ExchangeCapabilities | None = None
        self._last_request_time: datetime | None = None
        self._request_count = 0

        logger.info(f"[{self.exchange_id}] Exchange connector initialized")

    # -------------------------------------------------------------------------
    # Connection Management
    # -------------------------------------------------------------------------

    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to the exchange.

        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the exchange."""
        pass

    @abstractmethod
    async def is_connected(self) -> bool:
        """Check if exchange connection is active."""
        pass

    @property
    def connected(self) -> bool:
        """Property to check connection status."""
        return self._connected

    # -------------------------------------------------------------------------
    # Market Data
    # -------------------------------------------------------------------------

    @abstractmethod
    async def get_ticker(self, symbol: Symbol) -> Ticker | None:
        """
        Get current ticker data for a symbol.

        Args:
            symbol: Trading pair symbol

        Returns:
            Ticker data or None if unavailable
        """
        pass

    @abstractmethod
    async def get_ohlcv(
        self,
        symbol: Symbol,
        timeframe: str = "1h",
        limit: int = 100,
        since: datetime | None = None
    ) -> list[OHLCV]:
        """
        Get OHLCV (candlestick) data.

        Args:
            symbol: Trading pair symbol
            timeframe: Candle timeframe (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Number of candles to fetch
            since: Start time for historical data

        Returns:
            List of OHLCV candles
        """
        pass

    @abstractmethod
    async def get_orderbook(
        self,
        symbol: Symbol,
        limit: int = 20
    ) -> dict[str, list[tuple]]:
        """
        Get order book for a symbol.

        Args:
            symbol: Trading pair symbol
            limit: Number of price levels to fetch

        Returns:
            Dictionary with 'bids' and 'asks' lists of (price, amount) tuples
        """
        pass

    async def get_recent_trades(
        self,
        symbol: Symbol,
        limit: int = 100
    ) -> list[Trade]:
        """
        Get recent public trades.

        Args:
            symbol: Trading pair symbol
            limit: Number of trades to fetch

        Returns:
            List of recent trades
        """
        # Optional implementation - not all exchanges support this
        return []

    # -------------------------------------------------------------------------
    # Account Data
    # -------------------------------------------------------------------------

    @abstractmethod
    async def get_balance(self, asset: str | None = None) -> Balance | None | dict[str, Balance]:
        """
        Get account balance.

        Args:
            asset: Specific asset to get balance for, or None for all balances

        Returns:
            Balance for specific asset, or dict of all balances
        """
        pass

    async def get_all_balances(self) -> dict[str, Balance]:
        """Get all account balances."""
        result = await self.get_balance()
        if isinstance(result, dict):
            return result
        return {}

    # -------------------------------------------------------------------------
    # Trading Operations
    # -------------------------------------------------------------------------

    @abstractmethod
    async def create_order(self, request: OrderRequest) -> Order | None:
        """
        Create a new order.

        Args:
            request: Order request parameters

        Returns:
            Created order information or None if failed
        """
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: Symbol | None = None) -> bool:
        """
        Cancel an existing order.

        Args:
            order_id: Order ID to cancel
            symbol: Trading pair symbol (required by some exchanges)

        Returns:
            True if cancellation successful
        """
        pass

    @abstractmethod
    async def get_order(self, order_id: str, symbol: Symbol | None = None) -> Order | None:
        """
        Get order information.

        Args:
            order_id: Order ID to query
            symbol: Trading pair symbol

        Returns:
            Order information or None if not found
        """
        pass

    @abstractmethod
    async def get_open_orders(self, symbol: Symbol | None = None) -> list[Order]:
        """
        Get all open orders.

        Args:
            symbol: Filter by symbol, or None for all

        Returns:
            List of open orders
        """
        pass

    async def get_order_history(
        self,
        symbol: Symbol | None = None,
        since: datetime | None = None,
        limit: int = 100
    ) -> list[Order]:
        """
        Get order history.

        Args:
            symbol: Filter by symbol
            since: Start time
            limit: Maximum orders to return

        Returns:
            List of historical orders
        """
        # Optional implementation
        return []

    async def get_trade_history(
        self,
        symbol: Symbol | None = None,
        since: datetime | None = None,
        limit: int = 100
    ) -> list[Trade]:
        """
        Get personal trade history.

        Args:
            symbol: Filter by symbol
            since: Start time
            limit: Maximum trades to return

        Returns:
            List of trades
        """
        # Optional implementation
        return []

    # -------------------------------------------------------------------------
    # Position Management (for margin/futures)
    # -------------------------------------------------------------------------

    async def get_positions(self, symbol: Symbol | None = None) -> list[Position]:
        """
        Get open positions (for margin/futures exchanges).

        Args:
            symbol: Filter by symbol

        Returns:
            List of positions
        """
        # Default implementation returns empty list (for spot exchanges)
        return []

    async def close_position(self, symbol: Symbol) -> Position | None:
        """
        Close a position (for margin/futures exchanges).

        Args:
            symbol: Position symbol to close

        Returns:
            Closed position information
        """
        raise NotImplementedError("Position closing not supported")

    # -------------------------------------------------------------------------
    # WebSocket Streaming
    # -------------------------------------------------------------------------

    async def subscribe_ticker(self, symbol: Symbol, handler: Callable[[Ticker], None]) -> bool:
        """
        Subscribe to real-time ticker updates.

        Args:
            symbol: Trading pair to subscribe to
            handler: Callback function for ticker updates

        Returns:
            True if subscription successful
        """
        logger.warning(f"[{self.exchange_id}] WebSocket ticker not implemented")
        return False

    async def subscribe_orderbook(
        self,
        symbol: Symbol,
        handler: Callable[[Symbol, list, list], None]
    ) -> bool:
        """
        Subscribe to real-time order book updates.

        Args:
            symbol: Trading pair to subscribe to
            handler: Callback function for orderbook updates

        Returns:
            True if subscription successful
        """
        logger.warning(f"[{self.exchange_id}] WebSocket orderbook not implemented")
        return False

    async def subscribe_trades(self, symbol: Symbol, handler: Callable[[Trade], None]) -> bool:
        """
        Subscribe to real-time trade updates.

        Args:
            symbol: Trading pair to subscribe to
            handler: Callback function for trade updates

        Returns:
            True if subscription successful
        """
        logger.warning(f"[{self.exchange_id}] WebSocket trades not implemented")
        return False

    async def subscribe_orders(self, handler: Callable[[Order], None]) -> bool:
        """
        Subscribe to order updates.

        Args:
            handler: Callback function for order updates

        Returns:
            True if subscription successful
        """
        logger.warning(f"[{self.exchange_id}] WebSocket orders not implemented")
        return False

    async def unsubscribe_all(self) -> None:
        """Unsubscribe from all WebSocket channels."""
        pass

    # -------------------------------------------------------------------------
    # Exchange Information
    # -------------------------------------------------------------------------

    @abstractmethod
    def get_capabilities(self) -> ExchangeCapabilities:
        """Get exchange capabilities and features."""
        pass

    def supports_feature(self, feature: str) -> bool:
        """Check if exchange supports a specific feature."""
        caps = self.get_capabilities()
        return getattr(caps, f"supports_{feature}", False)

    async def get_trading_fees(self, symbol: Symbol | None = None) -> dict[str, Decimal]:
        """
        Get trading fees.

        Args:
            symbol: Specific symbol or None for general fees

        Returns:
            Dictionary with 'maker' and 'taker' fees
        """
        caps = self.get_capabilities()
        return {
            "maker": caps.fee_maker,
            "taker": caps.fee_taker
        }

    async def get_symbol_info(self, symbol: Symbol) -> dict[str, Any]:
        """
        Get trading symbol information.

        Args:
            symbol: Trading pair

        Returns:
            Symbol information dictionary
        """
        return {
            "symbol": str(symbol),
            "min_amount": Decimal("0"),
            "max_amount": None,
            "amount_precision": 8,
            "price_precision": 2,
        }

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------

    def format_symbol(self, symbol: Symbol) -> str:
        """
        Format symbol for this exchange.

        Override in subclass for exchange-specific formatting.
        """
        return str(symbol)

    def parse_symbol(self, symbol_str: str) -> Symbol:
        """Parse exchange-specific symbol string."""
        return Symbol.from_string(symbol_str)

    def _log_request(self, method: str, params: dict | None = None) -> None:
        """Log API request (for rate limiting/debugging)."""
        self._last_request_time = datetime.utcnow()
        self._request_count += 1

        if params:
            logger.debug(f"[{self.exchange_id}] {method}: {params}")
        else:
            logger.debug(f"[{self.exchange_id}] {method}")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.exchange_id}, connected={self._connected})"


# =============================================================================
# Exception Classes
# =============================================================================

class ExchangeError(Exception):
    """Base exception for exchange errors."""
    pass


class AuthenticationError(ExchangeError):
    """Authentication failed."""
    pass


class InsufficientFundsError(ExchangeError):
    """Not enough balance for operation."""
    pass


class OrderNotFoundError(ExchangeError):
    """Order not found."""
    pass


class InvalidOrderError(ExchangeError):
    """Invalid order parameters."""
    pass


class RateLimitError(ExchangeError):
    """Rate limit exceeded."""
    pass


class NetworkError(ExchangeError):
    """Network connection error."""
    pass


class ExchangeNotAvailableError(ExchangeError):
    """Exchange API not available."""
    pass
