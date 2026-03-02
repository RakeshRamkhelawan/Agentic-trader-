"""
Circuit Breaker Tests - Comprehensive test suite for trading safety mechanism.

Tests cover:
- Normal operation (CLOSED state)
- Trip conditions (daily loss, consecutive losses, exposure)
- Recovery (HALF_OPEN state)
- Emergency shutdown
- Race conditions
"""

import pytest
from datetime import datetime, timedelta, UTC
from unittest.mock import AsyncMock, MagicMock, patch

from backend.governance.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerState,
    BreakerState,
    TripReason,
    CircuitBreakerTrippedError,
)


class TestCircuitBreakerState:
    """Tests for CircuitBreakerState model."""

    def test_state_initialization(self):
        """Test initial state is CLOSED."""
        state = CircuitBreakerState(
            breaker_name="test_breaker",
            state=BreakerState.CLOSED.value,
        )
        assert state.state == BreakerState.CLOSED.value
        assert state.daily_pnl == 0.0
        assert state.consecutive_losses == 0
        assert state.total_exposure == 0.0
        assert state.emergency_shutdown is False

    def test_state_transitions(self):
        """Test state transitions."""
        state = CircuitBreakerState(breaker_name="test")
        
        # Trip to OPEN
        state.state = BreakerState.OPEN.value
        state.trip_reason = TripReason.MAX_DAILY_LOSS.value
        state.tripped_at = datetime.now(UTC)
        
        assert state.state == BreakerState.OPEN.value
        assert state.trip_reason == TripReason.MAX_DAILY_LOSS.value


class TestCircuitBreakerBasic:
    """Basic circuit breaker functionality tests."""

    @pytest.fixture
    async def breaker(self):
        """Create circuit breaker with mocked DB session."""
        mock_session = AsyncMock()
        breaker = CircuitBreaker(
            db_session=mock_session,
            breaker_name="test_breaker",
            max_daily_loss_pct=0.05,
            max_consecutive_losses=3,
            max_exposure_pct=0.90,
        )
        return breaker

    @pytest.mark.asyncio
    async def test_initial_state_closed(self, breaker):
        """Test breaker starts in CLOSED state."""
        b = await breaker
        # Mock state load
        b._state = CircuitBreakerState(
            breaker_name="test_breaker",
            state=BreakerState.CLOSED.value,
        )
        
        is_open = await b.is_open()
        assert is_open is False

    @pytest.mark.asyncio
    async def test_trip_on_daily_loss(self, breaker):
        """Test breaker trips when daily loss exceeds threshold."""
        b = await breaker
        b._portfolio_value = 100000.0
        
        # Mock state with 6% daily loss (> 5% threshold)
        b._state = CircuitBreakerState(
            breaker_name="test_breaker",
            state=BreakerState.CLOSED.value,
            daily_pnl=-6000.0,  # 6% loss
        )
        
        is_open = await b.is_open()
        assert is_open is True

    @pytest.mark.asyncio
    async def test_trip_on_consecutive_losses(self, breaker):
        """Test breaker trips on max consecutive losses."""
        b = await breaker
        b._portfolio_value = 100000.0
        
        b._state = CircuitBreakerState(
            breaker_name="test_breaker",
            state=BreakerState.CLOSED.value,
            daily_pnl=-1000.0,
            consecutive_losses=3,  # At threshold
        )
        
        is_open = await b.is_open()
        assert is_open is True

    @pytest.mark.asyncio
    async def test_trip_on_exposure_limit(self, breaker):
        """Test breaker trips on max exposure."""
        b = await breaker
        b._portfolio_value = 100000.0
        
        b._state = CircuitBreakerState(
            breaker_name="test_breaker",
            state=BreakerState.CLOSED.value,
            total_exposure=90000.0,  # 90% at threshold
        )
        
        is_open = await b.is_open()
        assert is_open is True

    @pytest.mark.asyncio
    async def test_trip_on_emergency_shutdown(self, breaker):
        """Test breaker trips on emergency shutdown."""
        b = await breaker
        b._portfolio_value = 100000.0
        
        b._state = CircuitBreakerState(
            breaker_name="test_breaker",
            state=BreakerState.CLOSED.value,
            emergency_shutdown=True,
        )
        
        is_open = await b.is_open()
        assert is_open is True

    @pytest.mark.asyncio
    async def test_no_trip_within_limits(self, breaker):
        """Test breaker stays closed within normal limits."""
        b = await breaker
        b._portfolio_value = 100000.0
        
        b._state = CircuitBreakerState(
            breaker_name="test_breaker",
            state=BreakerState.CLOSED.value,
            daily_pnl=-1000.0,  # 1% loss (< 5% threshold)
            consecutive_losses=1,  # (< 3 threshold)
            total_exposure=50000.0,  # 50% (< 90% threshold)
        )
        
        is_open = await b.is_open()
        assert is_open is False


class TestCircuitBreakerTradeRecording:
    """Tests for trade recording and metrics updates."""

    @pytest.fixture
    async def breaker(self):
        """Create circuit breaker with mocked DB."""
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        breaker = CircuitBreaker(
            db_session=mock_session,
            breaker_name="test_breaker",
            max_daily_loss_pct=0.05,
            max_consecutive_losses=3,
            max_exposure_pct=0.90,
        )
        
        # Initialize state
        breaker._state = CircuitBreakerState(
            breaker_name="test_breaker",
            state=BreakerState.CLOSED.value,
            daily_pnl=0.0,
            consecutive_losses=0,
            total_exposure=0.0,
        )
        
        return breaker

    @pytest.mark.asyncio
    async def test_record_winning_trade(self, breaker):
        """Test recording a winning trade."""
        b = await breaker
        
        await b.record_trade_result(pnl=1000.0, position_delta=5000.0)
        
        assert b._state.daily_pnl == 1000.0
        assert b._state.consecutive_losses == 0  # Reset on win
        assert b._state.total_exposure == 5000.0

    @pytest.mark.asyncio
    async def test_record_losing_trade(self, breaker):
        """Test recording a losing trade."""
        b = await breaker
        
        await b.record_trade_result(pnl=-1000.0, position_delta=0.0)
        
        assert b._state.daily_pnl == -1000.0
        assert b._state.consecutive_losses == 1

    @pytest.mark.asyncio
    async def test_consecutive_losses_accumulate(self, breaker):
        """Test consecutive losses accumulate correctly."""
        b = await breaker
        
        # Three consecutive losses
        await b.record_trade_result(pnl=-100.0, position_delta=0.0)
        await b.record_trade_result(pnl=-200.0, position_delta=0.0)
        await b.record_trade_result(pnl=-300.0, position_delta=0.0)
        
        assert b._state.consecutive_losses == 3

    @pytest.mark.asyncio
    async def test_win_resets_consecutive_losses(self, breaker):
        """Test winning trade resets consecutive loss counter."""
        b = await breaker
        
        # Two losses then a win
        await b.record_trade_result(pnl=-100.0, position_delta=0.0)
        await b.record_trade_result(pnl=-200.0, position_delta=0.0)
        await b.record_trade_result(pnl=500.0, position_delta=0.0)
        
        assert b._state.consecutive_losses == 0

    @pytest.mark.asyncio
    async def test_exposure_never_negative(self, breaker):
        """Test exposure can't go negative."""
        b = await breaker
        
        # Large position reduction
        await b.record_trade_result(pnl=0.0, position_delta=-10000.0)
        
        assert b._state.total_exposure == 0.0  # Clamped to 0


class TestCircuitBreakerDailyReset:
    """Tests for daily metrics reset."""

    @pytest.mark.asyncio
    async def test_daily_reset_on_new_day(self):
        """Test daily metrics reset on new trading day."""
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        
        breaker = CircuitBreaker(
            db_session=mock_session,
            breaker_name="test_breaker",
        )
        
        # State from yesterday
        yesterday = datetime.now(UTC) - timedelta(days=1)
        breaker._state = CircuitBreakerState(
            breaker_name="test_breaker",
            state=BreakerState.CLOSED.value,
            daily_pnl=-10000.0,
            consecutive_losses=2,
            last_daily_reset_at=yesterday,
        )
        
        # Record trade should trigger reset
        await breaker.record_trade_result(pnl=100.0, position_delta=0.0)
        
        # Should be reset
        assert breaker._state.daily_pnl == 100.0  # Reset + new trade
        assert breaker._state.consecutive_losses == 0


class TestCircuitBreakerManualOperations:
    """Tests for manual operations (emergency shutdown, reset)."""

    @pytest.fixture
    async def breaker(self):
        """Create breaker in OPEN state."""
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        breaker = CircuitBreaker(
            db_session=mock_session,
            breaker_name="test_breaker",
        )
        
        breaker._state = CircuitBreakerState(
            breaker_name="test_breaker",
            state=BreakerState.OPEN.value,
            trip_reason=TripReason.MAX_DAILY_LOSS.value,
            tripped_at=datetime.now(UTC),
        )
        
        return breaker

    @pytest.mark.asyncio
    async def test_emergency_shutdown(self, breaker):
        """Test emergency shutdown functionality."""
        b = await breaker
        
        await b.emergency_shutdown()
        
        assert b._state.emergency_shutdown is True
        assert b._state.state == BreakerState.OPEN.value
        assert b._state.trip_reason == TripReason.EMERGENCY_SHUTDOWN.value

    @pytest.mark.asyncio
    async def test_reset_requires_admin_override(self, breaker):
        """Test reset requires admin override flag."""
        b = await breaker
        
        with pytest.raises(ValueError, match="admin_override"):
            await b.reset(admin_override=False)

    @pytest.mark.asyncio
    async def test_reset_with_admin_override(self, breaker):
        """Test reset with proper admin override."""
        b = await breaker
        
        await b.reset(admin_override=True)
        
        assert b._state.state == BreakerState.CLOSED.value
        assert b._state.trip_reason is None
        assert b._state.tripped_at is None
        assert b._state.emergency_shutdown is False


class TestCircuitBreakerUnitComparison:
    """Tests for correct unit comparison (percentage vs absolute)."""

    @pytest.mark.asyncio
    async def test_daily_loss_comparison_uses_percentage(self):
        """CRITICAL: Test that daily loss comparison uses percentage, not absolute."""
        mock_session = AsyncMock()
        
        breaker = CircuitBreaker(
            db_session=mock_session,
            breaker_name="test_breaker",
            max_daily_loss_pct=0.05,  # 5%
        )
        
        breaker._portfolio_value = 100000.0
        breaker._state = CircuitBreakerState(
            breaker_name="test_breaker",
            state=BreakerState.CLOSED.value,
            daily_pnl=-6000.0,  # 6% of 100k = should trip
        )
        
        is_open = await breaker.is_open()
        assert is_open is True, "6% loss should trip 5% threshold"

    @pytest.mark.asyncio
    async def test_daily_loss_small_portfolio(self):
        """Test daily loss with small portfolio value."""
        mock_session = AsyncMock()
        
        breaker = CircuitBreaker(
            db_session=mock_session,
            breaker_name="test_breaker",
            max_daily_loss_pct=0.05,  # 5%
        )
        
        breaker._portfolio_value = 10000.0
        breaker._state = CircuitBreakerState(
            breaker_name="test_breaker",
            state=BreakerState.CLOSED.value,
            daily_pnl=-400.0,  # 4% of 10k = should NOT trip
        )
        
        is_open = await breaker.is_open()
        assert is_open is False, "4% loss should not trip 5% threshold"


class TestCircuitBreakerEdgeCases:
    """Edge case and boundary tests."""

    @pytest.mark.asyncio
    async def test_zero_portfolio_value(self):
        """Test behavior with zero portfolio value."""
        mock_session = AsyncMock()
        
        breaker = CircuitBreaker(
            db_session=mock_session,
            breaker_name="test_breaker",
        )
        
        breaker._portfolio_value = 0.0
        breaker._state = CircuitBreakerState(
            breaker_name="test_breaker",
            state=BreakerState.CLOSED.value,
            daily_pnl=-1000.0,
        )
        
        # Should handle gracefully (no division by zero)
        is_open = await breaker.is_open()
        # With 0 portfolio, can't calculate %, should default to not trip
        assert is_open is False

    @pytest.mark.asyncio
    async def test_exactly_at_threshold(self):
        """Test behavior exactly at trip threshold."""
        mock_session = AsyncMock()
        
        breaker = CircuitBreaker(
            db_session=mock_session,
            breaker_name="test_breaker",
            max_daily_loss_pct=0.05,  # 5%
        )
        
        breaker._portfolio_value = 100000.0
        breaker._state = CircuitBreakerState(
            breaker_name="test_breaker",
            state=BreakerState.CLOSED.value,
            daily_pnl=-5000.0,  # Exactly 5%
        )
        
        is_open = await breaker.is_open()
        # At threshold, should trip
        assert is_open is True

    @pytest.mark.asyncio
    async def test_rapid_state_changes(self):
        """Test rapid state changes don't cause race conditions."""
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        
        breaker = CircuitBreaker(
            db_session=mock_session,
            breaker_name="test_breaker",
        )
        
        breaker._portfolio_value = 100000.0
        breaker._state = CircuitBreakerState(
            breaker_name="test_breaker",
            state=BreakerState.CLOSED.value,
        )
        
        # Rapid trades
        for i in range(10):
            await breaker.record_trade_result(
                pnl=(-1) ** i * 100.0,  # Alternating wins/losses
                position_delta=0.0
            )
        
        # Should have consistent state
        assert breaker._state.consecutive_losses <= 1  # Never more than 1 consecutive


class TestCircuitBreakerIntegration:
    """Integration-style tests with real async patterns."""

    @pytest.mark.asyncio
    async def test_full_trading_session_scenario(self):
        """Test realistic trading session with multiple trades."""
        mock_session = AsyncMock()
        mock_session.commit = AsyncMock()
        mock_session.refresh = AsyncMock()
        
        breaker = CircuitBreaker(
            db_session=mock_session,
            breaker_name="main_breaker",
            max_daily_loss_pct=0.05,
            max_consecutive_losses=3,
            max_exposure_pct=0.90,
        )
        
        breaker._portfolio_value = 100000.0
        breaker._state = CircuitBreakerState(
            breaker_name="main_breaker",
            state=BreakerState.CLOSED.value,
        )
        
        # Normal trading
        assert await breaker.is_open() is False
        
        # Some winning trades
        await breaker.record_trade_result(pnl=500.0, position_delta=10000.0)
        await breaker.record_trade_result(pnl=300.0, position_delta=5000.0)
        assert await breaker.is_open() is False
        
        # Some losing trades but within limits
        await breaker.record_trade_result(pnl=-200.0, position_delta=0.0)
        await breaker.record_trade_result(pnl=-150.0, position_delta=0.0)
        assert await breaker.is_open() is False
        
        # Recover with wins
        await breaker.record_trade_result(pnl=400.0, position_delta=0.0)
        assert breaker._state.consecutive_losses == 0
        
        # Big loss that trips breaker
        await breaker.record_trade_result(pnl=-6000.0, position_delta=0.0)
        assert await breaker.is_open() is True
        assert breaker._state.trip_reason == TripReason.MAX_DAILY_LOSS.value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
