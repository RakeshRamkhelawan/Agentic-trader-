from typing import Optional

from backend.schemas.orders import OrderRequest


class RiskViolationError(Exception):
    """Raised when an order violates risk limits."""

    pass


class RiskValidator:
    """
    Validates orders against pre-defined risk limits.
    """

    def __init__(self, max_order_size: float, max_daily_loss: float):
        self.max_order_size = max_order_size
        self.max_daily_loss = max_daily_loss
        self.kill_switch_active = False

    def activate_kill_switch(self):
        self.kill_switch_active = True

    def validate_order(self, order: OrderRequest, current_price: float):
        """
        Check order against limits. Raises RiskViolationError if invalid.
        """
        if self.kill_switch_active:
            raise RiskViolationError("KILL SWITCH ACTIVE: Trading halted.")

        order_value = order.qty * current_price

        if order_value > self.max_order_size:
            raise RiskViolationError(
                f"Order value {order_value:.2f} exceeds limit {self.max_order_size:.2f}"
            )

        # TODO: Add daily loss check (requires state tracking)
