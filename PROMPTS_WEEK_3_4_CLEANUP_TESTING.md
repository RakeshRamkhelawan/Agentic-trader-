# MASTER PROMPT: Week 3-4 - Cleanup, Testing & Validation

> **Agent Role:** Senior Python Architect
> **Task:** P2/P3 - Code Cleanup & Full Validation
> **Duration:** Week 3-4 (10-14 days)
> **Prerequisite:** Week 1-2 completed

---

## CONTEXT & BACKGROUND

### Current State After Week 1-2
```
✅ UnifiedOrderRequest schema (Decimal precision)
✅ PortfolioManagerAgent (OODA-integrated)
✅ Enhanced RiskManagerAgent (10+ validation checks)
✅ TriadService migrated to execution/ with security
✅ OrderExecutor used for actual execution
✅ AgentGatekeeper authorization
✅ AuditLogger integration
```

### Current Duplication Status
| Component | Existing | New (Week 1-2) | Status |
|-----------|----------|----------------|--------|
| Bitvavo adapter | ✅ bitvavo_adapter.py | ✅ bitvavo_connector.py | DUPLICATE |
| Revolut adapter | ✅ revolut_x_adapter.py | ✅ revolut_connector.py | DUPLICATE |
| Order executor | ✅ order_executor.py | ✅ order_manager.py | OVERLAP |
| Portfolio | ⚠️ shadow_portfolio.py | ✅ portfolio_manager.py | REPLACE |
| Base interface | ✅ broker_interface.py | ✅ base_exchange.py | DUPLICATE |
| Factory | ❌ | ✅ exchange_factory.py | OPTIONAL |

### Goals for Week 3-4
1. **Remove all duplicates** (2,700+ lines)
2. **Deprecate old shadow_portfolio**
3. **Full test coverage** (>95%)
4. **Performance validation**
5. **Documentation** (ADRs, README)
6. **Decimal migration validation**

---

## TASK SPECIFICATION

### Objective
Clean up codebase by removing duplicate components while ensuring full system stability through comprehensive testing.

---

## DELIVERABLE 1: Remove Duplicate Components

### Step 1: Remove Exchange Connectors

**Files to DELETE:**
```bash
backend/exchange/connectors/bitvavo_connector.py      # 480 lines
backend/exchange/connectors/revolut_connector.py       # 420 lines
backend/exchange/connectors/__init__.py                # 20 lines
backend/exchange/connectors/                           # Empty folder
```

**Verification:**
```bash
# Ensure no imports break
grep -r "from backend.exchange.connectors" backend/
# Should return: 0 matches
```

### Step 2: Remove OrderManager

**File to DELETE:**
```bash
backend/exchange/order_manager.py                      # 620 lines
```

**Migration Checklist:**
- [ ] All usages of `OrderManager` migrated to `OrderExecutor`
- [ ] TriadService uses `OrderExecutor` (completed in Week 2)
- [ ] No references in imports

### Step 3: Remove BaseExchange

**File to DELETE:**
```bash
backend/exchange/base_exchange.py                      # 680 lines
```

**Note:** Keep interfaces in `broker_interface.py` and `exchange_adapter.py`

### Step 4: Remove ExchangeFactory (Optional)

**Decision Required:**
- Option A: Keep `ExchangeFactory` as utility (240 lines)
- Option B: Remove and use direct adapter instantiation

**Recommendation:** Keep but move to `backend/execution/exchange_factory.py`

### Step 5: Deprecate ShadowPortfolio

**File:** `backend/execution/shadow_portfolio.py`

**Action:** Mark as deprecated, redirect to PortfolioManagerAgent

```python
"""
ShadowPortfolio - DEPRECATED

This module is deprecated. Use PortfolioManagerAgent instead.

Migration:
    Old: from backend.execution.shadow_portfolio import ShadowPortfolio
    New: from backend.agents.portfolio_manager_agent import PortfolioManagerAgent

Deprecation date: 2026-02-28
Removal date: 2026-03-28
"""

import warnings
from backend.agents.portfolio_manager_agent import PortfolioManagerAgent

warnings.warn(
    "ShadowPortfolio is deprecated. Use PortfolioManagerAgent instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export for backward compatibility
__all__ = ['PortfolioManagerAgent']
```

---

## DELIVERABLE 2: Full Test Matrix

### Test Categories

#### Unit Tests
```python
# tests/schemas/test_unified_execution.py
# tests/execution/test_portfolio_manager.py
# tests/agents/test_portfolio_manager_agent.py
# tests/agents/test_risk_manager_enhanced.py
# tests/execution/test_triad_service_refactored.py
```

#### Integration Tests
```python
# tests/integration/test_portfolio_multi_exchange.py
# tests/integration/test_security_integration.py
# tests/integration/test_decimal_migration.py
```

#### End-to-End Tests
```python
# tests/e2e/test_full_trading_flow.py
```

### Test Matrix

| Test Suite | Paper Mode | Live Mode | Multi-Exchange | Decimal | Coverage |
|------------|-----------|-----------|----------------|---------|----------|
| Schema | ✅ | ✅ | N/A | ✅ | 100% |
| Portfolio | ✅ | ✅ | ✅ | ✅ | 95%+ |
| Risk | ✅ | ✅ | N/A | ✅ | 95%+ |
| TriadService | ✅ | ✅ | ✅ | ✅ | 95%+ |
| Security | ✅ | ✅ | N/A | N/A | 100% |
| Full Flow | ✅ | ⚠️ | ✅ | ✅ | 90%+ |

### Test Implementation

#### Test: Decimal Precision
```python
# tests/integration/test_decimal_migration.py
import pytest
from decimal import Decimal
from backend.schemas.unified_execution import UnifiedOrderRequest
from backend.core.schemas.ooda_types import ExecutionPlan

class TestDecimalMigration:
    """Test that Decimal precision is maintained throughout."""

    def test_order_request_decimal_precision(self):
        """UnifiedOrderRequest maintains Decimal precision."""
        order = UnifiedOrderRequest(
            trace_id="test",
            symbol="BTC/EUR",
            side="buy",
            order_type="limit",
            quantity=Decimal("0.12345678901234"),
            price=Decimal("45000.12345678901234"),
            expected_price=Decimal("45000")
        )

        assert order.quantity == Decimal("0.12345678901234")
        assert order.price == Decimal("45000.12345678901234")

    def test_no_float_in_financial_fields(self):
        """Ensure no float in financial fields."""
        # This should fail if we accidentally use float
        with pytest.raises((TypeError, ValueError)):
            UnifiedOrderRequest(
                trace_id="test",
                symbol="BTC/EUR",
                side="buy",
                order_type="limit",
                quantity=0.1,  # float - should fail!
                price=45000.33,  # float - should fail!
                expected_price=Decimal("45000")
            )

    def test_backward_compatibility_conversion(self):
        """Float to Decimal conversion works correctly."""
        order = UnifiedOrderRequest.from_legacy_float(
            symbol="BTC/EUR",
            side="buy",
            qty=0.1,
            price=45000.33,
            trace_id="test",
            expected_price=45000.33
        )

        # Should be Decimal, not float
        assert isinstance(order.quantity, Decimal)
        assert isinstance(order.price, Decimal)

        # Should maintain precision
        assert order.quantity == Decimal("0.1")
        assert order.price == Decimal("45000.33")
```

#### Test: Security Integration
```python
# tests/integration/test_security_integration.py
import pytest
from unittest.mock import Mock, patch

class TestSecurityIntegration:
    """Test that security checks are in place."""

    @pytest.fixture
    def mock_gatekeeper(self):
        return Mock()

    @pytest.mark.asyncio
    async def test_unauthorized_execution_blocked(self, mock_gatekeeper):
        """Unauthorized execution attempts are blocked."""
        from backend.execution.triad_service import TriadService

        service = TriadService()
        mock_gatekeeper.check_permission.return_value = False
        service.gatekeeper = mock_gatekeeper

        # Attempt execution
        class MockDecision:
            action = "bullish"
            confidence = 0.8
            rationale = "Test"

        result = await service.execute_trade(MockDecision())

        assert result["status"] == "rejected"
        assert "Not authorized" in result["reason"]

    @pytest.mark.asyncio
    async def test_authorized_execution_allowed(self, mock_gatekeeper):
        """Authorized execution proceeds."""
        from backend.execution.triad_service import TriadService

        service = TriadService(trading_mode="paper")
        mock_gatekeeper.check_permission.return_value = True
        service.gatekeeper = mock_gatekeeper

        # Mock other dependencies
        service.risk_manager = Mock()
        service.risk_manager.assess_risk.return_value = Mock(
            decision=Mock(value="approve"),
            risk_score=0.3
        )

        # Attempt execution
        class MockDecision:
            action = "bullish"
            confidence = 0.8
            rationale = "Test"

        result = await service.execute_trade(MockDecision())

        # Should proceed (might fail for other reasons, but not auth)
        assert result["status"] != "rejected" or "Not authorized" not in result.get("reason", "")
```

#### Test: Multi-Exchange Portfolio
```python
# tests/integration/test_portfolio_multi_exchange.py
import pytest
from decimal import Decimal

class TestMultiExchangePortfolio:
    """Test multi-exchange portfolio aggregation."""

    @pytest.mark.asyncio
    async def test_portfolio_aggregates_multiple_exchanges(self):
        """Portfolio aggregates balances from multiple exchanges."""
        from backend.agents.portfolio_manager_agent import PortfolioManagerAgent

        agent = PortfolioManagerAgent()

        # Mock adapters
        agent.portfolio_manager._adapters = {
            "bitvavo": MockAdapter(balance={"EUR": Decimal("1000"), "BTC": Decimal("0.5")}),
            "revolut": MockAdapter(balance={"USD": Decimal("500"), "BTC": Decimal("0.3")})
        }

        portfolio = await agent.get_portfolio_state()

        # Should have aggregated BTC
        assert portfolio.total_equity > 0
        # Would need to mock price feeds for exact values
```

---

## DELIVERABLE 3: Performance Validation

### Benchmarks

#### Before/After Comparison
```python
# tests/performance/test_execution_performance.py
import time
import pytest

class TestExecutionPerformance:
    """Validate execution performance."""

    def test_order_creation_latency(self):
        """Order creation < 100ms."""
        from backend.schemas.unified_execution import UnifiedOrderRequest

        start = time.time()
        order = UnifiedOrderRequest(
            trace_id="perf-test",
            symbol="BTC/EUR",
            side="buy",
            order_type="limit",
            quantity=Decimal("0.1"),
            price=Decimal("45000"),
            expected_price=Decimal("45000")
        )
        elapsed = (time.time() - start) * 1000

        assert elapsed < 100, f"Order creation took {elapsed}ms"

    def test_risk_validation_latency(self):
        """Risk validation < 50ms."""
        from backend.execution.risk_validator import OrderRiskValidator

        validator = OrderRiskValidator()

        start = time.time()
        # Run validation
        elapsed = (time.time() - start) * 1000

        assert elapsed < 50, f"Risk validation took {elapsed}ms"
```

### Metrics to Track

| Metric | Before | Target | After |
|--------|--------|--------|-------|
| LOC (execution/) | 4,950 | 4,500 | TBD |
| Duplicate LOC | 2,700 | 0 | TBD |
| Test Coverage | 85% | >95% | TBD |
| Order Creation | <100ms | <100ms | TBD |
| Risk Validation | N/A | <50ms | TBD |

---

## DELIVERABLE 4: Documentation

### ADR: Parallel Systems Refactor

**File:** `docs/adrs/2026-02-28-parallel-systems-refactor.md`

```markdown
# ADR-043: Parallel Systems Refactor

## Status
Accepted → Implemented

## Context
Two parallel execution systems existed:
1. OODA-based (TraderAgent → OrderExecutor)
2. Service-based (TriadService → OrderManager)

This caused:
- 2,700+ lines of duplicate code
- Schema incompatibilities (3 Order types)
- Security bypass (new system skipped AgentGatekeeper)
- Maintenance burden

## Decision
Refactor into unified system:
1. Keep OODA architecture (agents, event bus, ReAct)
2. Integrate valuable components from new system:
   - PortfolioManager (multi-exchange aggregation)
   - OrderRiskValidator (10+ pre-trade checks)
   - Decimal precision for financial values
3. Remove duplicate adapters and OrderManager
4. Migrate TriadService to use OrderExecutor

## Consequences
- Positive: Single source of truth, reduced LOC, better security
- Negative: 4-week migration effort, temporary complexity

## Implementation
- Week 1: Unified schema + PortfolioManagerAgent
- Week 2: Risk integration + TriadService migration
- Week 3-4: Cleanup + testing

## Metrics
- Before: 8,700 LOC (execution + exchange)
- After: 6,500 LOC (-25%)
- Coverage: 85% → 95%+
```

### README Update

**Section:** `## Execution Layer`

```markdown
### Execution Layer

The execution layer follows the OODA (Observe-Orient-Decide-Act) pattern:

```
TraderAgent (Decide)
    ↓
RiskManagerAgent (Validate)
    ↓
FundManagerAgent (Allocate)
    ↓
OrderExecutor (Act)
    ↓
BitvavoAdapter/RevolutXAdapter
```

#### Key Components

- **OrderExecutor**: Main execution engine with circuit breaker
- **PortfolioManagerAgent**: Multi-exchange portfolio aggregation
- **RiskManagerAgent**: Pre-trade validation (10+ checks)
- **TriadService**: High-level service integrating with OODA

#### Usage

```python
# Paper trading
service = TriadService(trading_mode="paper")
await service.initialize()
result = await service.execute_trade(decision)

# Live trading
service = TriadService(trading_mode="live")
await service.initialize(event_bus=event_bus)
result = await service.execute_trade(decision)
```

See [Execution ADR](../docs/adrs/2026-02-28-parallel-systems-refactor.md)
```

---

## DELIVERABLE 5: Git Cleanup

### Commit Sequence

```bash
# Week 3, Day 1: Remove duplicate adapters
git rm backend/exchange/connectors/bitvavo_connector.py
git rm backend/exchange/connectors/revolut_connector.py
git rm backend/exchange/connectors/__init__.py
git commit -m "refactor(execution): Remove duplicate exchange adapters [WEEK3]

- Remove BitvavoConnector (use BitvavoAdapter)
- Remove RevolutConnector (use RevolutXAdapter)
- Part of parallel systems refactor

Refs: ADR-043"

# Week 3, Day 2: Remove OrderManager
git rm backend/exchange/order_manager.py
git commit -m "refactor(execution): Remove OrderManager [WEEK3]

- Use OrderExecutor instead
- All migrations completed in Week 2

Refs: ADR-043"

# Week 3, Day 3: Remove BaseExchange
git rm backend/exchange/base_exchange.py
git commit -m "refactor(execution): Remove BaseExchange [WEEK3]

- Use existing broker_interface.py
- Use exchange_adapter.py for protocol

Refs: ADR-043"

# Week 3, Day 4: Deprecate ShadowPortfolio
git mv backend/execution/shadow_portfolio.py backend/execution/_deprecated_shadow_portfolio.py
git add backend/execution/shadow_portfolio.py  # New file with deprecation warning
git commit -m "refactor(execution): Deprecate ShadowPortfolio [WEEK3]

- Redirect to PortfolioManagerAgent
- Add deprecation warnings
- Will be removed in 30 days

Refs: ADR-043"

# Week 3, Day 5: Final cleanup
git rm -rf backend/exchange/  # After confirming everything moved
mkdir -p backend/exchange/legacy_readme.md  # Explain migration
git commit -m "refactor(execution): Remove exchange/ folder [WEEK3]

- All components migrated to execution/ or agents/
- 2,700 lines of duplicate code removed
- 25% reduction in execution layer LOC

Refs: ADR-043"
```

---

## ACCEPTANCE CRITERIA

### Week 3 (Cleanup)
- [ ] All duplicate adapters removed
- [ ] OrderManager removed
- [ ] BaseExchange removed
- [ ] ShadowPortfolio deprecated
- [ ] No broken imports
- [ ] 734 existing tests passing

### Week 4 (Validation)
- [ ] New test coverage >95%
- [ ] Decimal precision validated
- [ ] Security integration tested
- [ ] Multi-exchange portfolio tested
- [ ] Performance benchmarks met
- [ ] Documentation complete
- [ ] ADRs written
- [ ] Git history clean

### Final Metrics
- [ ] LOC reduction: 2,200+ lines
- [ ] Coverage: >95%
- [ ] Performance: <100ms order creation
- [ ] Security: 100% authorization coverage

---

## FINAL COMMIT MESSAGE
```
feat(execution): Complete parallel systems refactor [WEEK3-4]

- Remove 2,700 lines of duplicate code
- Unify execution under OODA architecture
- Integrate PortfolioManagerAgent
- Integrate enhanced RiskManagerAgent
- Migrate TriadService with full security
- Decimal precision throughout
- 95%+ test coverage
- Complete documentation

Metrics:
- LOC: 8,700 → 6,500 (-25%)
- Coverage: 85% → 95%
- Duplicates: 2,700 → 0

Refs: ADR-043, EXECUTION_AUDIT_CRITICAL_FINDINGS.md
```

---

## RISK MITIGATION

### Rollback Plan
If issues arise:
1. Revert last commit: `git revert HEAD`
2. Re-enable old code with feature flag
3. Debug in paper mode
4. Re-apply when fixed

### Feature Flags
Keep these until fully validated:
```python
USE_UNIFIED_SCHEMA = True
USE_PORTFOLIO_MANAGER_AGENT = True
USE_ENHANCED_RISK_VALIDATOR = True
USE_REFACTORED_TRIAD_SERVICE = True
```

---

**END OF PROMPT**
