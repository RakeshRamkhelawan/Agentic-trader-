import pytest

from backend.execution.shadow_portfolio import ShadowPortfolioManager
from backend.schemas.orders import OrderRequest, OrderSide, OrderStatus, OrderType


@pytest.fixture
def manager():
    return ShadowPortfolioManager(initial_cash=10000.0)


@pytest.mark.asyncio
async def test_buy_stock_decreases_cash(manager):
    """Happy Path: Kopen kost geld en geeft aandelen."""
    # Setup marktprijs (manager moet weten wat de prijs is)
    manager.update_price("AAPL", 150.0)

    order = OrderRequest(symbol="AAPL", qty=10, side=OrderSide.BUY, order_type=OrderType.MARKET)
    result = await manager.submit_order(order)

    assert result.status == OrderStatus.FILLED
    assert result.avg_price == 150.0

    # Cash: 10000 - (10 * 150) = 8500
    assert manager.cash_balance == 8500.0
    # Positie: +10
    assert manager.positions["AAPL"] == 10.0


@pytest.mark.asyncio
async def test_sell_stock_increases_cash(manager):
    """Happy Path: Verkopen geeft geld."""
    manager.update_price("AAPL", 150.0)
    # Eerst kopen
    await manager.submit_order(
        OrderRequest(symbol="AAPL", qty=10, side=OrderSide.BUY, order_type=OrderType.MARKET)
    )

    # Prijs stijgt
    manager.update_price("AAPL", 160.0)

    # Verkopen
    await manager.submit_order(
        OrderRequest(symbol="AAPL", qty=5, side=OrderSide.SELL, order_type=OrderType.MARKET)
    )

    # Cash: 8500 + (5 * 160) = 8500 + 800 = 9300
    assert manager.cash_balance == 9300.0
    assert manager.positions["AAPL"] == 5.0


@pytest.mark.asyncio
async def test_insufficient_funds(manager):
    """Unhappy Path: Niet genoeg geld."""
    manager.update_price("BTC", 50000.0)
    # Probeer 1 BTC te kopen met 10k cash
    order = OrderRequest(symbol="BTC", qty=1.0, side=OrderSide.BUY, order_type=OrderType.MARKET)

    result = await manager.submit_order(order)
    assert result.status == OrderStatus.REJECTED
    assert "Insufficient funds" in result.error_message
