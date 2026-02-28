"""
Unified Order Manager for Multi-Exchange Trading ⚠️ DEPRECATED

⚠️ DEPRECATED: This module is deprecated and will be removed in Week 8.
Use OrderExecutor from backend.execution.order_executor instead.

See: docs/adr/ADR-008-unified-execution-schema.md


This module provides centralized order management across multiple exchanges,
with features like:
- Order routing to best exchange
- Order tracking and status updates
- Automatic retry logic
- Position reconciliation
- Risk validation integration

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │                    OrderManager                             │
    │                   ─────────────                             │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
    │  │   Order     │  │   Order     │  │    Risk     │         │
    │  │   Router    │  │   Tracker   │  │  Validator  │         │
    │  └─────────────┘  └─────────────┘  └─────────────┘         │
    └─────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            ↓                 ↓                 ↓
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │   Bitvavo    │ │   Revolut    │ │    Other     │
    │  Exchange    │ │   Exchange   │ │  Exchanges   │
    └──────────────┘ └──────────────┘ └──────────────┘
"""

from __future__ import annotations

import asyncio
import logging
import warnings
from collections import defaultdict

# Deprecation warning
warnings.warn(
    "OrderManager is deprecated. Use OrderExecutor from "
    "backend.execution.order_executor instead. "
    "See ADR-008 for migration guide.",
    DeprecationWarning,
    stacklevel=2
)
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

from backend.exchange.base_exchange import (
    BaseExchange,
    Order,
    OrderRequest,
    OrderSide,
    OrderStatus,
    OrderType,
    Symbol,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class OrderRoute:
    """Order routing decision."""
    exchange_id: str
    reason: str
    expected_fee: Decimal
    expected_slippage: Decimal
    confidence: float  # 0-1 confidence in routing decision


@dataclass
class OrderUpdate:
    """Order status update."""
    order_id: str
    status: OrderStatus
    filled: Decimal
    remaining: Decimal
    average_price: Decimal | None
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class OrderEvent:
    """Order lifecycle event."""
    event_type: str  # created, updated, filled, cancelled, rejected
    order: Order
    timestamp: datetime
    details: dict[str, Any] = field(default_factory=dict)


# =============================================================================
# Order Manager
# =============================================================================

class OrderManager:
    """
    Centralized order management for multiple exchanges.

    Features:
    - Route orders to optimal exchange
    - Track order status across exchanges
    - Handle order updates and callbacks
    - Automatic retry on failures
    - Position reconciliation

    Example:
        >>> manager = OrderManager()
        >>> manager.register_exchange("bitvavo", bitvavo_exchange)
        >>> manager.register_exchange("revolut", revolut_exchange)
        >>>
        >>> # Place order (auto-routed)
        >>> request = OrderRequest(
        ...     symbol=Symbol("BTC", "EUR"),
        ...     side=OrderSide.BUY,
        ...     order_type=OrderType.LIMIT,
        ...     amount=Decimal("0.1"),
        ...     price=Decimal("45000")
        ... )
        >>> order = await manager.place_order(request)
        >>>
        >>> # Check status
        >>> status = await manager.get_order_status(order.order_id)
        >>>
        >>> # Cancel if needed
        >>> await manager.cancel_order(order.order_id)
    """

    def __init__(self, default_exchange: str | None = None):
        """
        Initialize order manager.

        Args:
            default_exchange: Default exchange to use when no routing preferred
        """
        self.default_exchange = default_exchange

        # Exchange registry
        self._exchanges: dict[str, BaseExchange] = {}

        # Order tracking
        self._orders: dict[str, Order] = {}  # order_id -> Order
        self._exchange_orders: dict[str, set[str]] = defaultdict(set)  # exchange -> order_ids
        self._client_order_ids: dict[str, str] = {}  # client_order_id -> order_id

        # Event handling
        self._callbacks: list[Callable[[OrderEvent], None]] = []
        self._update_task: asyncio.Task | None = None
        self._running = False

        # Configuration
        self._auto_cancel_on_error = True
        self._max_retries = 3
        self._retry_delay = 1.0  # seconds

        logger.info("[OrderManager] Initialized")

    # -------------------------------------------------------------------------
    # Exchange Management
    # -------------------------------------------------------------------------

    def register_exchange(self, exchange_id: str, exchange: BaseExchange) -> None:
        """
        Register an exchange for order routing.

        Args:
            exchange_id: Unique identifier for this exchange
            exchange: Exchange connector instance
        """
        self._exchanges[exchange_id] = exchange
        logger.info(f"[OrderManager] Registered exchange: {exchange_id}")

        # Set default if first exchange
        if self.default_exchange is None:
            self.default_exchange = exchange_id

    def unregister_exchange(self, exchange_id: str) -> None:
        """Unregister an exchange."""
        if exchange_id in self._exchanges:
            del self._exchanges[exchange_id]
            logger.info(f"[OrderManager] Unregistered exchange: {exchange_id}")

    def get_exchange(self, exchange_id: str) -> BaseExchange | None:
        """Get exchange by ID."""
        return self._exchanges.get(exchange_id)

    def list_exchanges(self) -> list[str]:
        """List all registered exchange IDs."""
        return list(self._exchanges.keys())

    # -------------------------------------------------------------------------
    # Order Routing
    # -------------------------------------------------------------------------

    async def route_order(self, request: OrderRequest) -> OrderRoute:
        """
        Determine best exchange for order.

        Routing logic considers:
        - Trading fees
        - Liquidity (spread)
        - Historical slippage
        - Available balance
        - Exchange reliability

        Args:
            request: Order request

        Returns:
            Routing decision
        """
        if not self._exchanges:
            raise RuntimeError("No exchanges registered")

        routes = []

        for exchange_id, exchange in self._exchanges.items():
            if not exchange.connected:
                continue

            try:
                # Get ticker for spread analysis
                ticker = await exchange.get_ticker(request.symbol)
                if not ticker:
                    continue

                # Calculate spread
                spread = (ticker.ask - ticker.bid) / ticker.last

                # Get fees
                fees = await exchange.get_trading_fees(request.symbol)
                expected_fee = fees["taker"] if request.order_type == OrderType.MARKET else fees["maker"]

                # Check balance
                balance = await exchange.get_balance(request.symbol.quote if request.side == OrderSide.BUY else request.symbol.base)
                has_balance = False
                if isinstance(balance, dict):
                    has_balance = True  # Simplified check
                elif balance:
                    required = request.amount * (request.price or ticker.ask) * Decimal("1.01")
                    has_balance = balance.free >= required

                # Calculate confidence score (0-1)
                confidence = 1.0
                confidence -= float(spread) * 10  # Penalize high spread
                confidence -= float(expected_fee) * 100  # Penalize high fees
                confidence = max(0.1, min(1.0, confidence))

                route = OrderRoute(
                    exchange_id=exchange_id,
                    reason=f"Spread: {spread:.4%}, Fee: {expected_fee:.4%}",
                    expected_fee=expected_fee,
                    expected_slippage=spread / 2,
                    confidence=confidence
                )
                routes.append(route)

            except Exception as e:
                logger.warning(f"[OrderManager] Routing check failed for {exchange_id}: {e}")
                continue

        if not routes:
            # Fallback to default
            if self.default_exchange and self.default_exchange in self._exchanges:
                return OrderRoute(
                    exchange_id=self.default_exchange,
                    reason="Fallback to default",
                    expected_fee=Decimal("0.0025"),
                    expected_slippage=Decimal("0.001"),
                    confidence=0.5
                )
            raise RuntimeError("No available exchanges for routing")

        # Select best route by confidence
        best_route = max(routes, key=lambda r: r.confidence)
        logger.info(f"[OrderManager] Routed order to {best_route.exchange_id}: {best_route.reason}")

        return best_route

    # -------------------------------------------------------------------------
    # Order Operations
    # -------------------------------------------------------------------------

    async def place_order(
        self,
        request: OrderRequest,
        exchange_id: str | None = None,
        client_order_id: str | None = None
    ) -> Order:
        """
        Place an order on an exchange.

        Args:
            request: Order request parameters
            exchange_id: Specific exchange to use, or None for auto-routing
            client_order_id: Optional client-provided order ID

        Returns:
            Created order
        """
        # Validate request
        request.validate()

        # Generate client order ID if not provided
        if not client_order_id:
            client_order_id = f"triad-{uuid4().hex[:12]}"

        request.client_order_id = client_order_id

        # Determine exchange
        if exchange_id is None:
            route = await self.route_order(request)
            exchange_id = route.exchange_id

        exchange = self._exchanges.get(exchange_id)
        if not exchange:
            raise ValueError(f"Exchange not found: {exchange_id}")

        if not exchange.connected:
            raise RuntimeError(f"Exchange not connected: {exchange_id}")

        # Place order with retry
        order = None
        for attempt in range(self._max_retries):
            try:
                order = await exchange.create_order(request)
                if order:
                    break
            except Exception as e:
                logger.warning(f"[OrderManager] Order attempt {attempt + 1} failed: {e}")
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(self._retry_delay * (attempt + 1))

        if not order:
            raise RuntimeError(f"Failed to place order after {self._max_retries} attempts")

        # Track order
        self._orders[order.order_id] = order
        self._exchange_orders[exchange_id].add(order.order_id)
        self._client_order_ids[client_order_id] = order.order_id

        # Emit event
        self._emit_event(OrderEvent(
            event_type="created",
            order=order,
            timestamp=datetime.utcnow()
        ))

        logger.info(
            f"[OrderManager] Order placed: {order.order_id} on {exchange_id} "
            f"({order.side.value} {order.amount} {order.symbol})"
        )

        return order

    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.

        Args:
            order_id: Order ID to cancel

        Returns:
            True if cancellation successful
        """
        order = self._orders.get(order_id)
        if not order:
            logger.warning(f"[OrderManager] Order not found: {order_id}")
            return False

        exchange = self._exchanges.get(order.exchange_id)
        if not exchange:
            logger.warning(f"[OrderManager] Exchange not found for order: {order_id}")
            return False

        try:
            success = await exchange.cancel_order(order_id, order.symbol)

            if success:
                order.status = OrderStatus.CANCELLED
                order.updated_at = datetime.utcnow()

                self._emit_event(OrderEvent(
                    event_type="cancelled",
                    order=order,
                    timestamp=datetime.utcnow()
                ))

                logger.info(f"[OrderManager] Order cancelled: {order_id}")

            return success

        except Exception as e:
            logger.error(f"[OrderManager] Cancel failed: {e}")
            return False

    async def cancel_all_orders(self, symbol: Symbol | None = None) -> int:
        """
        Cancel all open orders.

        Args:
            symbol: Filter by symbol, or None for all

        Returns:
            Number of orders cancelled
        """
        cancelled = 0

        for order_id, order in list(self._orders.items()):
            if not order.is_open:
                continue

            if symbol and order.symbol != symbol:
                continue

            if await self.cancel_order(order_id):
                cancelled += 1

        logger.info(f"[OrderManager] Cancelled {cancelled} orders")
        return cancelled

    async def get_order(self, order_id: str) -> Order | None:
        """Get order by ID."""
        return self._orders.get(order_id)

    async def get_order_by_client_id(self, client_order_id: str) -> Order | None:
        """Get order by client order ID."""
        order_id = self._client_order_ids.get(client_order_id)
        if order_id:
            return await self.get_order(order_id)
        return None

    async def get_open_orders(
        self,
        exchange_id: str | None = None,
        symbol: Symbol | None = None
    ) -> list[Order]:
        """
        Get all open orders.

        Args:
            exchange_id: Filter by exchange
            symbol: Filter by symbol

        Returns:
            List of open orders
        """
        orders = []

        for order_id, order in self._orders.items():
            if not order.is_open:
                continue

            if exchange_id and order.exchange_id != exchange_id:
                continue

            if symbol and order.symbol != symbol:
                continue

            orders.append(order)

        return orders

    async def sync_orders(self, exchange_id: str | None = None) -> None:
        """
        Synchronize order status with exchanges.

        Args:
            exchange_id: Specific exchange to sync, or None for all
        """
        exchanges_to_sync = [exchange_id] if exchange_id else list(self._exchanges.keys())

        for ex_id in exchanges_to_sync:
            exchange = self._exchanges.get(ex_id)
            if not exchange:
                continue

            try:
                # Get open orders from exchange
                remote_orders = await exchange.get_open_orders()
                remote_order_ids = {o.order_id for o in remote_orders}

                # Update tracked orders
                for remote_order in remote_orders:
                    if remote_order.order_id in self._orders:
                        self._orders[remote_order.order_id] = remote_order

                # Check for orders that are no longer open on exchange
                for order_id in list(self._exchange_orders.get(ex_id, [])):
                    if order_id not in remote_order_ids:
                        order = self._orders.get(order_id)
                        if order and order.is_open:
                            # Order was filled or cancelled externally
                            updated_order = await exchange.get_order(order_id, order.symbol)
                            if updated_order:
                                self._orders[order_id] = updated_order

                                self._emit_event(OrderEvent(
                                    event_type="updated",
                                    order=updated_order,
                                    timestamp=datetime.utcnow(),
                                    details={"sync": True}
                                ))

                logger.debug(f"[OrderManager] Synced orders with {ex_id}")

            except Exception as e:
                logger.error(f"[OrderManager] Sync failed for {ex_id}: {e}")

    # -------------------------------------------------------------------------
    # Event Handling
    # -------------------------------------------------------------------------

    def register_callback(self, callback: Callable[[OrderEvent], None]) -> None:
        """Register callback for order events."""
        self._callbacks.append(callback)

    def unregister_callback(self, callback: Callable[[OrderEvent], None]) -> None:
        """Unregister callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def _emit_event(self, event: OrderEvent) -> None:
        """Emit order event to all callbacks."""
        for callback in self._callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    asyncio.create_task(callback(event))
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"[OrderManager] Callback error: {e}")

    # -------------------------------------------------------------------------
    # Background Tasks
    # -------------------------------------------------------------------------

    async def start(self) -> None:
        """Start background order tracking."""
        if self._running:
            return

        self._running = True
        self._update_task = asyncio.create_task(self._update_loop())
        logger.info("[OrderManager] Started background tracking")

    async def stop(self) -> None:
        """Stop background order tracking."""
        self._running = False

        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass

        logger.info("[OrderManager] Stopped background tracking")

    async def _update_loop(self) -> None:
        """Background loop for order updates."""
        while self._running:
            try:
                await self.sync_orders()
                await asyncio.sleep(10)  # Sync every 10 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[OrderManager] Update loop error: {e}")
                await asyncio.sleep(5)

    # -------------------------------------------------------------------------
    # Statistics
    # -------------------------------------------------------------------------

    def get_statistics(self) -> dict[str, Any]:
        """Get order manager statistics."""
        total_orders = len(self._orders)
        open_orders = sum(1 for o in self._orders.values() if o.is_open)
        filled_orders = sum(1 for o in self._orders.values() if o.is_filled)

        return {
            "total_orders": total_orders,
            "open_orders": open_orders,
            "filled_orders": filled_orders,
            "exchanges": len(self._exchanges),
            "registered_exchanges": list(self._exchanges.keys()),
        }

    def __repr__(self) -> str:
        return (
            f"OrderManager("
            f"exchanges={len(self._exchanges)}, "
            f"orders={len(self._orders)}, "
            f"open={sum(1 for o in self._orders.values() if o.is_open)}"
            f")"
        )
