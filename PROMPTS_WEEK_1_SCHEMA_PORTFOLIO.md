# MASTER PROMPT: Week 1 - Unified Schema + PortfolioManagerAgent

> **Agent Role:** Senior Python Architect
> **Task:** P0 Critical - Foundation for Exchange Integration Refactor
> **Duration:** Week 1 (5-7 days)
> **Output:** Production-ready code with 100% test coverage

---

## CONTEXT & BACKGROUND

### Repository
```
https://github.com/RakeshRamkhelawan/Agentic-trader-
```

### Tech Stack
- Python 3.13+
- FastAPI 0.104+
- Pydantic v2
- CCXT (exchange connectivity)
- Redis 7.4.7 (event bus)
- ClickHouse (analytics)
- Pytest 8.4+
- Poetry (dependency management)

### Current Architecture
**OODA Loop System (EXISTING):**
```
Observation → Orientation → Decision → Action
   ↓              ↓            ↓         ↓
DataScout   AnalystAgent  TraderAgent  OrderExecutor
                                      ↓
                              BitvavoAdapter/RevolutXAdapter
```

**New System (TO INTEGRATE):**
```
TriadService → OrderManager → BitvavoConnector/RevolutConnector
     ↓
PortfolioManager (multi-exchange aggregation)
OrderRiskValidator (pre-trade validation)
```

### Critical Audit Findings
1. **Schema Conflict:** 3 incompatible Order types
   - `schemas/orders.py`: float quantities, UUID ids
   - `core/schemas/ooda_types.py`: float quantities, string ids
   - `exchange/base_exchange.py`: Decimal quantities, custom Symbol

2. **Security Gap:** New system bypasses AgentGatekeeper and audit logging

3. **Duplication:** 2,700+ lines of duplicate adapter code

---

## TASK SPECIFICATION

### Objective
Create unified schema foundation and PortfolioManagerAgent that integrates multi-exchange portfolio aggregation into OODA architecture.

### Deliverables

#### 1. UnifiedOrderRequest Schema
**File:** `backend/schemas/unified_execution.py`

**Requirements:**
```python
from decimal import Decimal
from pydantic import BaseModel, Field, model_validator
from typing import Optional
from enum import Enum
import uuid

class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"

class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

class TimeInForce(str, Enum):
    GTC = "gtc"  # Good Till Cancelled
    IOC = "ioc"  # Immediate Or Cancel
    FOK = "fok"  # Fill Or Kill
    GTD = "gtd"  # Good Till Date
    POST_ONLY = "post_only"

class UnifiedOrderRequest(BaseModel):
    """
    Unified order request schema combining best of existing and new systems.

    Bridges OODA ExecutionPlan with exchange OrderRequest.
    """
    # Identification (from both systems)
    client_order_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique client order ID"
    )
    trace_id: str = Field(
        ...,
        description="Distributed trace ID for audit logging"
    )

    # Symbol (unified format)
    symbol: str = Field(
        ...,
        pattern=r"^[A-Z0-9]+/[A-Z0-9]+$",
        description="Trading pair in BASE/QUOTE format (e.g., BTC/EUR)"
    )

    # Order details
    side: OrderSide
    order_type: OrderType

    # Financial values as Decimal (from new system - CRITICAL for precision)
    quantity: Decimal = Field(
        ...,
        gt=0,
        description="Order quantity as Decimal for precision"
    )
    price: Optional[Decimal] = Field(
        None,
        gt=0,
        description="Limit price (None for market orders)"
    )
    stop_price: Optional[Decimal] = Field(
        None,
        gt=0,
        description="Stop price for stop orders"
    )
    expected_price: Decimal = Field(
        ...,
        gt=0,
        description="Expected fill price for slippage calculation"
    )

    # Advanced options (from new system)
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
    strategy_id: Optional[str] = Field(
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
    metadata: dict = Field(
        default_factory=dict,
        description="Exchange-specific parameters"
    )

    model_config = ConfigDict(frozen=True, validate_assignment=True)

    @model_validator(mode='after')
    def validate_limit_order(self) -> 'UnifiedOrderRequest':
        """Ensure limit orders have a price."""
        if self.order_type in (OrderType.LIMIT, OrderType.STOP_LIMIT):
            if self.price is None:
                raise ValueError("Limit orders require a price")
        return self

    @model_validator(mode='after')
    def validate_stop_order(self) -> 'UnifiedOrderRequest':
        """Ensure stop orders have a stop price."""
        if self.order_type in (OrderType.STOP, OrderType.STOP_LIMIT):
            if self.stop_price is None:
                raise ValueError("Stop orders require a stop_price")
        return self

    def to_decimal_string(self) -> dict:
        """Convert Decimal fields to strings for JSON serialization."""
        return {
            'client_order_id': self.client_order_id,
            'trace_id': self.trace_id,
            'symbol': self.symbol,
            'side': self.side.value,
            'order_type': self.order_type.value,
            'quantity': str(self.quantity),
            'price': str(self.price) if self.price else None,
            'stop_price': str(self.stop_price) if self.stop_price else None,
            'expected_price': str(self.expected_price),
            'time_in_force': self.time_in_force.value,
            'post_only': self.post_only,
            'reduce_only': self.reduce_only,
            'strategy_id': self.strategy_id,
            'caller_name': self.caller_name,
            'caller_role': self.caller_role,
            'metadata': self.metadata
        }

    @classmethod
    def from_legacy_float(
        cls,
        symbol: str,
        side: str,
        qty: float,
        price: Optional[float] = None,
        **kwargs
    ) -> 'UnifiedOrderRequest':
        """
        Create from legacy float-based order (backward compatibility).

        WARNING: This converts float to Decimal which may lose precision.
        Use only during transition period.
        """
        return cls(
            symbol=symbol,
            side=OrderSide(side.lower()),
            order_type=OrderType.LIMIT if price else OrderType.MARKET,
            quantity=Decimal(str(qty)),  # Convert via string to minimize error
            price=Decimal(str(price)) if price else None,
            expected_price=Decimal(str(price)) if price else Decimal("0"),
            **kwargs
        )


class UnifiedOrderResponse(BaseModel):
    """Unified order response from exchange."""

    order_id: str
    client_order_id: str
    status: str  # pending, open, filled, cancelled, rejected

    filled_quantity: Decimal = Decimal("0")
    remaining_quantity: Decimal
    average_price: Optional[Decimal] = None

    fee: Decimal = Decimal("0")
    fee_currency: str = ""

    error_message: Optional[str] = None
    raw_response: Optional[dict] = None

    timestamp: float = Field(default_factory=lambda: datetime.now(UTC).timestamp())

    model_config = ConfigDict(frozen=True)
```

**Tests Required:**
```python
# tests/schemas/test_unified_execution.py
import pytest
from decimal import Decimal
from backend.schemas.unified_execution import UnifiedOrderRequest, OrderType

class TestUnifiedOrderRequest:
    def test_decimal_precision(self):
        """Ensure Decimal maintains precision."""
        order = UnifiedOrderRequest(
            trace_id="test-123",
            symbol="BTC/EUR",
            side="buy",
            order_type=OrderType.LIMIT,
            quantity=Decimal("0.12345678"),
            price=Decimal("45000.12345678"),
            expected_price=Decimal("45000")
        )
        assert order.quantity == Decimal("0.12345678")
        assert order.price == Decimal("45000.12345678")

    def test_legacy_float_conversion(self):
        """Test backward compatibility with float."""
        order = UnifiedOrderRequest.from_legacy_float(
            symbol="BTC/EUR",
            side="buy",
            qty=0.1,
            price=45000.33,
            trace_id="test-123",
            expected_price=45000.33
        )
        assert isinstance(order.quantity, Decimal)
        assert order.quantity == Decimal("0.1")

    def test_limit_order_requires_price(self):
        """Validation: limit orders need price."""
        with pytest.raises(ValueError):
            UnifiedOrderRequest(
                trace_id="test-123",
                symbol="BTC/EUR",
                side="buy",
                order_type=OrderType.LIMIT,
                quantity=Decimal("0.1"),
                expected_price=Decimal("45000")
                # Missing price!
            )
```

#### 2. Refactored PortfolioManager
**File:** `backend/execution/portfolio_manager.py`

**Migration:** Move from `backend/exchange/portfolio_manager.py`

**Changes Required:**
1. Use `Decimal` instead of `float` for all financial values
2. Accept existing exchange adapters (BitvavoAdapter, RevolutXAdapter)
3. Convert return values to OODA `PortfolioState` schema

```python
from decimal import Decimal
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime

from backend.execution.bitvavo_adapter import BitvavoAdapter
from backend.execution.revolut_x_adapter import RevolutXAdapter
from backend.core.schemas.ooda_types import PortfolioState, CapitalAllocation

@dataclass
class AssetAllocation:
    """Asset allocation across exchanges."""
    asset: str
    total: Decimal
    free: Decimal
    used: Decimal
    by_exchange: Dict[str, Decimal] = field(default_factory=dict)
    price_usd: Optional[Decimal] = None
    value_usd: Optional[Decimal] = None

@dataclass
class PortfolioSnapshot:
    """Complete portfolio snapshot."""
    timestamp: datetime
    total_value_usd: Decimal
    assets: Dict[str, AssetAllocation]
    exchanges: List[str]

class PortfolioManager:
    """
    Multi-exchange portfolio manager.

    Integrates with existing execution adapters.
    Provides unified view of positions across exchanges.
    """

    def __init__(self):
        self._adapters: Dict[str, any] = {}
        self._price_cache: Dict[str, tuple] = {}

    def register_adapter(self, name: str, adapter):
        """Register an exchange adapter."""
        self._adapters[name] = adapter

    async def get_portfolio(self) -> PortfolioSnapshot:
        """Get aggregated portfolio across all exchanges."""
        # Aggregate from all registered adapters
        # ... (implementation from existing exchange/portfolio_manager.py)

    async def get_portfolio_state(self) -> PortfolioState:
        """
        Convert to OODA PortfolioState.

        Returns:
            PortfolioState compatible with FundManagerAgent
        """
        snapshot = await self.get_portfolio()

        return PortfolioState(
            total_equity=float(snapshot.total_value_usd),  # Convert for OODA compat
            available_capital=float(self._get_free_capital(snapshot)),
            total_exposure_pct=self._calculate_exposure(snapshot),
            num_open_positions=len(snapshot.assets),
            timestamp=datetime.utcnow().timestamp()
        )
```

#### 3. PortfolioManagerAgent
**File:** `backend/agents/portfolio_manager_agent.py`

```python
"""
PortfolioManagerAgent - OODA wrapper for PortfolioManager.

Provides multi-exchange portfolio aggregation as an agent service.
Integrates with FundManagerAgent for capital allocation decisions.
"""

from typing import Any, Optional

from backend.agents.base_agent import BaseAgent
from backend.execution.portfolio_manager import PortfolioManager
from backend.core.schemas.ooda_types import PortfolioState, CapitalAllocation
from backend.execution.bitvavo_adapter import BitvavoAdapter
from backend.execution.revolut_x_adapter import RevolutXAdapter


class PortfolioManagerAgent(BaseAgent):
    """
    Agent wrapper for multi-exchange portfolio management.

    Extends BaseAgent to participate in OODA loop while
    providing cross-exchange portfolio visibility.
    """

    def __init__(
        self,
        llm_provider: Any | None = None,
        event_bus: Any | None = None,
    ):
        super().__init__(
            agent_name="PortfolioManager",
            llm_provider=llm_provider,
            event_bus=event_bus,
        )

        # Initialize portfolio manager
        self.portfolio_manager = PortfolioManager()
        self._adapters_initialized = False

    async def initialize_adapters(self):
        """Initialize and register exchange adapters."""
        if self._adapters_initialized:
            return

        from backend.core.config.settings import settings

        # Initialize Bitvavo if configured
        if settings.BITVAVO_API_KEY:
            bitvavo = BitvavoAdapter()
            if await bitvavo.initialize():
                self.portfolio_manager.register_adapter("bitvavo", bitvavo)
                self.logger.info("Bitvavo adapter registered")

        # Initialize Revolut if configured
        if settings.REVOLUT_API_KEY:
            revolut = RevolutXAdapter()
            if await revolut.connect():
                self.portfolio_manager.register_adapter("revolut", revolut)
                self.logger.info("Revolut adapter registered")

        self._adapters_initialized = True

    async def analyze(
        self,
        features: dict[str, Any],
        context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Analyze portfolio state (ReAct pattern).

        Returns portfolio analysis for other agents.
        """
        await self.initialize_adapters()

        # Get portfolio state
        portfolio = await self.portfolio_manager.get_portfolio_state()

        # Analyze allocation
        analysis = {
            "total_equity": portfolio.total_equity,
            "available_capital": portfolio.available_capital,
            "exposure_pct": portfolio.total_exposure_pct,
            "open_positions": portfolio.num_open_positions,
            "risk_level": self._assess_risk_level(portfolio),
        }

        # Publish thought
        await self.publish_thought(
            reasoning=f"Portfolio exposure: {portfolio.total_exposure_pct:.1%}, "
                     f"Available: ${portfolio.available_capital:,.2f}",
            confidence=0.95,
            data=analysis
        )

        return analysis

    async def get_portfolio_state(self) -> PortfolioState:
        """Get OODA-compatible portfolio state."""
        await self.initialize_adapters()
        return await self.portfolio_manager.get_portfolio_state()

    def _assess_risk_level(self, portfolio: PortfolioState) -> str:
        """Assess portfolio risk level."""
        if portfolio.total_exposure_pct > 0.8:
            return "high"
        elif portfolio.total_exposure_pct > 0.5:
            return "medium"
        return "low"
```

#### 4. Feature Flag
**File:** `backend/core/config/feature_flags.py`

```python
"""Feature flags for gradual rollout."""

from pydantic_settings import BaseSettings

class FeatureFlags(BaseSettings):
    """Feature flags for safe rollout of new features."""

    # Week 1: Unified Schema
    USE_UNIFIED_SCHEMA: bool = False
    USE_PORTFOLIO_MANAGER_AGENT: bool = False

    # Week 2: Risk Integration
    USE_ENHANCED_RISK_VALIDATOR: bool = False

    # Week 3: TriadService Migration
    USE_REFACTORED_TRIAD_SERVICE: bool = False

    class Config:
        env_prefix = "FEATURE_"

# Global instance
feature_flags = FeatureFlags()
```

#### 5. ADR Document
**File:** `docs/adrs/2026-02-28-unified-execution-schema.md`

```markdown
# ADR-042: Unified Execution Schema

## Status
Proposed → Week 1 Implementation

## Context
Three incompatible order schemas exist:
1. schemas/orders.py (float, UUID)
2. core/schemas/ooda_types.py (float, str)
3. exchange/base_exchange.py (Decimal, custom Symbol)

## Decision
Create UnifiedOrderRequest with:
- Decimal for all financial values
- String IDs for compatibility
- Fields from both existing schemas
- Backward compatibility methods

## Consequences
- Positive: Single source of truth, type safety, Decimal precision
- Negative: Migration effort, temporary duplication

## Implementation
- Week 1: Schema + PortfolioManagerAgent
- Week 2: Risk integration
- Week 3: Cleanup
```

---

## TESTING REQUIREMENTS

### Unit Tests
```bash
pytest tests/schemas/test_unified_execution.py -v
pytest tests/execution/test_portfolio_manager.py -v
pytest tests/agents/test_portfolio_manager_agent.py -v
```

### Integration Tests
```bash
pytest tests/integration/test_portfolio_multi_exchange.py -v
```

### Coverage
- Minimum 95% coverage for new code
- All 734 existing tests must pass

---

## ACCEPTANCE CRITERIA

- [ ] `UnifiedOrderRequest` created with all fields
- [ ] `PortfolioManager` refactored to use Decimal
- [ ] `PortfolioManagerAgent` created and tested
- [ ] Feature flags implemented
- [ ] ADR written and approved
- [ ] All tests passing (734+ existing + new)
- [ ] Docker compose runs without errors
- [ ] No breaking changes to existing API

---

## COMMIT MESSAGE
```
feat(execution): UnifiedOrderRequest + PortfolioManagerAgent [WEEK1]

- Add UnifiedOrderRequest schema with Decimal precision
- Refactor PortfolioManager to execution/ folder
- Create PortfolioManagerAgent for OODA integration
- Add feature flags for gradual rollout
- Full test coverage

Refs: EXECUTION_AUDIT_CRITICAL_FINDINGS.md
```

---

**END OF PROMPT**
