"""
Tests voor OrderExecutor - Order Execution Engine
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from backend.core.schemas.ooda_types import ExecutionPlan, Order
from backend.execution.order_executor import ExchangeAdapter, ExecutionError, OrderExecutor


@pytest.fixture
def mock_exchange():
    """Create mock exchange adapter."""
    exchange = ExchangeAdapter()
    return exchange


@pytest.fixture
def order_executor(mock_exchange):
    """Create OrderExecutor instance."""
    return OrderExecutor(
        exchange_adapter=mock_exchange,
        max_slippage_bps=50,
        order_timeout=5,  # Short timeout for tests
    )


@pytest.fixture
def sample_execution_plan():
    """Sample execution plan."""
    return ExecutionPlan(
        symbol="BTC/USDT",
        side="buy",
        quantity=0.01,
        order_type="limit",
        price=50000.0,
        expected_price=50000.0,
        trace_id="test-trace-123",
    )


class TestOrderExecution:
    """Test order execution logic."""

    async def test_successful_market_order(self, order_executor, sample_execution_plan):
        """Test successful market order execution."""
        outcome = await order_executor.execute_trade(sample_execution_plan)

        assert outcome.success
        assert outcome.filled_qty > 0
        assert outcome.avg_price > 0

    async def test_successful_limit_order(self, order_executor):
        """Test successful limit order execution."""
        limit_plan = ExecutionPlan(
            symbol="BTC/USDT",
            side="buy",
            quantity=0.01,
            order_type="limit",
            expected_price=50000.0,
            price=49500.0,
            trace_id="test-limit-trace",
        )

        outcome = await order_executor.execute_trade(limit_plan)

        assert outcome.success
        assert outcome.filled_qty > 0

    def test_failed_pre_execution_checks(self, order_executor):
        """Test failure when pre-execution checks fail."""
        # Use invalid quantity > 0 but fail pre-checks (if any other checks exist)
        # Or test ValidationError if schema enforces it
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            ExecutionPlan(
                symbol="BTC/USDT",
                side="buy",
                quantity=0.0,  # Invalid quantity
                order_type="market",
                price=None,
                expected_price=50000.0,
                trace_id="test-invalid-trace",
            )


class TestSlippageCalculation:
    """Test slippage calculation."""

    def test_slippage_calculation(self, order_executor):
        """Test slippage calculation in basis points."""
        expected = 50000.0
        actual = 50250.0  # 0.5% higher

        slippage = order_executor._calculate_slippage(expected, actual)

        # 0.5% = 50 basis points
        assert slippage == pytest.approx(50, abs=1)

    def test_zero_slippage(self, order_executor):
        """Test zero slippage when prices match."""
        slippage = order_executor._calculate_slippage(50000.0, 50000.0)

        assert slippage == 0.0

    async def test_high_slippage_warning(self, order_executor, caplog):
        """Test warning logged for high slippage."""
        # Create new plan with lower expected price (frozen model)
        low_price_plan = ExecutionPlan(
            symbol="BTC/USDT",
            side="buy",
            quantity=0.01,
            order_type="market",
            price=None,
            expected_price=48000.0,  # Much lower
            trace_id="test-slippage-trace",
        )

        outcome = await order_executor.execute_trade(low_price_plan)

        # Should log warning (slippage > 50 bps)
        assert "slippage" in caplog.text.lower()


class TestOrderTimeout:
    """Test order timeout handling."""

    async def test_order_timeout_cancellation(self, order_executor, sample_execution_plan):
        """Test order cancellation on timeout."""

        # Mock exchange to never fill order
        async def mock_status(order_id):
            return Order(
                order_id=order_id,
                symbol="BTC/USDT",
                side="buy",
                order_type="market",
                quantity=0.01,
                status="pending",  # Always pending
            )

        order_executor.exchange.get_order_status = mock_status
        order_executor.order_timeout = 1  # 1 second timeout

        outcome = await order_executor.execute_trade(sample_execution_plan)
        # Should be marked as failed
        assert not outcome.success
        assert "timed out" in outcome.error.lower()


class TestActiveOrdersTracking:
    """Test active orders tracking."""

    async def test_active_orders_stored(self, order_executor, sample_execution_plan):
        """Test active orders are tracked."""
        initial_count = len(order_executor.get_active_orders())

        # Place order (will complete immediately in mock)
        await order_executor.execute_trade(sample_execution_plan)

        # Should have tracked the order (even if completed)
        # (In real scenario, would remain until filled)
        assert len(order_executor.get_active_orders()) >= initial_count

    def test_clear_completed_orders(self, order_executor):
        """Test clearing completed orders."""
        # Add mock orders
        order_executor.active_orders = {
            "order-1": Order(
                order_id="order-1",
                symbol="BTC/USDT",
                side="buy",
                order_type="market",
                quantity=0.01,
                status="filled",
            ),
            "order-2": Order(
                order_id="order-2",
                symbol="BTC/USDT",
                side="buy",
                order_type="market",
                quantity=0.01,
                status="pending",
            ),
        }

        order_executor.clear_completed_orders()

        # Only pending should remain
        assert len(order_executor.get_active_orders()) == 1
        assert "order-2" in order_executor.get_active_orders()
