"""
Circuit Breaker - Trading Safety System.

Automatische stopzetting van trading bij gevaarlijke condities.
"""

import logging
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.core.database import Base

logger = logging.getLogger(__name__)


class BreakerState(str, Enum):
    """Circuit breaker state."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Tripped, trading blocked


class TripReason(str, Enum):
    """Reason for circuit breaker trip."""

    MAX_DAILY_LOSS = "max_daily_loss"
    CONSECUTIVE_LOSSES = "consecutive_losses"
    MAX_EXPOSURE = "max_exposure"
    EMERGENCY_SHUTDOWN = "emergency_shutdown"


class CircuitBreakerState(Base):
    """
    Persistent circuit breaker state.

    Tracks breaker status, trip reason, and trading metrics.
    """

    __tablename__ = "circuit_breaker_state"

    id = Column(Integer, primary_key=True, autoincrement=True)
    breaker_name = Column(String(64), nullable=False, unique=True, index=True)
    state = Column(String(16), nullable=False, default="closed")
    trip_reason = Column(String(64), nullable=True)
    tripped_at = Column(DateTime, nullable=True)

    # Trading metrics
    daily_pnl = Column(Float, nullable=False, default=0.0)
    consecutive_losses = Column(Integer, nullable=False, default=0)
    total_exposure = Column(Float, nullable=False, default=0.0)

    # Reset tracking
    last_reset_at = Column(DateTime, nullable=True)
    last_daily_reset_at = Column(DateTime, nullable=True)

    # Emergency shutdown
    emergency_shutdown = Column(Boolean, nullable=False, default=False)

    updated_at = Column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    def __repr__(self):
        return f"<CircuitBreakerState {self.breaker_name}: {self.state}>"


class CircuitBreakerTrippedError(Exception):
    """Exception raised when circuit breaker is tripped."""

    pass


class CircuitBreaker:
    """
    Circuit Breaker voor trading safety.

    Features:
    - Max daily loss protection
    - Consecutive loss tracking
    - Position exposure limits
    - Emergency manual shutdown
    - Persistent state
    """

    def __init__(
        self,
        db_session: AsyncSession,
        breaker_name: str = "main_breaker",
        max_daily_loss_pct: float = 0.05,
        max_consecutive_losses: int = 3,
        max_exposure_pct: float = 0.90,
    ):
        """
        Initialize Circuit Breaker.

        Args:
            db_session: Async database session
            breaker_name: Unique breaker identifier
            max_daily_loss_pct: Max daily loss percentage (0.05 = 5%)
            max_consecutive_losses: Max consecutive losing trades
            max_exposure_pct: Max position exposure (0.90 = 90% of capital)
        """
        self.db_session = db_session
        self.breaker_name = breaker_name
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_consecutive_losses = max_consecutive_losses
        self.max_exposure_pct = max_exposure_pct

        self._state: CircuitBreakerState | None = None

    async def _load_state(self) -> CircuitBreakerState:
        """Load or create breaker state."""
        if self._state:
            return self._state

        result = await self.db_session.execute(
            select(CircuitBreakerState).where(CircuitBreakerState.breaker_name == self.breaker_name)
        )
        state = result.scalar_one_or_none()

        if not state:
            # Create new state
            state = CircuitBreakerState(
                breaker_name=self.breaker_name,
                state=BreakerState.CLOSED.value,
                last_daily_reset_at=datetime.now(UTC),
            )
            self.db_session.add(state)
            await self.db_session.commit()
            await self.db_session.refresh(state)

        self._state = state
        return state

    async def is_tripped(self) -> bool:
        """
        Check if circuit breaker is tripped.

        Returns:
            True if breaker is OPEN (tripped)
        """
        state = await self._load_state()
        return state.state == BreakerState.OPEN.value

    async def get_trip_reason(self) -> str | None:
        """Get reason for trip."""
        state = await self._load_state()
        return state.trip_reason

    async def check_and_trip(self) -> bool:
        """
        Check all watchdogs en trip indien nodig.

        Returns:
            True if breaker tripped
        """
        state = await self._load_state()

        # Already tripped
        if state.state == BreakerState.OPEN.value:
            return True

        # Check emergency shutdown
        if state.emergency_shutdown:
            await self._trip(TripReason.EMERGENCY_SHUTDOWN, state)
            return True

        # Check daily loss limit
        if state.daily_pnl <= -self.max_daily_loss_pct:
            await self._trip(TripReason.MAX_DAILY_LOSS, state)
            return True

        # Check consecutive losses
        if state.consecutive_losses >= self.max_consecutive_losses:
            await self._trip(TripReason.CONSECUTIVE_LOSSES, state)
            return True

        # Check exposure limit
        if state.total_exposure >= self.max_exposure_pct:
            await self._trip(TripReason.MAX_EXPOSURE, state)
            return True

        return False

    async def _trip(self, reason: TripReason, state: CircuitBreakerState):
        """Trip the breaker."""
        state.state = BreakerState.OPEN.value
        state.trip_reason = reason.value
        state.tripped_at = datetime.now(UTC)

        await self.db_session.commit()
        await self.db_session.refresh(state)

        logger.critical(
            f"🔴 CIRCUIT BREAKER TRIPPED: {reason.value} "
            f"(daily_pnl={state.daily_pnl:.2%}, "
            f"consecutive_losses={state.consecutive_losses}, "
            f"exposure={state.total_exposure:.2%})"
        )

    async def record_trade_result(self, pnl: float, position_delta: float = 0.0):
        """
        Record trade result en update metrics.

        Args:
            pnl: P&L van trade (positief = winst, negatief = verlies)
            position_delta: Verandering in position size
        """
        state = await self._load_state()

        # Reset daily metrics indien nieuwe dag
        await self._check_daily_reset(state)

        # Update daily PnL
        state.daily_pnl += pnl

        # Update consecutive losses
        if pnl < 0:
            state.consecutive_losses += 1
        else:
            state.consecutive_losses = 0  # Reset on win

        # Update exposure
        state.total_exposure += position_delta
        state.total_exposure = max(0.0, state.total_exposure)  # Can't be negative

        await self.db_session.commit()
        await self.db_session.refresh(state)

        logger.info(
            f"Trade recorded: pnl={pnl:.2%}, "
            f"daily_pnl={state.daily_pnl:.2%}, "
            f"consecutive_losses={state.consecutive_losses}, "
            f"exposure={state.total_exposure:.2%}"
        )

        # Check if should trip
        await self.check_and_trip()

    async def _check_daily_reset(self, state: CircuitBreakerState):
        """Reset daily metrics indien nieuwe dag."""
        now = datetime.now(UTC)
        last_reset = state.last_daily_reset_at or now

        # Check if new day
        if now.date() > last_reset.date():
            logger.info("New trading day - resetting daily metrics")
            state.daily_pnl = 0.0
            state.last_daily_reset_at = now

    async def emergency_shutdown(self):
        """
        Manual emergency shutdown.

        CRITICAL: Kan alleen manual gereset worden!
        """
        state = await self._load_state()
        state.emergency_shutdown = True
        await self._trip(TripReason.EMERGENCY_SHUTDOWN, state)

        logger.critical("🚨 EMERGENCY SHUTDOWN ACTIVATED 🚨")

    async def reset(self, admin_override: bool = False):
        """
        Reset circuit breaker (manual only).

        Args:
            admin_override: Admin override flag (vereist)

        Raises:
            ValueError: If admin_override not provided
        """
        if not admin_override:
            raise ValueError("Circuit breaker reset requires admin_override=True")

        state = await self._load_state()

        logger.warning(
            f"Circuit breaker RESET by admin "
            f"(previous state: {state.state}, reason: {state.trip_reason})"
        )

        state.state = BreakerState.CLOSED.value
        state.trip_reason = None
        state.tripped_at = None
        state.emergency_shutdown = False
        state.last_reset_at = datetime.now(UTC)

        await self.db_session.commit()
        await self.db_session.refresh(state)

    async def get_status(self) -> dict[str, Any]:
        """Get current breaker status."""
        state = await self._load_state()

        return {
            "breaker_name": state.breaker_name,
            "state": state.state,
            "is_tripped": state.state == BreakerState.OPEN.value,
            "trip_reason": state.trip_reason,
            "tripped_at": state.tripped_at.isoformat() if state.tripped_at else None,
            "metrics": {
                "daily_pnl": state.daily_pnl,
                "consecutive_losses": state.consecutive_losses,
                "total_exposure": state.total_exposure,
            },
            "limits": {
                "max_daily_loss_pct": self.max_daily_loss_pct,
                "max_consecutive_losses": self.max_consecutive_losses,
                "max_exposure_pct": self.max_exposure_pct,
            },
            "emergency_shutdown": state.emergency_shutdown,
            "last_reset_at": (state.last_reset_at.isoformat() if state.last_reset_at else None),
        }
