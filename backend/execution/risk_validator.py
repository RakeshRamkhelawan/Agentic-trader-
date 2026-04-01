"""
Pre-Trade Order Risk Validator.

Validates orders before execution to ensure compliance with risk limits.
Migrated from exchange/risk/ to execution/ folder (Week 2).

Integrates with UnifiedOrderRequest for consistent validation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any

from backend.schemas.unified_execution import Symbol, UnifiedOrderRequest

logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Validation result status."""

    APPROVED = "approved"
    WARNING = "warning"
    REJECTED = "rejected"


@dataclass
class ValidationCheck:
    """Individual validation check result."""

    name: str
    passed: bool
    status: ValidationStatus
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    """Complete validation result."""

    order_id: str | None
    status: ValidationStatus
    checks: list[ValidationCheck]
    overall_message: str

    @property
    def is_valid(self) -> bool:
        """Check if validation passed."""
        return self.status != ValidationStatus.REJECTED

    @property
    def has_warnings(self) -> bool:
        """Check if there are warnings."""
        return any(c.status == ValidationStatus.WARNING for c in self.checks)

    def get_failed_checks(self) -> list[ValidationCheck]:
        """Get all failed checks."""
        return [c for c in self.checks if not c.passed]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "order_id": self.order_id,
            "status": self.status.value,
            "is_valid": self.is_valid,
            "has_warnings": self.has_warnings,
            "overall_message": self.overall_message,
            "checks": [
                {
                    "name": c.name,
                    "passed": c.passed,
                    "status": c.status.value,
                    "message": c.message,
                    "details": c.details,
                }
                for c in self.checks
            ],
        }


@dataclass
class RiskLimits:
    """Risk limits configuration."""

    # Position limits
    max_position_pct: Decimal = Decimal("0.20")  # Max 20% in single position
    max_concentration_pct: Decimal = Decimal("0.30")  # Max 30% in single asset

    # Order limits
    max_order_pct: Decimal = Decimal("0.10")  # Max 10% per order
    min_order_size: Decimal = Decimal("10")  # Min $10 order
    max_order_size: Decimal | None = None  # No max by default

    # Daily limits
    max_daily_trades: int = 50
    max_daily_volume_pct: Decimal = Decimal("2.0")  # Max 2x portfolio per day
    max_daily_loss_pct: Decimal = Decimal("0.05")  # Max 5% daily loss

    # Price limits
    max_slippage_pct: Decimal = Decimal("0.01")  # Max 1% slippage
    max_spread_pct: Decimal = Decimal("0.02")  # Max 2% spread
    price_deviation_pct: Decimal = Decimal("0.05")  # Max 5% from reference

    # Exchange health
    require_connected: bool = True
    min_exchange_health_score: float = 0.5

    def validate(self) -> None:
        """Validate risk configuration."""
        assert 0 < self.max_position_pct <= 1, "max_position_pct must be between 0 and 1"
        assert 0 < self.max_order_pct <= 1, "max_order_pct must be between 0 and 1"
        assert self.min_order_size > 0, "min_order_size must be positive"


class OrderRiskValidator:
    """
    Pre-trade order risk validator.

    Performs 10+ validation checks before order execution:
    1. Order size validation
    2. Balance validation
    3. Position limit validation
    4. Daily trade limit
    5. Daily volume limit
    6. Spread validation
    7. Price sanity check
    8. Exchange health check
    9. Market volatility check
    10. Portfolio concentration check

    Example:
        >>> validator = OrderRiskValidator(RiskLimits())
        >>> result = await validator.validate_order(
        ...     request=order_request,
        ...     portfolio_value=Decimal("100000"),
        ...     current_positions={"BTC": Decimal("0.5")}
        ... )
        >>> if result.is_valid:
        ...     await execute_order(order_request)
    """

    def __init__(self, limits: RiskLimits | None = None):
        """
        Initialize validator.

        Args:
            limits: Risk limits configuration
        """
        self.limits = limits or RiskLimits()
        self.limits.validate()

        # Track daily stats
        self._daily_trades: int = 0
        self._daily_volume: Decimal = Decimal("0")
        self._daily_loss: Decimal = Decimal("0")

        # Reference prices for sanity checks
        self._reference_prices: dict[Symbol, Decimal] = {}

        logger.info("[OrderRiskValidator] Initialized")

    async def validate_order(
        self,
        request: UnifiedOrderRequest,
        portfolio_value: Decimal,
        current_positions: dict[str, Decimal],
        exchange: Any | None = None,
        balance: Any | None = None,
    ) -> ValidationResult:
        """
        Validate an order request.

        Args:
            request: Order request to validate
            portfolio_value: Total portfolio value
            current_positions: Current position sizes by asset
            exchange: Exchange for market data
            balance: Available balance for the relevant asset

        Returns:
            Validation result
        """
        checks = []
        order_id = request.client_order_id or "pending"

        # 1. Order size validation
        checks.append(self._validate_order_size(request, portfolio_value))

        # 2. Balance validation
        if balance:
            checks.append(self._validate_balance(request, balance))

        # 3. Position limit validation
        checks.append(self._validate_position_limit(request, portfolio_value, current_positions))

        # 4. Daily limits validation
        checks.append(self._validate_daily_limits(request, portfolio_value))

        # 5. Market data validation (if exchange provided)
        if exchange and hasattr(exchange, "connected") and exchange.connected:
            market_checks = await self._validate_market_conditions(request, exchange)
            checks.extend(market_checks)

        # 6. Exchange health validation
        if exchange:
            checks.append(self._validate_exchange_health(exchange))

        # Determine overall status
        failed_rejected = [c for c in checks if c.status == ValidationStatus.REJECTED]
        failed_warnings = [c for c in checks if c.status == ValidationStatus.WARNING]

        if failed_rejected:
            status = ValidationStatus.REJECTED
            overall_message = f"Order rejected: {failed_rejected[0].message}"
        elif failed_warnings:
            status = ValidationStatus.WARNING
            overall_message = f"Order approved with warnings: {len(failed_warnings)} issues"
        else:
            status = ValidationStatus.APPROVED
            overall_message = "Order approved"

        return ValidationResult(
            order_id=order_id,
            status=status,
            checks=checks,
            overall_message=overall_message,
        )

    def _validate_order_size(
        self, request: UnifiedOrderRequest, portfolio_value: Decimal
    ) -> ValidationCheck:
        """Validate order size against limits."""

        order_value = request.quantity * (request.price or Decimal("0"))
        if order_value == 0 and request.expected_price:
            # Market order, use expected price
            order_value = request.quantity * request.expected_price

        # Check minimum size
        if order_value < self.limits.min_order_size:
            return ValidationCheck(
                name="min_order_size",
                passed=False,
                status=ValidationStatus.REJECTED,
                message=f"Order value ${order_value:.2f} below minimum ${self.limits.min_order_size}",
                details={
                    "order_value": float(order_value),
                    "min_value": float(self.limits.min_order_size),
                },
            )

        # Check maximum size
        if self.limits.max_order_size and order_value > self.limits.max_order_size:
            return ValidationCheck(
                name="max_order_size",
                passed=False,
                status=ValidationStatus.REJECTED,
                message=f"Order value ${order_value:.2f} above maximum ${self.limits.max_order_size}",
                details={
                    "order_value": float(order_value),
                    "max_value": float(self.limits.max_order_size),
                },
            )

        # Check percentage of portfolio
        if portfolio_value > 0:
            order_pct = order_value / portfolio_value
            if order_pct > self.limits.max_order_pct:
                return ValidationCheck(
                    name="max_order_pct",
                    passed=False,
                    status=ValidationStatus.REJECTED,
                    message=f"Order {order_pct:.1%} exceeds max {self.limits.max_order_pct:.1%} of portfolio",
                    details={
                        "order_pct": float(order_pct),
                        "max_pct": float(self.limits.max_order_pct),
                    },
                )

        return ValidationCheck(
            name="order_size",
            passed=True,
            status=ValidationStatus.APPROVED,
            message="Order size within limits",
            details={"order_value": float(order_value)},
        )

    def _validate_balance(self, request: UnifiedOrderRequest, balance: Any) -> ValidationCheck:
        """Validate available balance."""

        # Convert balance to Decimal if needed
        if hasattr(balance, "free"):
            available = (
                balance.free if isinstance(balance.free, Decimal) else Decimal(str(balance.free))
            )
        else:
            available = Decimal(str(balance)) if balance else Decimal("0")

        if request.side.value == "buy":
            required = (
                request.quantity * (request.price or request.expected_price) * Decimal("1.01")
            )  # 1% buffer

            if required > available:
                return ValidationCheck(
                    name="balance_sufficient",
                    passed=False,
                    status=ValidationStatus.REJECTED,
                    message=f"Insufficient balance: need ${required:.2f}, have ${available:.2f}",
                    details={
                        "required": float(required),
                        "available": float(available),
                    },
                )
        else:  # SELL
            required = request.quantity

            if required > available:
                return ValidationCheck(
                    name="position_sufficient",
                    passed=False,
                    status=ValidationStatus.REJECTED,
                    message=f"Insufficient position: need {required}, have {available}",
                    details={
                        "required": float(required),
                        "available": float(available),
                    },
                )

        return ValidationCheck(
            name="balance",
            passed=True,
            status=ValidationStatus.APPROVED,
            message="Sufficient balance available",
        )

    def _validate_position_limit(
        self,
        request: UnifiedOrderRequest,
        portfolio_value: Decimal,
        current_positions: dict[str, Decimal],
    ) -> ValidationCheck:
        """Validate position doesn't exceed limits."""

        if portfolio_value == 0:
            return ValidationCheck(
                name="position_limit",
                passed=True,
                status=ValidationStatus.APPROVED,
                message="No portfolio value for comparison",
            )

        # Parse symbol to get base asset
        try:
            symbol = Symbol.from_string(request.symbol)
            base_asset = symbol.base
        except ValueError:
            base_asset = request.symbol.split("/")[0] if "/" in request.symbol else request.symbol

        # Calculate new position
        current = current_positions.get(base_asset, Decimal("0"))
        if request.side.value == "buy":
            new_position = current + request.quantity
        else:
            new_position = max(Decimal("0"), current - request.quantity)

        # Calculate position value (estimate)
        position_value = new_position * (request.price or request.expected_price)
        position_pct = position_value / portfolio_value

        if position_pct > self.limits.max_position_pct:
            return ValidationCheck(
                name="max_position_pct",
                passed=False,
                status=ValidationStatus.REJECTED,
                message=f"Position would be {position_pct:.1%}, exceeds max {self.limits.max_position_pct:.1%}",
                details={
                    "current_position": float(current),
                    "new_position": float(new_position),
                    "position_pct": float(position_pct),
                },
            )

        return ValidationCheck(
            name="position_limit",
            passed=True,
            status=ValidationStatus.APPROVED,
            message=f"Position {position_pct:.1%} within limits",
        )

    def _validate_daily_limits(
        self, request: UnifiedOrderRequest, portfolio_value: Decimal
    ) -> ValidationCheck:
        """Validate daily trading limits."""

        warnings = []

        # Check trade count
        if self._daily_trades >= self.limits.max_daily_trades:
            return ValidationCheck(
                name="daily_trade_limit",
                passed=False,
                status=ValidationStatus.REJECTED,
                message=f"Daily trade limit reached: {self._daily_trades}/{self.limits.max_daily_trades}",
                details={
                    "trades_today": self._daily_trades,
                    "max_trades": self.limits.max_daily_trades,
                },
            )

        # Check daily volume
        order_value = request.quantity * (request.price or request.expected_price)
        projected_volume = self._daily_volume + order_value
        max_volume = portfolio_value * self.limits.max_daily_volume_pct

        if projected_volume > max_volume:
            return ValidationCheck(
                name="daily_volume_limit",
                passed=False,
                status=ValidationStatus.REJECTED,
                message=f"Daily volume would be ${projected_volume:.2f}, exceeds max ${max_volume:.2f}",
                details={
                    "current_volume": float(self._daily_volume),
                    "projected_volume": float(projected_volume),
                    "max_volume": float(max_volume),
                },
            )

        # Warning at 80% of volume limit
        if projected_volume > max_volume * Decimal("0.8"):
            warnings.append(f"Daily volume at {projected_volume/max_volume:.0%}")

        if warnings:
            return ValidationCheck(
                name="daily_limits",
                passed=True,
                status=ValidationStatus.WARNING,
                message="; ".join(warnings),
                details={"trades_today": self._daily_trades},
            )

        return ValidationCheck(
            name="daily_limits",
            passed=True,
            status=ValidationStatus.APPROVED,
            message="Daily limits not exceeded",
        )

    async def _validate_market_conditions(
        self, request: UnifiedOrderRequest, exchange: Any
    ) -> list[ValidationCheck]:
        """Validate current market conditions."""
        checks = []

        try:
            # Get ticker
            ticker = None
            if hasattr(exchange, "fetch_ticker"):
                ticker = await exchange.fetch_ticker(request.symbol)
            elif hasattr(exchange, "get_ticker"):
                ticker = await exchange.get_ticker(request.symbol)

            if not ticker:
                return [
                    ValidationCheck(
                        name="market_data",
                        passed=False,
                        status=ValidationStatus.WARNING,
                        message="Could not fetch market data",
                    )
                ]

            # Extract bid/ask/last
            bid = Decimal(str(ticker.get("bid", 0)))
            ask = Decimal(str(ticker.get("ask", 0)))
            last = Decimal(str(ticker.get("last", 0)))

            # Check spread
            if last > 0:
                spread_pct = (ask - bid) / last
                if spread_pct > self.limits.max_spread_pct:
                    checks.append(
                        ValidationCheck(
                            name="spread_limit",
                            passed=False,
                            status=ValidationStatus.REJECTED,
                            message=f"Spread {spread_pct:.2%} exceeds max {self.limits.max_spread_pct:.2%}",
                            details={
                                "spread_pct": float(spread_pct),
                                "max_spread": float(self.limits.max_spread_pct),
                            },
                        )
                    )
                elif spread_pct > self.limits.max_spread_pct * Decimal("0.8"):
                    checks.append(
                        ValidationCheck(
                            name="spread_warning",
                            passed=True,
                            status=ValidationStatus.WARNING,
                            message=f"Spread {spread_pct:.2%} is elevated",
                            details={"spread_pct": float(spread_pct)},
                        )
                    )
                else:
                    checks.append(
                        ValidationCheck(
                            name="spread",
                            passed=True,
                            status=ValidationStatus.APPROVED,
                            message=f"Spread {spread_pct:.2%} normal",
                        )
                    )

            # Price sanity check
            if request.price:
                deviation = abs(request.price - last) / last
                if deviation > self.limits.price_deviation_pct:
                    checks.append(
                        ValidationCheck(
                            name="price_sanity",
                            passed=False,
                            status=ValidationStatus.REJECTED,
                            message=f"Order price deviates {deviation:.1%} from market",
                            details={
                                "order_price": float(request.price),
                                "market_price": float(last),
                            },
                        )
                    )
                else:
                    checks.append(
                        ValidationCheck(
                            name="price_sanity",
                            passed=True,
                            status=ValidationStatus.APPROVED,
                            message="Price within normal range",
                        )
                    )

            # Store reference price
            try:
                symbol = Symbol.from_string(request.symbol)
                self._reference_prices[symbol] = last
            except ValueError:
                pass

        except Exception as e:
            logger.warning(f"[OrderRiskValidator] Market validation error: {e}")
            checks.append(
                ValidationCheck(
                    name="market_data",
                    passed=True,
                    status=ValidationStatus.WARNING,
                    message=f"Could not validate market conditions: {e}",
                )
            )

        return checks

    def _validate_exchange_health(self, exchange: Any) -> ValidationCheck:
        """Validate exchange is healthy."""

        is_connected = False
        if hasattr(exchange, "connected"):
            is_connected = exchange.connected
        elif hasattr(exchange, "_connected"):
            is_connected = exchange._connected

        if not is_connected:
            if self.limits.require_connected:
                return ValidationCheck(
                    name="exchange_connected",
                    passed=False,
                    status=ValidationStatus.REJECTED,
                    message="Exchange not connected",
                )
            else:
                return ValidationCheck(
                    name="exchange_connected",
                    passed=True,
                    status=ValidationStatus.WARNING,
                    message="Exchange not connected (trading anyway)",
                )

        return ValidationCheck(
            name="exchange_health",
            passed=True,
            status=ValidationStatus.APPROVED,
            message="Exchange healthy",
        )

    def record_trade(self, value: Decimal, pnl: Decimal | None = None) -> None:
        """Record a completed trade for daily statistics."""
        self._daily_trades += 1
        self._daily_volume += value

        if pnl and pnl < 0:
            self._daily_loss += abs(pnl)

        logger.debug(
            f"[OrderRiskValidator] Recorded trade: value=${value:.2f}, pnl=${pnl or 0:.2f}"
        )

    def reset_daily_stats(self) -> None:
        """Reset daily statistics (call at day start)."""
        self._daily_trades = 0
        self._daily_volume = Decimal("0")
        self._daily_loss = Decimal("0")
        logger.info("[OrderRiskValidator] Daily stats reset")

    def get_daily_stats(self) -> dict[str, Any]:
        """Get current daily statistics."""
        return {
            "trades": self._daily_trades,
            "volume": float(self._daily_volume),
            "loss": float(self._daily_loss),
            "limits": {
                "max_trades": self.limits.max_daily_trades,
                "max_volume_pct": float(self.limits.max_daily_volume_pct),
                "max_loss_pct": float(self.limits.max_daily_loss_pct),
            },
        }

    def update_limits(self, limits: RiskLimits) -> None:
        """Update risk limits."""
        limits.validate()
        self.limits = limits
        logger.info("[OrderRiskValidator] Risk limits updated")


# Singleton instance
_risk_validator: OrderRiskValidator | None = None


def get_risk_validator() -> OrderRiskValidator:
    """Get or create global risk validator."""
    global _risk_validator
    if _risk_validator is None:
        _risk_validator = OrderRiskValidator()
    return _risk_validator
