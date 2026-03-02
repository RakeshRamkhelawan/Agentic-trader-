"""
Unit tests for Smart Order Router with Circuit Breaker.
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.execution.smart_order_router import (
    CircuitBreakerState,
    ExchangeCircuitBreaker,
    NoRouteFoundError,
    SmartOrderRouter,
)
from backend.schemas.orders import OrderRequest, OrderSide


@pytest.fixture
def mock_adapter():
    """Create a mock execution adapter."""
    adapter = AsyncMock()
    adapter.get_ticker = AsyncMock(return_value={"bid": 50000, "ask": 50100, "volume": 1000})
    adapter.submit_order = AsyncMock(
        return_value=MagicMock(
            order_id="test-123", status="filled", filled_qty=1.0, avg_price=50050
        )
    )
    return adapter


@pytest.fixture
def failing_adapter():
    """Create a mock adapter that always fails."""
    adapter = AsyncMock()
    adapter.get_ticker = AsyncMock(side_effect=Exception("Connection error"))
    adapter.submit_order = AsyncMock(side_effect=Exception("Connection error"))
    return adapter


@pytest.fixture
def router_with_circuit_breaker(mock_adapter):
    """Create a router with circuit breaker enabled."""
    router = SmartOrderRouter(enable_circuit_breaker=True)
    router.register_adapter(
        "bitvavo",
        mock_adapter,
        supported_symbols=["BTC-EUR", "ETH-EUR"],
        failure_threshold=5,
        recovery_timeout=0.1,  # Short timeout for testing
    )
    return router


class TestExchangeCircuitBreaker:
    """Test cases for ExchangeCircuitBreaker."""

    def test_initial_state(self):
        """Test initial state is CLOSED."""
        cb = ExchangeCircuitBreaker("test_exchange")
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.can_execute() is True

    def test_failure_counting(self):
        """Test failure counting."""
        cb = ExchangeCircuitBreaker("test_exchange", failure_threshold=3)

        # Record 2 failures - should still be CLOSED
        cb.record_failure()
        cb.record_failure()
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 2

        # 3rd failure - should OPEN
        cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN
        assert cb.can_execute() is False

    def test_success_resets_failures(self):
        """Test that success resets failure count in CLOSED state."""
        cb = ExchangeCircuitBreaker("test_exchange")

        cb.record_failure()
        cb.record_failure()
        assert cb.failure_count == 2

        cb.record_success()
        assert cb.failure_count == 0

    def test_recovery_timeout(self):
        """Test recovery timeout transitions to HALF_OPEN."""
        cb = ExchangeCircuitBreaker("test_exchange", failure_threshold=1, recovery_timeout=0.01)

        # Open the circuit
        cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN
        assert cb.can_execute() is False

        # Wait for recovery timeout
        time.sleep(0.02)

        # Should now allow execution (HALF_OPEN)
        assert cb.can_execute() is True
        assert cb.state == CircuitBreakerState.HALF_OPEN

    def test_half_open_success_closes(self):
        """Test that successes in HALF_OPEN close the circuit."""
        cb = ExchangeCircuitBreaker(
            "test_exchange", failure_threshold=1, recovery_timeout=0.01, success_threshold=2
        )

        # Open and transition to half-open
        cb.record_failure()
        time.sleep(0.02)
        cb.can_execute()  # Transition to half-open

        assert cb.state == CircuitBreakerState.HALF_OPEN

        # Record successes
        cb.record_success()
        assert cb.state == CircuitBreakerState.HALF_OPEN  # Need 2 successes

        cb.record_success()
        assert cb.state == CircuitBreakerState.CLOSED

    def test_half_open_failure_reopens(self):
        """Test that failure in HALF_OPEN reopens the circuit."""
        cb = ExchangeCircuitBreaker("test_exchange", failure_threshold=1, recovery_timeout=0.01)

        # Open and transition to half-open
        cb.record_failure()
        time.sleep(0.02)
        cb.can_execute()

        assert cb.state == CircuitBreakerState.HALF_OPEN

        # Failure should reopen
        cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN

    def test_half_open_max_calls(self):
        """Test that half_open limits concurrent test calls."""
        cb = ExchangeCircuitBreaker(
            "test_exchange", failure_threshold=1, recovery_timeout=0.01, half_open_max_calls=2
        )

        # Open and transition to half-open
        cb.record_failure()
        time.sleep(0.02)

        # First 2 calls should succeed
        assert cb.can_execute() is True
        assert cb.can_execute() is True

        # 3rd call should fail (max reached)
        assert cb.can_execute() is False

    def test_get_metrics(self):
        """Test metrics collection."""
        cb = ExchangeCircuitBreaker("test_exchange")
        cb.record_failure()

        metrics = cb.get_metrics()

        assert metrics["exchange"] == "test_exchange"
        assert metrics["state"] == "closed"
        assert metrics["failure_count"] == 1


class TestSmartOrderRouterCircuitBreaker:
    """Test cases for SmartOrderRouter with Circuit Breaker."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_created_on_registration(self, mock_adapter):
        """Test that circuit breaker is created when adapter is registered."""
        router = SmartOrderRouter(enable_circuit_breaker=True)
        router.register_adapter("bitvavo", mock_adapter, ["BTC-EUR"])

        cb = router.get_circuit_breaker("bitvavo")
        assert cb is not None
        assert cb.exchange == "bitvavo"

    @pytest.mark.asyncio
    async def test_circuit_breaker_skipped_when_disabled(self, mock_adapter):
        """Test that circuit breaker is not created when disabled."""
        router = SmartOrderRouter(enable_circuit_breaker=False)
        router.register_adapter("bitvavo", mock_adapter, ["BTC-EUR"])

        cb = router.get_circuit_breaker("bitvavo")
        assert cb is None

    @pytest.mark.asyncio
    async def test_successful_call_records_success(self, router_with_circuit_breaker, mock_adapter):
        """Test that successful calls record success for circuit breaker."""
        router = router_with_circuit_breaker

        prices = await router.get_best_prices("BTC-EUR")

        assert "bitvavo" in prices

        cb = router.get_circuit_breaker("bitvavo")
        assert cb.failure_count == 0  # Success should reset failures

    @pytest.mark.asyncio
    async def test_failed_call_records_failure(self, failing_adapter):
        """Test that failed calls record failure for circuit breaker."""
        router = SmartOrderRouter(enable_circuit_breaker=True)
        router.register_adapter(
            "failing_exchange", failing_adapter, ["BTC-EUR"], failure_threshold=5
        )

        # First call will fail
        prices = await router.get_best_prices("BTC-EUR")

        assert "failing_exchange" not in prices

        cb = router.get_circuit_breaker("failing_exchange")
        assert cb.failure_count == 1

    @pytest.mark.asyncio
    async def test_circuit_opens_after_threshold(self, failing_adapter):
        """Test that circuit opens after failure threshold."""
        router = SmartOrderRouter(enable_circuit_breaker=True)
        router.register_adapter(
            "failing_exchange", failing_adapter, ["BTC-EUR"], failure_threshold=3
        )

        # Make 3 failing calls
        for _ in range(3):
            await router.get_best_prices("BTC-EUR")

        cb = router.get_circuit_breaker("failing_exchange")
        assert cb.state == CircuitBreakerState.OPEN
        assert cb.can_execute() is False

    @pytest.mark.asyncio
    async def test_open_circuit_skips_exchange(self, failing_adapter):
        """Test that open circuit causes exchange to be skipped."""
        router = SmartOrderRouter(enable_circuit_breaker=True)
        router.register_adapter(
            "failing_exchange", failing_adapter, ["BTC-EUR"], failure_threshold=1
        )

        # Open the circuit
        await router.get_best_prices("BTC-EUR")

        # Next call should skip the failing exchange
        prices = await router.get_best_prices("BTC-EUR", skip_unhealthy=True)

        assert "failing_exchange" not in prices

    @pytest.mark.asyncio
    async def test_failover_to_healthy_exchange(self, mock_adapter, failing_adapter):
        """Test automatic failover to healthy exchange."""
        router = SmartOrderRouter(enable_circuit_breaker=True)

        # Register failing exchange first
        router.register_adapter(
            "failing_exchange", failing_adapter, ["BTC-EUR"], failure_threshold=1
        )

        # Register healthy exchange
        router.register_adapter("healthy_exchange", mock_adapter, ["BTC-EUR"], failure_threshold=5)

        # Open the failing circuit
        await router.get_best_prices("BTC-EUR")

        # Route order - should failover to healthy exchange
        order = OrderRequest(symbol="BTC-EUR", side=OrderSide.BUY, order_type="market", qty=1.0)

        results = await router.route_order(order, use_vwap=False)

        assert len(results) == 1
        # Should have used healthy exchange (failing is OPEN)
        mock_adapter.submit_order.assert_called_once()

    @pytest.mark.asyncio
    async def test_all_exchanges_unhealthy_raises_error(self, failing_adapter):
        """Test that error is raised when all exchanges are unhealthy."""
        router = SmartOrderRouter(enable_circuit_breaker=True)
        router.register_adapter(
            "failing_exchange", failing_adapter, ["BTC-EUR"], failure_threshold=1
        )

        # Open the circuit
        await router.get_best_prices("BTC-EUR")

        order = OrderRequest(symbol="BTC-EUR", side=OrderSide.BUY, order_type="market", qty=1.0)

        with pytest.raises(NoRouteFoundError, match="All execution adapters failed"):
            await router.route_and_execute(order)

    @pytest.mark.asyncio
    async def test_get_all_circuit_breaker_metrics(self, router_with_circuit_breaker):
        """Test collecting metrics from all circuit breakers."""
        router = router_with_circuit_breaker

        metrics = router.get_all_circuit_breaker_metrics()

        assert "bitvavo" in metrics
        assert metrics["bitvavo"]["state"] == "closed"
        assert metrics["bitvavo"]["exchange"] == "bitvavo"

    @pytest.mark.asyncio
    async def test_execution_failure_records_circuit_breaker(self, mock_adapter):
        """Test that execution failure records in circuit breaker."""
        # Make submit_order fail
        mock_adapter.submit_order = AsyncMock(side_effect=Exception("Execution failed"))

        router = SmartOrderRouter(enable_circuit_breaker=True)
        router.register_adapter("failing_exec", mock_adapter, ["BTC-EUR"], failure_threshold=5)

        order = OrderRequest(symbol="BTC-EUR", side=OrderSide.BUY, order_type="market", qty=1.0)

        try:
            await router.route_and_execute(order)
        except NoRouteFoundError:
            pass

        cb = router.get_circuit_breaker("failing_exec")
        assert cb.failure_count == 1


class TestCircuitBreakerPerformance:
    """Performance tests for circuit breaker (must be < 10μs)."""

    def test_circuit_breaker_check_latency(self):
        """Test that circuit breaker check is ultra-fast."""
        cb = ExchangeCircuitBreaker("test_exchange")

        import time

        start = time.perf_counter()

        # Run 1000 checks
        for _ in range(1000):
            cb.can_execute()

        elapsed = time.perf_counter() - start
        avg_latency = elapsed / 1000

        # Should be less than 10 microseconds on average
        assert avg_latency < 10e-6, f"Average latency {avg_latency}s exceeds 10μs"
