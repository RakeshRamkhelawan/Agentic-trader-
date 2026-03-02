# MASTER PROMPT: Week 2 - RiskManager Enhancement + TriadService Migration

> **Agent Role:** Senior Python Architect
> **Task:** P1 High - Security Integration & OODA Compliance
> **Duration:** Week 2 (5-7 days)
> **Prerequisite:** Week 1 completed (Unified Schema + PortfolioManagerAgent)

---

## CONTEXT & BACKGROUND

### Current State After Week 1
```
✅ UnifiedOrderRequest schema (Decimal precision)
✅ PortfolioManagerAgent (OODA-integrated)
✅ Feature flags for gradual rollout
```

### Critical Security Gaps
1. **TriadService** executes trades WITHOUT:
   - AgentGatekeeper authorization checks
   - AuditLogger logging
   - Event bus publication
   - Risk validation (position limits, daily limits)

2. **RiskManagerAgent** lacks:
   - Pre-trade order validation (10+ checks)
   - Position limit enforcement
   - Daily trade/volume limits
   - Spread validation

### Files to Modify
| File | Action | Reason |
|------|--------|--------|
| `agents/risk_manager_agent.py` | Extend | Add OrderRiskValidator integration |
| `exchange/triad_service.py` | Migrate | Move to `execution/`, add security |
| `execution/order_executor.py` | Enhance | Accept UnifiedOrderRequest |

---

## TASK SPECIFICATION

### Objective
Integrate security and risk validation into trading flow while migrating TriadService to use existing OrderExecutor infrastructure.

---

## DELIVERABLE 1: Enhanced RiskManagerAgent

**File:** `backend/agents/risk_manager_agent.py`

### Current Implementation
```python
class RiskManagerAgent(BaseAgent):
    async def assess_risk(self, proposal: TradeProposal) -> RiskAssessment:
        # Basic risk assessment
        risk_score = self._calculate_risk(proposal)
        return RiskAssessment(...)
```

### Enhanced Implementation
```python
"""
RiskManagerAgent - Enhanced with OrderRiskValidator.

Integrates 10+ pre-trade validation checks from exchange/risk/order_validator.py
into OODA Risk Assessment flow.
"""

from typing import Any
from decimal import Decimal

from backend.agents.base_agent import BaseAgent
from backend.core.schemas.ooda_types import TradeProposal, RiskAssessment, RiskDecision
from backend.execution.risk_validator import OrderRiskValidator, RiskLimits
from backend.schemas.unified_execution import (
    UnifiedOrderRequest, OrderSide, OrderType, TimeInForce
)


class RiskManagerAgent(BaseAgent):
    """
    Enhanced Risk Manager with pre-trade validation.

    Combines existing risk assessment with OrderRiskValidator
    for comprehensive trade validation.
    """

    def __init__(
        self,
        llm_provider: Any | None = None,
        event_bus: Any | None = None,
        portfolio_manager=None,  # PortfolioManagerAgent
    ):
        super().__init__(
            agent_name="RiskManager",
            llm_provider=llm_provider,
            event_bus=event_bus,
        )

        # Initialize enhanced risk validator
        self.risk_validator = OrderRiskValidator(
            RiskLimits(
                max_position_pct=Decimal("0.20"),      # 20% max single position
                max_order_pct=Decimal("0.10"),         # 10% max per order
                min_order_size=Decimal("10"),          # $10 minimum
                max_daily_trades=50,
                max_daily_volume_pct=Decimal("2.0"),   # 2x portfolio daily
                max_daily_loss_pct=Decimal("0.05"),    # 5% max daily loss
                max_slippage_pct=Decimal("0.01"),      # 1% max slippage
                max_spread_pct=Decimal("0.02"),        # 2% max spread
            )
        )

        self.portfolio_manager = portfolio_manager
        self.daily_stats = {
            "trades": 0,
            "volume": Decimal("0"),
            "loss": Decimal("0"),
        }

    async def assess_risk(self, proposal: TradeProposal) -> RiskAssessment:
        """
        Enhanced risk assessment with OrderRiskValidator.

        Args:
            proposal: Trade proposal from TraderAgent

        Returns:
            RiskAssessment with decision (approve/reject/reduce)
        """
        self.heartbeat()

        # Convert TradeProposal to UnifiedOrderRequest
        order_request = self._convert_proposal(proposal)

        # Get portfolio state
        portfolio_value = Decimal("10000")  # Default
        current_positions = {}

        if self.portfolio_manager:
            portfolio = await self.portfolio_manager.get_portfolio_state()
            portfolio_value = Decimal(str(portfolio.total_equity))
            # Get current positions
            current_positions = await self._get_current_positions()

        # Run OrderRiskValidator checks
        validation = await self.risk_validator.validate_order(
            request=order_request,
            portfolio_value=portfolio_value,
            current_positions=current_positions,
            exchange=None,  # Would get from exchange adapter
            balance=None    # Would get from exchange
        )

        # Combine with existing risk assessment
        base_risk_score = self._calculate_base_risk(proposal)

        # Adjust based on validation
        if not validation.is_valid:
            risk_score = 1.0  # Maximum risk - reject
            decision = RiskDecision.REJECT
            rationale = f"Risk validation failed: {validation.overall_message}"
        elif validation.has_warnings:
            risk_score = base_risk_score * 1.2  # Increase risk score
            decision = RiskDecision.REDUCE_SIZE
            rationale = f"Risk warnings: {validation.overall_message}"
        else:
            risk_score = base_risk_score
            decision = RiskDecision.APPROVE
            rationale = "Risk validation passed"

        # Calculate win probability
        win_probability = self._calculate_win_probability(proposal, risk_score)

        # Determine modified size if needed
        modified_size = None
        if decision == RiskDecision.REDUCE_SIZE:
            modified_size = proposal.size * 0.5  # Reduce by 50%

        # Create assessment
        assessment = RiskAssessment(
            trade_id=proposal.trade_id,
            decision=decision,
            rationale=rationale,
            risk_score=min(risk_score, 1.0),
            win_probability=win_probability,
            modified_size=modified_size,
            timestamp=datetime.utcnow().timestamp()
        )

        # Publish thought
        await self.publish_thought(
            reasoning=rationale,
            confidence=1.0 - risk_score,
            data={
                "trade_id": proposal.trade_id,
                "risk_score": risk_score,
                "checks_performed": len(validation.checks)
            }
        )

        # Update daily stats
        if decision == RiskDecision.APPROVE:
            self._update_daily_stats(order_request)

        return assessment

    def _convert_proposal(self, proposal: TradeProposal) -> UnifiedOrderRequest:
        """Convert TradeProposal to UnifiedOrderRequest."""
        from decimal import Decimal

        return UnifiedOrderRequest(
            trace_id=f"risk-{proposal.trade_id}",
            symbol=proposal.symbol,
            side=OrderSide(proposal.side),
            order_type=OrderType.LIMIT if proposal.entry_price else OrderType.MARKET,
            quantity=Decimal(str(proposal.size)),
            price=Decimal(str(proposal.entry_price)) if proposal.entry_price else None,
            expected_price=Decimal(str(proposal.entry_price or 0)),
            strategy_id=proposal.strategy_id,
            time_in_force=TimeInForce.GTC,
            post_only=False
        )

    async def _get_current_positions(self) -> dict:
        """Get current positions from portfolio manager."""
        if not self.portfolio_manager:
            return {}

        portfolio = await self.portfolio_manager.get_portfolio_state()
        # Return positions dict
        return {}  # Implementation depends on portfolio data

    def _calculate_base_risk(self, proposal: TradeProposal) -> float:
        """Calculate base risk score from proposal."""
        # Existing risk calculation logic
        base_risk = 0.3  # Start at 30%

        # Adjust based on confidence
        base_risk *= (1.0 - proposal.confidence)

        # Adjust based on leverage (if any)
        if proposal.leverage and proposal.leverage > 1:
            base_risk *= proposal.leverage

        return min(base_risk, 1.0)

    def _calculate_win_probability(
        self,
        proposal: TradeProposal,
        risk_score: float
    ) -> float:
        """Estimate win probability."""
        # Simple model: higher confidence = higher win prob
        # But higher risk = lower win prob
        win_prob = proposal.confidence * (1.0 - risk_score)
        return max(0.0, min(1.0, win_prob))

    def _update_daily_stats(self, order_request: UnifiedOrderRequest) -> None:
        """Update daily trading statistics."""
        self.daily_stats["trades"] += 1

        order_value = order_request.quantity * (order_request.price or Decimal("0"))
        self.daily_stats["volume"] += order_value


# tests/agents/test_risk_manager_enhanced.py
import pytest
from decimal import Decimal
from backend.agents.risk_manager_agent import RiskManagerAgent
from backend.core.schemas.ooda_types import TradeProposal, RiskDecision

class TestRiskManagerEnhanced:
    @pytest.fixture
    def agent(self):
        return RiskManagerAgent()

    @pytest.mark.asyncio
    async def test_position_limit_enforcement(self, agent):
        """Test that position limits are enforced."""
        # Create proposal that exceeds position limit
        proposal = TradeProposal(
            symbol="BTC/EUR",
            side="buy",
            size=1000.0,  # Way too large
            entry_price=45000,
            stop_loss=40000,
            take_profit=50000,
            rationale="Test",
            strategy_id="test",
            confidence=0.8
        )

        assessment = await agent.assess_risk(proposal)

        # Should reject or reduce
        assert assessment.decision in [RiskDecision.REJECT, RiskDecision.REDUCE_SIZE]

    @pytest.mark.asyncio
    async def test_daily_trade_limit(self, agent):
        """Test daily trade count limit."""
        # Simulate 50 trades already
        agent.daily_stats["trades"] = 50

        proposal = TradeProposal(
            symbol="BTC/EUR",
            side="buy",
            size=0.1,
            entry_price=45000,
            stop_loss=40000,
            take_profit=50000,
            rationale="Test",
            strategy_id="test",
            confidence=0.8
        )

        assessment = await agent.assess_risk(proposal)

        # Should reject due to daily limit
        assert assessment.decision == RiskDecision.REJECT
```

---

## DELIVERABLE 2: Migrated TriadService

**Source:** `backend/exchange/triad_service.py`
**Target:** `backend/execution/triad_service.py`

### Key Changes Required

1. **Use OrderExecutor instead of OrderManager**
2. **Add AgentGatekeeper authorization**
3. **Add AuditLogger logging**
4. **Publish to EventBus**
5. **Use UnifiedOrderRequest**
6. **Call RiskManagerAgent for validation**

```python
"""
TriadService - Refactored for OODA Integration.

Migrates from standalone service to OODA-compliant execution.
Uses OrderExecutor for actual execution.
Integrates with AgentGatekeeper and AuditLogger.
"""

from typing import Dict, Optional, Any
from decimal import Decimal
from datetime import datetime

from backend.execution.order_executor import OrderExecutor
from backend.execution.exchange_adapter_protocol import ExchangeAdapterProtocol
from backend.execution.bitvavo_adapter import BitvavoAdapter
from backend.execution.revolut_x_adapter import RevolutXAdapter
from backend.agents.risk_manager_agent import RiskManagerAgent
from backend.agents.portfolio_manager_agent import PortfolioManagerAgent
from backend.core.schemas.unified_execution import (
    UnifiedOrderRequest, OrderSide, OrderType, TimeInForce
)
from backend.core.schemas.ooda_types import (
    TradeProposal, RiskAssessment, RiskDecision,
    ExecutionPlan, ExecutionOutcome
)
from backend.governance.agent_gatekeeper import AgentGatekeeper, ToolPermission
from backend.core.security.audit_logger import AuditLogger
from backend.events.event_bus import EventBus


class TriadService:
    """
    Refactored Triad Service using OODA infrastructure.

    Changes from original:
    - Uses OrderExecutor instead of OrderManager
    - Calls RiskManagerAgent before execution
    - Checks AgentGatekeeper authorization
    - Logs to AuditLogger
    - Publishes events to EventBus
    """

    def __init__(
        self,
        trading_mode: str = "paper",
        agent_name: str = "TriadService",
        agent_role: str = "strategist"
    ):
        self.trading_mode = trading_mode
        self.agent_name = agent_name
        self.agent_role = agent_role

        # Initialize OODA components
        self.order_executor: Optional[OrderExecutor] = None
        self.risk_manager: Optional[RiskManagerAgent] = None
        self.portfolio_manager: Optional[PortfolioManagerAgent] = None

        # Security & audit
        self.gatekeeper = AgentGatekeeper()
        self.audit_logger = AuditLogger()
        self.event_bus: Optional[EventBus] = None

        # Stats
        self.stats = {
            "trades_executed": 0,
            "trades_rejected": 0,
            "risk_rejections": 0,
        }

    async def initialize(
        self,
        event_bus: Optional[EventBus] = None,
        exchange_adapter: Optional[ExchangeAdapterProtocol] = None
    ):
        """Initialize service with dependencies."""
        self.event_bus = event_bus

        # Initialize portfolio manager
        self.portfolio_manager = PortfolioManagerAgent(
            event_bus=event_bus
        )
        await self.portfolio_manager.initialize_adapters()

        # Initialize risk manager with portfolio access
        self.risk_manager = RiskManagerAgent(
            event_bus=event_bus,
            portfolio_manager=self.portfolio_manager
        )

        # Initialize order executor
        if exchange_adapter is None:
            # Default to Bitvavo if available
            from backend.core.config.settings import settings
            if settings.BITVAVO_API_KEY:
                exchange_adapter = BitvavoAdapter()
                await exchange_adapter.initialize()

        if exchange_adapter:
            self.order_executor = OrderExecutor(
                exchange_adapter=exchange_adapter,
                gatekeeper=self.gatekeeper,
                audit_logger=self.audit_logger
            )

    async def execute_trade(
        self,
        decision: Any,  # BuddhiDecision
        symbol: str = "BTC/EUR",
        quantity: Optional[Decimal] = None,
        exchange_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute trade with full OODA integration.

        Flow:
        1. Create TradeProposal
        2. RiskManagerAgent.assess_risk()
        3. AgentGatekeeper authorization
        4. AuditLogger.log_execution_attempt()
        5. OrderExecutor.execute_trade()
        6. EventBus.publish()
        """

        # 1. Check authorization
        if not self.gatekeeper.check_permission(
            agent_name=self.agent_name,
            tool=ToolPermission.PLACE_ORDER
        ):
            await self.audit_logger.log_security_event(
                event="unauthorized_execution_attempt",
                agent=self.agent_name,
                symbol=symbol
            )
            return {
                "status": "rejected",
                "reason": "Not authorized to place orders"
            }

        # 2. Create TradeProposal for risk assessment
        proposal = TradeProposal(
            symbol=symbol,
            side="buy" if decision.action == "bullish" else "sell",
            size=float(quantity or Decimal("0.1")),
            entry_price=None,  # Market order
            stop_loss=0,  # Would calculate
            take_profit=0,  # Would calculate
            rationale=decision.rationale,
            strategy_id="triad",
            confidence=decision.confidence
        )

        # 3. Risk assessment
        if self.risk_manager:
            risk_assessment = await self.risk_manager.assess_risk(proposal)

            if risk_assessment.decision == RiskDecision.REJECT:
                self.stats["risk_rejections"] += 1
                await self.audit_logger.log_rejected_trade(
                    proposal=proposal,
                    reason=risk_assessment.rationale
                )
                return {
                    "status": "rejected",
                    "reason": risk_assessment.rationale,
                    "risk_score": risk_assessment.risk_score
                }

            if risk_assessment.decision == RiskDecision.REDUCE_SIZE:
                proposal.size = risk_assessment.modified_size or proposal.size * 0.5

        # 4. Create ExecutionPlan
        plan = ExecutionPlan(
            symbol=proposal.symbol,
            side=proposal.side,
            quantity=proposal.size,
            order_type="MARKET" if proposal.entry_price is None else "LIMIT",
            price=proposal.entry_price,
            expected_price=proposal.entry_price or 0,
            trace_id=f"triad-{datetime.utcnow().timestamp()}",
            caller_name=self.agent_name,
            caller_role=self.agent_role
        )

        # 5. Log attempt
        await self.audit_logger.log_execution_attempt(plan)

        # 6. Execute via OrderExecutor
        if self.order_executor:
            outcome = await self.order_executor.execute_trade(plan)

            # 7. Publish event
            if self.event_bus:
                await self.event_bus.publish("execution", {
                    "trace_id": plan.trace_id,
                    "status": "filled" if outcome.success else "failed",
                    "symbol": plan.symbol,
                    "filled_qty": outcome.filled_qty,
                    "avg_price": outcome.avg_price
                })

            if outcome.success:
                self.stats["trades_executed"] += 1
            else:
                self.stats["trades_rejected"] += 1

            return {
                "status": "filled" if outcome.success else "failed",
                "trace_id": plan.trace_id,
                "filled_qty": outcome.filled_qty,
                "avg_price": outcome.avg_price,
                "error": outcome.error
            }
        else:
            return {
                "status": "error",
                "reason": "OrderExecutor not initialized"
            }


# tests/execution/test_triad_service_refactored.py
import pytest
from decimal import Decimal
from backend.execution.triad_service import TriadService

class TestTriadServiceRefactored:
    @pytest.fixture
    async def service(self):
        service = TriadService(trading_mode="paper")
        await service.initialize()
        return service

    @pytest.mark.asyncio
    async def test_unauthorized_execution_blocked(self, service):
        """Test that unauthorized execution is blocked."""
        # Mock gatekeeper to deny permission
        service.gatekeeper.check_permission = lambda **kwargs: False

        # Mock decision
        class MockDecision:
            action = "bullish"
            confidence = 0.8
            rationale = "Test"

        result = await service.execute_trade(MockDecision())

        assert result["status"] == "rejected"
        assert "Not authorized" in result["reason"]

    @pytest.mark.asyncio
    async def test_risky_trade_rejected(self, service):
        """Test that high-risk trades are rejected."""
        # Mock decision with very large position
        class MockDecision:
            action = "bullish"
            confidence = 0.8
            rationale = "Test"

        result = await service.execute_trade(
            MockDecision(),
            quantity=Decimal("1000000")  # Way too large
        )

        assert result["status"] == "rejected"
        assert "risk" in result.get("reason", "").lower()
```

---

## DELIVERABLE 3: Risk Validator Module

**File:** `backend/execution/risk_validator.py`

**Migration:** Move from `backend/exchange/risk/order_validator.py`

**Changes:**
1. Import `UnifiedOrderRequest` instead of custom `OrderRequest`
2. Ensure all return values use Decimal
3. Add compatibility layer for float inputs

```python
"""
Risk Validator - Pre-trade order validation.

Migrated from exchange/risk/ to execution/ folder.
Uses UnifiedOrderRequest for consistency.
"""

from decimal import Decimal
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from backend.schemas.unified_execution import UnifiedOrderRequest
from backend.execution.exchange_adapter import ExchangeAdapter


class ValidationStatus(Enum):
    APPROVED = "approved"
    WARNING = "warning"
    REJECTED = "rejected"


@dataclass
class ValidationCheck:
    name: str
    passed: bool
    status: ValidationStatus
    message: str
    details: Dict[str, Any]


@dataclass
class ValidationResult:
    order_id: Optional[str]
    status: ValidationStatus
    checks: List[ValidationCheck]
    overall_message: str

    @property
    def is_valid(self) -> bool:
        return self.status != ValidationStatus.REJECTED


class RiskLimits:
    """Configuration for risk limits."""

    def __init__(
        self,
        max_position_pct: Decimal = Decimal("0.20"),
        max_order_pct: Decimal = Decimal("0.10"),
        min_order_size: Decimal = Decimal("10"),
        max_daily_trades: int = 50,
        max_daily_volume_pct: Decimal = Decimal("2.0"),
        max_daily_loss_pct: Decimal = Decimal("0.05"),
        max_slippage_pct: Decimal = Decimal("0.01"),
        max_spread_pct: Decimal = Decimal("0.02"),
    ):
        self.max_position_pct = max_position_pct
        self.max_order_pct = max_order_pct
        self.min_order_size = min_order_size
        self.max_daily_trades = max_daily_trades
        self.max_daily_volume_pct = max_daily_volume_pct
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_slippage_pct = max_slippage_pct
        self.max_spread_pct = max_spread_pct


class OrderRiskValidator:
    """
    Pre-trade order risk validator.

    Performs 10+ validation checks before order execution.
    """

    def __init__(self, limits: Optional[RiskLimits] = None):
        self.limits = limits or RiskLimits()
        self.daily_stats = {
            "trades": 0,
            "volume": Decimal("0"),
            "loss": Decimal("0"),
        }

    async def validate_order(
        self,
        request: UnifiedOrderRequest,
        portfolio_value: Decimal,
        current_positions: Dict[str, Decimal],
        exchange: Optional[ExchangeAdapter] = None,
        balance: Optional[Any] = None
    ) -> ValidationResult:
        """Validate order against all risk checks."""

        checks = []

        # Check 1: Order size
        checks.append(self._check_order_size(request, portfolio_value))

        # Check 2: Balance
        if balance:
            checks.append(self._check_balance(request, balance))

        # Check 3: Position limit
        checks.append(self._check_position_limit(request, portfolio_value, current_positions))

        # Check 4: Daily limits
        checks.append(self._check_daily_limits(request, portfolio_value))

        # Check 5: Market conditions (if exchange available)
        if exchange:
            market_checks = await self._check_market_conditions(request, exchange)
            checks.extend(market_checks)

        # Determine overall status
        failed_rejected = [c for c in checks if c.status == ValidationStatus.REJECTED]
        failed_warnings = [c for c in checks if c.status == ValidationStatus.WARNING]

        if failed_rejected:
            status = ValidationStatus.REJECTED
            message = failed_rejected[0].message
        elif failed_warnings:
            status = ValidationStatus.WARNING
            message = f"Warnings: {len(failed_warnings)}"
        else:
            status = ValidationStatus.APPROVED
            message = "All checks passed"

        return ValidationResult(
            order_id=request.client_order_id,
            status=status,
            checks=checks,
            overall_message=message
        )

    def _check_order_size(
        self,
        request: UnifiedOrderRequest,
        portfolio_value: Decimal
    ) -> ValidationCheck:
        """Validate order size against limits."""

        order_value = request.quantity * (request.price or Decimal("0"))

        # Check minimum
        if order_value < self.limits.min_order_size:
            return ValidationCheck(
                name="min_order_size",
                passed=False,
                status=ValidationStatus.REJECTED,
                message=f"Order ${order_value:.2f} below minimum ${self.limits.min_order_size}",
                details={"order_value": order_value}
            )

        # Check percentage of portfolio
        if portfolio_value > 0:
            order_pct = order_value / portfolio_value
            if order_pct > self.limits.max_order_pct:
                return ValidationCheck(
                    name="max_order_pct",
                    passed=False,
                    status=ValidationStatus.REJECTED,
                    message=f"Order {order_pct:.1%} exceeds max {self.limits.max_order_pct:.1%}",
                    details={"order_pct": order_pct}
                )

        return ValidationCheck(
            name="order_size",
            passed=True,
            status=ValidationStatus.APPROVED,
            message="Order size within limits",
            details={}
        )

    # ... (additional check methods)
```

---

## TESTING REQUIREMENTS

### Integration Tests
```bash
# Week 2 integration tests
pytest tests/agents/test_risk_manager_enhanced.py -v
pytest tests/execution/test_triad_service_refactored.py -v
pytest tests/integration/test_security_integration.py -v
```

### Security Tests
- [ ] Unauthorized execution blocked
- [ ] Risky trades rejected
- [ ] Audit logs written
- [ ] Events published
- [ ] All 10 validation checks run

---

## ACCEPTANCE CRITERIA

- [ ] RiskManagerAgent extended with OrderRiskValidator
- [ ] TriadService migrated to `execution/` folder
- [ ] OrderExecutor used for actual execution
- [ ] AgentGatekeeper authorization added
- [ ] AuditLogger integration complete
- [ ] EventBus publication working
- [ ] All 10 risk validation checks implemented
- [ ] 100% test coverage for new code
- [ ] All 734 existing tests passing

---

## COMMIT MESSAGE
```
feat(risk): Enhanced RiskManager + TriadService migration [WEEK2]

- Extend RiskManagerAgent with OrderRiskValidator (10 checks)
- Migrate TriadService to execution/ with OODA integration
- Add AgentGatekeeper authorization checks
- Add AuditLogger logging
- Add EventBus publication
- Full security compliance

Refs: EXECUTION_AUDIT_CRITICAL_FINDINGS.md
```

---

**END OF PROMPT**
