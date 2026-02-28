"""
Unified Execution Schema for Agentic Trader Platform.

This module provides a unified order schema that bridges:
- OODA ExecutionPlan (existing)
- schemas/orders.OrderRequest (existing)
- exchange/base_exchange.OrderRequest (new)

Key features:
- Decimal precision for all financial values
- Time in force support (GTC/IOC/FOK)
- Post-only and reduce-only flags
- Audit fields (trace_id, strategy_id)
- Backward compatibility with float conversion

Week 1 of Exchange Integration Refactor.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class OrderSide(str, Enum):
    """Order side enumeration."""
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """Order type enumeration."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class TimeInForce(str, Enum):
    """Time in force enumeration."""
    GTC = "gtc"           # Good Till Cancelled
    IOC = "ioc"           # Immediate Or Cancel
    FOK = "fok"           # Fill Or Kill
    GTD = "gtd"           # Good Till Date
    POST_ONLY = "post_only"


class OrderStatus(str, Enum):
    """Order status enumeration."""
    PENDING = "pending"
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class UnifiedOrderRequest(BaseModel):
    """
    Unified order request schema.

    Combines best features from existing schemas:
    - Decimal precision (from exchange/)
    - Audit fields (from OODA)
    - Validation (from schemas/orders)

    Example:
        >>> order = UnifiedOrderRequest(
        ...     trace_id="trace-123",
        ...     symbol="BTC/EUR",
        ...     side=OrderSide.BUY,
        ...     order_type=OrderType.LIMIT,
        ...     quantity=Decimal("0.1"),
        ...     price=Decimal("45000.50"),
        ...     expected_price=Decimal("45000"),
        ...     time_in_force=TimeInForce.GTC,
        ...     post_only=True
        ... )
    """

    # Identification
    client_order_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique client order ID"
    )
    trace_id: str = Field(
        ...,
        description="Distributed trace ID for audit logging"
    )

    # Symbol (unified format: BASE/QUOTE)
    symbol: str = Field(
        ...,
        pattern=r"^[A-Z0-9]+/[A-Z0-9]+$",
        description="Trading pair in BASE/QUOTE format (e.g., BTC/EUR)"
    )

    # Order details
    side: OrderSide = Field(..., description="Order side (buy/sell)")
    order_type: OrderType = Field(..., description="Order type (market/limit/stop)")

    # Financial values as Decimal (CRITICAL for precision)
    quantity: Decimal = Field(
        ...,
        gt=0,
        description="Order quantity as Decimal for precision"
    )
    price: Decimal | None = Field(
        None,
        gt=0,
        description="Limit price (None for market orders)"
    )
    stop_price: Decimal | None = Field(
        None,
        gt=0,
        description="Stop price for stop orders"
    )
    expected_price: Decimal = Field(
        ...,
        gt=0,
        description="Expected fill price for slippage calculation"
    )

    # Advanced options (from exchange/)
    time_in_force: TimeInForce = Field(
        default=TimeInForce.GTC,
        description="Order time in force"
    )
    post_only: bool = Field(
        default=False,
        description="Post-only flag (fail if would take liquidity)"
    )
    reduce_only: bool = Field(
        default=False,
        description="Reduce-only flag (only reduce position)"
    )

    # OODA integration fields
    strategy_id: str | None = Field(
        default="manual",
        description="Strategy identifier for audit trail"
    )
    caller_name: str = Field(
        default="unknown",
        description="Agent or service requesting execution"
    )
    caller_role: str = Field(
        default="untrusted",
        description="Security role of caller"
    )

    # Metadata for extensibility
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Exchange-specific parameters"
    )

    model_config = ConfigDict(frozen=True, validate_assignment=True)

    @model_validator(mode="after")
    def validate_limit_order_has_price(self) -> UnifiedOrderRequest:
        """Ensure limit orders have a price."""
        if self.order_type in (OrderType.LIMIT, OrderType.STOP_LIMIT):
            if self.price is None:
                raise ValueError("Limit orders require a price")
        return self

    @model_validator(mode="after")
    def validate_stop_order_has_stop_price(self) -> UnifiedOrderRequest:
        """Ensure stop orders have a stop price."""
        if self.order_type in (OrderType.STOP, OrderType.STOP_LIMIT):
            if self.stop_price is None:
                raise ValueError("Stop orders require a stop_price")
        return self

    @model_validator(mode="after")
    def validate_market_order_no_price(self) -> UnifiedOrderRequest:
        """Ensure market orders don't have limit price."""
        if self.order_type == OrderType.MARKET:
            if self.price is not None:
                raise ValueError("Market orders should not have a limit price")
        return self

    @property
    def order_value(self) -> Decimal:
        """Calculate order value (quantity * price)."""
        if self.price is None:
            return self.quantity * self.expected_price
        return self.quantity * self.price

    @property
    def symbol_base(self) -> str:
        """Extract base asset from symbol (e.g., BTC from BTC/EUR)."""
        return self.symbol.split("/")[0]

    @property
    def symbol_quote(self) -> str:
        """Extract quote asset from symbol (e.g., EUR from BTC/EUR)."""
        return self.symbol.split("/")[1]

    def to_decimal_string_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary with Decimals as strings.

        Useful for JSON serialization where Decimal isn't supported.
        """
        return {
            "client_order_id": self.client_order_id,
            "trace_id": self.trace_id,
            "symbol": self.symbol,
            "side": self.side.value,
            "order_type": self.order_type.value,
            "quantity": str(self.quantity),
            "price": str(self.price) if self.price else None,
            "stop_price": str(self.stop_price) if self.stop_price else None,
            "expected_price": str(self.expected_price),
            "time_in_force": self.time_in_force.value,
            "post_only": self.post_only,
            "reduce_only": self.reduce_only,
            "strategy_id": self.strategy_id,
            "caller_name": self.caller_name,
            "caller_role": self.caller_role,
            "metadata": self.metadata
        }

    @classmethod
    def from_legacy_float(
        cls,
        symbol: str,
        side: str,
        qty: float,
        price: float | None = None,
        expected_price: float | None = None,
        trace_id: str | None = None,
        strategy_id: str = "manual",
        **kwargs
    ) -> UnifiedOrderRequest:
        """
        Create from legacy float-based order (backward compatibility).

        WARNING: This converts float to Decimal which may have precision
        limitations. Use only during transition period.

        Args:
            symbol: Trading pair (e.g., "BTC/EUR")
            side: "buy" or "sell"
            qty: Order quantity (float)
            price: Limit price (float, None for market)
            expected_price: Expected fill price (float)
            trace_id: Trace ID (generated if None)
            strategy_id: Strategy identifier
            **kwargs: Additional fields

        Returns:
            UnifiedOrderRequest with Decimal fields
        """
        # Convert via string to minimize floating point errors
        decimal_qty = Decimal(str(qty))
        decimal_price = Decimal(str(price)) if price is not None else None
        decimal_expected = Decimal(str(expected_price)) if expected_price is not None else (
            decimal_price or Decimal("0")
        )

        # Generate trace_id if not provided
        if trace_id is None:
            trace_id = f"legacy-{datetime.now(UTC).timestamp()}"

        return cls(
            trace_id=trace_id,
            symbol=symbol,
            side=OrderSide(side.lower()),
            order_type=OrderType.LIMIT if price is not None else OrderType.MARKET,
            quantity=decimal_qty,
            price=decimal_price,
            expected_price=decimal_expected,
            strategy_id=strategy_id,
            **kwargs
        )

    @classmethod
    def from_ooda_execution_plan(
        cls,
        plan: Any,  # ExecutionPlan
        trace_id: str | None = None
    ) -> UnifiedOrderRequest:
        """
        Convert OODA ExecutionPlan to UnifiedOrderRequest.

        Args:
            plan: ExecutionPlan from OODA loop
            trace_id: Optional trace ID override

        Returns:
            UnifiedOrderRequest
        """
        # Import here to avoid circular imports
        from decimal import Decimal

        return cls(
            trace_id=trace_id or plan.trace_id,
            symbol=plan.symbol,
            side=OrderSide(plan.side),
            order_type=OrderType(plan.order_type.lower()),
            quantity=Decimal(str(plan.quantity)),
            price=Decimal(str(plan.price)) if plan.price else None,
            expected_price=Decimal(str(plan.expected_price)),
            strategy_id=getattr(plan, 'strategy_id', 'ooda'),
            caller_name=getattr(plan, 'caller_name', 'unknown'),
            caller_role=getattr(plan, 'caller_role', 'untrusted'),
            metadata=getattr(plan, 'params', {})
        )


class UnifiedOrderResponse(BaseModel):
    """
    Unified order response from exchange.

    Standardizes responses across different exchanges.
    """

    order_id: str = Field(..., description="Exchange order ID")
    client_order_id: str = Field(..., description="Client order ID")
    status: OrderStatus = Field(..., description="Order status")

    # Fill details
    filled_quantity: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        description="Filled quantity"
    )
    remaining_quantity: Decimal = Field(
        ...,
        ge=0,
        description="Remaining quantity to fill"
    )
    average_price: Decimal | None = Field(
        None,
        ge=0,
        description="Average fill price"
    )

    # Fees
    fee: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        description="Trading fee paid"
    )
    fee_currency: str = Field(
        default="",
        description="Currency of fee"
    )

    # Error handling
    error_message: str | None = Field(
        None,
        description="Error message if rejected/failed"
    )
    raw_response: dict[str, Any] | None = Field(
        None,
        description="Raw exchange response"
    )

    # Timing
    timestamp: float = Field(
        default_factory=lambda: datetime.now(UTC).timestamp(),
        description="Response timestamp"
    )

    model_config = ConfigDict(frozen=True)

    @property
    def is_filled(self) -> bool:
        """Check if order is completely filled."""
        return self.status == OrderStatus.FILLED

    @property
    def is_open(self) -> bool:
        """Check if order is still open."""
        return self.status in (OrderStatus.OPEN, OrderStatus.PARTIALLY_FILLED)

    @property
    def fill_percentage(self) -> Decimal:
        """Calculate fill percentage."""
        total = self.filled_quantity + self.remaining_quantity
        if total == 0:
            return Decimal("0")
        return (self.filled_quantity / total) * 100


class Symbol(BaseModel):
    """
    Trading pair symbol representation.

    Provides validation and utility methods for trading pairs.
    """

    base: str = Field(..., pattern=r"^[A-Z0-9]+$", description="Base asset")
    quote: str = Field(..., pattern=r"^[A-Z0-9]+$", description="Quote asset")

    model_config = ConfigDict(frozen=True)

    def __str__(self) -> str:
        return f"{self.base}/{self.quote}"

    @classmethod
    def from_string(cls, symbol_str: str) -> Symbol:
        """Create Symbol from string like 'BTC/EUR' or 'BTC-EUR'."""
        for sep in ["/", "-", "_"]:
            if sep in symbol_str:
                parts = symbol_str.split(sep)
                if len(parts) == 2:
                    return cls(base=parts[0].upper(), quote=parts[1].upper())
        raise ValueError(f"Invalid symbol format: {symbol_str}")


# Backward compatibility aliases
OrderRequest = UnifiedOrderRequest
OrderResponse = UnifiedOrderResponse
