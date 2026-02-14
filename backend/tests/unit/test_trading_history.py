from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.models.orders import Order, OrderStatus
from backend.services.trading_service import TradingService


@pytest.mark.asyncio
async def test_get_order_history():
    service = TradingService()
    db = AsyncMock()
    
    # Mock DB result
    mock_order = MagicMock(spec=Order)
    mock_order.id = "order-hist-1"
    mock_order.symbol = "ETH-USD"
    mock_order.side = "sell"
    mock_order.status = OrderStatus.FILLED
    mock_order.created_at.isoformat.return_value = "2024-01-02T00:00:00"
    
    # Setup mock result
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_order]
    
    # db.execute is AsyncMock, returns coroutine that resolves to mock_result
    db.execute.return_value = mock_result
    
    orders = await service.get_order_history(db, "tenant-1", limit=10)
    
    assert len(orders) == 1
    assert orders[0]["order_id"] == "order-hist-1"
    assert orders[0]["status"] == OrderStatus.FILLED
