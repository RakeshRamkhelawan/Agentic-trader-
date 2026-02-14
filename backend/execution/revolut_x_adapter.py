"""
Revolut X Exchange Adapter
Wraps RevolutXClient for integration with OrderExecutor
"""

import logging
from typing import Optional
from datetime import datetime

from backend.integrations.revolut_x_client import (
    RevolutXClient,
    OrderSide as RevolutOrderSide,
    OrderType as RevolutOrderType,
    Order as RevolutOrder,
)
from backend.core.schemas.ooda_types import Order

logger = logging.getLogger(__name__)


class RevolutXAdapter:
    """
    Revolut X exchange adapter for OrderExecutor integration.

    Bridges OODA Order schema with Revolut X API.
    """

    def __init__(
        self, api_key: Optional[str] = None, private_key_path: Optional[str] = None
    ):
        """
        Initialize Revolut X adapter.

        Args:
            api_key: Revolut X API key (or from env)
            private_key_path: Path to Ed25519 private key
        """
        self.client = RevolutXClient(api_key=api_key, private_key_path=private_key_path)
        self._connected = False
        logger.info("✅ RevolutXAdapter initialized")

    async def connect(self) -> bool:
        """
        Connect to Revolut X API.

        Returns:
            True if connected successfully
        """
        if self._connected:
            return True

        self._connected = await self.client.connect()
        return self._connected

    async def disconnect(self):
        """Disconnect from Revolut X API"""
        await self.client.disconnect()
        self._connected = False

    def _map_side(self, side: str) -> RevolutOrderSide:
        """Map OODA side to Revolut X OrderSide"""
        side_lower = side.lower()
        if side_lower == "buy":
            return RevolutOrderSide.BUY
        elif side_lower == "sell":
            return RevolutOrderSide.SELL
        else:
            raise ValueError(f"Invalid order side: {side}")

    def _map_order_type(self, order_type: str) -> RevolutOrderType:
        """Map OODA order type to Revolut X OrderType"""
        type_lower = order_type.lower()
        if type_lower == "market":
            return RevolutOrderType.MARKET
        elif type_lower == "limit":
            return RevolutOrderType.LIMIT
        else:
            raise ValueError(f"Invalid order type: {order_type}")

    def _map_symbol(self, symbol: str) -> str:
        """
        Map OODA symbol to Revolut X format.

        OODA uses: BTC/USDT, ETH/USDT
        Revolut X uses: BTC-USD, ETH-USD
        """
        # Replace / with -
        revolut_symbol = symbol.replace("/", "-")

        # Replace USDT with USD (Revolut X uses USD)
        revolut_symbol = revolut_symbol.replace("USDT", "USD")

        return revolut_symbol

    def _revolut_to_ooda_order(self, revolut_order: RevolutOrder) -> Order:
        """Convert Revolut X Order to OODA Order schema"""
        return Order(
            order_id=revolut_order.id,
            symbol=revolut_order.symbol.replace("-", "/"),  # BTC-USD -> BTC/USD
            side=revolut_order.side,
            order_type=revolut_order.type,
            quantity=float(revolut_order.quantity),
            price=float(revolut_order.price) if revolut_order.price else None,
            status=self._map_status(revolut_order.status),
            filled_quantity=float(revolut_order.filled_quantity),
            avg_fill_price=float(revolut_order.price) if revolut_order.price else None,
        )

    def _map_status(self, revolut_status: str) -> str:
        """
        Map Revolut X status to OODA status.

        Revolut X: new, open, filled, cancelled, rejected
        OODA: pending, open, filled, cancelled, rejected
        """
        status_map = {
            "new": "pending",
            "open": "open",
            "filled": "filled",
            "cancelled": "cancelled",
            "rejected": "rejected",
        }
        return status_map.get(revolut_status, revolut_status)

    async def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
    ) -> Order:
        """
        Place order on Revolut X.

        Args:
            symbol: Trading pair (OODA format: BTC/USDT)
            side: "buy" or "sell"
            order_type: "market" or "limit"
            quantity: Order quantity
            price: Limit price (required for limit orders)

        Returns:
            OODA Order object
        """
        if not self._connected:
            await self.connect()

        # Map parameters
        revolut_symbol = self._map_symbol(symbol)
        revolut_side = self._map_side(side)
        revolut_type = self._map_order_type(order_type)

        logger.info(
            f"📤 Placing {order_type} {side} order on Revolut X: "
            f"{quantity} {revolut_symbol} @ {price or 'market'}"
        )

        # Place order on Revolut X
        revolut_order = await self.client.place_order(
            symbol=revolut_symbol,
            side=revolut_side,
            quantity=str(quantity),
            price=str(price) if price else None,
            order_type=revolut_type,
            execution_instructions=["post_only"] if order_type == "limit" else None,
        )

        if not revolut_order:
            raise RuntimeError(f"Failed to place order on Revolut X")

        # Convert to OODA Order
        ooda_order = self._revolut_to_ooda_order(revolut_order)

        logger.info(
            f"✅ Order placed on Revolut X: {ooda_order.order_id} "
            f"(status: {ooda_order.status})"
        )

        return ooda_order

    async def get_order_status(self, order_id: str) -> Order:
        """
        Get order status from Revolut X.

        Args:
            order_id: Revolut X order ID

        Returns:
            Updated OODA Order object
        """
        if not self._connected:
            await self.connect()

        # Get active orders and find the requested one
        active_orders = await self.client.get_active_orders()

        for revolut_order in active_orders:
            if revolut_order.id == order_id:
                return self._revolut_to_ooda_order(revolut_order)

        # If not in active orders, it might be filled or cancelled
        # For now, return a "filled" status (should query historical orders)
        logger.warning(f"Order {order_id} not found in active orders, assuming filled")

        return Order(
            order_id=order_id,
            symbol="BTC/USD",
            side="buy",
            order_type="limit",
            quantity=0.0,
            status="filled",
            filled_quantity=0.0,
            avg_fill_price=0.0,
        )

    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancel order on Revolut X.

        Args:
            order_id: Revolut X order ID

        Returns:
            True if cancelled successfully
        """
        if not self._connected:
            await self.connect()

        logger.info(f"🚫 Cancelling order on Revolut X: {order_id}")

        success = await self.client.cancel_order(order_id)

        if success:
            logger.info(f"✅ Order cancelled: {order_id}")
        else:
            logger.error(f"❌ Failed to cancel order: {order_id}")

        return success

    async def get_balance(self, currency: str = "USD") -> float:
        """
        Get account balance for currency.

        Args:
            currency: Currency code (e.g., "USD", "BTC")

        Returns:
            Available balance
        """
        if not self._connected:
            await self.connect()

        # Not implemented yet - would need account balance endpoint
        logger.warning("get_balance() not yet implemented for Revolut X")
        return 0.0

    # ========================================================================
    # MARKET DATA METHODS (for DataScout integration)
    # ========================================================================

    async def fetch_ticker(self, symbol: str) -> dict:
        """
        Fetch ticker data for DataScout.

        Args:
            symbol: OODA format symbol (e.g., 'BTC/USDT')

        Returns:
            Dict with: last, volume, bid, ask, timestamp
        """
        if not self._connected:
            await self.connect()

        # Map OODA symbol to Revolut X format
        revolut_symbol = self._map_symbol(symbol)

        logger.info(f"[DATA] Fetching ticker for {symbol} -> {revolut_symbol}")

        ticker = await self.client.get_ticker(revolut_symbol)

        logger.info(
            f"[DATA] {symbol}: ${ticker['last']:,.2f}, "
            f"Volume: {ticker['volume']:,.0f}, "
            f"Spread: ${ticker['ask'] - ticker['bid']:.2f}"
        )

        return ticker

    async def fetch_orderbook(self, symbol: str, limit: int = 10) -> dict:
        """
        Fetch orderbook snapshot for DataScout.

        Args:
            symbol: OODA format symbol (e.g., 'BTC/USDT')
            limit: Number of levels per side

        Returns:
            Dict with: bids, asks
        """
        if not self._connected:
            await self.connect()

        revolut_symbol = self._map_symbol(symbol)

        logger.debug(f"[DATA] Fetching orderbook for {symbol} -> {revolut_symbol}")

        orderbook = await self.client.get_orderbook(revolut_symbol, depth=limit)

        return orderbook

    async def fetch_funding_rate(self, symbol: str) -> float:
        """
        Fetch funding rate (not available on Revolut X spot market).

        Args:
            symbol: OODA format symbol

        Returns:
            0.0 (spot market has no funding)
        """
        # Revolut X only has spot trading, no perpetual futures
        logger.debug(f"[DATA] Funding rate not available for spot market: {symbol}")
        return 0.0
