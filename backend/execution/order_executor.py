"""
OrderExecutor - Order Execution Engine

Handles actual order placement, monitoring, en execution quality tracking.
This is the execution component voor the OODA pipeline.
"""

import asyncio
import logging
from typing import Optional, Dict
from datetime import datetime, UTC

from backend.core.schemas.ooda_types import (
    ExecutionPlan,
    ExecutionOutcome,
    Order
)


class ExecutionError(Exception):
    """Execution error exception."""
    pass


class ExchangeAdapter:
    """
    Exchange API adapter interface.
    
    This is a mock adapter. In production, replace with real exchange SDK
    (e.g., ccxt, binance-connector, etc.)
    """
    
    async def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None
    ) -> Order:
        """
        Place order on exchange.
        
        Args:
            symbol: Trading pair
            side: "buy" or "sell"
            order_type: "market" or "limit"
            quantity: Order quantity
            price: Limit price (None for market)
        
        Returns:
            Order object
        """
        # Mock implementation - replace with real exchange API
        order = Order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            status="pending"
        )
        
        logging.info(
            f"[MOCK] Placed {order_type} {side} order: "
            f"{quantity} {symbol} @ {price or 'market'}"
        )
        
        return order
    
    async def get_order_status(self, order_id: str) -> Order:
        """
        Get order status from exchange.
        
        Args:
            order_id: Order ID
        
        Returns:
            Updated Order object
        """
        # Mock - always returns filled after delay
        await asyncio.sleep(0.1)
        
        # Return mock filled order
        return Order(
            order_id=order_id,
            symbol="BTC/USDT",
            side="buy",
            order_type="market",
            quantity=0.01,
            status="filled",
            filled_quantity=0.01,
            avg_fill_price=50000.0
        )
    
    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancel order on exchange.
        
        Args:
            order_id: Order ID
        
        Returns:
            Success status
        """
        logging.info(f"[MOCK] Cancelled order {order_id}")
        return True


class OrderExecutor:
    """
    Order execution engine voor OODA pipeline.
    
    Handles actual order placement on exchanges with slippage
    monitoring en timeout handling.
    """
    
    def __init__(
        self,
        exchange_adapter: Optional[ExchangeAdapter] = None,
        max_slippage_bps: int = 50,  # 0.5% max slippage
        order_timeout: int = 30  # 30 seconds
    ):
        """
        Initialize OrderExecutor.
        
        Args:
            exchange_adapter: Exchange API adapter
            max_slippage_bps: Max acceptable slippage in basis points
            order_timeout: Order fill timeout in seconds
        """
        self.exchange = exchange_adapter or ExchangeAdapter()
        self.max_slippage_bps = max_slippage_bps
        self.order_timeout = order_timeout
        self.active_orders: Dict[str, Order] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def execute_trade(
        self,
        execution_plan: ExecutionPlan
    ) -> ExecutionOutcome:
        """
        Execute trade volgens plan.
        
        Args:
            execution_plan: Execution plan from Trader
        
        Returns:
            ExecutionOutcome with results
        """
        self.logger.info(
            f"Executing trade: {execution_plan.side} "
            f"{execution_plan.quantity} {execution_plan.symbol}"
        )
        
        # 1. Pre-execution checks
        if not await self._pre_execution_checks(execution_plan):
            return ExecutionOutcome(
                trace_id=execution_plan.trace_id,
                success=False,
                error="Pre-execution checks failed"
            )
        
        # 2. Place order
        try:
            order = await self.exchange.place_order(
                symbol=execution_plan.symbol,
                side=execution_plan.side,
                order_type=execution_plan.order_type,
                quantity=execution_plan.quantity,
                price=execution_plan.price
            )
            
            self.active_orders[order.order_id] = order
            
        except Exception as e:
            self.logger.error(f"Order placement failed: {e}")
            return ExecutionOutcome(
                trace_id=execution_plan.trace_id,
                success=False,
                error=f"Order placement failed: {str(e)}"
            )
        
        # 3. Monitor fill
        try:
            filled_order = await self._wait_for_fill(
                order,
                timeout=self.order_timeout
            )
        except ExecutionError as e:
            return ExecutionOutcome(
                trace_id=execution_plan.trace_id,
                success=False,
                error=str(e)
            )
        
        # 4. Calculate execution quality
        slippage_bps = self._calculate_slippage(
            expected_price=execution_plan.expected_price,
            actual_price=filled_order.avg_fill_price or 0.0
        )
        
        if slippage_bps > self.max_slippage_bps:
            self.logger.warning(
                f"High slippage: {slippage_bps:.1f} bps "
                f"(max: {self.max_slippage_bps} bps)"
            )
        
        # 5. Return outcome
        return ExecutionOutcome(
            trace_id=execution_plan.trace_id,
            success=True,
            filled_qty=filled_order.filled_quantity,
            avg_price=filled_order.avg_fill_price,
            slippage=slippage_bps,
            fees=0.0  # TODO: Calculate from exchange response
        )
    
    async def _pre_execution_checks(
        self,
        execution_plan: ExecutionPlan
    ) -> bool:
        """
        Pre-execution validation checks.
        
        Args:
            execution_plan: Execution plan
        
        Returns:
            True if checks pass
        """
        # Check size > 0
        if execution_plan.quantity <= 0:
            self.logger.error("Invalid size: must be > 0")
            return False
        
        # Check expected price > 0
        if execution_plan.expected_price <= 0:
            self.logger.error("Invalid expected price")
            return False
        
        # Add more checks as needed:
        # - Account balance check
        # - Max position size check
        # - Trading hours check
        # etc.
        
        return True
    
    async def _wait_for_fill(
        self,
        order: Order,
        timeout: int
    ) -> Order:
        """
        Wait for order to fill.
        
        Args:
            order: Order object
            timeout: Timeout in seconds
        
        Returns:
            Filled Order
        
        Raises:
            ExecutionError: If timeout or order rejected
        """
        start_time = datetime.now(UTC)
        poll_interval = 1  # Poll every 1 second
        
        while (datetime.now(UTC) - start_time).total_seconds() < timeout:
            # Check order status
            updated_order = await self.exchange.get_order_status(order.order_id)
            
            if updated_order.status == "filled":
                self.logger.info(
                    f"Order {order.order_id} filled: "
                    f"{updated_order.filled_quantity} @ "
                    f"{updated_order.avg_fill_price}"
                )
                return updated_order
            
            elif updated_order.status in ["cancelled", "rejected"]:
                raise ExecutionError(
                    f"Order {order.order_id} {updated_order.status}"
                )
            
            # Wait before next poll
            await asyncio.sleep(poll_interval)
        
        # Timeout - cancel order
        self.logger.warning(f"Order {order.order_id} timed out, cancelling")
        await self.exchange.cancel_order(order.order_id)
        
        raise ExecutionError(
            f"Order {order.order_id} timed out after {timeout}s"
        )
    
    def _calculate_slippage(
        self,
        expected_price: float,
        actual_price: float
    ) -> float:
        """
        Calculate slippage in basis points.
        
        Positive slippage = worse than expected
        
        Args:
            expected_price: Expected fill price
            actual_price: Actual fill price
        
        Returns:
            Slippage in basis points
        """
        if expected_price <= 0:
            return 0.0
        
        diff = abs(actual_price - expected_price)
        slippage_bps = (diff / expected_price) * 10000
        
        return slippage_bps
    
    def get_active_orders(self) -> Dict[str, Order]:
        """Get all active orders."""
        return self.active_orders.copy()
    
    def clear_completed_orders(self):
        """Clear completed orders from tracking."""
        self.active_orders = {
            oid: order
            for oid, order in self.active_orders.items()
            if order.status == "pending"
        }
