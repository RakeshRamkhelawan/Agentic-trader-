from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.execution.smart_order_router import (NoRouteFoundError,
                                                  SmartOrderRouter)
from backend.schemas.orders import OrderRequest, OrderSide, OrderType


# Mock adapters
@pytest.fixture
def revolut_adapter():
    adapter = MagicMock()
    adapter.submit_order = AsyncMock(return_value="REV_123")
    return adapter

@pytest.fixture
def ibkr_adapter():
    adapter = MagicMock()
    adapter.submit_order = AsyncMock(return_value="IB_456")
    return adapter

@pytest.mark.asyncio
async def test_route_crypto_to_revolut(revolut_adapter, ibkr_adapter):
    """Happy Path: Crypto pairs gaan naar Revolut."""
    sor = SmartOrderRouter()
    sor.register_adapter("revolut", revolut_adapter, ["BTC-EUR", "ETH-EUR"])
    sor.register_adapter("ibkr", ibkr_adapter, ["AAPL", "TSLA"])
    
    order = OrderRequest(symbol="BTC-EUR", qty=1.0, side=OrderSide.BUY, order_type=OrderType.MARKET)
    
    # Act
    result = await sor.route_and_execute(order)
    
    # Assert
    assert result == "REV_123"
    revolut_adapter.submit_order.assert_called_once()
    ibkr_adapter.submit_order.assert_not_called()

@pytest.mark.asyncio
async def test_route_stock_to_ibkr(revolut_adapter, ibkr_adapter):
    """Happy Path: Stocks gaan naar IBKR."""
    sor = SmartOrderRouter()
    sor.register_adapter("revolut", revolut_adapter, ["BTC-EUR"])
    sor.register_adapter("ibkr", ibkr_adapter, ["AAPL"])
    
    order = OrderRequest(symbol="AAPL", qty=10, side=OrderSide.BUY, order_type=OrderType.MARKET)
    
    await sor.route_and_execute(order)
    
    ibkr_adapter.submit_order.assert_called_once()

@pytest.mark.asyncio
async def test_no_route_found():
    """Unhappy Path: Onbekend symbool gooit error."""
    sor = SmartOrderRouter()
    # Geen adapters
    
    order = OrderRequest(symbol="UNKNOWN", qty=1, side=OrderSide.BUY, order_type=OrderType.MARKET)
    
    with pytest.raises(NoRouteFoundError):
        await sor.route_and_execute(order)
