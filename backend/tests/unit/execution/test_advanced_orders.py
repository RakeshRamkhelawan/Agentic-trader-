"""
Unit tests for Advanced Order Types (Sprint 3).
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.execution.advanced_orders import (
    AdvancedOrderManager,
    AdvancedOrderStatus,
    IcebergConfig,
    IcebergExecutor,
    StopLimitConfig,
    StopLimitExecutor,
    TWAPConfig,
    TWAPExecutor,
)
from backend.schemas.orders import OrderSide


@pytest.fixture
def mock_adapter():
    """Create a mock execution adapter."""
    adapter = AsyncMock()
    adapter.submit_order = AsyncMock(
        return_value=MagicMock(
            order_id="test-123",
            status="filled",
            filled_qty=1.0,
            avg_price=50000.0,
        )
    )
    adapter.get_ticker = AsyncMock(
        return_value={
            "last": 50000.0,
            "bid": 49900.0,
            "ask": 50100.0,
        }
    )
    return adapter


class TestIcebergExecutor:
    """Test cases for Iceberg orders."""

    @pytest.mark.asyncio
    async def test_iceberg_execution(self, mock_adapter):
        """Test basic iceberg execution."""
        config = IcebergConfig(
            total_quantity=10.0,
            visible_quantity=2.0,
        )

        executor = IcebergExecutor(
            symbol="BTC-EUR",
            side=OrderSide.BUY,
            config=config,
            adapter=mock_adapter,
        )

        results = await executor.execute()

        # Should execute 5 chunks of 2.0
        assert len(results) == 5
        assert executor.status == AdvancedOrderStatus.COMPLETED
        assert executor.filled_quantity == 10.0

    @pytest.mark.asyncio
    async def test_iceberg_cancel(self, mock_adapter):
        """Test iceberg cancellation."""
        config = IcebergConfig(total_quantity=100.0, visible_quantity=1.0)
        executor = IcebergExecutor("BTC-EUR", OrderSide.SELL, config, mock_adapter)

        # Cancel immediately
        await executor.cancel()

        # Start execution - should stop quickly
        asyncio.create_task(executor.execute())
        await asyncio.sleep(0.1)

        assert executor._cancelled
        assert executor.status == AdvancedOrderStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_iceberg_callback(self, mock_adapter):
        """Test iceberg callback mechanism."""
        callbacks = []

        def callback(result):
            callbacks.append(result)

        config = IcebergConfig(total_quantity=4.0, visible_quantity=2.0)
        executor = IcebergExecutor(
            "BTC-EUR", OrderSide.BUY, config, mock_adapter, callback
        )

        await executor.execute()

        assert len(callbacks) == 2  # 2 chunks


class TestTWAPExecutor:
    """Test cases for TWAP orders."""

    @pytest.mark.asyncio
    async def test_twap_execution(self, mock_adapter):
        """Test basic TWAP execution."""
        config = TWAPConfig(
            total_quantity=10.0,
            num_slices=5,
            duration_seconds=1,  # Short for testing
            randomize=False,
        )

        executor = TWAPExecutor(
            symbol="BTC-EUR",
            side=OrderSide.BUY,
            config=config,
            adapter=mock_adapter,
        )

        results = await executor.execute()

        # Should execute 5 slices
        assert len(results) == 5
        assert executor.status == AdvancedOrderStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_twap_with_randomization(self, mock_adapter):
        """Test TWAP with randomized intervals."""
        config = TWAPConfig(
            total_quantity=4.0,
            num_slices=2,
            duration_seconds=0.5,
            randomize=True,
        )

        executor = TWAPExecutor("BTC-EUR", OrderSide.SELL, config, mock_adapter)
        results = await executor.execute()

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_twap_cancel(self, mock_adapter):
        """Test TWAP cancellation."""
        config = TWAPConfig(total_quantity=100.0, num_slices=100, duration_seconds=10)
        executor = TWAPExecutor("BTC-EUR", OrderSide.BUY, config, mock_adapter)

        await executor.cancel()

        assert executor._cancelled


class TestStopLimitExecutor:
    """Test cases for Stop-Limit orders."""

    @pytest.mark.asyncio
    async def test_stop_limit_trigger_sell(self, mock_adapter):
        """Test sell stop-limit trigger."""
        config = StopLimitConfig(
            stop_price=49000.0,  # Trigger when price drops to this
            limit_price=48900.0,
            quantity=1.0,
        )

        executor = StopLimitExecutor(
            symbol="BTC-EUR",
            side=OrderSide.SELL,
            config=config,
            adapter=mock_adapter,
        )

        # Mock price below stop
        mock_adapter.get_ticker = AsyncMock(
            return_value={
                "last": 48000.0,  # Below stop price
            }
        )

        results = await executor.execute()

        assert executor._triggered
        assert len(results) == 1
        assert executor.status == AdvancedOrderStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_stop_limit_trigger_buy(self, mock_adapter):
        """Test buy stop-limit trigger."""
        config = StopLimitConfig(
            stop_price=51000.0,  # Trigger when price rises to this
            limit_price=51100.0,
            quantity=1.0,
        )

        executor = StopLimitExecutor(
            "BTC-EUR",
            side=OrderSide.BUY,
            config=config,
            adapter=mock_adapter,
        )

        # Mock price above stop
        mock_adapter.get_ticker = AsyncMock(
            return_value={
                "last": 52000.0,  # Above stop price
            }
        )

        results = await executor.execute()

        assert executor._triggered
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_trailing_stop_update(self, mock_adapter):
        """Test trailing stop price update."""
        config = StopLimitConfig(
            stop_price=50000.0,
            limit_price=49000.0,
            quantity=1.0,
            trailing_amount=1000.0,
        )

        executor = StopLimitExecutor("BTC-EUR", OrderSide.SELL, config, mock_adapter)

        # Simulate price rise
        executor._update_trailing_stop(51000.0)

        # Stop price should have moved up
        assert executor.config.stop_price > 50000.0

    @pytest.mark.asyncio
    async def test_stop_limit_cancel(self, mock_adapter):
        """Test stop-limit cancellation."""
        config = StopLimitConfig(stop_price=40000.0, limit_price=39000.0, quantity=1.0)
        executor = StopLimitExecutor("BTC-EUR", OrderSide.SELL, config, mock_adapter)

        await executor.cancel()

        assert executor._cancelled


class TestAdvancedOrderManager:
    """Test cases for AdvancedOrderManager."""

    @pytest.fixture
    def manager(self):
        return AdvancedOrderManager()

    @pytest.mark.asyncio
    async def test_submit_iceberg(self, manager, mock_adapter):
        """Test submitting iceberg order."""
        config = IcebergConfig(total_quantity=10.0, visible_quantity=2.0)

        order_id = await manager.submit_iceberg(
            "BTC-EUR", OrderSide.BUY, config, mock_adapter
        )

        assert order_id.startswith("adv_")
        assert order_id in manager._active_orders

    @pytest.mark.asyncio
    async def test_submit_twap(self, manager, mock_adapter):
        """Test submitting TWAP order."""
        config = TWAPConfig(total_quantity=5.0, num_slices=5, duration_seconds=1)

        order_id = await manager.submit_twap(
            "BTC-EUR", OrderSide.SELL, config, mock_adapter
        )

        assert order_id.startswith("adv_")
        assert order_id in manager._active_orders

    @pytest.mark.asyncio
    async def test_submit_stop_limit(self, manager, mock_adapter):
        """Test submitting stop-limit order."""
        config = StopLimitConfig(stop_price=49000.0, limit_price=48000.0, quantity=1.0)

        order_id = await manager.submit_stop_limit(
            "BTC-EUR", OrderSide.SELL, config, mock_adapter
        )

        assert order_id.startswith("adv_")
        assert order_id in manager._active_orders

    @pytest.mark.asyncio
    async def test_cancel_order(self, manager, mock_adapter):
        """Test cancelling order."""
        config = IcebergConfig(total_quantity=100.0, visible_quantity=1.0)
        order_id = await manager.submit_iceberg(
            "BTC-EUR", OrderSide.BUY, config, mock_adapter
        )

        result = await manager.cancel_order(order_id)

        assert result

    @pytest.mark.asyncio
    async def test_get_order_status(self, manager, mock_adapter):
        """Test getting order status."""
        config = IcebergConfig(total_quantity=4.0, visible_quantity=2.0)
        order_id = await manager.submit_iceberg(
            "BTC-EUR", OrderSide.BUY, config, mock_adapter
        )

        status = manager.get_order_status(order_id)

        assert status is not None
        assert isinstance(status, AdvancedOrderStatus)

    def test_get_active_orders(self, manager):
        """Test getting all active orders."""
        # Initially empty
        active = manager.get_active_orders()
        assert active == {}


class TestOrderConfigurations:
    """Test configuration dataclasses."""

    def test_iceberg_config(self):
        """Test IcebergConfig creation."""
        config = IcebergConfig(total_quantity=100.0, visible_quantity=10.0)

        assert config.total_quantity == 100.0
        assert config.visible_quantity == 10.0
        assert config.min_fill_quantity is None

    def test_twap_config(self):
        """Test TWAPConfig creation."""
        config = TWAPConfig(
            total_quantity=50.0,
            num_slices=10,
            duration_seconds=300,
            randomize=True,
        )

        assert config.total_quantity == 50.0
        assert config.num_slices == 10
        assert config.duration_seconds == 300
        assert config.randomize

    def test_stop_limit_config(self):
        """Test StopLimitConfig creation."""
        config = StopLimitConfig(
            stop_price=50000.0,
            limit_price=49000.0,
            quantity=1.0,
            trailing_amount=1000.0,
        )

        assert config.stop_price == 50000.0
        assert config.limit_price == 49000.0
        assert config.quantity == 1.0
        assert config.trailing_amount == 1000.0


class TestPerformanceBenchmarks:
    """Performance benchmarks for advanced orders."""

    @pytest.mark.asyncio
    async def test_iceberg_execution_time(self, mock_adapter):
        """Benchmark iceberg execution overhead."""
        config = IcebergConfig(total_quantity=4.0, visible_quantity=2.0)
        executor = IcebergExecutor("BTC-EUR", OrderSide.BUY, config, mock_adapter)

        import time

        start = time.perf_counter()

        await executor.execute()

        elapsed = time.perf_counter() - start

        print(f"\nIceberg execution time: {elapsed*1000:.2f}ms")

        # Should be < 100ms for 2 chunks
        assert elapsed < 0.1

    @pytest.mark.asyncio
    async def test_twap_execution_time(self, mock_adapter):
        """Benchmark TWAP execution."""
        config = TWAPConfig(total_quantity=4.0, num_slices=2, duration_seconds=0.2)
        executor = TWAPExecutor("BTC-EUR", OrderSide.BUY, config, mock_adapter)

        import time

        start = time.perf_counter()

        await executor.execute()

        elapsed = time.perf_counter() - start

        print(f"\nTWAP execution time: {elapsed*1000:.2f}ms")

        # Should complete in ~200ms + overhead
        assert elapsed < 0.5
