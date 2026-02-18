import uuid
from datetime import datetime

import pytest
from pydantic import ValidationError

# We importeren de classes die we NOG NIET hebben gemaakt (TDD)
from backend.schemas.market_data import MarketTick
from backend.schemas.orders import OrderRequest, OrderSide, OrderType

# --- MARKET DATA TESTS ---


def test_market_tick_valid():
    """Happy Path: Valid market tick."""
    tick = MarketTick(
        symbol="BTC-EUR",
        price=50000.50,
        volume=1.5,
        timestamp=datetime.now(),
        source="revolut",
    )
    assert tick.symbol == "BTC-EUR"
    assert tick.price == 50000.50


def test_market_tick_negative_price():
    """Unhappy Path: Price cannot be negative."""
    with pytest.raises(ValidationError):
        MarketTick(
            symbol="BTC-EUR", price=-100.0, volume=1.0, timestamp=datetime.now()  # FOUT
        )


def test_market_tick_invalid_timestamp():
    """Unhappy Path: Invalid timestamp string."""
    with pytest.raises(ValidationError):
        MarketTick(
            symbol="BTC-EUR", price=100.0, volume=1.0, timestamp="niet-een-tijd"  # FOUT
        )


# --- ORDER REQUEST TESTS ---


def test_order_request_valid():
    """Happy Path: Valid order request."""
    order = OrderRequest(
        symbol="AAPL",
        qty=10.0,
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        strategy_id="momentum_v1",
    )
    assert order.qty == 10.0
    assert isinstance(order.client_order_id, uuid.UUID)  # Moet auto-generated zijn


def test_order_request_zero_qty():
    """Unhappy Path: Quantity must be positive."""
    with pytest.raises(ValidationError):
        OrderRequest(
            symbol="AAPL",
            qty=0.0,  # FOUT
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
        )


def test_order_request_limit_without_price():
    """Unhappy Path: Limit order requires limit_price."""
    # Dit is een business logic validatie die we in het model willen
    with pytest.raises(ValidationError, match="Limit price is required"):
        OrderRequest(
            symbol="AAPL",
            qty=1.0,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            limit_price=None,  # FOUT
        )
