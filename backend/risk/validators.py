import logging
from datetime import date
from typing import Optional

from backend.schemas.orders import OrderRequest

logger = logging.getLogger(__name__)


class RiskViolationError(Exception):
    """Raised when an order violates risk limits."""

    pass


class RiskValidator:
    """
    Validates orders against pre-defined risk limits.

    Tracks daily PnL and enforces:
    - Max order size per trade
    - Max daily loss limit
    - Kill switch halts all trading
    """

    def __init__(self, max_order_size: float, max_daily_loss: float):
        self.max_order_size = max_order_size
        self.max_daily_loss = max_daily_loss
        self.kill_switch_active = False
        self._daily_pnl: float = 0.0
        self._pnl_date: Optional[date] = None

    def activate_kill_switch(self):
        self.kill_switch_active = True

    def deactivate_kill_switch(self):
        self.kill_switch_active = False

    def record_trade_result(self, pnl: float) -> None:
        """
        Record a trade's PnL for daily loss tracking.

        Auto-resets if the date has changed since last recording.

        Args:
            pnl: Realized PnL of the trade (positive or negative)
        """
        today = date.today()
        if self._pnl_date != today:
            self._daily_pnl = 0.0
            self._pnl_date = today

        self._daily_pnl += pnl

        if self._daily_pnl <= -self.max_daily_loss:
            logger.warning(
                "Daily loss limit reached: %.2f <= -%.2f. Activating kill switch.",
                self._daily_pnl,
                self.max_daily_loss,
            )
            self.activate_kill_switch()

    def get_daily_pnl(self) -> float:
        """Return current daily PnL. Resets on new day."""
        today = date.today()
        if self._pnl_date != today:
            self._daily_pnl = 0.0
            self._pnl_date = today
        return self._daily_pnl

    def validate_order(self, order: OrderRequest, current_price: float):
        """
        Check order against limits. Raises RiskViolationError if invalid.
        """
        if self.kill_switch_active:
            raise RiskViolationError("KILL SWITCH ACTIVE: Trading halted.")

        order_value = order.qty * current_price

        if order_value > self.max_order_size:
            raise RiskViolationError(
                "Order value %.2f exceeds limit %.2f"
                % (order_value, self.max_order_size)
            )

        # Daily loss check
        today = date.today()
        if self._pnl_date != today:
            self._daily_pnl = 0.0
            self._pnl_date = today

        remaining_budget = self.max_daily_loss + self._daily_pnl
        if remaining_budget <= 0:
            raise RiskViolationError(
                "Daily loss limit exhausted: PnL %.2f, limit %.2f"
                % (self._daily_pnl, self.max_daily_loss)
            )
