from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.models.orders import Order, OrderStatus
from backend.services.trading_service import TradingService


@pytest.mark.asyncio
async def test_get_active_orders():
    service = TradingService()
    db = AsyncMock()
    
    # Mock DB result
    mock_order = MagicMock(spec=Order)
    mock_order.id = "order-123"
    mock_order.symbol = "BTC-USD"
    mock_order.side = "buy"
    mock_order.quantity = 1.0
    mock_order.filled_qty = 0.0
    mock_order.status = OrderStatus.SUBMITTED # Valid status
    mock_order.created_at.isoformat.return_value = "2024-01-01T00:00:00"
    
    db.execute.return_value.scalars.return_value.all.return_value = [mock_order]
    
    orders = await service.get_active_orders(db, "tenant-1")
    
    assert len(orders) == 1
    assert orders[0]["order_id"] == "order-123"
    assert orders[0]["status"] == OrderStatus.SUBMITTED

@pytest.mark.asyncio
async def test_cancel_all_orders():
    service = TradingService()
    db = AsyncMock()
    
    # Mock active orders
    mock_order = MagicMock(spec=Order)
    mock_order.id = "order-123"
    mock_order.symbol = "BTC-USD"
    mock_order.status = OrderStatus.SUBMITTED
    
    db.execute.return_value.scalars.return_value.all.return_value = [mock_order]
    
    # Mock settings and adapter
    service.settings_service = AsyncMock()
    service.settings_service.get_user_preferences.return_value.default_exchange = "binance"
    
    mock_adapter = AsyncMock()
    mock_adapter.cancel_order = AsyncMock() # Ensure method is async
    service._get_exchange_adapter = AsyncMock(return_value=mock_adapter)
    
    result = await service.cancel_all_orders(db, "tenant-1")
    
    assert result["status"] == "success"
    assert result["cancelled_count"] == 1
    
    # Check if adapter.cancel_order was called
    # Since we mocked _get_exchange_adapter to return a mock, we need to ensure the mock method is async compatible
    # or just check call args if we didn't await it (but we did).
    
    # In valid async test with AsyncMock:
    mock_adapter.cancel_order.assert_awaited_once_with("order-123", "BTC-USD")
    assert mock_order.status == OrderStatus.CANCELLED
