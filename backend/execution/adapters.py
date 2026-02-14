"""
Execution Adapters.
"""

from typing import Optional, List, Dict
import logging
from backend.execution.order_executor import ExchangeAdapter
from backend.core.schemas.ooda_types import Order


class StubExchangeAdapter(ExchangeAdapter):
    """
    Stub adapter for integration testing.
    Keeps track of placed orders in memory.
    """

    def __init__(self):
        self.placed_orders: List[Order] = []
        self.logger = logging.getLogger(self.__class__.__name__)

    async def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
    ) -> Order:
        """Record order and return mock filled order."""
        order = Order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            status="pending",
        )
        self.placed_orders.append(order)
        self.logger.info(f"[STUB] Placed order: {order}")
        return order

    async def get_order_status(self, order_id: str) -> Order:
        """Simulate immediate fill."""
        # Find order
        order = next((o for o in self.placed_orders if o.order_id == order_id), None)
        if not order:
            raise Exception("Order not found")

        # Return filled version
        return Order(
            order_id=order.order_id,
            symbol=order.symbol,
            side=order.side,
            order_type=order.order_type,
            quantity=order.quantity,
            status="filled",
            filled_quantity=order.quantity,
            avg_fill_price=order.price or 100000.0,  # Mock price
        )
