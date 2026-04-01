import pytest

from backend.risk.validators import RiskValidator, RiskViolationError
from backend.schemas.orders import OrderRequest, OrderSide, OrderType

# --- CONFIG ---
MAX_ORDER_SIZE = 1000.0
MAX_DAILY_LOSS = 50.0


@pytest.fixture
def validator():
    return RiskValidator(max_order_size=MAX_ORDER_SIZE, max_daily_loss=MAX_DAILY_LOSS)


def test_validate_small_order(validator):
    """Happy Path: Kleine order mag door."""
    order = OrderRequest(
        symbol="BTC", qty=0.001, side=OrderSide.BUY, order_type=OrderType.MARKET
    )
    # Mock prijs = 50k -> Order = 50 euro -> OK
    validator.validate_order(order, current_price=50000.0)


def test_reject_fat_finger(validator):
    """Unhappy Path: Te grote order."""
    # 1 BTC = 50k > 1k limiet
    order = OrderRequest(
        symbol="BTC", qty=1.0, side=OrderSide.BUY, order_type=OrderType.MARKET
    )

    with pytest.raises(RiskViolationError, match="Order value .* exceeds limit"):
        validator.validate_order(order, current_price=50000.0)


def test_kill_switch(validator):
    """Unhappy Path: Kill Switch activeert."""
    validator.activate_kill_switch()

    order = OrderRequest(
        symbol="BTC", qty=0.001, side=OrderSide.BUY, order_type=OrderType.MARKET
    )

    with pytest.raises(RiskViolationError, match="KILL SWITCH ACTIVE"):
        validator.validate_order(order, current_price=50000.0)
