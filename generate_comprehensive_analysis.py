from datetime import datetime
from pathlib import Path

BASE_DIR = Path(
    r"c:\Users\rsram\Downloads\agentic_trader_platform_1734_20260109_210621"
)
DOCS_DIR = BASE_DIR / "docs"
DOCS_DIR.mkdir(exist_ok=True)


def read_file_safe(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except:
        return ""


def analyze_existing_docs():
    master_content = read_file_safe(BASE_DIR / "master_full.txt")
    fase01_content = read_file_safe(BASE_DIR / "fase01_full.txt")
    handover_content = read_file_safe(BASE_DIR / "handover_full.txt")
    epic01_content = read_file_safe(BASE_DIR / "epic01_full.txt")

    return {
        "master": master_content,
        "fase01": fase01_content,
        "handover": handover_content,
        "epic01": epic01_content,
    }


def generate_phase_review_document(docs):
    content = f"""# Phase-by-Phase Review Document
## Samkhya Yoga Agentic Trader — Comprehensive Architecture & Implementation Analysis

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Document Version:** 1.0  
**Status:** Production-Grade Review

---

## Executive Summary

This document provides a comprehensive phase-by-phase review of the Samkhya Yoga Agentic Trader implementation, analyzing technical feasibility, interdependencies, test coverage, and architectural elevation opportunities across all 7 phases (~180 microtasks).

**Key Findings:**
- ✅ Strong TDD foundation with real Swiss Ephemeris integration
- ✅ Clear triple-track architecture (OODA + Elemental + Navagraha)
- ⚠️ Phase 1 complexity requires restructuring (65 microtasks → 4-5 milestones)
- ⚠️ Caching strategy undefined for ephemeris calculations
- ⚠️ NavagrahaState threading not fully specified across layers
- 🎯 15 critical elevation opportunities identified

---

## Phase 1: Consciousness-OODA-Navagraha Bridge

### Current State

**Scope:** 9 tasks, ~65 microtasks covering:
- Real Swiss Ephemeris integration (pyswisseph + Kerykeion)
- NavagrahaState calculation and validation
- OODA loop foundational structure
- Elemental agent base classes
- Guna modulation framework
- Karma/Viveka learning foundations

**Existing Implementation:**
- ✅ `backend/core/navagraha/ephemeris.py` — EphemerisCalculator class exists
- ✅ `backend/core/navagraha/models.py` — PlanetState, GunaType models defined
- ✅ `backend/orchestration/navagraha_cache_integration.py` — Basic caching implemented
- ✅ `backend/tests/unit/core/navagraha/test_ephemeris.py` — Invariant tests present
- ⚠️ OODA coordinator exists but Navagraha integration incomplete

### Strengths

1. **Real Ephemeris Foundation:** No mocks, using NASA JPL DE431 via pyswisseph
2. **Invariant Testing:** Critical constraints enforced (9 planets, Rahu retrograde, etc.)
3. **Clear Data Models:** PlanetState, GunaType, NavagrahaState schemas defined
4. **Existing Caching Layer:** Foundation present in `navagraha_cache_integration.py`

### Gaps & Risks

| Gap | Impact | Risk Level |
|-----|--------|------------|
| **65 Microtasks Ungrouped** | Unclear dependencies, hard to track progress | HIGH |
| **NavagrahaState → OODA Threading Unclear** | Integration points not specified | HIGH |
| **Cache TTL Strategy Undefined** | Positions (5min), Aspects (15min), Rahu Kala (daily) | MEDIUM |
| **Ephemeris Calculation Latency** | No budget specified for OODA cycle impact | MEDIUM |
| **Guna Calculation Not Cached** | Repeated computation waste | LOW |

### Elevation Suggestions

#### 1. **Restructure Phase 1 into 5 Manageable Milestones** (Priority: HIGH)

**Current Problem:** 65 microtasks in flat list makes tracking impossible.

**Proposed Structure:**

**Milestone 1.1: Ephemeris Core (12 microtasks)**
- Swiss Ephemeris integration & validation
- 9-planet calculation with invariant enforcement
- Retrograde detection (Rahu/Ketu)
- Test suite: Invariant tests passing

**Milestone 1.2: NavagrahaState Computation (15 microtasks)**
- Aggregate state calculation from planetary positions
- Guna computation (sattva/rajas/tamas from planets)
- Rahu Kala gate logic
- Dasha period determination
- Test suite: State transitions validated

**Milestone 1.3: Caching Layer (10 microtasks)**
- Multi-level cache (positions 5min, aspects 15min, rahu_kala daily)
- Redis integration for distributed caching
- Cache invalidation triggers
- Performance tests: <50ms cache hit, <500ms cache miss

**Milestone 1.4: OODA-Navagraha Integration (18 microtasks)**
- NavagrahaState injection into OODA Observe phase
- Gate enforcement (Rahu Kala blocks Act phase)
- Dasha-based strategy selection in Orient phase
- Integration tests: Full OODA cycle with real ephemeris

**Milestone 1.5: Elemental Agent Foundation (10 microtasks)**
- BaseElementalAgent with guna-modulated behavior
- Prana lifecycle (observe → decay)
- Guna → behavior mapping (sattva=calm, rajas=active, tamas=inert)
- Unit tests: Guna modulation verified

**Benefits:**
- Clear checkpoints every 10-15 microtasks
- Parallel work possible (Milestone 1.1 + 1.3 can run concurrently)
- Early validation at each milestone

#### 2. **Define Explicit NavagrahaState Threading Pattern** (Priority: HIGH)

**Current Problem:** State calculated but unclear where/how it flows through system.

**Proposed Threading Model:**

```
```
NavagrahaState Lifecycle:
┌─────────────────┐
│ OODA Coordinator│
│   (Entry Point) │
└────────┬────────┘
         │ calculate_navagraha_state()
         ▼
┌─────────────────────────┐
│ NavagrahaStateCalculator│ ← Cache Check (Redis, TTL: 5min positions)
│  - Ephemeris positions  │
│  - Guna aggregation     │
│  - Rahu Kala check      │
│  - Dasha determination  │
└────────┬────────────────┘
         │ NavagrahaState object
         ▼
┌─────────────────┐
│ OODA Phases     │
│ - Observe: state│ ← Attach to context
│ - Orient: dasha │ ← Strategy selection
│ - Decide: gunas │ ← Risk modulation
│ - Act: rahu_kala│ ← Gate check
└────────┬────────┘
         │ state passed to agents
         ▼
┌─────────────────┐
│ Elemental Agents│
│ - Prana decay   │ ← Based on guna (sattva slow, tamas fast)
│ - Behavior mod  │ ← rajas=aggressive, sattva=cautious
└─────────────────┘
```
```

**Implementation Points:**
- Calculate once at start of OODA cycle (before Observe)
- Store in request context: `ooda_context.navagraha_state`
- Pass to all agents via constructor or method injection
- Cache for 5 minutes (positions), daily (rahu_kala)

#### 3. **Add Latency Budgets & Performance Requirements** (Priority: MEDIUM)

**Target Latencies (95th percentile):**
- Ephemeris calculation (cold): <500ms
- Ephemeris calculation (cached): <50ms
- Full OODA cycle: <2 seconds
- Guna modulation: <10ms
- Rahu Kala check: <5ms (cached daily)

**Monitoring:**
- Prometheus histogram: `navagraha_calculation_duration_seconds`
- Alert if P95 > 500ms (cold) or > 100ms (cached)

---

## Phase 2: Market Data Integration & OODA Observe

### Current State

**Scope:** Core market data pipeline for OODA Observe phase
- CCXT exchange adapters
- Real-time WebSocket feeds
- Historical data backfill
- Data normalization & validation

**Existing Implementation:**
- ✅ `backend/execution/ccxt_adapter.py` — Multi-exchange support
- ✅ `backend/api/trading_api.py` — REST endpoints for market data
- ✅ `backend/api/websocket_endpoints.py` — Real-time data streaming
- ✅ CCXT already integrated with 100+ exchanges

### Strengths

1. **Production-Ready CCXT:** Battle-tested library, no custom exchange APIs
2. **WebSocket Infrastructure:** Real-time streaming foundation exists
3. **Multi-Exchange Support:** Unified interface via CCXT

### Gaps & Risks

| Gap | Impact | Risk Level |
|-----|--------|------------|
| **No Contract Tests for CCXT** | Exchange API changes break silently | HIGH |
| **Rate Limit Handling Unclear** | Potential IP bans | HIGH |
| **Data Quality Validation Missing** | Bad data → bad trades | MEDIUM |
| **Historical Data Gaps** | Backtest unreliable | MEDIUM |

### Elevation Suggestions

#### 1. **Implement Contract Testing for CCXT APIs** (Priority: HIGH)

**Pattern:**
```python
# tests/integration/test_ccxt_contracts.py
def test_binance_ticker_contract():
    exchange = ccxt.binance()
    ticker = exchange.fetch_ticker('BTC/USDT')
    
    assert 'symbol' in ticker
    assert 'last' in ticker
    assert 'bid' in ticker
    assert 'ask' in ticker
    assert ticker['last'] > 0
```

**Benefits:**
- Detect API changes before production
- Run nightly against real exchanges (test accounts)
- Alert on contract violations

#### 2. **Add Data Quality Layer** (Priority: MEDIUM)

**Validation Rules:**
- Price > 0
- Bid < Ask (spread sanity)
- Volume not NaN
- Timestamp within 5 minutes of now
- No duplicate ticks

**Implementation:**
```python
class MarketDataValidator:
    def validate_ticker(self, ticker: dict) -> bool:
        if ticker.get('last', 0) <= 0:
            raise InvalidPriceError
        if ticker.get('bid', 0) >= ticker.get('ask', float('inf')):
            raise InvalidSpreadError
        return True
```

#### 3. **Circuit Breaker for Rate Limits** (Priority: HIGH)

See "Revised Architecture Design" section for full pattern.

---

## Phase 3: Orient — Pattern Recognition & Strategy Selection

### Current State

**Scope:** OODA Orient phase implementation
- Pattern detection (technical indicators, regime detection)
- Dasha-based strategy selection
- Sentiment analysis integration
- LLM fallback chain (Ollama → Gemini → DeepSeek)

**Existing Implementation:**
- ⚠️ Orient logic partially implemented in `orchestration/ooda_coordinator.py`
- ⚠️ Dasha logic present but not connected to strategy selection
- ❌ LLM fallback chain not implemented

### Strengths

1. **Dasha Foundation:** Calculation logic exists in navagraha module
2. **Strategy Framework:** Multiple strategy classes defined

### Gaps & Risks

| Gap | Impact | Risk Level |
|-----|--------|------------|
| **Dasha → Strategy Mapping Undefined** | No clear link | HIGH |
| **LLM Token Budget Not Enforced** | Cost overrun | HIGH |
| **No Fallback on LLM Failure** | System halt | MEDIUM |
| **Sentiment API Contract Missing** | Silent failures | MEDIUM |

### Elevation Suggestions

#### 1. **Define Dasha → Strategy Mapping Table** (Priority: HIGH)

```python
DASHA_STRATEGY_MAP = {
    "Sun": "TrendFollowing",      # Decisive, momentum
    "Moon": "MeanReversion",       # Cyclical, range-bound
    "Mars": "Breakout",            # Aggressive, volatility
    "Mercury": "Arbitrage",        # Quick, small edges
    "Jupiter": "Growth",           # Long-term, accumulation
    "Venus": "Balanced",           # Hedged, defensive
    "Saturn": "Value",             # Patient, contrarian
    "Rahu": "Opportunistic",       # Unconventional, high-risk
    "Ketu": "Minimal",             # Detached, reduce positions
}

def select_strategy(dasha: str, market_regime: str) -> Strategy:
    base_strategy = DASHA_STRATEGY_MAP[dasha]
    if market_regime == "high_volatility" and base_strategy == "Aggressive":
        return "ReducedPosition"  # Safety override
    return base_strategy
```

#### 2. **LLM Fallback Chain with Token Budget** (Priority: HIGH)

See "Worked Examples (Pseudocode)" section for full implementation.

#### 3. **Sentiment API Contract Tests** (Priority: MEDIUM)

Similar to CCXT contract tests, validate sentiment API schema.

---

## Phase 4: Decide — Risk Assessment & Position Sizing

### Current State

**Scope:** OODA Decide phase
- Risk assessment using Fire element (Risk Guardian)
- Position sizing based on Kelly Criterion + guna modulation
- Portfolio rebalancing logic
- MiFID II pre-trade checks

**Existing Implementation:**
- ✅ `backend/agents/elemental_risk_guardian.py` — Fire element agent exists
- ✅ Risk management foundation in `execution/` module
- ⚠️ MiFID II checks not implemented

### Strengths

1. **Risk Guardian Agent:** Dedicated Fire element for risk assessment
2. **Existing Risk Framework:** Position limits, stop-loss logic present

### Gaps & Risks

| Gap | Impact | Risk Level |
|-----|--------|------------|
| **MiFID II Pre-Trade Checks Missing** | Regulatory non-compliance | CRITICAL |
| **Position Sizing Not Guna-Modulated** | Philosophy not integrated | HIGH |
| **No Portfolio-Level Risk Limits** | Concentration risk | MEDIUM |

### Elevation Suggestions

#### 1. **Implement MiFID II Pre-Trade Checks** (Priority: CRITICAL)

See "Worked Examples (Pseudocode)" section for full logic.

#### 2. **Guna-Modulated Position Sizing** (Priority: HIGH)

```python
def calculate_position_size(
    base_size: float,
    guna_state: GunaState,
    kelly_fraction: float
) -> float:
    guna_modulation = {
        "sattva_dominant": 0.7,  # Cautious
        "rajas_dominant": 1.2,   # Aggressive
        "tamas_dominant": 0.3    # Minimal
    }
    
    modulator = guna_modulation[guna_state.dominant_guna]
    return base_size * kelly_fraction * modulator
```

#### 3. **Portfolio-Level Risk Aggregation** (Priority: MEDIUM)

- Maximum 30% in single asset
- Maximum 50% in single sector
- Daily VaR limit: 2% of portfolio
- Monitor via Prometheus: `portfolio_concentration_ratio`

---

## Phase 5: Act — Execution & Order Management

### Current State

**Scope:** OODA Act phase
- Smart order routing
- Rahu Kala gate enforcement
- Order execution via CCXT
- Slippage tracking
- Execution quality monitoring

**Existing Implementation:**
- ✅ `backend/execution/smart_order_router.py` — Routing logic exists
- ✅ `backend/execution/order_executor.py` — Execution engine present
- ⚠️ Rahu Kala gate not enforced at execution level

### Strengths

1. **Smart Routing:** Multi-exchange routing for best execution
2. **Execution Engine:** Production-ready order management

### Gaps & Risks

| Gap | Impact | Risk Level |
|-----|--------|------------|
| **Rahu Kala Gate Not Enforced** | Trades during inauspicious time | HIGH |
| **No Best Execution Proof** | MiFID II non-compliance | HIGH |
| **Slippage Not Monitored** | Hidden costs | MEDIUM |

### Elevation Suggestions

#### 1. **Rahu Kala Gate Enforcement** (Priority: HIGH)

```python
class OrderExecutor:
    def execute_order(self, order: Order) -> ExecutionResult:
        navagraha_state = self.get_current_navagraha_state()
        
        if navagraha_state.is_rahu_kala():
            logger.warning("Rahu Kala active, blocking execution")
            return ExecutionResult(
                status="BLOCKED",
                reason="RAHU_KALA_ACTIVE",
                blocked_until=navagraha_state.rahu_kala_end_time
            )
        
        return self._execute_on_exchange(order)
```

#### 2. **Best Execution Audit Trail** (Priority: HIGH)

For MiFID II compliance, log:
- Timestamp of decision
- Available venues & quotes
- Venue selected + rationale
- Executed price vs. best quote
- Slippage calculation

Store in ClickHouse for 7-year retention.

#### 3. **Slippage Monitoring** (Priority: MEDIUM)

```python
slippage = (executed_price - expected_price) / expected_price
prometheus_histogram.observe(slippage)

if abs(slippage) > 0.01:  # 1% threshold
    alert("High slippage detected")
```

---

## Phase 6: Karma Feedback Loop & Learning

### Current State

**Scope:** Adaptive learning from trade outcomes
- Karma accumulation (good/bad outcomes)
- Parameter adjustment based on karma
- Viveka (discrimination) pattern refinement
- Overfitting prevention

**Existing Implementation:**
- ⚠️ Karma concept mentioned but not implemented
- ❌ Learning mechanism not present

### Strengths

1. **Clear Philosophical Framework:** Karma → learning mapping defined

### Gaps & Risks

| Gap | Impact | Risk Level |
|-----|--------|------------|
| **No Overfitting Safeguards** | Chasing lucky streaks | CRITICAL |
| **Learning Rate Unbounded** | Parameter instability | HIGH |
| **No A/B Testing Framework** | Can't validate changes | MEDIUM |

### Elevation Suggestions

#### 1. **Karma Feedback with Safety Bounds** (Priority: CRITICAL)

See "Worked Examples (Pseudocode)" section for full implementation with:
- Maximum parameter shift: 20% per review
- Minimum sample size: 30 trades
- Statistical significance testing (p < 0.05)
- Exponential moving average (not recency-biased)

#### 2. **Shadow Portfolio for A/B Testing** (Priority: HIGH)

Run new parameter sets in parallel on paper trading:
- 70% production parameters
- 30% experimental parameters (shadow)
- Compare performance over 30 days
- Promote only if statistically better

#### 3. **Overfitting Detection** (Priority: HIGH)

Monitor:
- Sharpe ratio: production vs. backtest divergence
- Win rate: recent vs. historical
- Alert if recent performance > 2σ above historical

---

## Phase 7: Multi-Tenant, Compliance & Production Hardening

### Current State

**Scope:** Production readiness
- Row-level security (RLS) for multi-tenancy
- OAuth2/OIDC authentication
- Vault secret rotation
- MiFID II reporting
- Prometheus/Grafana observability
- Circuit breakers, rate limiting

**Existing Implementation:**
- ✅ `backend/core/security/` — Auth, Vault integration exists
- ✅ `backend/governance/` — RBAC, audit logging present
- ✅ Prometheus, Grafana configs present
- ⚠️ Multi-tenant RLS not fully implemented
- ❌ MiFID II reporting not implemented

### Strengths

1. **Security Foundation:** OAuth2, Vault, RBAC infrastructure exists
2. **Observability Infrastructure:** Prometheus, Grafana, tracing in place

### Gaps & Risks

| Gap | Impact | Risk Level |
|-----|--------|------------|
| **RLS Not Enforced at DB Level** | Data leakage between tenants | CRITICAL |
| **No MiFID II T+1 Reporting** | Regulatory non-compliance | CRITICAL |
| **Secret Rotation Not Automated** | Security vulnerability | HIGH |
| **No Chaos Engineering Tests** | Unknown failure modes | MEDIUM |

### Elevation Suggestions

#### 1. **Implement Database-Level RLS** (Priority: CRITICAL)

```sql
-- PostgreSQL RLS policy
CREATE POLICY tenant_isolation ON trades
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

ALTER TABLE trades ENABLE ROW LEVEL SECURITY;
```

Application layer:
```python
@contextmanager
def tenant_context(tenant_id: str):
    conn.execute(f"SET app.current_tenant_id = '{tenant_id}'")
    yield
    conn.execute("RESET app.current_tenant_id")
```

#### 2. **MiFID II T+1 Reporting** (Priority: CRITICAL)

Daily batch job:
- Export all trades to regulatory format (XML)
- Include: instrument ID, price, quantity, venue, timestamp, client ID
- Upload to regulator portal via SFTP
- Retention: 7 years in cold storage (S3 Glacier)

#### 3. **Automated Secret Rotation** (Priority: HIGH)

```python
# Vault rotation policy
vault.secrets.kv.v2.configure(
    path="trading-system",
    max_versions=10,
    cas_required=False,
    delete_version_after="30d"
)

# Rotate every 90 days
@scheduled(cron="0 0 1 */3 *")
def rotate_secrets():
    for secret in ["exchange_api_key", "db_password"]:
        new_value = generate_secure_random()
        vault.write(secret, value=new_value)
        update_application_config(secret, new_value)
```

---

## Cross-Phase Critical Paths

### Dependency Graph

```
```
Phase 1 (Ephemeris + OODA Foundation)
  ├─→ Phase 2 (Market Data Integration)
  │     └─→ Phase 3 (Orient + Strategy Selection)
  │           └─→ Phase 4 (Risk Assessment)
  │                 └─→ Phase 5 (Execution)
  │                       └─→ Phase 6 (Karma Feedback)
  └─→ Phase 7 (Compliance + Hardening) [parallel with 2-6]
```
```

**Critical Path:** Phase 1 → 2 → 3 → 4 → 5 (must be sequential)  
**Parallelizable:** Phase 7 (security, observability) can run alongside 2-6

### Build-Once, Use-Everywhere Components

1. **NavagrahaStateCalculator** (Phase 1) — Used by all phases
2. **OODAContext** (Phase 1) — Threaded through 2-5
3. **CircuitBreakerRegistry** (Phase 2) — Shared by all external APIs
4. **AuditLogger** (Phase 7) — Required by 3-6 for compliance
5. **PrometheusMetrics** (Phase 7) — Instrumented in all phases

### Early Validation Checkpoints

- **Phase 1 Milestone 1.1:** Ephemeris calculation with invariant tests passing
- **Phase 2:** CCXT contract tests passing for top 5 exchanges
- **Phase 3:** Dasha → strategy mapping validated via backtest
- **Phase 4:** MiFID II pre-trade checks rejecting non-compliant orders
- **Phase 5:** Rahu Kala gate blocking executions during test window
- **Phase 6:** Karma feedback adjusting parameters within safety bounds

---

## Top 15 Elevation Opportunities (Prioritized)

| # | Opportunity | Phase | Priority | Effort | Impact |
|---|-------------|-------|----------|--------|--------|
| 1 | Restructure Phase 1 into 5 milestones | 1 | CRITICAL | 1 day | High clarity |
| 2 | Implement MiFID II pre-trade checks | 4 | CRITICAL | 3 days | Compliance |
| 3 | Add database-level RLS for multi-tenancy | 7 | CRITICAL | 2 days | Security |
| 4 | Implement MiFID II T+1 reporting | 7 | CRITICAL | 5 days | Compliance |
| 5 | Define explicit NavagrahaState threading | 1 | HIGH | 2 days | Architecture clarity |
| 6 | Add CCXT contract tests | 2 | HIGH | 2 days | Reliability |
| 7 | Implement circuit breaker pattern | 2 | HIGH | 1 day | Resilience |
| 8 | LLM fallback chain with token budget | 3 | HIGH | 2 days | Cost control |
| 9 | Dasha → strategy mapping table | 3 | HIGH | 1 day | Philosophy integration |
| 10 | Karma feedback with safety bounds | 6 | HIGH | 3 days | Prevent overfitting |
| 11 | Rahu Kala gate enforcement | 5 | HIGH | 1 day | Philosophy integration |
| 12 | Guna-modulated position sizing | 4 | HIGH | 2 days | Philosophy integration |
| 13 | Multi-level caching strategy | 1 | MEDIUM | 3 days | Performance |
| 14 | Best execution audit trail | 5 | MEDIUM | 2 days | Compliance |
| 15 | Automated secret rotation | 7 | MEDIUM | 2 days | Security |

**Total Effort:** ~30 days  
**Critical Path Items:** 13 days

---

## Risk Mitigation Roadmap

### High-Risk Areas (Phases 5-7)

#### Phase 5: Execution Risks
- **Risk:** Exchange downtime during execution
- **Mitigation:** Circuit breaker + retry with exponential backoff
- **Monitoring:** `exchange_availability_ratio` metric

#### Phase 6: Learning Risks
- **Risk:** Overfitting to recent lucky streak
- **Mitigation:** Minimum 30 trades, statistical significance, max 20% parameter shift
- **Monitoring:** `karma_parameter_shift_magnitude` metric

#### Phase 7: Compliance Risks
- **Risk:** MiFID II audit failure
- **Mitigation:** 100% trade coverage in audit log, 7-year retention, daily validation
- **Monitoring:** `mifid_audit_coverage_ratio` metric (must be 1.0)

### Contingency Plans

| Failure Scenario | Detection | Response | Recovery Time |
|------------------|-----------|----------|---------------|
| Swiss Ephemeris calc fails | Timeout > 1s | Use last known positions + alert | <1 minute |
| Exchange API down | HTTP 5xx or timeout | Circuit breaker → fallback exchange | <30 seconds |
| LLM token budget exceeded | Counter check | Skip LLM, use rule-based fallback | Immediate |
| Rahu Kala gate failure | State missing | Block all executions + alert | <5 minutes |
| Database RLS breach | Audit log anomaly | Lock tenant + security alert | <1 minute |

---

## Conclusion

The Samkhya Yoga Agentic Trader has a solid foundation but requires targeted architectural elevation to achieve production-grade reliability and compliance. The 15 prioritized opportunities above address critical gaps in compliance (MiFID II), security (RLS), resilience (circuit breakers), and philosophical coherence (guna modulation, karma feedback).

**Next Steps:**
1. Implement Phase 1 milestone restructuring (this document)
2. Build cross-cutting components (NavagrahaStateCalculator, CircuitBreakerRegistry)
3. Execute critical path: Phases 1 → 2 → 3 → 4 → 5
4. Parallel track: Phase 7 compliance & security
5. Final integration: Phase 6 karma feedback

**Success Criteria:**
- All 7 phases reviewed ✅
- 15 elevation opportunities identified ✅
- Phase 1 restructured into 5 milestones ✅
- Critical path prioritized ✅
- Risk mitigation roadmap defined ✅

---

*End of Phase-by-Phase Review Document*
"""

    output_path = DOCS_DIR / "PHASE_BY_PHASE_REVIEW.md"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ Generated: {output_path}")
    return str(output_path)


def main():
    print("=" * 80)
    print("COMPREHENSIVE ANALYSIS GENERATION")
    print("=" * 80)

    print("\n[1] Reading existing documentation...")
    docs = analyze_existing_docs()
    print(f"    - Master Kanban: {len(docs['master'])} chars")
    print(f"    - FASE 01: {len(docs['fase01'])} chars")
    print(f"    - Handover: {len(docs['handover'])} chars")
    print(f"    - EPIC 01: {len(docs['epic01'])} chars")

    print("\n[2] Generating Phase-by-Phase Review Document...")
    phase_review_path = generate_phase_review_document(docs)

    print("\n" + "=" * 80)
    print("GENERATION COMPLETE")
    print("=" * 80)
    print("\nDeliverables created:")
    print(f"  1. {phase_review_path}")
    print("\nNext: Generate remaining deliverables...")


if __name__ == "__main__":
    main()
