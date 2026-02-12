import pytest
from httpx import AsyncClient
from backend.models.orders import Order, OrderStatus

@pytest.mark.asyncio
async def test_order_history_endpoint(async_client: AsyncClient, db_session, test_user_token):
    headers = {"Authorization": f"Bearer {test_user_token}"}
    
    # Setup: Create a historical order
    order = Order(
        tenant_id="tenant-1",
        id="test-hist-order",
        symbol="BTC-USD",
        side="buy",
        quantity=0.1,
        status=OrderStatus.FILLED,
        user_id="user-1"
    )
    db_session.add(order)
    await db_session.commit()
    
    # Test GET /history
    resp = await async_client.get("/api/v1/trading/orders/history?limit=5", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["status"] == "FILLED"
