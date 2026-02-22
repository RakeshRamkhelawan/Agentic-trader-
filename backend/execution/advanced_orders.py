"""
Advanced Order Types - Iceberg, TWAP, Stop-Limit (Sprint 3).

Implements sophisticated order execution strategies:
- Iceberg: Hide large order size, show only small visible portion
- TWAP: Time-Weighted Average Price execution over time
- Stop-Limit: Risk-aware orders with trigger price and limit price

All order types are async and non-blocking to the main router.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Dict, List, Optional

from backend.execution.broker_interface import ExecutionInterface, OrderResult
from backend.schemas.orders import OrderRequest, OrderSide, OrderType

logger = logging.getLogger(__name__)


class AdvancedOrderStatus(Enum):
    """Status of advanced order execution."""

    PENDING = "pending"
    ACTIVE = "active"
    PARTIAL = "partial"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass
class IcebergConfig:
    """Configuration for Iceberg order."""

    total_quantity: float
    visible_quantity: float
    min_fill_quantity: Optional[float] = None


@dataclass
class TWAPConfig:
    """Configuration for TWAP order."""

    total_quantity: float
    num_slices: int = 10
    duration_seconds: int = 300  # 5 minutes
    randomize: bool = True  # Add randomization to avoid detection


@dataclass
class StopLimitConfig:
    """Configuration for Stop-Limit order."""

    stop_price: float
    limit_price: float
    quantity: float
    trailing_amount: Optional[float] = None  # For trailing stop


class AdvancedOrderExecutor(ABC):
    """Abstract base for advanced order execution."""

    def __init__(
        self,
        adapter: ExecutionInterface,
        callback: Optional[Callable[[OrderResult], None]] = None,
    ):
        self.adapter = adapter
        self.callback = callback
        self.status = AdvancedOrderStatus.PENDING
        self.filled_quantity = 0.0
        self.results: List[OrderResult] = []

    @abstractmethod
    async def execute(self) -> List[OrderResult]:
        """Execute the advanced order strategy."""
        pass

    @abstractmethod
    async def cancel(self) -> bool:
        """Cancel the ongoing order execution."""
        pass

    def _notify(self, result: OrderResult) -> None:
        """Notify callback of order result."""
        if self.callback:
            try:
                self.callback(result)
            except Exception as e:
                logger.error(f"Callback error: {e}")


class IcebergExecutor(AdvancedOrderExecutor):
    """
    Iceberg order executor.

    Breaks large orders into smaller visible chunks.
    Only shows small portion of order at a time to minimize market impact.
    """

    def __init__(
        self,
        symbol: str,
        side: OrderSide,
        config: IcebergConfig,
        adapter: ExecutionInterface,
        callback: Optional[Callable[[OrderResult], None]] = None,
    ):
        super().__init__(adapter, callback)
        self.symbol = symbol
        self.side = side
        self.config = config
        self._cancelled = False

    async def execute(self) -> List[OrderResult]:
        """
        Execute iceberg order.

        Slices large order into visible chunks and executes sequentially.
        """
        self.status = AdvancedOrderStatus.ACTIVE
        remaining = self.config.total_quantity
        visible = self.config.visible_quantity

        logger.info(
            f"Starting Iceberg execution: {self.config.total_quantity} "
            f"in chunks of {visible}"
        )

        while remaining > 0 and not self._cancelled:
            # Calculate next chunk size
            chunk_size = min(visible, remaining)

            # Submit visible portion
            order = OrderRequest(
                symbol=self.symbol,
                side=self.side,
                order_type=OrderType.LIMIT,
                qty=chunk_size,
            )

            try:
                result = await self.adapter.submit_order(order)
                self.results.append(result)
                self.filled_quantity += result.filled_qty
                remaining -= result.filled_qty

                self._notify(result)

                # Wait for fill or timeout before next chunk
                if remaining > 0:
                    await asyncio.sleep(1.0)  # Brief pause between chunks

            except Exception as e:
                logger.error(f"Iceberg chunk failed: {e}")
                self.status = AdvancedOrderStatus.FAILED
                return self.results

        if self._cancelled:
            self.status = AdvancedOrderStatus.CANCELLED
        elif remaining <= 0:
            self.status = AdvancedOrderStatus.COMPLETED
        else:
            self.status = AdvancedOrderStatus.PARTIAL

        return self.results

    async def cancel(self) -> bool:
        """Cancel iceberg execution."""
        self._cancelled = True
        logger.info("Iceberg order cancelled")
        return True


class TWAPExecutor(AdvancedOrderExecutor):
    """
    TWAP (Time-Weighted Average Price) executor.

    Executes order evenly distributed over time to achieve
    time-weighted average price.
    """

    def __init__(
        self,
        symbol: str,
        side: OrderSide,
        config: TWAPConfig,
        adapter: ExecutionInterface,
        callback: Optional[Callable[[OrderResult], None]] = None,
    ):
        super().__init__(adapter, callback)
        self.symbol = symbol
        self.side = side
        self.config = config
        self._cancelled = False
        self._start_time: Optional[datetime] = None

    async def execute(self) -> List[OrderResult]:
        """
        Execute TWAP order.

        Divides order into time slices and executes at regular intervals.
        """
        self.status = AdvancedOrderStatus.ACTIVE
        self._start_time = datetime.now(timezone.utc)

        slice_quantity = self.config.total_quantity / self.config.num_slices
        interval = self.config.duration_seconds / self.config.num_slices

        logger.info(
            f"Starting TWAP execution: {self.config.total_quantity} "
            f"in {self.config.num_slices} slices over {self.config.duration_seconds}s"
        )

        for i in range(self.config.num_slices):
            if self._cancelled:
                break

            # Randomize interval slightly to avoid detection
            sleep_time = interval
            if self.config.randomize:
                import random

                sleep_time *= random.uniform(0.8, 1.2)

            # Wait before executing slice (except first)
            if i > 0:
                await asyncio.sleep(sleep_time)

            # Execute slice
            order = OrderRequest(
                symbol=self.symbol,
                side=self.side,
                order_type=OrderType.MARKET,  # TWAP typically uses market orders
                qty=slice_quantity,
            )

            try:
                result = await self.adapter.submit_order(order)
                self.results.append(result)
                self.filled_quantity += result.filled_qty

                self._notify(result)

                logger.debug(f"TWAP slice {i+1}/{self.config.num_slices} executed")

            except Exception as e:
                logger.error(f"TWAP slice {i+1} failed: {e}")
                # Continue with next slice rather than failing entire order

        # Determine final status
        if self._cancelled:
            self.status = AdvancedOrderStatus.CANCELLED
        elif self.filled_quantity >= self.config.total_quantity * 0.95:
            self.status = AdvancedOrderStatus.COMPLETED
        else:
            self.status = AdvancedOrderStatus.PARTIAL

        return self.results

    async def cancel(self) -> bool:
        """Cancel TWAP execution."""
        self._cancelled = True
        logger.info("TWAP order cancelled")
        return True


class StopLimitExecutor(AdvancedOrderExecutor):
    """
    Stop-Limit order executor.

    Monitors price and triggers limit order when stop price is reached.
    Optional trailing stop functionality.
    """

    def __init__(
        self,
        symbol: str,
        side: OrderSide,
        config: StopLimitConfig,
        adapter: ExecutionInterface,
        callback: Optional[Callable[[OrderResult], None]] = None,
    ):
        super().__init__(adapter, callback)
        self.symbol = symbol
        self.side = side
        self.config = config
        self._cancelled = False
        self._triggered = False
        self._highest_price: Optional[float] = None  # For trailing stop

    async def execute(self) -> List[OrderResult]:
        """
        Execute stop-limit order.

        Monitors price until stop trigger, then submits limit order.
        """
        self.status = AdvancedOrderStatus.ACTIVE

        logger.info(
            f"Starting Stop-Limit monitor: stop={self.config.stop_price}, "
            f"limit={self.config.limit_price}"
        )

        # Monitor loop
        while not self._cancelled and not self._triggered:
            try:
                # Get current price
                ticker = await self.adapter.get_ticker(self.symbol)
                current_price = ticker.get("last", 0)

                # Check stop trigger
                if self._should_trigger(current_price):
                    self._triggered = True
                    logger.info(f"Stop triggered at {current_price}")
                    break

                # Update trailing stop if enabled
                if self.config.trailing_amount:
                    self._update_trailing_stop(current_price)

                # Poll interval
                await asyncio.sleep(1.0)

            except Exception as e:
                logger.error(f"Stop-Limit monitoring error: {e}")
                await asyncio.sleep(5.0)  # Back off on error

        # Submit limit order if triggered
        if self._triggered and not self._cancelled:
            order = OrderRequest(
                symbol=self.symbol,
                side=self.side,
                order_type=OrderType.LIMIT,
                qty=self.config.quantity,
                limit_price=self.config.limit_price,
            )

            try:
                result = await self.adapter.submit_order(order)
                self.results.append(result)
                self.filled_quantity = result.filled_qty
                self.status = AdvancedOrderStatus.COMPLETED
                self._notify(result)

            except Exception as e:
                logger.error(f"Stop-Limit order failed: {e}")
                self.status = AdvancedOrderStatus.FAILED

        elif self._cancelled:
            self.status = AdvancedOrderStatus.CANCELLED

        return self.results

    def _should_trigger(self, current_price: float) -> bool:
        """Check if stop price has been reached."""
        if self.side == OrderSide.SELL:
            # Sell stop: trigger when price drops below stop price
            return current_price <= self.config.stop_price
        else:
            # Buy stop: trigger when price rises above stop price
            return current_price >= self.config.stop_price

    def _update_trailing_stop(self, current_price: float) -> None:
        """Update trailing stop price based on favorable movement."""
        if self._highest_price is None:
            self._highest_price = current_price
            return

        if self.side == OrderSide.SELL:
            # For sell trailing stop: raise stop as price rises
            if current_price > self._highest_price:
                self._highest_price = current_price
                self.config.stop_price = current_price - self.config.trailing_amount
        else:
            # For buy trailing stop: lower stop as price falls
            if current_price < self._highest_price:
                self._highest_price = current_price
                self.config.stop_price = current_price + self.config.trailing_amount

    async def cancel(self) -> bool:
        """Cancel stop-limit order."""
        self._cancelled = True
        logger.info("Stop-Limit order cancelled")
        return True


class AdvancedOrderManager:
    """
    Manager for advanced order execution.

    Handles lifecycle of iceberg, TWAP, and stop-limit orders.
    """

    def __init__(self):
        self._active_orders: Dict[str, AdvancedOrderExecutor] = {}
        self._order_counter = 0

    def _generate_order_id(self) -> str:
        """Generate unique order ID."""
        self._order_counter += 1
        return f"adv_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{self._order_counter}"

    async def submit_iceberg(
        self,
        symbol: str,
        side: OrderSide,
        config: IcebergConfig,
        adapter: ExecutionInterface,
        callback: Optional[Callable[[OrderResult], None]] = None,
    ) -> str:
        """Submit iceberg order."""
        order_id = self._generate_order_id()
        executor = IcebergExecutor(symbol, side, config, adapter, callback)
        self._active_orders[order_id] = executor

        # Start execution in background
        asyncio.create_task(self._run_executor(order_id, executor))

        return order_id

    async def submit_twap(
        self,
        symbol: str,
        side: OrderSide,
        config: TWAPConfig,
        adapter: ExecutionInterface,
        callback: Optional[Callable[[OrderResult], None]] = None,
    ) -> str:
        """Submit TWAP order."""
        order_id = self._generate_order_id()
        executor = TWAPExecutor(symbol, side, config, adapter, callback)
        self._active_orders[order_id] = executor

        asyncio.create_task(self._run_executor(order_id, executor))

        return order_id

    async def submit_stop_limit(
        self,
        symbol: str,
        side: OrderSide,
        config: StopLimitConfig,
        adapter: ExecutionInterface,
        callback: Optional[Callable[[OrderResult], None]] = None,
    ) -> str:
        """Submit stop-limit order."""
        order_id = self._generate_order_id()
        executor = StopLimitExecutor(symbol, side, config, adapter, callback)
        self._active_orders[order_id] = executor

        asyncio.create_task(self._run_executor(order_id, executor))

        return order_id

    async def _run_executor(
        self,
        order_id: str,
        executor: AdvancedOrderExecutor,
    ) -> None:
        """Run executor and cleanup when done."""
        try:
            await executor.execute()
        except Exception as e:
            logger.error(f"Executor {order_id} failed: {e}")
        finally:
            # Cleanup after some time to allow result inspection
            await asyncio.sleep(60.0)
            self._active_orders.pop(order_id, None)

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an active order."""
        executor = self._active_orders.get(order_id)
        if executor:
            return await executor.cancel()
        return False

    def get_order_status(self, order_id: str) -> Optional[AdvancedOrderStatus]:
        """Get status of an order."""
        executor = self._active_orders.get(order_id)
        if executor:
            return executor.status
        return None

    def get_active_orders(self) -> Dict[str, AdvancedOrderStatus]:
        """Get all active orders and their statuses."""
        return {
            order_id: executor.status
            for order_id, executor in self._active_orders.items()
        }
