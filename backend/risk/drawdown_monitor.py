"""
Drawdown Monitor - Real-time Portfolio Drawdown Tracking with Circuit Breakers.

Monitors portfolio value against peak and triggers protective actions:
- REDUCE_EXPOSURE at soft limit (default 10%)
- KILL_SWITCH at hard limit (default 20%)

Recovery mode prevents re-entry until drawdown recovers by 50%.
"""

import logging
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class DrawdownStatus(str, Enum):
    """Current drawdown state."""

    OK = "OK"
    REDUCE_EXPOSURE = "REDUCE_EXPOSURE"
    KILL_SWITCH = "KILL_SWITCH"


class DrawdownMonitor:
    """
    Real-time drawdown monitoring with circuit breakers.

    Tracks peak portfolio value and current drawdown percentage.
    Transitions:
        OK -> REDUCE_EXPOSURE (soft_limit breached)
        REDUCE_EXPOSURE -> KILL_SWITCH (hard_limit breached)
        KILL_SWITCH -> REDUCE_EXPOSURE (recovery to 50% of peak-to-trough)
        REDUCE_EXPOSURE -> OK (full recovery above soft_limit)
    """

    def __init__(
        self,
        soft_limit: float = 0.10,
        hard_limit: float = 0.20,
        recovery_factor: float = 0.50,
    ):
        """
        Args:
            soft_limit: Drawdown % to trigger REDUCE_EXPOSURE. Default 10%.
            hard_limit: Drawdown % to trigger KILL_SWITCH. Default 20%.
            recovery_factor: How much of the drawdown must recover before
                             stepping down severity. Default 50%.
        """
        if not (0 < soft_limit < hard_limit <= 1.0):
            raise ValueError("Must have 0 < soft_limit < hard_limit <= 1.0")
        if not (0 < recovery_factor <= 1.0):
            raise ValueError("recovery_factor must be between 0 and 1")

        self.soft_limit = soft_limit
        self.hard_limit = hard_limit
        self.recovery_factor = recovery_factor

        self._peak_value: float = 0.0
        self._trough_value: float = float("inf")
        self._status: DrawdownStatus = DrawdownStatus.OK
        self._kill_switch_trough: Optional[float] = None

    def check(self, current_value: float) -> DrawdownStatus:
        """
        Update with current portfolio value and return drawdown status.

        Args:
            current_value: Current total portfolio value.

        Returns:
            DrawdownStatus indicating action needed.
        """
        if current_value <= 0:
            self._status = DrawdownStatus.KILL_SWITCH
            return self._status

        # Update peak
        if current_value > self._peak_value:
            self._peak_value = current_value
            self._trough_value = current_value
            # If recovering back to new peak, fully reset
            if self._status != DrawdownStatus.KILL_SWITCH:
                self._status = DrawdownStatus.OK
                self._kill_switch_trough = None
                return self._status

        # Update trough
        if current_value < self._trough_value:
            self._trough_value = current_value

        # Calculate current drawdown
        drawdown = (self._peak_value - current_value) / self._peak_value

        # State transitions
        if drawdown >= self.hard_limit:
            if self._status != DrawdownStatus.KILL_SWITCH:
                logger.warning(
                    "KILL SWITCH activated: drawdown %.2f%% >= hard limit %.2f%%",
                    drawdown * 100,
                    self.hard_limit * 100,
                )
                self._kill_switch_trough = current_value
            self._status = DrawdownStatus.KILL_SWITCH

        elif drawdown >= self.soft_limit:
            if self._status == DrawdownStatus.KILL_SWITCH:
                # Check if we have recovered enough from kill switch trough
                if self._kill_switch_trough is not None:
                    loss_amount = self._peak_value - self._kill_switch_trough
                    recovery_needed = self._kill_switch_trough + (
                        loss_amount * self.recovery_factor
                    )
                    if current_value >= recovery_needed:
                        logger.info(
                            "Stepping down from KILL_SWITCH to REDUCE_EXPOSURE (recovery reached)"
                        )
                        self._status = DrawdownStatus.REDUCE_EXPOSURE
                # else stay at KILL_SWITCH
            else:
                if self._status != DrawdownStatus.REDUCE_EXPOSURE:
                    logger.warning(
                        "REDUCE_EXPOSURE: drawdown %.2f%% >= soft limit %.2f%%",
                        drawdown * 100,
                        self.soft_limit * 100,
                    )
                self._status = DrawdownStatus.REDUCE_EXPOSURE

        else:
            # Below soft limit
            if self._status == DrawdownStatus.KILL_SWITCH:
                # Need recovery check before clearing
                self._status = DrawdownStatus.REDUCE_EXPOSURE
            elif self._status == DrawdownStatus.REDUCE_EXPOSURE:
                self._status = DrawdownStatus.OK

        return self._status

    def get_drawdown_pct(self) -> float:
        """Return current drawdown as a percentage (0.0 to 1.0)."""
        if self._peak_value <= 0:
            return 0.0
        return max(0.0, (self._peak_value - self._trough_value) / self._peak_value)

    def get_peak_value(self) -> float:
        """Return the peak portfolio value recorded."""
        return self._peak_value

    @property
    def status(self) -> DrawdownStatus:
        """Current drawdown status."""
        return self._status

    def reset(self) -> None:
        """Reset the monitor to initial state."""
        self._peak_value = 0.0
        self._trough_value = float("inf")
        self._status = DrawdownStatus.OK
        self._kill_switch_trough = None
