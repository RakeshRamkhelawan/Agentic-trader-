import pytest
from httpx import AsyncClient

from backend.models.orders import Order, OrderStatus


@pytest.mark.asyncio
async def test_trading_api_endpoints(async_client: AsyncClient, db_session, test_user_token):
    headers = {"Authorization": f"Bearer {test_user_token}"}
    
    # 1. Setup: Create a dummy active order in DB
    order = Order(
        tenant_id="tenant-1",
        id="test-order-api",
        symbol="BTC-USD",
        side="buy",
        quantity=0.5,
        status=OrderStatus.SUBMITTED, # Correct Enum
        user_id="user-1"
    )
    db_session.add(order)
    await db_session.commit()
    
    # 2. Test GET /active
    resp = await async_client.get("/api/v1/trading/orders/active", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    
    # 3. Test DELETE /orders
    resp = await async_client.delete("/api/v1/trading/orders", headers=headers)
    assert resp.status_code == 200
    result = resp.json()
    assert result["status"] == "success" or result["status"] == "partial_success"
