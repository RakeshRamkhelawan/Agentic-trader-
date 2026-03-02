# ADR-042: Unified Execution Schema

## Status
Accepted → Implemented (Week 1)

## Context

The Agentic Trader Platform had three incompatible order schemas:

1. **schemas/orders.py** (Existing)
   - Uses `float` for quantities/prices
   - Uses `uuid.UUID` for order IDs
   - Pydantic v2 with validation

2. **core/schemas/ooda_types.py** (Existing)
   - Uses `float` for quantities/prices
   - Uses `str` for IDs
   - Includes audit fields (trace_id, caller_name)

3. **exchange/base_exchange.py** (New)
   - Uses `Decimal` for quantities/prices
   - Custom `Symbol` class
   - Includes time_in_force, post_only flags

This caused:
- Type incompatibility between components
- Floating-point precision errors in financial calculations
- Duplicated validation logic
- Confusion for developers

## Decision

Create a unified order schema (`UnifiedOrderRequest`) that combines the best features:

1. **Use `Decimal` for all financial values**
   - Eliminates floating-point precision errors
   - Critical for accurate P&L calculations

2. **Include audit fields from OODA**
   - `trace_id` for distributed tracing
   - `caller_name` and `caller_role` for authorization
   - `strategy_id` for audit trail

3. **Include advanced options from exchange/**
   - `time_in_force` (GTC/IOC/FOK)
   - `post_only` and `reduce_only` flags
   - `metadata` dict for exchange-specific options

4. **Maintain backward compatibility**
   - `from_legacy_float()` conversion method
   - `from_ooda_execution_plan()` adapter
   - Gradual migration path

## Consequences

### Positive
- Single source of truth for order data
- Type safety with Pydantic v2
- Financial precision with Decimal
- Complete audit trail
- Extensible metadata

### Negative
- Migration effort required
- Temporary duplication during transition
- All components must be updated

## Implementation

### Week 1: Foundation
- [x] Create `UnifiedOrderRequest` schema
- [x] Create `UnifiedOrderResponse` schema
- [x] Create `Symbol` helper class
- [x] Add backward compatibility methods
- [x] Write comprehensive tests
- [x] Create PortfolioManagerAgent
- [x] Add feature flags

### Week 2: Integration
- [ ] Update RiskManagerAgent
- [ ] Migrate TriadService
- [ ] Add security integration

### Week 3-4: Cleanup
- [ ] Remove duplicate schemas
- [ ] Deprecate old types
- [ ] Full test coverage

## Code Example

```python
# Before (float - dangerous)
order = OrderRequest(
    symbol="BTC/EUR",
    qty=0.1,           # float!
    limit_price=45000.33  # float!
)
# qty * price = 4500.032999999999 (precision loss!)

# After (Decimal - exact)
order = UnifiedOrderRequest(
    trace_id="trace-123",
    symbol="BTC/EUR",
    side=OrderSide.BUY,
    order_type=OrderType.LIMIT,
    quantity=Decimal("0.1"),      # Exact!
    price=Decimal("45000.33"),    # Exact!
    expected_price=Decimal("45000.33"),
    time_in_force=TimeInForce.GTC,
    post_only=True
)
# quantity * price = Decimal('4500.033') (exact!)
```

## References

- EXECUTION_AUDIT_CRITICAL_FINDINGS.md
- FULL_SCOPE_AUDIT_EXCHANGE_INTEGRATION.md
- Week 1 Implementation: PROMPTS_WEEK_1_SCHEMA_PORTFOLIO.md

## Date
February 28, 2026
