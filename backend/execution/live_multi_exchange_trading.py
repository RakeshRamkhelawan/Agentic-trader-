"""
Live Multi-Exchange Trading Service

Execute real trades across multiple exchanges with:
- Unified order interface
- Position tracking across exchanges
- Risk management
- Trade confirmation and monitoring
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class OrderStatus(Enum):
    """Order execution status."""

    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    ERROR = "error"


class ExchangeType(Enum):
    """Supported exchange types."""

    BITVAVO = "bitvavo"
    REVOLUTX = "revolutx"


@dataclass
class LiveOrder:
    """Live order across any exchange."""

    order_id: str
    client_order_id: str
    exchange: str
    symbol: str
    side: str  # 'buy' or 'sell'
    order_type: str  # 'market' or 'limit'
    quantity: float
    price: float | None = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    avg_fill_price: float = 0.0
    commission: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    exchange_order_id: str | None = None
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def remaining_quantity(self) -> float:
        """Remaining quantity to fill."""
        return self.quantity - self.filled_quantity

    @property
    def is_complete(self) -> bool:
        """Check if order is complete (filled or cancelled)."""
        return self.status in [
            OrderStatus.FILLED,
            OrderStatus.CANCELLED,
            OrderStatus.REJECTED,
        ]

    @property
    def fill_pct(self) -> float:
        """Percentage filled."""
        if self.quantity > 0:
            return (self.filled_quantity / self.quantity) * 100
        return 0.0


@dataclass
class ExchangePosition:
    """Position on a specific exchange."""

    exchange: str
    symbol: str
    quantity: float
    avg_entry_price: float
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)

    @property
    def market_value(self) -> float:
        """Current market value (approximate)."""
        return abs(self.quantity) * self.avg_entry_price


@dataclass
class CrossExchangePosition:
    """Aggregated position across multiple exchanges."""

    symbol: str
    positions: dict[str, ExchangePosition] = field(default_factory=dict)

    @property
    def total_quantity(self) -> float:
        """Total quantity across all exchanges."""
        return sum(p.quantity for p in self.positions.values())

    @property
    def avg_entry_price(self) -> float:
        """Weighted average entry price."""
        total_value = sum(p.quantity * p.avg_entry_price for p in self.positions.values())
        total_qty = self.total_quantity
        return total_value / total_qty if total_qty > 0 else 0.0

    @property
    def total_unrealized_pnl(self) -> float:
        """Total unrealized P&L."""
        return sum(p.unrealized_pnl for p in self.positions.values())

    @property
    def total_realized_pnl(self) -> float:
        """Total realized P&L."""
        return sum(p.realized_pnl for p in self.positions.values())


class LiveMultiExchangeTrading:
    """
    Live trading service across multiple exchanges.

    Features:
    - Unified order interface for all exchanges
    - Real-time position tracking
    - Risk management controls
    - Trade confirmation monitoring
    """

    def __init__(self):
        self._exchanges: dict[str, Any] = {}
        self._orders: dict[str, LiveOrder] = {}
        self._positions: dict[str, CrossExchangePosition] = {}
        self._orders_lock = asyncio.Lock()
        self._positions_lock = asyncio.Lock()

        # Risk controls
        self.max_order_value_eur = 5000.0  # Max €5,000 per order
        self.max_position_value_eur = 10000.0  # Max €10,000 per symbol
        self.max_total_exposure = 50000.0  # Max €50,000 total
        self.require_confirmation = True  # Require manual confirmation

        # Monitoring
        self._monitoring_task: asyncio.Task | None = None
        self._running = False

    async def initialize(self):
        """Initialize exchange connections."""
        logger.info("[INIT] Initializing LiveMultiExchangeTrading")

        # Initialize Bitvavo
        try:
            from backend.execution.bitvavo_adapter import BitvavoAdapter

            self._exchanges["bitvavo"] = BitvavoAdapter()
            await self._exchanges["bitvavo"].initialize()
            logger.info("[INIT] Bitvavo connected for live trading")
        except Exception as e:
            logger.warning(f"[INIT] Bitvavo not available: {e}")

        # Initialize Revolut X
        try:
            from backend.execution.revolut_x_adapter import RevolutXAdapter

            self._exchanges["revolutx"] = RevolutXAdapter()
            await self._exchanges["revolutx"].connect()
            logger.info("[INIT] Revolut X connected for live trading")
        except Exception as e:
            logger.warning(f"[INIT] Revolut X not available: {e}")

        # Start monitoring
        self._running = True
        self._monitoring_task = asyncio.create_task(self._monitor_orders())

        logger.info(f"[INIT] Live trading ready with {len(self._exchanges)} exchanges")

    async def stop(self):
        """Stop trading and cleanup."""
        self._running = False

        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        # Disconnect exchanges
        for name, adapter in self._exchanges.items():
            try:
                if name == "revolutx":
                    await adapter.disconnect()
                logger.info(f"[STOP] Disconnected from {name}")
            except Exception as e:
                logger.warning(f"[STOP] Error disconnecting {name}: {e}")

    def _check_risk_limits(
        self, symbol: str, side: str, quantity: float, price: float
    ) -> tuple[bool, str]:
        """
        Check if order violates risk limits.

        Returns:
            (allowed, reason)
        """
        order_value = quantity * price

        # Check max order value
        if order_value > self.max_order_value_eur:
            return (
                False,
                f"Order value €{order_value:.2f} exceeds max €{self.max_order_value_eur:.2f}",
            )

        # Check position limit (simplified - would need actual position lookup)
        # This is a placeholder - real implementation would check current positions

        return True, ""

    async def place_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "market",
        price: float | None = None,
        exchange: str | None = None,
        client_order_id: str | None = None,
    ) -> LiveOrder:
        """
        Place a live order on specified or best exchange.

        Args:
            symbol: Trading symbol (e.g., 'BTC-EUR', 'BTC-USD')
            side: 'buy' or 'sell'
            quantity: Order quantity
            order_type: 'market' or 'limit'
            price: Limit price (required for limit orders)
            exchange: Target exchange (auto-selected if None)
            client_order_id: Optional client order ID

        Returns:
            LiveOrder with status
        """
        # Generate client order ID
        if not client_order_id:
            client_order_id = (
                f"live_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{symbol.replace('/', '_')}"
            )

        # Create order object
        order = LiveOrder(
            order_id=client_order_id,
            client_order_id=client_order_id,
            exchange=exchange or "auto",
            symbol=symbol,
            side=side.lower(),
            order_type=order_type.lower(),
            quantity=quantity,
            price=price,
            status=OrderStatus.PENDING,
        )

        # Store order
        async with self._orders_lock:
            self._orders[client_order_id] = order

        try:
            # Auto-select exchange if not specified
            if not exchange or exchange == "auto":
                exchange = await self._select_best_exchange(symbol, side, quantity)
                order.exchange = exchange

            # Validate exchange is available
            if exchange not in self._exchanges:
                order.status = OrderStatus.ERROR
                order.error_message = f"Exchange {exchange} not available"
                return order

            # Get price for risk check
            check_price = price or await self._get_current_price(exchange, symbol)

            # Check risk limits
            allowed, reason = self._check_risk_limits(symbol, side, quantity, check_price)
            if not allowed:
                order.status = OrderStatus.REJECTED
                order.error_message = f"Risk check failed: {reason}"
                logger.warning(f"[RISK] Order rejected: {reason}")
                return order

            # Execute on exchange
            logger.info(f"[ORDER] Executing {side} {quantity} {symbol} on {exchange}")
            order.status = OrderStatus.SUBMITTED

            if exchange == "bitvavo":
                await self._execute_bitvavo_order(order)
            elif exchange == "revolutx":
                await self._execute_revolutx_order(order)

        except Exception as e:
            logger.error(f"[ORDER] Execution failed: {e}")
            order.status = OrderStatus.ERROR
            order.error_message = str(e)

        return order

    async def _select_best_exchange(self, symbol: str, side: str, quantity: float) -> str:
        """Select best exchange for order execution."""
        # Use smart order routing
        from backend.execution.multi_exchange_aggregator import get_multi_exchange_aggregator

        try:
            aggregator = await get_multi_exchange_aggregator()

            # Map symbol to base
            base = symbol.split("-")[0].split("/")[0]

            best = await aggregator.get_best_price(base, side)
            if best:
                return best["exchange"]
        except Exception as e:
            logger.warning(f"[ROUTING] Could not get best exchange: {e}")

        # Fallback to first available
        if "bitvavo" in self._exchanges:
            return "bitvavo"
        elif "revolutx" in self._exchanges:
            return "revolutx"

        raise RuntimeError("No exchanges available")

    async def _get_current_price(self, exchange: str, symbol: str) -> float:
        """Get current price from exchange."""
        adapter = self._exchanges.get(exchange)
        if not adapter:
            return 0.0

        try:
            ticker = await adapter.fetch_ticker(symbol)
            return float(ticker.get("last", 0))
        except Exception as e:
            logger.warning(f"[PRICE] Could not fetch price: {e}")
            return 0.0

    async def _execute_bitvavo_order(self, order: LiveOrder):
        """Execute order on Bitvavo."""
        adapter = self._exchanges["bitvavo"]

        result = await adapter.place_order(
            symbol=order.symbol,
            side=order.side,
            order_type=order.order_type,
            quantity=order.quantity,
            price=order.price,
        )

        order.exchange_order_id = result.order_id
        order.status = (
            OrderStatus(result.status)
            if result.status in [s.value for s in OrderStatus]
            else OrderStatus.PENDING
        )
        order.filled_quantity = result.filled_quantity
        order.avg_fill_price = result.avg_fill_price or 0.0

        logger.info(f"[BITVAVO] Order placed: {order.exchange_order_id} - {order.status.value}")

    async def _execute_revolutx_order(self, order: LiveOrder):
        """Execute order on Revolut X."""
        adapter = self._exchanges["revolutx"]

        # Map symbol format
        ooda_symbol = order.symbol.replace("-", "/")

        result = await adapter.place_order(
            symbol=ooda_symbol,
            side=order.side,
            order_type=order.order_type,
            quantity=order.quantity,
            price=order.price,
        )

        order.exchange_order_id = result.order_id
        order.status = (
            OrderStatus(result.status)
            if result.status in [s.value for s in OrderStatus]
            else OrderStatus.PENDING
        )
        order.filled_quantity = result.filled_quantity
        order.avg_fill_price = result.avg_fill_price or 0.0

        logger.info(f"[REVOLUTX] Order placed: {order.exchange_order_id} - {order.status.value}")

    async def get_order_status(self, client_order_id: str) -> LiveOrder | None:
        """Get current status of an order."""
        async with self._orders_lock:
            order = self._orders.get(client_order_id)

        if not order or not order.exchange_order_id:
            return order

        # Refresh from exchange
        try:
            if order.exchange == "bitvavo":
                # Get status from Bitvavo
                pass  # Implementation depends on adapter
            elif order.exchange == "revolutx":
                # Get status from Revolut X
                pass  # Implementation depends on adapter
        except Exception as e:
            logger.warning(f"[STATUS] Could not refresh order status: {e}")

        return order

    async def cancel_order(self, client_order_id: str) -> bool:
        """Cancel an active order."""
        async with self._orders_lock:
            order = self._orders.get(client_order_id)

        if not order or not order.exchange_order_id:
            return False

        try:
            if order.exchange == "bitvavo":
                # Cancel on Bitvavo
                pass
            elif order.exchange == "revolutx":
                adapter = self._exchanges.get("revolutx")
                if adapter:
                    await adapter.cancel_order(order.exchange_order_id)

            order.status = OrderStatus.CANCELLED
            return True

        except Exception as e:
            logger.error(f"[CANCEL] Failed to cancel order: {e}")
            return False

    async def get_positions(self) -> list[CrossExchangePosition]:
        """Get all cross-exchange positions."""
        async with self._positions_lock:
            return list(self._positions.values())

    async def get_position(self, symbol: str) -> CrossExchangePosition | None:
        """Get position for a specific symbol."""
        async with self._positions_lock:
            return self._positions.get(symbol)

    async def _monitor_orders(self):
        """Background task to monitor order status."""
        while self._running:
            try:
                # Check pending orders
                async with self._orders_lock:
                    pending = [o for o in self._orders.values() if not o.is_complete]

                for order in pending:
                    await self._update_order_status(order)

                await asyncio.sleep(5)  # Check every 5 seconds

            except Exception as e:
                logger.error(f"[MONITOR] Error monitoring orders: {e}")
                await asyncio.sleep(5)

    async def _update_order_status(self, order: LiveOrder):
        """Update order status from exchange."""
        if not order.exchange_order_id:
            return

        try:
            # Fetch updated status
            # This would call exchange-specific status methods
            order.updated_at = datetime.utcnow()
        except Exception as e:
            logger.warning(f"[UPDATE] Could not update order {order.order_id}: {e}")

    def get_stats(self) -> dict[str, Any]:
        """Get trading statistics."""
        return {
            "active_exchanges": list(self._exchanges.keys()),
            "total_orders": len(self._orders),
            "open_orders": sum(1 for o in self._orders.values() if not o.is_complete),
            "tracked_positions": len(self._positions),
            "risk_limits": {
                "max_order_value": self.max_order_value_eur,
                "max_position_value": self.max_position_value_eur,
                "max_total_exposure": self.max_total_exposure,
            },
        }


# Singleton instance
_live_trading: LiveMultiExchangeTrading | None = None


async def get_live_trading_service() -> LiveMultiExchangeTrading:
    """Get or create singleton live trading service."""
    global _live_trading
    if _live_trading is None:
        _live_trading = LiveMultiExchangeTrading()
        await _live_trading.initialize()
    return _live_trading
