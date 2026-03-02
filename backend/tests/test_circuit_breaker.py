"""
Tests voor Circuit Breaker.

Test safety limits, trip conditions, reset logic, en persistence.
"""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.core.database import Base
from backend.governance.circuit_breaker import (
    BreakerState,
    CircuitBreaker,
    CircuitBreakerState,
    CircuitBreakerTrippedError,
    TripReason,
)


@pytest.fixture
async def db_session():
    """In-memory test database session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    await engine.dispose()


class TestCircuitBreaker:
    """Tests for Circuit Breaker."""

    @pytest.mark.asyncio
    async def test_initial_state_closed(self, db_session):
        """Circuit breaker starts in CLOSED state."""
        breaker = CircuitBreaker(db_session, breaker_name="test_breaker")

        is_tripped = await breaker.is_tripped()
        status = await breaker.get_status()

        assert not is_tripped
        assert status["state"] == BreakerState.CLOSED.value
        assert status["metrics"]["daily_pnl"] == 0.0
        assert status["metrics"]["consecutive_losses"] == 0

    @pytest.mark.asyncio
    async def test_max_daily_loss_trip(self, db_session):
        """Circuit breaker trips bij max daily loss."""
        breaker = CircuitBreaker(
            db_session, breaker_name="daily_loss_test", max_daily_loss_pct=0.05  # -5%
        )

        # Record -6% loss
        await breaker.record_trade_result(pnl=-0.06)

        # Should trip
        is_tripped = await breaker.is_tripped()
        reason = await breaker.get_trip_reason()

        assert is_tripped
        assert reason == TripReason.MAX_DAILY_LOSS.value

    @pytest.mark.asyncio
    async def test_consecutive_losses_trip(self, db_session):
        """Circuit breaker trips na consecutive losses."""
        breaker = CircuitBreaker(
            db_session, breaker_name="consecutive_test", max_consecutive_losses=3
        )

        # Record 3 consecutive losses
        for i in range(3):
            await breaker.record_trade_result(pnl=-0.01)

        # Should trip
        is_tripped = await breaker.is_tripped()
        reason = await breaker.get_trip_reason()

        assert is_tripped
        assert reason == TripReason.CONSECUTIVE_LOSSES.value

    @pytest.mark.asyncio
    async def test_consecutive_losses_reset_on_win(self, db_session):
        """Consecutive losses reset bij winning trade."""
        breaker = CircuitBreaker(
            db_session, breaker_name="win_reset_test", max_consecutive_losses=3
        )

        # 2 losses
        await breaker.record_trade_result(pnl=-0.01)
        await breaker.record_trade_result(pnl=-0.01)

        # 1 win (reset)
        await breaker.record_trade_result(pnl=0.02)

        # 2 more losses (should NOT trip)
        await breaker.record_trade_result(pnl=-0.01)
        await breaker.record_trade_result(pnl=-0.01)

        is_tripped = await breaker.is_tripped()
        status = await breaker.get_status()

        assert not is_tripped
        assert status["metrics"]["consecutive_losses"] == 2

    @pytest.mark.asyncio
    async def test_max_exposure_trip(self, db_session):
        """Circuit breaker trips bij max exposure."""
        breaker = CircuitBreaker(
            db_session, breaker_name="exposure_test", max_exposure_pct=0.90  # 90%
        )

        # Build up position to 95%
        await breaker.record_trade_result(pnl=0.0, position_delta=0.95)

        # Should trip
        is_tripped = await breaker.is_tripped()
        reason = await breaker.get_trip_reason()

        assert is_tripped
        assert reason == TripReason.MAX_EXPOSURE.value

    @pytest.mark.asyncio
    async def test_emergency_shutdown(self, db_session):
        """Emergency shutdown trips breaker."""
        breaker = CircuitBreaker(db_session, breaker_name="emergency_test")

        await breaker.emergency_shutdown()

        is_tripped = await breaker.is_tripped()
        reason = await breaker.get_trip_reason()
        status = await breaker.get_status()

        assert is_tripped
        assert reason == TripReason.EMERGENCY_SHUTDOWN.value
        assert status["emergency_shutdown"]

    @pytest.mark.asyncio
    async def test_manual_reset(self, db_session):
        """Manual reset clears breaker."""
        breaker = CircuitBreaker(db_session, breaker_name="reset_test", max_daily_loss_pct=0.05)

        # Trip breaker
        await breaker.record_trade_result(pnl=-0.06)
        assert await breaker.is_tripped()

        # Reset
        await breaker.reset(admin_override=True)

        is_tripped = await breaker.is_tripped()
        status = await breaker.get_status()

        assert not is_tripped
        assert status["state"] == BreakerState.CLOSED.value
        assert status["trip_reason"] is None

    @pytest.mark.asyncio
    async def test_reset_requires_admin_override(self, db_session):
        """Reset vereist admin override."""
        breaker = CircuitBreaker(db_session, breaker_name="override_test")

        # Trip breaker
        await breaker.emergency_shutdown()

        # Reset without override should fail
        with pytest.raises(ValueError, match="admin_override"):
            await breaker.reset(admin_override=False)

        # Should still be tripped
        assert await breaker.is_tripped()

    @pytest.mark.asyncio
    async def test_trip_persistence(self, db_session):
        """Breaker state persists across instances."""
        # Trip breaker
        breaker1 = CircuitBreaker(db_session, breaker_name="persist_test", max_daily_loss_pct=0.05)
        await breaker1.record_trade_result(pnl=-0.06)
        assert await breaker1.is_tripped()

        # Create new instance (simuleert restart)
        breaker2 = CircuitBreaker(db_session, breaker_name="persist_test", max_daily_loss_pct=0.05)

        # Should still be tripped
        is_tripped = await breaker2.is_tripped()
        reason = await breaker2.get_trip_reason()

        assert is_tripped
        assert reason == TripReason.MAX_DAILY_LOSS.value

    @pytest.mark.asyncio
    async def test_get_status(self, db_session):
        """Get status returns complete info."""
        breaker = CircuitBreaker(
            db_session,
            breaker_name="status_test",
            max_daily_loss_pct=0.05,
            max_consecutive_losses=3,
            max_exposure_pct=0.90,
        )

        # Record some activity
        await breaker.record_trade_result(pnl=-0.02, position_delta=0.5)

        status = await breaker.get_status()

        assert status["breaker_name"] == "status_test"
        assert status["state"] == BreakerState.CLOSED.value
        assert not status["is_tripped"]
        assert status["metrics"]["daily_pnl"] == -0.02
        assert status["metrics"]["consecutive_losses"] == 1
        assert status["metrics"]["total_exposure"] == 0.5
        assert status["limits"]["max_daily_loss_pct"] == 0.05
        assert status["limits"]["max_consecutive_losses"] == 3
        assert status["limits"]["max_exposure_pct"] == 0.90
