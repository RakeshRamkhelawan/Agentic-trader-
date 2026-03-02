# MASTER PROMPTS INDEX - Exchange Integration Refactor

> **Project:** Agentic Trader Platform
> **Scope:** Full refactor of exchange/execution layer
> **Timeline:** 4 weeks
> **Status:** Ready for execution

---

## Quick Start

Use these prompts sequentially with your LLM code agents (Claude, Gemini, Copilot):

1. **Week 1:** `PROMPTS_WEEK_1_SCHEMA_PORTFOLIO.md` - Foundation
2. **Week 2:** `PROMPTS_WEEK_2_RISK_TRIAD.md` - Security integration
3. **Week 3-4:** `PROMPTS_WEEK_3_4_CLEANUP_TESTING.md` - Cleanup & validation

---

## Prompt Overview

### Prompt 1: Week 1 - Foundation
**File:** `PROMPTS_WEEK_1_SCHEMA_PORTFOLIO.md`

**Scope:**
- Create `UnifiedOrderRequest` schema (Decimal precision)
- Refactor `PortfolioManager` to `execution/` folder
- Create `PortfolioManagerAgent` (OODA integration)
- Feature flags for gradual rollout
- ADR documentation

**Lines of Code:** ~1,500
**Tests:** 15+ new tests
**Risk:** Low (additive changes)

**Key Deliverables:**
```python
backend/schemas/unified_execution.py       # Unified schema
backend/execution/portfolio_manager.py     # Refactored PM
backend/agents/portfolio_manager_agent.py  # Agent wrapper
backend/core/config/feature_flags.py       # Feature flags
docs/adrs/2026-02-28-unified-schema.md     # ADR
```

---

### Prompt 2: Week 2 - Security Integration
**File:** `PROMPTS_WEEK_2_RISK_TRIAD.md`

**Scope:**
- Extend `RiskManagerAgent` with `OrderRiskValidator` (10 checks)
- Migrate `TriadService` to `execution/` folder
- Add `AgentGatekeeper` authorization
- Add `AuditLogger` integration
- Add `EventBus` publication
- Security integration tests

**Lines of Code:** ~2,000
**Tests:** 20+ new tests
**Risk:** Medium (security critical)

**Key Deliverables:**
```python
backend/agents/risk_manager_agent.py       # Enhanced
backend/execution/triad_service.py         # Migrated
backend/execution/risk_validator.py        # Moved
backend/governance/security_integration.py # New
tests/integration/test_security.py         # Tests
```

---

### Prompt 3: Week 3-4 - Cleanup & Validation
**File:** `PROMPTS_WEEK_3_4_CLEANUP_TESTING.md`

**Scope:**
- Remove duplicate components (2,700 lines)
- Deprecate `ShadowPortfolio`
- Full test matrix (unit/integration/e2e)
- Performance validation
- Decimal migration validation
- Documentation (README + ADR)
- Git cleanup

**Lines Removed:** ~2,700
**Tests:** 30+ new tests
**Risk:** High (destructive changes)

**Files Removed:**
```
backend/exchange/connectors/bitvavo_connector.py  (-480 lines)
backend/exchange/connectors/revolut_connector.py  (-420 lines)
backend/exchange/order_manager.py                 (-620 lines)
backend/exchange/base_exchange.py                 (-680 lines)
backend/exchange/                                 (-2,700 total)
```

---

## Decision Matrix

### Your Choices → Implementation

| Decision | Choice | Implementation |
|----------|--------|----------------|
| **Decimal migration** | Gradual (B) | `from_legacy_float()` method + feature flag |
| **Timeline** | 4 weeks | As specified in prompts |
| **Parallel system** | Yes (A) | Feature flags keep old code accessible |
| **First step** | Schema (B) | Week 1 starts with UnifiedOrderRequest |

---

## Usage Instructions

### For Human Developers

1. **Review each prompt** before giving to LLM
2. **Adjust file paths** if your repo structure differs
3. **Run tests after each week** before proceeding
4. **Keep feature flags ON** until Week 4 validation complete

### For LLM Agents

Each prompt is **self-contained** with:
- Full context and background
- Existing code references
- Concrete implementation details
- Test requirements
- Acceptance criteria

**Execute sequentially** - Week 2 depends on Week 1, etc.

---

## File Structure After Refactor

```
backend/
├── agents/
│   ├── portfolio_manager_agent.py      # [NEW Week 1]
│   ├── risk_manager_agent.py           # [ENHANCED Week 2]
│   └── ...
├── execution/
│   ├── portfolio_manager.py            # [MOVED Week 1]
│   ├── risk_validator.py               # [MOVED Week 2]
│   ├── triad_service.py                # [MOVED Week 2]
│   ├── bitvavo_adapter.py              # [EXISTING]
│   ├── revolut_x_adapter.py            # [EXISTING]
│   ├── order_executor.py               # [EXISTING]
│   ├── shadow_portfolio.py             # [DEPRECATED Week 3]
│   └── ...
├── schemas/
│   ├── unified_execution.py            # [NEW Week 1]
│   ├── orders.py                       # [EXISTING - keep for compat]
│   └── ...
├── core/config/
│   └── feature_flags.py                # [NEW Week 1]
└── exchange/                           # [DELETED Week 3]
    └── (removed)

docs/
├── adrs/
│   ├── 2026-02-28-unified-schema.md    # [NEW Week 1]
│   └── 2026-02-28-parallel-systems-refactor.md  # [NEW Week 4]
└── README.md                           # [UPDATED Week 4]

tests/
├── schemas/test_unified_execution.py   # [NEW Week 1]
├── agents/test_portfolio_manager_agent.py  # [NEW Week 1]
├── agents/test_risk_manager_enhanced.py    # [NEW Week 2]
├── execution/test_triad_service_refactored.py  # [NEW Week 2]
├── integration/test_security.py        # [NEW Week 2]
├── integration/test_decimal_migration.py     # [NEW Week 4]
└── performance/test_execution.py       # [NEW Week 4]
```

---

## Success Metrics

### Quantitative

| Metric | Before | Target | Week 4 |
|--------|--------|--------|--------|
| **Total LOC** | 8,700 | 6,500 | TBD |
| **Duplicate LOC** | 2,700 | 0 | TBD |
| **Test Coverage** | 85% | >95% | TBD |
| **Tests Passing** | 734 | 734+ | TBD |

### Qualitative

- ✅ Single source of truth for orders
- ✅ Decimal precision throughout
- ✅ Security checks on all execution paths
- ✅ Audit logging complete
- ✅ Event bus integration
- ✅ Multi-exchange portfolio support
- ✅ 10+ risk validation checks

---

## Risk Management

### High Risk Points

1. **Week 2 Security Integration**
   - Risk: Breaking authorization flow
   - Mitigation: Extensive testing, feature flags

2. **Week 3 Code Removal**
   - Risk: Accidentally breaking dependencies
   - Mitigation: Search all imports before removal

3. **Decimal Migration**
   - Risk: Precision loss during conversion
   - Mitigation: `from_legacy_float()` with string conversion

### Rollback Strategy

If critical issues arise:

```bash
# Quick rollback to Week 1 state
git revert --no-commit Week2..HEAD
git commit -m "rollback: Emergency revert to Week 1"

# Or use feature flags
export FEATURE_USE_REFACTORED_TRIAD_SERVICE=false
```

---

## Support Resources

### Documentation
- `FULL_SCOPE_AUDIT_EXCHANGE_INTEGRATION.md` - Full audit (14KB)
- `EXECUTION_AUDIT_CRITICAL_FINDINGS.md` - Critical issues (11KB)
- `EXCHANGE_INTEGRATION_SUMMARY.md` - Pre-refactor state (16KB)

### Code References
- `backend/agents/base_agent.py` - Agent architecture
- `backend/execution/order_executor.py` - Execution engine
- `backend/core/schemas/ooda_types.py` - OODA types

---

## Checklist for Each Week

### Week 1 Start
- [ ] Review Prompt 1
- [ ] Ensure Week 1 environment ready
- [ ] Backup current state: `git tag pre-week1`
- [ ] Run baseline tests: `pytest --collect-only | wc -l`

### Week 2 Start
- [ ] Week 1 tests passing
- [ ] Review Prompt 2
- [ ] Verify UnifiedOrderRequest working
- [ ] Update dependencies if needed

### Week 3 Start
- [ ] Week 2 tests passing
- [ ] Review Prompt 3
- [ ] Verify security integration working
- [ ] Prepare for destructive changes

### Week 4 Start
- [ ] All cleanup complete
- [ ] Run full test suite
- [ ] Performance benchmarking
- [ ] Documentation review

### Week 4 End
- [ ] All tests passing (734+)
- [ ] Coverage >95%
- [ ] Documentation complete
- [ ] ADRs approved
- [ ] Production ready

---

## Questions?

If prompts need clarification:
1. Check audit documents for context
2. Review existing code in referenced files
3. Adjust file paths for your repo structure
4. Keep feature flags ON until fully validated

---

**Ready to execute?** Start with Prompt 1: `PROMPTS_WEEK_1_SCHEMA_PORTFOLIO.md`

Good luck! 🚀
