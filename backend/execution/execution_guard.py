import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("ExecutionGuard")


class ExecutionGuard:
    """
    Deterministic safety layer for order execution.
    Operates on hard rules independent of AI agent logic.
    """

    def __init__(
        self,
        initial_capital: float,
        max_daily_loss_pct: float = 0.05,
        max_consecutive_losses: int = 3,
        max_open_positions: int = 8,
        max_position_pct: float = 0.03,
        api_latency_threshold_ms: int = 5000,
    ):
        self.initial_capital = initial_capital
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_consecutive_losses = max_consecutive_losses
        self.max_open_positions = max_open_positions
        self.max_position_pct = max_position_pct
        self.latency_threshold = api_latency_threshold_ms

        # State tracking
        self.current_consecutive_losses = 0
        self.daily_start_capital = initial_capital
        self.start_of_day = datetime.utcnow().date()
        self._emergency_stop = False
        self._cooldown_until: Optional[datetime] = None
        self._last_api_latency = 0

        logger.info(
            f"[GUARD] Initialized with €{initial_capital:,.2f} capital. "
            f"Limits: Daily Loss {max_daily_loss_pct:.1%}, Max Pos: {max_open_positions}"
        )

    def _check_date_reset(self):
        """Reset daily counters if it's a new day."""
        now = datetime.utcnow()
        if now.date() > self.start_of_day:
            logger.info(f"[GUARD] New day detected ({now.date()}). Resetting daily limits.")
            self.start_of_day = now.date()
            # Note: daily_start_capital should be updated to current portfolio value
            # by the caller if we want to track progressive daily loss.
            # For now we keep it relative to life-start or last reset.
            self.current_consecutive_losses = 0
            self._emergency_stop = False
            self._cooldown_until = None

    def check_order(
        self,
        symbol: str,
        side: str,
        size_eur: float,
        current_portfolio_value: float,
        open_positions_count: int,
        api_latency_ms: int = 0,
    ) -> Tuple[bool, str]:
        """
        Verify if an order is allowed under current safety constraints.
        Returns: (is_allowed, reason)
        """
        self._check_date_reset()

        if self._emergency_stop:
            return False, "EMERGENCY_STOP_ACTIVE"

        # 1. Cooldown check
        if self._cooldown_until and datetime.utcnow() < self._cooldown_until:
            wait_sec = (self._cooldown_until - datetime.utcnow()).total_seconds()
            return False, f"COOLDOWN_ACTIVE (Wait {int(wait_sec)}s)"

        # 2. Daily Loss Check
        drawdown = (self.daily_start_capital - current_portfolio_value) / self.daily_start_capital
        if drawdown >= self.max_daily_loss_pct:
            self._emergency_stop = True
            logger.critical(f"[GUARD] Daily loss limit exceeded: {drawdown:.2%}")
            return False, f"DAILY_LOSS_LIMIT_REACHED ({drawdown:.2%})"

        # 3. Max Open Positions (only for entries)
        if side.lower() == "buy" and open_positions_count >= self.max_open_positions:
            return False, f"MAX_OPEN_POSITIONS_REACHED ({open_positions_count})"

        # 4. Max Position Size (single position)
        if side.lower() == "buy":
            pos_pct = size_eur / current_portfolio_value if current_portfolio_value > 0 else 1.0
            if pos_pct > self.max_position_pct:
                return False, f"POSITION_TOO_LARGE ({pos_pct:.1%} > {self.max_position_pct:.1%})"

        # 5. API Latency Check
        if api_latency_ms > self.latency_threshold:
            self._cooldown_until = datetime.utcnow() + timedelta(minutes=5)
            logger.warning(f"[GUARD] High API latency detected: {api_latency_ms}ms. Pausing 5m.")
            return False, f"HIGH_LATENCY ({api_latency_ms}ms)"

        return True, "APPROVED"

    def record_trade_result(self, pnl_eur: float):
        """Record trade outcome to update consecutive loss counter."""
        if pnl_eur < 0:
            self.current_consecutive_losses += 1
            if self.current_consecutive_losses >= self.max_consecutive_losses:
                self._cooldown_until = datetime.utcnow() + timedelta(minutes=30)
                logger.warning(
                    f"[GUARD] {self.current_consecutive_losses} consecutive losses. "
                    f"Entering 30m cooldown until {self._cooldown_until}"
                )
        else:
            if self.current_consecutive_losses > 0:
                logger.info("[GUARD] Profit recorded. Resetting consecutive loss counter.")
            self.current_consecutive_losses = 0

    def trigger_emergency_stop(self, reason: str):
        """Manual or automated emergency stop."""
        logger.critical(f"[GUARD] EMERGENCY STOP TRIGGERED: {reason}")
        self._emergency_stop = True

    def is_emergency(self) -> bool:
        return self._emergency_stop

    def get_status(self) -> Dict[str, Any]:
        """Return current safety status for API/UI."""
        return {
            "emergency_stop": self._emergency_stop,
            "consecutive_losses": self.current_consecutive_losses,
            "cooldown_active": (
                self._cooldown_until > datetime.utcnow() if self._cooldown_until else False
            ),
            "cooldown_until": self._cooldown_until.isoformat() if self._cooldown_until else None,
            "daily_drawdown_pct": (self.daily_start_capital - self.daily_start_capital)
            / self.daily_start_capital,  # Simplified
        }
