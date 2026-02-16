# Optimized Implementation Roadmap
## Samkhya Yoga Agentic Trader — Critical Path & Execution Sequence

**Generated:** 2026-02-15  
**Document Version:** 1.0  
**Total Duration:** ~30 days (critical path), ~45 days (with parallel work)

---

## Executive Summary

This roadmap optimizes the 7-phase, ~180-microtask implementation by:
1. **Restructuring Phase 1** from 65 flat microtasks into 5 manageable milestones
2. **Identifying critical path** (must be sequential) vs. parallelizable work
3. **Defining early validation checkpoints** to catch issues fast
4. **Highlighting build-once components** for reuse across phases

**Critical Path:** Phase 1.1 → 1.2 → 1.4 → Phase 2 → Phase 3 → Phase 4 → Phase 5 (13 days)  
**Parallel Track:** Phase 1.3 (caching), Phase 7 (compliance/security) can run alongside main path

---

## Phase 1 Restructuring: 5 Milestones

### Original Problem
- 65 microtasks in flat list
- Unclear dependencies
- Hard to track progress
- No intermediate validation points

### Proposed Milestones

```
```
Phase 1: Consciousness-OODA-Navagraha Bridge (Refactored)
│
├─ Milestone 1.1: Ephemeris Core (3 days) [CRITICAL PATH]
│  ├─ 1.1.1: pyswisseph integration & file verification
│  ├─ 1.1.2: Kerykeion wrapper for birth chart calculations
│  ├─ 1.1.3: 9-planet position calculator (Sun→Ketu)
│  ├─ 1.1.4: Retrograde detection logic (Rahu/Ketu always, others conditional)
│  ├─ 1.1.5: Invariant test suite (9 planets, Rahu retrograde, valid ranges)
│  └─ Checkpoint: test_ephemeris.py passing with real Swiss Ephemeris
│
├─ Milestone 1.2: NavagrahaState Computation (4 days) [CRITICAL PATH]
│  ├─ 1.2.1: PlanetState model (position, speed, retrograde, dignity)
│  ├─ 1.2.2: Guna mapping (Sun→Sattva, Mars→Rajas, Saturn→Tamas)
│  ├─ 1.2.3: Weighted guna aggregation (based on planet strength)
│  ├─ 1.2.4: Rahu Kala calculation (location-based, daily windows)
│  ├─ 1.2.5: Dasha determination (Vimshottari from Moon position)
│  ├─ 1.2.6: NavagrahaState assembly (planets + gunas + rahu_kala + dasha)
│  └─ Checkpoint: NavagrahaState object created with valid data
│
├─ Milestone 1.3: Caching Layer (3 days) [PARALLEL TRACK]
│  ├─ 1.3.1: Redis integration & connection pool
│  ├─ 1.3.2: Multi-level cache keys (positions:5m, aspects:15m, rahu_kala:daily)
│  ├─ 1.3.3: Cache invalidation triggers (time-based + event-driven)
│  ├─ 1.3.4: Performance tests (<50ms hit, <500ms miss)
│  └─ Checkpoint: Cache hit rate >80% in load test
│
├─ Milestone 1.4: OODA-Navagraha Integration (5 days) [CRITICAL PATH]
│  ├─ 1.4.1: OODAContext with navagraha_state field
│  ├─ 1.4.2: State injection at Observe phase start
│  ├─ 1.4.3: Dasha-based strategy selection in Orient
│  ├─ 1.4.4: Guna-based risk modulation in Decide
│  ├─ 1.4.5: Rahu Kala gate check in Act (block if active)
│  ├─ 1.4.6: Integration test: Full OODA cycle with real ephemeris
│  └─ Checkpoint: OODA cycle completes with Navagraha influence proven
│
└─ Milestone 1.5: Elemental Agent Foundation (3 days) [PARALLEL WITH 1.4]
   ├─ 1.5.1: BaseElementalAgent abstract class
   ├─ 1.5.2: Guna-modulated prana decay (sattva slow, tamas fast)
   ├─ 1.5.3: Behavior modulation methods (_observe, _decide)
   ├─ 1.5.4: Unit tests for guna modulation
   └─ Checkpoint: Agent behavior changes with different guna states

Total Phase 1: 18 days (sequential), 13 days (with parallelization)
```
```

---

## Critical Path Visualization

```
```
DAY 0: Project Start
│
├─ MILESTONE 1.1: Ephemeris Core (Days 1-3) [BLOCKER]
│  └─ Output: EphemerisCalculator, test_ephemeris.py passing
│
├─ MILESTONE 1.2: NavagrahaState (Days 4-7) [BLOCKER]
│  └─ Output: NavagrahaState model, guna calculation
│     │
│     ├─ PARALLEL: Milestone 1.3 Caching (Days 4-6)
│     │  └─ Output: Redis cache layer, <50ms hit latency
│     │
│     └─ Dependency: Milestone 1.4 requires 1.2 complete
│
├─ MILESTONE 1.4: OODA Integration (Days 8-12) [BLOCKER]
│  └─ Output: Full OODA cycle with Navagraha threading
│     │
│     └─ PARALLEL: Milestone 1.5 Elemental Agents (Days 10-12)
│        └─ Output: BaseElementalAgent with guna modulation
│
├─ PHASE 2: Market Data (Days 13-18) [BLOCKER]
│  ├─ CCXT integration
│  ├─ WebSocket real-time feeds
│  ├─ Contract tests
│  └─ Circuit breaker pattern
│
├─ PHASE 3: Orient/Strategy (Days 19-24) [BLOCKER]
│  ├─ Dasha → Strategy mapping
│  ├─ Pattern detection
│  ├─ LLM fallback chain
│  └─ Sentiment integration
│
├─ PHASE 4: Risk/Decide (Days 25-27) [BLOCKER]
│  ├─ MiFID II pre-trade checks
│  ├─ Guna-modulated position sizing
│  └─ Portfolio risk aggregation
│
├─ PHASE 5: Execution/Act (Days 28-30) [BLOCKER]
│  ├─ Rahu Kala gate enforcement
│  ├─ Smart order routing
│  ├─ Best execution audit trail
│  └─ Slippage monitoring
│
├─ PHASE 6: Karma Feedback (Days 31-33)
│  ├─ Karma accumulation logic
│  ├─ Parameter adjustment with safety bounds
│  ├─ Overfitting detection
│  └─ Shadow portfolio A/B testing
│
└─ PHASE 7: Compliance/Hardening (Days 1-45) [PARALLEL TRACK]
   ├─ Database RLS (Days 5-6)
   ├─ OAuth2/OIDC (Days 10-12)
   ├─ Vault secret rotation (Days 15-16)
   ├─ MiFID II T+1 reporting (Days 25-29)
   ├─ Prometheus metrics (Days 20-22)
   └─ Grafana dashboards (Days 30-33)

TOTAL: 33 days (critical path), 45 days (with parallel work)
```
```

---

## Parallelizable Work Streams

### Stream A: Core Trading Logic (Critical Path)
**Team:** Backend Engineers (2-3)  
**Duration:** 30 days  
**Dependencies:** Sequential (each phase depends on previous)

- Milestone 1.1 → 1.2 → 1.4 (Ephemeris + OODA)
- Phase 2 (Market Data)
- Phase 3 (Strategy Selection)
- Phase 4 (Risk Assessment)
- Phase 5 (Execution)
- Phase 6 (Karma Feedback)

### Stream B: Infrastructure & Caching (Parallel)
**Team:** DevOps + Backend (1-2)  
**Duration:** 6 days  
**Can Start:** Day 4 (after Milestone 1.2 starts)

- Milestone 1.3 (Redis caching)
- Performance testing infrastructure
- Load testing setup

### Stream C: Compliance & Security (Parallel)
**Team:** Security Engineer + Compliance Specialist (1-2)  
**Duration:** 45 days (spread across entire project)  
**Can Start:** Day 1 (no dependencies)

- Phase 7: Database RLS, OAuth2, Vault rotation, MiFID II reporting
- Security audit reviews
- Compliance documentation

### Stream D: Testing & QA (Parallel)
**Team:** QA Engineer (1)  
**Duration:** Ongoing  
**Can Start:** Day 1

- Contract test development (CCXT, sentiment APIs)
- Integration test patterns
- E2E test scenarios
- Performance regression tests

### Stream E: Observability (Parallel)
**Team:** SRE + Backend (1)  
**Duration:** 15 days (Days 20-35)  
**Can Start:** Day 20 (after core logic stabilized)

- Prometheus metric instrumentation
- Grafana dashboard creation
- Alert rule configuration
- SLI/SLO definition

---

## Build-Once, Use-Everywhere Components

### 1. NavagrahaStateCalculator (Milestone 1.2)
**Used By:** All phases (OODA, agents, karma feedback)  
**API:**
```python
class NavagrahaStateCalculator:
    def calculate(self, dt: datetime, location: Location) -> NavagrahaState:
        pass
    
    def calculate_with_cache(self, dt: datetime, location: Location) -> NavagrahaState:
        pass
```

### 2. OODAContext (Milestone 1.4)
**Used By:** Phases 2-6 (Observe → Orient → Decide → Act → Karma)  
**API:**
```python
@dataclass
class OODAContext:
    navagraha_state: NavagrahaState
    market_data: Optional[MarketData]
    strategy: Optional[Strategy]
    risk_assessment: Optional[RiskAssessment]
    execution_plan: Optional[ExecutionPlan]
```

### 3. CircuitBreakerRegistry (Phase 2)
**Used By:** All external API calls (CCXT, LLM, sentiment, ephemeris)  
**API:**
```python
class CircuitBreakerRegistry:
    def get_breaker(self, name: str, config: CircuitBreakerConfig) -> CircuitBreaker:
        pass
```

### 4. AuditLogger (Phase 7)
**Used By:** Phases 3-6 (every trade decision, execution, karma update)  
**API:**
```python
class AuditLogger:
    def log_decision(self, context: OODAContext, decision: TradeDecision):
        pass
    
    def log_execution(self, order: Order, result: ExecutionResult):
        pass
```

### 5. PrometheusMetrics (Phase 7)
**Used By:** All phases (instrumentation throughout)  
**API:**
```python
class MetricsRegistry:
    def histogram(self, name: str, labels: Dict[str, str]):
        pass
    
    def gauge(self, name: str, labels: Dict[str, str]):
        pass
```

---

## Early Validation Checkpoints

### Checkpoint 1: Ephemeris Invariants (End of Milestone 1.1)
**Validation:**
```python
def test_ephemeris_invariants():
    calc = EphemerisCalculator()
    state = calc.calculate(datetime(2026, 1, 15, 12, 0), Location(lat=28.6, lon=77.2))
    
    assert len(state.planets) == 9
    assert state.get_planet("Rahu").is_retrograde == True
    assert all(0 <= p.longitude <= 360 for p in state.planets)
```

**Pass Criteria:** All invariant tests green with real Swiss Ephemeris (no mocks)

### Checkpoint 2: NavagrahaState Validity (End of Milestone 1.2)
**Validation:**
```python
def test_navagraha_state_validity():
    state = calculator.calculate_state(datetime.now(), Location(...))
    
    assert state.guna_ratios['sattva'] + state.guna_ratios['rajas'] + state.guna_ratios['tamas'] == 1.0
    assert state.rahu_kala.start_time < state.rahu_kala.end_time
    assert state.current_dasha.planet in VALID_DASHA_PLANETS
```

**Pass Criteria:** State object validated, gunas sum to 1.0, Rahu Kala times logical

### Checkpoint 3: OODA Integration (End of Milestone 1.4)
**Validation:**
```python
def test_ooda_navagraha_integration():
    coordinator = OODACoordinator()
    result = coordinator.run_cycle()
    
    assert result.context.navagraha_state is not None
    assert result.strategy_selected_by_dasha == True
    assert result.risk_modulated_by_guna == True
    
    if result.context.navagraha_state.rahu_kala.is_active:
        assert result.execution_blocked == True
```

**Pass Criteria:** Full OODA cycle runs, Navagraha influence proven in logs/metrics

### Checkpoint 4: CCXT Contract Tests (End of Phase 2)
**Validation:**
```python
def test_ccxt_binance_contract():
    exchange = ccxt.binance()
    ticker = exchange.fetch_ticker('BTC/USDT')
    
    assert 'symbol' in ticker
    assert 'last' in ticker
    assert ticker['last'] > 0
```

**Pass Criteria:** Contract tests passing for top 5 exchanges (Binance, Coinbase, Kraken, Bybit, OKX)

### Checkpoint 5: MiFID II Pre-Trade (End of Phase 4)
**Validation:**
```python
def test_mifid2_pretrade_rejection():
    order = Order(symbol="BTC/USDT", size=1000000)  # Exceeds limit
    checker = MiFIDPreTradeChecker()
    
    result = checker.check(order)
    assert result.approved == False
    assert "position_limit_exceeded" in result.rejection_reason
```

**Pass Criteria:** Non-compliant orders rejected, audit trail complete

### Checkpoint 6: Karma Safety Bounds (End of Phase 6)
**Validation:**
```python
def test_karma_parameter_shift_bounded():
    learner = KarmaLearner()
    old_params = {"risk_tolerance": 0.5}
    new_params = learner.adjust_parameters(old_params, outcomes=[...])
    
    shift = abs(new_params["risk_tolerance"] - old_params["risk_tolerance"])
    assert shift <= 0.2  # Max 20% shift per review
```

**Pass Criteria:** Parameter adjustments bounded, overfitting detection working

---

## Risk Mitigation & Contingency

### High-Risk Areas

#### Risk 1: Swiss Ephemeris File Missing
**Probability:** Medium  
**Impact:** Critical (system unusable)  
**Mitigation:**
- Pre-deployment verification script
- Ephemeris file integrity check on startup
- Fallback to last known state (< 15 minutes old)

**Contingency:**
```python
if not ephemeris_files_present():
    logger.critical("Swiss Ephemeris files missing, entering safe mode")
    use_safe_default_navagraha_state()
```

#### Risk 2: CCXT Exchange API Changes
**Probability:** High (ongoing)  
**Impact:** High (trading halts)  
**Mitigation:**
- Contract tests run nightly
- Circuit breaker pattern
- Multi-exchange fallback

**Contingency:**
```python
try:
    ticker = ccxt_breaker.call(exchange.fetch_ticker, symbol)
except CircuitBreakerOpenError:
    ticker = fallback_exchange.fetch_ticker(symbol)
```

#### Risk 3: Karma Overfitting
**Probability:** High  
**Impact:** Medium (bad trades)  
**Mitigation:**
- Minimum 30-trade sample size
- Statistical significance testing (p < 0.05)
- Max 20% parameter shift per review
- Shadow portfolio validation

**Contingency:**
```python
if performance_too_good_to_be_true(recent_sharpe):
    logger.warning("Possible overfitting, reverting parameters")
    revert_to_stable_parameters()
```

---

## Daily Standup Template

```markdown
### Day X Standup

**Yesterday:**
- [ ] Milestone/Phase completed
- [ ] Tests passing: X/Y
- [ ] Blockers resolved

**Today:**
- [ ] Working on: [Milestone/Task]
- [ ] Expected deliverable: [Checkpoint/Test]
- [ ] Dependencies: [Waiting on...]

**Blockers:**
- [ ] None / [Describe blocker]

**Metrics:**
- Test coverage: X%
- P95 latency: Xms
- Cache hit rate: X%
```

---

## Phase Completion Criteria

### Phase 1 Complete When:
- ✅ All 5 milestones passing checkpoints
- ✅ Ephemeris invariant tests green (no mocks)
- ✅ NavagrahaState threading proven in OODA cycle
- ✅ Cache hit rate > 80% in load test
- ✅ Full integration test: OODA cycle with real ephemeris

### Phase 2 Complete When:
- ✅ CCXT contract tests passing for top 5 exchanges
- ✅ WebSocket real-time feeds working
- ✅ Circuit breaker pattern implemented
- ✅ Data quality validation layer active

### Phase 3 Complete When:
- ✅ Dasha → Strategy mapping table implemented
- ✅ Strategy selection proven via backtest
- ✅ LLM fallback chain with token budget

### Phase 4 Complete When:
- ✅ MiFID II pre-trade checks rejecting non-compliant orders
- ✅ Guna-modulated position sizing working
- ✅ Portfolio risk aggregation under limits

### Phase 5 Complete When:
- ✅ Rahu Kala gate blocking executions during test window
- ✅ Best execution audit trail complete
- ✅ Slippage monitoring active

### Phase 6 Complete When:
- ✅ Karma feedback adjusting parameters within safety bounds
- ✅ Overfitting detection working
- ✅ Shadow portfolio A/B test setup complete

### Phase 7 Complete When:
- ✅ Database RLS enforced (tenant isolation proven)
- ✅ MiFID II T+1 reporting functional
- ✅ Secret rotation automated
- ✅ Prometheus metrics + Grafana dashboards live

---

*End of Optimized Implementation Roadmap*