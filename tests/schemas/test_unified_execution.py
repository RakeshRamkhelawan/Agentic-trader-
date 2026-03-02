"""
Tests for Unified Execution Schema.

Week 1 of Exchange Integration Refactor.
"""

import pytest
from decimal import Decimal
from datetime import UTC, datetime

from backend.schemas.unified_execution import (
    UnifiedOrderRequest,
    UnifiedOrderResponse,
    Symbol,
    OrderSide,
    OrderType,
    TimeInForce,
    OrderStatus
)


class TestUnifiedOrderRequest:
    """Test UnifiedOrderRequest schema."""
    
    def test_basic_creation(self):
        """Test basic order creation."""
        order = UnifiedOrderRequest(
            trace_id="test-123",
            symbol="BTC/EUR",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal("0.1"),
            price=Decimal("45000"),
            expected_price=Decimal("45000")
        )
        
        assert order.symbol == "BTC/EUR"
        assert order.side == OrderSide.BUY
        assert order.quantity == Decimal("0.1")
        assert order.price == Decimal("45000")
    
    def test_decimal_precision(self):
        """Ensure Decimal maintains precision."""
        order = UnifiedOrderRequest(
            trace_id="test-123",
            symbol="BTC/EUR",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal("0.12345678901234"),
            price=Decimal("45000.12345678901234"),
            expected_price=Decimal("45000")
        )
        
        # Should maintain exact precision
        assert order.quantity == Decimal("0.12345678901234")
        assert order.price == Decimal("45000.12345678901234")
        
        # String representation should be exact
        assert str(order.quantity) == "0.12345678901234"
        assert str(order.price) == "45000.12345678901234"
    
    def test_no_float_precision_loss(self):
        """Demonstrate why we use Decimal instead of float."""
        # Float has precision issues
        float_qty = 0.1
        float_price = 45000.33
        float_result = float_qty * float_price
        # Result: 4500.032999999999 (precision loss!)
        
        # Decimal is exact
        decimal_qty = Decimal("0.1")
        decimal_price = Decimal("45000.33")
        decimal_result = decimal_qty * decimal_price
        # Result: Decimal('4500.033') (exact!)
        
        assert decimal_result == Decimal("4500.033")
    
    def test_limit_order_requires_price(self):
        """Validation: limit orders need price."""
        with pytest.raises(ValueError) as exc_info:
            UnifiedOrderRequest(
                trace_id="test-123",
                symbol="BTC/EUR",
                side=OrderSide.BUY,
                order_type=OrderType.LIMIT,
                quantity=Decimal("0.1"),
                expected_price=Decimal("45000")
                # Missing price!
            )
        assert "price" in str(exc_info.value).lower()
    
    def test_market_order_no_price(self):
        """Market orders should not have limit price."""
        order = UnifiedOrderRequest(
            trace_id="test-123",
            symbol="BTC/EUR",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("0.1"),
            expected_price=Decimal("45000")
        )
        
        assert order.price is None
        assert order.order_type == OrderType.MARKET
    
    def test_stop_order_requires_stop_price(self):
        """Stop orders require stop_price."""
        with pytest.raises(ValueError) as exc_info:
            UnifiedOrderRequest(
                trace_id="test-123",
                symbol="BTC/EUR",
                side=OrderSide.BUY,
                order_type=OrderType.STOP,
                quantity=Decimal("0.1"),
                expected_price=Decimal("45000")
                # Missing stop_price!
            )
        assert "stop" in str(exc_info.value).lower()
    
    def test_symbol_validation(self):
        """Symbol must be in BASE/QUOTE format."""
        # Valid symbols
        order1 = UnifiedOrderRequest(
            trace_id="test-123",
            symbol="BTC/EUR",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("0.1"),
            expected_price=Decimal("45000")
        )
        assert order1.symbol_base == "BTC"
        assert order1.symbol_quote == "EUR"
        
        # Invalid symbol format
        with pytest.raises(ValueError):
            UnifiedOrderRequest(
                trace_id="test-123",
                symbol="BTC-EUR",  # Wrong separator
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=Decimal("0.1"),
                expected_price=Decimal("45000")
            )
    
    def test_quantity_must_be_positive(self):
        """Quantity must be > 0."""
        with pytest.raises(ValueError):
            UnifiedOrderRequest(
                trace_id="test-123",
                symbol="BTC/EUR",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=Decimal("0"),  # Zero not allowed
                expected_price=Decimal("45000")
            )
        
        with pytest.raises(ValueError):
            UnifiedOrderRequest(
                trace_id="test-123",
                symbol="BTC/EUR",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=Decimal("-1"),  # Negative not allowed
                expected_price=Decimal("45000")
            )
    
    def test_immutability(self):
        """Order should be immutable (frozen)."""
        order = UnifiedOrderRequest(
            trace_id="test-123",
            symbol="BTC/EUR",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("0.1"),
            expected_price=Decimal("45000")
        )
        
        with pytest.raises(Exception):
            order.quantity = Decimal("0.2")  # Should fail
    
    def test_order_value_calculation(self):
        """Test order_value property."""
        order = UnifiedOrderRequest(
            trace_id="test-123",
            symbol="BTC/EUR",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal("0.1"),
            price=Decimal("45000"),
            expected_price=Decimal("45000")
        )
        
        assert order.order_value == Decimal("4500")
    
    def test_order_value_market_order(self):
        """Test order_value for market order (uses expected_price)."""
        order = UnifiedOrderRequest(
            trace_id="test-123",
            symbol="BTC/EUR",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=Decimal("0.1"),
            expected_price=Decimal("45000")
        )
        
        assert order.order_value == Decimal("4500")
    
    def test_to_decimal_string_dict(self):
        """Test serialization to string dict."""
        order = UnifiedOrderRequest(
            trace_id="test-123",
            symbol="BTC/EUR",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal("0.1"),
            price=Decimal("45000.50"),
            expected_price=Decimal("45000"),
            time_in_force=TimeInForce.GTC,
            post_only=True
        )
        
        d = order.to_decimal_string_dict()
        
        assert d["quantity"] == "0.1"
        assert d["price"] == "45000.50"
        assert d["side"] == "buy"
        assert d["time_in_force"] == "gtc"
        assert d["post_only"] is True


class TestUnifiedOrderRequestBackwardCompatibility:
    """Test backward compatibility features."""
    
    def test_from_legacy_float(self):
        """Create from legacy float-based order."""
        order = UnifiedOrderRequest.from_legacy_float(
            symbol="BTC/EUR",
            side="buy",
            qty=0.1,
            price=45000.33,
            expected_price=45000.33,
            trace_id="legacy-test"
        )
        
        # Should be Decimal, not float
        assert isinstance(order.quantity, Decimal)
        assert isinstance(order.price, Decimal)
        
        # Should maintain reasonable precision
        assert order.quantity == Decimal("0.1")
        assert order.price == Decimal("45000.33")
        assert order.side == OrderSide.BUY
        assert order.order_type == OrderType.LIMIT
    
    def test_from_legacy_float_market_order(self):
        """Create market order from legacy float."""
        order = UnifiedOrderRequest.from_legacy_float(
            symbol="BTC/EUR",
            side="sell",
            qty=0.5,
            price=None,  # No price = market order
            expected_price=44000.0,
            strategy_id="momentum_v1"
        )
        
        assert order.order_type == OrderType.MARKET
        assert order.price is None
        assert order.side == OrderSide.SELL
        assert order.strategy_id == "momentum_v1"
    
    def test_from_legacy_float_auto_trace_id(self):
        """Auto-generate trace_id if not provided."""
        order = UnifiedOrderRequest.from_legacy_float(
            symbol="BTC/EUR",
            side="buy",
            qty=0.1,
            expected_price=45000.0
        )
        
        assert order.trace_id.startswith("legacy-")
    
    def test_from_legacy_float_preserves_kwargs(self):
        """Additional kwargs are preserved."""
        order = UnifiedOrderRequest.from_legacy_float(
            symbol="BTC/EUR",
            side="buy",
            qty=0.1,
            price=45000.0,
            expected_price=45000.0,
            post_only=True,
            reduce_only=False,
            metadata={"key": "value"}
        )
        
        assert order.post_only is True
        assert order.reduce_only is False
        assert order.metadata == {"key": "value"}


class TestUnifiedOrderResponse:
    """Test UnifiedOrderResponse schema."""
    
    def test_basic_response(self):
        """Test basic response creation."""
        response = UnifiedOrderResponse(
            order_id="exch-123",
            client_order_id="client-456",
            status=OrderStatus.FILLED,
            filled_quantity=Decimal("0.1"),
            remaining_quantity=Decimal("0"),
            average_price=Decimal("45000")
        )
        
        assert response.is_filled is True
        assert response.is_open is False
        assert response.fill_percentage == 100
    
    def test_partial_fill(self):
        """Test partial fill response."""
        response = UnifiedOrderResponse(
            order_id="exch-123",
            client_order_id="client-456",
            status=OrderStatus.PARTIALLY_FILLED,
            filled_quantity=Decimal("0.05"),
            remaining_quantity=Decimal("0.05"),
            average_price=Decimal("45000")
        )
        
        assert response.is_filled is False
        assert response.is_open is True
        assert response.fill_percentage == 50
    
    def test_fill_percentage_zero(self):
        """Test fill percentage when nothing filled."""
        response = UnifiedOrderResponse(
            order_id="exch-123",
            client_order_id="client-456",
            status=OrderStatus.OPEN,
            filled_quantity=Decimal("0"),
            remaining_quantity=Decimal("0.1"),
            average_price=None
        )
        
        assert response.fill_percentage == 0
    
    def test_error_response(self):
        """Test rejected order response."""
        response = UnifiedOrderResponse(
            order_id="",
            client_order_id="client-456",
            status=OrderStatus.REJECTED,
            filled_quantity=Decimal("0"),
            remaining_quantity=Decimal("0.1"),
            error_message="Insufficient funds",
            raw_response={"error": "balance_too_low"}
        )
        
        assert response.status == OrderStatus.REJECTED
        assert response.error_message == "Insufficient funds"


class TestSymbol:
    """Test Symbol helper class."""
    
    def test_from_string_slash(self):
        """Parse symbol with slash."""
        sym = Symbol.from_string("BTC/EUR")
        assert sym.base == "BTC"
        assert sym.quote == "EUR"
        assert str(sym) == "BTC/EUR"
    
    def test_from_string_dash(self):
        """Parse symbol with dash."""
        sym = Symbol.from_string("BTC-EUR")
        assert sym.base == "BTC"
        assert sym.quote == "EUR"
    
    def test_from_string_underscore(self):
        """Parse symbol with underscore."""
        sym = Symbol.from_string("BTC_EUR")
        assert sym.base == "BTC"
        assert sym.quote == "EUR"
    
    def test_from_string_invalid(self):
        """Invalid format raises error."""
        with pytest.raises(ValueError):
            Symbol.from_string("BTCEUR")  # No separator
    
    def test_symbol_uppercase(self):
        """Symbol is normalized to uppercase."""
        sym = Symbol.from_string("btc/eur")
        assert sym.base == "BTC"
        assert sym.quote == "EUR"


class TestTimeInForce:
    """Test TimeInForce enum."""
    
    def test_time_in_force_values(self):
        """All TIF values present."""
        assert TimeInForce.GTC == "gtc"
        assert TimeInForce.IOC == "ioc"
        assert TimeInForce.FOK == "fok"
        assert TimeInForce.GTD == "gtd"
        assert TimeInForce.POST_ONLY == "post_only"


class TestOrderSide:
    """Test OrderSide enum."""
    
    def test_side_values(self):
        """Side enum values."""
        assert OrderSide.BUY == "buy"
        assert OrderSide.SELL == "sell"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
