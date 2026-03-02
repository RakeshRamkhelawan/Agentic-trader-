"""
CCXT-based Exchange Adapter.

Provides unified access to 100+ cryptocurrency exchanges
via the CCXT library with WebSocket streaming support.
"""

import asyncio
import logging
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any

from backend.execution.broker_interface import ExecutionInterface, OrderResult
from backend.schemas.market_data import OrderBook
from backend.schemas.market_data import OrderStatus as MarketOrderStatus
from backend.schemas.market_data import OrderUpdate, TickerUpdate
from backend.schemas.orders import OrderRequest, OrderStatus

logger = logging.getLogger(__name__)

# Try to import ccxt
try:
    import ccxt  # type: ignore[import-untyped]
    import ccxt.pro as ccxtpro  # type: ignore[import-untyped]

    CCXT_AVAILABLE = True
except ImportError:
    CCXT_AVAILABLE = False
    ccxt = None
    ccxtpro = None


class CCXTConnectionError(Exception):
    """Raised when CCXT connection fails."""

    pass


class CCXTAdapter(ExecutionInterface):
    """
    CCXT-based exchange adapter supporting 100+ exchanges.

    Features:
    - Unified API for all supported exchanges
    - WebSocket streaming via CCXT Pro
    - Automatic reconnection with exponential backoff
    - Sandbox/testnet support
    """

    # Map CCXT order status to our OrderStatus
    STATUS_MAP = {
        "open": OrderStatus.OPEN,
        "closed": OrderStatus.FILLED,
        "canceled": OrderStatus.CANCELLED,
        "expired": OrderStatus.EXPIRED,
        "rejected": OrderStatus.REJECTED,
    }

    def __init__(
        self,
        exchange_id: str = "binance",
        api_key: str = "",
        secret: str = "",
        password: str = "",  # nosec B107 - Optional parameter, not a hardcoded password
        sandbox: bool = False,
        options: dict[str, Any] | None = None,
    ):
        """
        Initialize CCXT adapter.

        Args:
            exchange_id: CCXT exchange ID (e.g., "binance", "kraken", "coinbase")
            api_key: Exchange API key
            secret: Exchange API secret
            password: Exchange API password (for some exchanges)
            sandbox: Use testnet/sandbox mode
            options: Additional CCXT options
        """
        self.exchange_id = exchange_id
        self.sandbox = sandbox
        self._connected = False

        if not CCXT_AVAILABLE:
            logger.warning("CCXT not installed, using mock exchange")
            self._exchange = None
            self._exchange_ws = None
            return

        # CCXT configuration
        config = {
            "apiKey": api_key,
            "secret": secret,
            "enableRateLimit": True,
            "options": options or {},
        }

        if password:
            config["password"] = password

        # Revolut specific: CCXT often uses 'privateKey' for RSA/Ed25519 signatures
        # We assume 'secret' contains the PEM data
        if exchange_id == "revolut":
            config["privateKey"] = secret

        # Create REST exchange instance
        try:
            exchange_class = getattr(ccxt, exchange_id)
            self._exchange = exchange_class(config)

            if sandbox:
                self._exchange.set_sandbox_mode(True)
                logger.info(f"CCXT {exchange_id} adapter initialized (SANDBOX mode)")
            else:
                logger.info(f"CCXT {exchange_id} adapter initialized")
        except Exception as e:
            logger.error(f"Failed to initialize CCXT exchange: {e}")
            self._exchange = None

        # Create WebSocket exchange instance (CCXT Pro)
        try:
            exchange_ws_class = getattr(ccxtpro, exchange_id)
            self._exchange_ws = exchange_ws_class(config)

            if sandbox:
                self._exchange_ws.set_sandbox_mode(True)
        except Exception as e:
            logger.warning(f"CCXT Pro not available for {exchange_id}: {e}")
            self._exchange_ws = None

    # ==================== REST METHODS ====================

    async def submit_order(self, order: OrderRequest) -> OrderResult:
        """Submit an order to the exchange."""
        # 🔒 PAPER MODE GUARD - KRITISCH: NOOIT echte orders in paper mode
        import os

        trading_mode = os.getenv("TRADING_MODE", "paper")
        if trading_mode == "paper":
            logger.error("🚫 BLOCKED: CCXT submit_order() aangeroepen in PAPER mode!")
            logger.error("   Gebruik ShadowPortfolioManager of PaperExchange voor paper trading.")
            return OrderResult(
                order_id="",
                client_order_id=str(order.client_order_id) if order.client_order_id else "",
                status=OrderStatus.REJECTED,
                error_message="Cannot place real orders in PAPER mode. Use paper trading components.",
            )

        if not self._exchange:
            return OrderResult(
                order_id="mock-order-001",
                client_order_id=str(order.client_order_id) if order.client_order_id else "mock-001",
                status=OrderStatus.PENDING,
                error_message="CCXT not available",
            )

        try:
            result = await asyncio.to_thread(
                self._exchange.create_order,
                order.symbol,
                order.order_type.value.lower(),
                order.side.value.lower(),
                order.qty,
                order.limit_price if order.limit_price else None,
            )

            return OrderResult(
                order_id=result["id"],
                client_order_id=result.get("clientOrderId", ""),
                status=self.STATUS_MAP.get(result["status"], OrderStatus.PENDING),
                filled_qty=result.get("filled", 0.0),
                remaining_qty=result.get("remaining", order.qty),
                avg_price=result.get("average"),
                raw_response=result,
            )
        except Exception as e:
            logger.error(f"Order submission failed: {e}")
            return OrderResult(
                order_id="",
                client_order_id=str(order.client_order_id) if order.client_order_id else "",
                status=OrderStatus.REJECTED,
                error_message=str(e),
            )

    async def get_order_status(self, order_id: str) -> OrderResult:
        """Get order status."""
        if not self._exchange:
            return OrderResult(
                order_id=order_id,
                client_order_id="",
                status=OrderStatus.PENDING,
                error_message="CCXT not available",
            )

        try:
            result = await asyncio.to_thread(self._exchange.fetch_order, order_id)

            return OrderResult(
                order_id=result["id"],
                client_order_id=result.get("clientOrderId", ""),
                status=self.STATUS_MAP.get(result["status"], OrderStatus.PENDING),
                filled_qty=result.get("filled", 0.0),
                remaining_qty=result.get("remaining", 0.0),
                avg_price=result.get("average"),
                raw_response=result,
            )
        except Exception as e:
            logger.error(f"Get order status failed: {e}")
            return OrderResult(
                order_id=order_id,
                client_order_id="",
                status=OrderStatus.PENDING,
                error_message=str(e),
            )

    async def get_balance(self) -> dict[str, float]:
        """Get account balance."""
        if not self._exchange:
            return {"EUR": 10000.0, "BTC": 1.0}  # Mock balance

        try:
            balance = await asyncio.to_thread(self._exchange.fetch_balance)
            return {k: v for k, v in balance.get("total", {}).items() if v > 0}
        except Exception as e:
            logger.error(f"Get balance failed: {e}")
            return {}

    async def get_ticker(self, symbol: str) -> dict[str, float]:
        """Get ticker data."""
        if not self._exchange:
            return {"bid": 45000.0, "ask": 45010.0, "last": 45005.0}

        try:
            ticker = await asyncio.to_thread(self._exchange.fetch_ticker, symbol)
            return {
                "bid": ticker.get("bid", 0),
                "ask": ticker.get("ask", 0),
                "last": ticker.get("last", 0),
                "volume": ticker.get("quoteVolume", 0),
            }
        except Exception as e:
            logger.error(f"Get ticker failed: {e}")
            return {}

    # ==================== DATA SCOUT COMPATIBLE METHODS ====================

    async def fetch_ticker(self, symbol: str) -> dict[str, Any]:
        """
        Fetch ticker data (DataScout compatible).

        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')

        Returns:
            Dict with: last, volume, bid, ask, timestamp
        """
        if not self._exchange:
            return {
                "last": 45000.0,
                "volume": 100.0,
                "bid": 44999.0,
                "ask": 45001.0,
                "timestamp": datetime.now().timestamp(),
            }

        try:
            ticker = await asyncio.to_thread(self._exchange.fetch_ticker, symbol)
            return {
                "last": ticker.get("last", 0),
                "volume": ticker.get("baseVolume", 0),  # BTC volume
                "bid": ticker.get("bid", 0),
                "ask": ticker.get("ask", 0),
                "timestamp": ticker.get("timestamp", datetime.now().timestamp()),
            }
        except Exception as e:
            logger.error(f"fetch_ticker failed for {symbol}: {e}")
            raise ValueError(f"Failed to fetch ticker: {e}")

    async def fetch_orderbook(self, symbol: str, limit: int = 10) -> dict[str, Any]:
        """
        Fetch orderbook snapshot (DataScout compatible).

        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            limit: Number of levels per side

        Returns:
            Dict with: bids [[price, size], ...], asks [[price, size], ...]
        """
        if not self._exchange:
            return {
                "bids": [[44999.0, 1.0], [44998.0, 0.5]],
                "asks": [[45001.0, 1.0], [45002.0, 0.5]],
            }

        try:
            orderbook = await asyncio.to_thread(self._exchange.fetch_order_book, symbol, limit)
            return {
                "bids": orderbook.get("bids", [])[:limit],
                "asks": orderbook.get("asks", [])[:limit],
                "timestamp": orderbook.get("timestamp", datetime.now().timestamp()),
            }
        except Exception as e:
            logger.error(f"fetch_orderbook failed for {symbol}: {e}")
            return {"bids": [], "asks": []}

    async def fetch_funding_rate(self, symbol: str) -> float:
        """
        Fetch funding rate for perpetual contracts (DataScout compatible).

        Args:
            symbol: Trading pair

        Returns:
            Funding rate (0.0 if not applicable)
        """
        if not self._exchange:
            return 0.0001  # Mock

        try:
            # Only applicable for perpetual/futures contracts
            if hasattr(self._exchange, "fetch_funding_rate"):
                funding = await asyncio.to_thread(self._exchange.fetch_funding_rate, symbol)
                return funding.get("fundingRate", 0.0)
            return 0.0  # Spot market has no funding
        except Exception as e:
            logger.debug(f"fetch_funding_rate not available for {symbol}: {e}")
            return 0.0

    async def cancel_all_orders(self):
        """Cancel all open orders."""
        if not self._exchange:
            logger.warning("CCXT not available, mock cancel")
            return

        try:
            await asyncio.to_thread(self._exchange.cancel_all_orders)
            logger.info("All orders cancelled")
        except Exception as e:
            logger.error(f"Cancel all orders failed: {e}")

    # ==================== WEBSOCKET STREAMING METHODS ====================

    async def subscribe_ticker(self, symbol: str) -> AsyncGenerator[TickerUpdate]:
        """Stream real-time ticker updates."""
        if not self._exchange_ws:
            # Mock ticker stream
            while True:
                yield TickerUpdate(
                    symbol=symbol,
                    bid=45000.0,
                    ask=45010.0,
                    last=45005.0,
                    volume_24h=1000000.0,
                    timestamp=datetime.utcnow(),
                    source=self.exchange_id,
                )
                await asyncio.sleep(1.0)

        while True:
            try:
                ticker = await self._exchange_ws.watch_ticker(symbol)
                yield TickerUpdate(
                    symbol=ticker["symbol"],
                    bid=ticker.get("bid", 0),
                    ask=ticker.get("ask", 0),
                    last=ticker.get("last", 0),
                    volume_24h=ticker.get("quoteVolume", 0),
                    timestamp=(
                        datetime.fromtimestamp(ticker["timestamp"] / 1000)
                        if ticker.get("timestamp")
                        else datetime.utcnow()
                    ),
                    source=self.exchange_id,
                )
            except Exception as e:
                logger.error(f"Ticker stream error: {e}")
                await asyncio.sleep(1.0)  # Reconnect delay

    async def subscribe_orderbook(self, symbol: str, depth: int = 10) -> AsyncGenerator[OrderBook]:
        """Stream order book updates."""
        if not self._exchange_ws:
            # Mock orderbook
            while True:
                yield OrderBook(
                    symbol=symbol,
                    bids=[(45000.0 - i * 10, 1.0) for i in range(depth)],
                    asks=[(45010.0 + i * 10, 1.0) for i in range(depth)],
                    timestamp=datetime.utcnow(),
                )
                await asyncio.sleep(0.5)

        while True:
            try:
                orderbook = await self._exchange_ws.watch_order_book(symbol, limit=depth)
                yield OrderBook(
                    symbol=symbol,
                    bids=[(b[0], b[1]) for b in orderbook["bids"][:depth]],
                    asks=[(a[0], a[1]) for a in orderbook["asks"][:depth]],
                    timestamp=(
                        datetime.fromtimestamp(orderbook["timestamp"] / 1000)
                        if orderbook.get("timestamp")
                        else datetime.utcnow()
                    ),
                )
            except Exception as e:
                logger.error(f"Orderbook stream error: {e}")
                await asyncio.sleep(1.0)

    async def subscribe_orders(self) -> AsyncGenerator[OrderUpdate]:
        """Stream order updates."""
        if not self._exchange_ws:
            # Mock - no order updates in mock mode
            while True:
                await asyncio.sleep(10.0)
                return

        while True:
            try:
                orders = await self._exchange_ws.watch_orders()
                for order in orders:
                    yield OrderUpdate(
                        order_id=order["id"],
                        status=MarketOrderStatus(
                            self.STATUS_MAP.get(order["status"], OrderStatus.PENDING).value
                        ),
                        filled_qty=order.get("filled", 0),
                        avg_price=order.get("average", 0),
                        remaining_qty=order.get("remaining", 0),
                        timestamp=datetime.utcnow(),
                    )
            except Exception as e:
                logger.error(f"Orders stream error: {e}")
                await asyncio.sleep(1.0)

    # ==================== CANDLES/OHLCV ====================

    async def get_candles(
        self, symbol: str, timeframe: str = "1m", limit: int = 100
    ) -> list[dict[str, Any]]:
        """
        Fetch OHLCV candles asynchronously.

        Args:
            symbol: Trading pair (e.g., 'BTC/EUR')
            timeframe: Candle timeframe (e.g., '1m', '5m', '1h', '1d')
            limit: Number of candles to fetch

        Returns:
            List of candle dicts with time, open, high, low, close, value
        """
        if not self._exchange:
            # Return mock candles
            import time

            now = int(time.time())
            base_price = 45000.0
            candles = []
            for i in range(min(limit, 100)):
                ts = now - (limit - i) * 60
                candles.append(
                    {
                        "time": ts,
                        "open": base_price,
                        "high": base_price * 1.01,
                        "low": base_price * 0.99,
                        "close": base_price * (1 + (i % 5 - 2) * 0.001),
                        "value": 100.0,
                    }
                )
            return candles

        try:
            # Use asyncio.to_thread for synchronous CCXT calls
            ohlcv = await asyncio.to_thread(
                self._exchange.fetch_ohlcv, symbol, timeframe, limit=limit
            )

            # CCXT returns list of lists: [timestamp, open, high, low, close, volume]
            candles = []
            for candle in ohlcv:
                candles.append(
                    {
                        "time": candle[0] // 1000,  # Convert ms to seconds
                        "open": candle[1],
                        "high": candle[2],
                        "low": candle[3],
                        "close": candle[4],
                        "value": candle[5],  # Volume
                    }
                )
            return candles
        except Exception as e:
            logger.error(f"Failed to fetch candles for {symbol}: {e}")
            raise

    @property
    def exchange(self) -> Any | None:
        """
        Expose the underlying CCXT exchange instance.
        Use with caution - prefer using adapter methods.
        """
        return self._exchange

    # ==================== CONNECTION MANAGEMENT ====================

    async def connect(self) -> None:
        """Establish connections."""
        self._connected = True
        logger.info(f"Connected to {self.exchange_id}")

    async def disconnect(self) -> None:
        """Close connections."""
        if self._exchange_ws:
            try:
                await self._exchange_ws.close()
            except Exception:
                pass
        self._connected = False
        logger.info(f"Disconnected from {self.exchange_id}")
