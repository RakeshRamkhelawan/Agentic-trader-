# Optimized Implementation Roadmap

**Generated:** 2026-02-14
**Version:** 1.0
**Timeline:** 12 weeks (3 months)

---

## Critical Path Analysis

```
```
CRITICAL PATH (Sequential Dependencies):
========================================

Week 1-2:  [Swiss Ephemeris Engine] ────────────┐
                                                  │
Week 2-3:  [Caching Layer + Redis Integration] ──┤
                                                  │
Week 3-4:  [Guna Modulation Engine] ─────────────┤
                                                  │
Week 4-5:  [OODA Coordinator + Agents] ──────────┤
                                                  │
Week 5-6:  [Execution Layer + Circuit Breakers] ─┤
                                                  │
Week 6-8:  [Karma Feedback + Learning Bounds] ───┤
                                                  │
Week 8-10: [MiFID II Compliance + Audit] ────────┤
                                                  │
Week 11-12: [Integration Testing + Hardening] ───┘


PARALLELIZABLE STREAMS:
=======================

Stream A (Infrastructure):
  - CI/CD Pipeline (Week 1)
  - Monitoring Setup (Week 1-2)
  - Docker Compose Dev Env (Week 1)

Stream B (Frontend):
  - Dashboard UI (Week 3-6)
  - WebSocket Client (Week 4-5)
  - Real-time Charts (Week 6-8)

Stream C (Testing):
  - Test Framework Setup (Week 1)
  - Unit Test Templates (Week 2)
  - Integration Test Harness (Week 4)

Stream D (Documentation):
  - API Documentation (Week 3-8)
  - Runbooks (Week 6-10)
  - User Guides (Week 10-12)
```
```

---

## Phase 1: Foundation (Weeks 1-4)

### Week 1: Infrastructure + Ephemeris Core

**Sprint Goal:** Development environment operational, ephemeris calculation working

**Critical Path Tasks:**
- ✅ Set up CI/CD pipeline (GitHub Actions)
- ✅ Configure Docker Compose for local dev
- ✅ Create Makefile for DevEx
- ✅ Deep health check script
- Implement Swiss Ephemeris calculation engine
- Create NavagrahaState data model
- Unit tests with invariant validation (Rahu retrograde, 9 planets)

**Parallelizable Tasks:**
- Prometheus + Grafana setup
- PostgreSQL schema initialization
- Redis configuration
- Test fixture creation

**Deliverables:**
- Working ephemeris calculation (unit tested)
- CI/CD pipeline executing tests
- Local development environment documented

**Success Criteria:**
- Ephemeris calculation < 100ms (P95)
- 100% test coverage on core calculation
- All 9 planets returned with valid positions
- Rahu always retrograde in tests

---

### Week 2: Caching Layer + Performance Optimization

**Sprint Goal:** Redis caching operational with 95%+ hit rate

**Critical Path Tasks:**
- Implement 3-tier caching (LRU → Redis → Calculation)
- Redis key schema for positions/aspects/rahu_kala
- Cache warming on startup
- TTL-based invalidation logic

**Parallelizable Tasks:**
- Performance benchmarking suite
- Cache metrics instrumentation
- Load testing scripts
- API documentation generation

**Deliverables:**
- Redis caching layer with >95% hit rate
- Cache invalidation API endpoints
- Performance benchmarks documented

**Success Criteria:**
- Cache hit rate > 95% under load
- Redis lookup < 5ms (P95)
- Cache warming completes in < 30s

---

### Week 3: Guna Modulation + WebSocket Foundation

**Sprint Goal:** Guna calculation from NavagrahaState, real-time updates via WebSocket

**Critical Path Tasks:**
- Implement Guna calculation algorithm
- Map planetary strengths to Sattva/Rajas/Tamas
- WebSocket server for real-time state broadcasts
- Redis Pub/Sub integration

**Parallelizable Tasks:**
- Frontend dashboard skeleton
- WebSocket client library
- Guna visualization components
- User authentication setup (Auth0)

**Deliverables:**
- Guna ratios calculated from ephemeris
- WebSocket broadcasting state updates
- Dashboard receiving real-time updates

**Success Criteria:**
- Guna ratios sum to 1.0 (invariant)
- WebSocket latency < 50ms to 100 clients
- Dashboard updates within 100ms of state change

---

### Week 4: Elemental Agents + Prana Lifecycle

**Sprint Goal:** 5 elemental agents with prana-based lifecycle

**Critical Path Tasks:**
- Implement base ElementalAgent class with prana
- Create 5 concrete agents (Ether, Air, Fire, Water, Earth)
- Prana decay and recovery logic
- Agent activation/dormant thresholds

**Parallelizable Tasks:**
- Agent-specific trading strategies
- Guna-strategy affinity matrix
- Agent performance metrics
- Integration test suite for agents

**Deliverables:**
- 5 functional elemental agents
- Prana lifecycle with safety bounds
- Agent activation logic tested

**Success Criteria:**
- Agents transition dormant when prana < 20
- Prana bounds enforced (0-100)
- All 5 agents pass integration tests

---

## Phase 2: Core OODA Loop (Weeks 5-6)

### Week 5: OODA Coordinator

**Sprint Goal:** Centralized OODA loop calling agents in parallel

**Critical Path Tasks:**
- Implement OODACoordinator class
- Parallel agent execution with asyncio.gather
- Weighted voting for decision aggregation
- Conflict resolution logic

**Parallelizable Tasks:**
- OODA cycle telemetry
- Decision audit logging
- Frontend OODA visualization
- OODA integration tests

**Deliverables:**
- Functional OODA coordinator
- Parallel agent execution
- Decision aggregation with weights

**Success Criteria:**
- Full OODA cycle < 500ms (P95)
- Agent parallelization saves 60% latency
- Weighted voting produces single decision

---

### Week 6: Execution Layer + Paper Trading

**Sprint Goal:** Order execution with paper trading mode

**Critical Path Tasks:**
- CCXT adapter for exchange integration
- Paper trading exchange implementation
- Order routing logic
- Pre-trade risk checks

**Parallelizable Tasks:**
- Circuit breaker implementation
- Execution metrics
- Slippage modeling
- Multi-exchange support

**Deliverables:**
- Paper trading execution working
- Pre-trade checks enforced
- Circuit breakers active

**Success Criteria:**
- Orders execute in paper mode
- Pre-trade checks block invalid orders
- Circuit breaker triggers after 3 failures

---

## Phase 3: Learning & Intelligence (Weeks 7-8)

### Week 7: Karma Feedback Loop

**Sprint Goal:** Learning from trade outcomes with overfitting guards

**Critical Path Tasks:**
- Implement Karma scoring logic
- Bounded parameter shifts (±10% max)
- Trade outcome evaluation
- Agent performance tracking

**Parallelizable Tasks:**
- Viveka pattern discriminator
- Learning rate schedule
- Karma visualization
- Backtest engine for validation

**Deliverables:**
- Karma feedback loop operational
- Safety bounds preventing overfitting
- Agent learning from outcomes

**Success Criteria:**
- Karma shifts capped at ±10% per review
- Agents enter conservative mode when karma < 0.3
- No parameter oscillation observed

---

### Week 8: LLM Integration + RAG Memory

**Sprint Goal:** LLM fallback chain with token budget enforcement

**Critical Path Tasks:**
- Ollama → Gemini → DeepSeek fallback chain
- Token budget manager (daily + per-cycle)
- ChromaDB integration for RAG
- Prompt guard for safety

**Parallelizable Tasks:**
- LLM response caching
- RAG memory pruning
- Token usage metrics
- LLM quality monitoring

**Deliverables:**
- LLM providers integrated
- Token budgets enforced
- RAG memory operational

**Success Criteria:**
- Fallback chain succeeds on provider failure
- Token budget prevents overuse
- RAG retrieves relevant context

---

## Phase 4: Compliance & Production (Weeks 9-10)

### Week 9: MiFID II Compliance

**Sprint Goal:** Full audit trail and regulatory compliance

**Critical Path Tasks:**
- MiFID II audit schema implementation
- Pre-trade compliance checks
- Best execution proof logging
- Trade decision audit records

**Parallelizable Tasks:**
- Compliance report generation
- Audit trail retention policy
- Regulatory query API
- Compliance dashboard

**Deliverables:**
- MiFID II audit trail complete
- Pre-trade checks enforce regulations
- 5-year data retention configured

**Success Criteria:**
- Every trade has audit_id
- Audit records include all required fields
- Retention policy enforced automatically

---

### Week 10: Multi-Tenant Isolation + RBAC

**Sprint Goal:** Row-level security and per-tenant budgets

**Critical Path Tasks:**
- PostgreSQL RLS policies
- Tenant budget tracking
- Per-tenant position limits
- OAuth2/OIDC integration complete

**Parallelizable Tasks:**
- Vault secret rotation
- Tenant management API
- Billing integration
- Tenant isolation tests

**Deliverables:**
- Multi-tenant isolation working
- Per-tenant budgets enforced
- Secret rotation automated

**Success Criteria:**
- Tenants cannot access others' data
- Position limits enforced per tenant
- Secret rotation causes zero downtime

---

## Phase 5: Hardening & Launch (Weeks 11-12)

### Week 11: Integration Testing + Chaos Engineering

**Sprint Goal:** End-to-end validation and failure resilience

**Critical Path Tasks:**
- E2E test suite covering full OODA cycle
- Chaos engineering scenarios (service down, network partition)
- Load testing (1000 concurrent users)
- Performance regression detection

**Parallelizable Tasks:**
- Security audit (Trivy, Bandit)
- Penetration testing
- Backup/restore procedures
- Disaster recovery plan

**Deliverables:**
- E2E tests passing
- System handles chaos scenarios
- Load test results documented

**Success Criteria:**
- E2E tests cover 80%+ scenarios
- System recovers from service failures
- Load test meets SLAs under 1000 users

---

### Week 12: Documentation + Launch Preparation

**Sprint Goal:** Production-ready system with complete documentation

**Critical Path Tasks:**
- Operational runbooks
- Incident response procedures
- User documentation
- API reference complete

**Parallelizable Tasks:**
- Marketing materials
- Demo environment setup
- Training materials
- Launch checklist

**Deliverables:**
- Complete documentation suite
- Runbooks for all common scenarios
- Launch-ready system

**Success Criteria:**
- All runbooks tested
- Documentation peer-reviewed
- Launch checklist 100% complete

---

## Risk Mitigation Roadmap

### High-Risk Items

**Risk 1: Ephemeris Performance Bottleneck**
- Mitigation Week 2: Aggressive caching + benchmarking
- Fallback: Cached positions up to 1 hour old

**Risk 2: Karma Overfitting**
- Mitigation Week 7: Bounded shifts + pattern validation
- Monitoring: Track parameter drift

**Risk 3: LLM Token Budget Overrun**
- Mitigation Week 8: Hard caps + fallback chain
- Monitoring: Daily budget alerts

**Risk 4: MiFID II Audit Gaps**
- Mitigation Week 9: Legal review of schema
- Validation: Sample audit queries

**Risk 5: Multi-Tenant Data Leakage**
- Mitigation Week 10: RLS + integration tests
- Audit: Security penetration testing

---

## Build-Once Components

These components should be implemented once and reused across phases:

1. **Metrics Instrumentation Framework** (Week 1)
   - Used by: All phases
   - Pattern: Decorator-based metrics

2. **Circuit Breaker Pattern** (Week 2)
   - Used by: Ephemeris, Exchange, LLM, Sentiment APIs
   - Pattern: Reusable CircuitBreaker class

3. **Audit Logger** (Week 3)
   - Used by: All decision points
   - Pattern: Centralized audit service

4. **Cache Manager** (Week 2)
   - Used by: Ephemeris, Market Data, LLM Responses
   - Pattern: Generic cache interface

5. **Configuration Service** (Week 1)
   - Used by: All services
   - Pattern: Centralized settings with Vault integration

---

## Parallel Work Coordination

```
```
Timeline Gantt Chart:

Week 1:  [Ephemeris Core]══════════╗
         [CI/CD + DevEx]════════════╬═══════════╗
         [Monitoring Setup]═════════╣           ║
                                    ║           ║
Week 2:  [Caching Layer]═══════════╣           ║
         [Performance Tests]════════╝           ║
                                                ║
Week 3:  [Guna Engine]═════════════════════╗   ║
         [WebSocket Server]════════════════╬═══╣
         [Frontend Dashboard]══════════════╝   ║
                                                ║
Week 4:  [Elemental Agents]════════════════════╣
         [Agent Tests]═════════════════════════╣
                                                ║
Week 5:  [OODA Coordinator]════════════════════╣
         [OODA Telemetry]══════════════════════╣
                                                ║
Week 6:  [Execution Layer]═════════════════════╣
         [Circuit Breakers]════════════════════╣
                                                ║
Week 7:  [Karma Loop]══════════════════════════╣
         [Viveka Discriminator]════════════════╣
                                                ║
Week 8:  [LLM Integration]═════════════════════╣
         [RAG Memory]══════════════════════════╣
                                                ║
Week 9:  [MiFID II Compliance]═════════════════╣
         [Audit Dashboard]═════════════════════╣
                                                ║
Week 10: [Multi-Tenant]════════════════════════╣
         [Secret Rotation]═════════════════════╣
                                                ║
Week 11: [E2E Testing]═════════════════════════╣
         [Chaos Engineering]═══════════════════╣
                                                ║
Week 12: [Documentation]═══════════════════════╣
         [Launch Prep]═════════════════════════╝

══════ Critical Path (Sequential)
══════ Parallelizable Work
```
```

---

## Success Metrics by Phase

| Phase | Key Metric | Target |
|-------|-----------|---------|
| Week 1 | Ephemeris calc latency | < 100ms (P95) |
| Week 2 | Cache hit rate | > 95% |
| Week 3 | WebSocket latency | < 50ms |
| Week 4 | Agent activation speed | < 100ms |
| Week 5 | OODA cycle duration | < 500ms (P95) |
| Week 6 | Order execution latency | < 300ms |
| Week 7 | Karma update frequency | Every trade |
| Week 8 | LLM fallback success rate | > 99% |
| Week 9 | Audit trail coverage | 100% trades |
| Week 10 | Tenant isolation tests | 100% pass |
| Week 11 | E2E test coverage | > 80% |
| Week 12 | Documentation completeness | 100% |

---

## Conclusion

This roadmap prioritizes:
✅ **Critical path first:** Ephemeris → OODA → Execution → Compliance
✅ **Parallel streams:** Infrastructure, frontend, testing run concurrently
✅ **Early validation:** Integration tests from Week 4
✅ **Risk mitigation:** High-risk items addressed early
✅ **Incremental delivery:** Working system at end of each phase
