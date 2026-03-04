# Roadmap: Van 8/10 naar 9/10 Architectuurscore

**Doel**: Implementeer de overige 9 ADR's om de architectuurkwaliteit te verhogen naar productie-niveau.

---

## ADR Checklist

### ✅ ADR-003: WebSocket Reliability & Backpressure
**Status**: Geïmplementeerd
**Impact**: Operationele stabiliteit
**Bestanden**:
- `docs/adr/ADR-003-websocket-reliability.md`
- `backend/api/websocket_manager_v2.py` (nieuw)
- `backend/observability/ws_metrics.py` (nieuw)
- `frontend/src/hooks/useWebSocket.ts` (nieuw)
- `infrastructure/grafana/dashboards/websocket_reliability.json` (nieuw)

---

## TODO: Overige 9 ADR's

### ADR-001: SLO/SLI Model per Kritieke Flow
**Priority**: Hoog
**Impact**: Meetbare betrouwbaarheid
**Scope**: API Gateway, Order Execution, Agent Decision Loop

**Definieer voor 3 kritieke flows**:

| Flow | SLI | SLO | Window |
|------|-----|-----|--------|
| Market Data → UI | p99 latency | <100ms | 1m |
| Order Intake → Execution | Success rate | >99.9% | 1h |
| OODA Decision Loop | Decision time | <200ms | 1m |

**Deliverables**:
- [ ] `docs/adr/ADR-001-slo-model.md`
- [ ] SLO configuratie in `backend/core/config/slo.py`
- [ ] Prometheus recording rules voor SLO metrics
- [ ] Grafana SLO dashboard
- [ ] Error budget alerts

---

### ADR-002: Observability: Metrics/Logs/Traces + Correlation IDs
**Priority**: Hoog
**Impact**: Debugbaarheid en troubleshooting
**Scope**: Alle services

**Vereisten**:
- Trace ID door hele request chain (HTTP → WS → Event Bus → DB)
- Structured logging met JSON format
- Exemplar linking voor high-latency traces
- Golden signals per service

**Deliverables**:
- [ ] `docs/adr/ADR-002-observability.md`
- [ ] `backend/core/telemetry/correlation.py` (middleware)
- [ ] Update `logging_config.py` voor structured logging
- [ ] OpenTelemetry instrumentatie
- [ ] Trace context propagation

---

### ADR-004: Eventing Keuze: Redis Streams vs Kafka/Redpanda
**Priority**: Medium
**Impact**: Architectuur consistentie
**Scope**: Event systeem

**Beslissingen**:
- Wanneer gebruik je Redis Streams vs Kafka?
- Delivery guarantees per use case
- Schema versioning strategie
- Consumer group management

**Deliverables**:
- [ ] `docs/adr/ADR-004-eventing-strategy.md`
- [ ] Beslissingsmatrix
- [ ] Schema registry implementatie
- [ ] Migration guide voor events

---

### ADR-005: Multi-Tenant Isolatie End-to-End
**Priority**: Hoog
**Impact**: Security & compliance
**Scope**: Auth, API, Storage

**Vereisten**:
- Tenant ID in JWT claims
- Tenant context propagation
- Per-tenant rate limits/quotas
- Tenant-isolatie in ClickHouse/ChromaDB queries
- Audit trails per tenant

**Deliverables**:
- [ ] `docs/adr/ADR-005-multi-tenancy.md`
- [ ] Tenant middleware in API
- [ ] Tenant context in `backend/core/context.py`
- [ ] Rate limiting per tenant
- [ ] Tenant-scoped queries in storage layer

---

### ADR-006: Security Boundaries + Threat Model (STRIDE)
**Priority**: Hoog
**Impact**: Security posture
**Scope**: Hele systeem

**Vereisten**:
- Trust boundaries diagram
- STRIDE analyse per component
- Mitigaties voor:
  - Secrets management
  - SSRF/egress control
  - Tenant data leakage
  - Privilege escalation

**Deliverables**:
- [ ] `docs/adr/ADR-006-security-threat-model.md`
- [ ] Trust boundaries diagram
- [ ] STRIDE analyse document
- [ ] Security runbook
- [ ] Pentest rapport placeholder

---

### ADR-007: Governance: Trade Approval Policy
**Priority**: Medium
**Impact**: Compliance & risk
**Scope**: Trading, Approvals

**Beslissingen**:
- Wanneer auto-approval vs manual approval?
- Policy-as-code implementatie
- Audit logging voor beslissingen
- Human-in-the-loop workflows

**Deliverables**:
- [ ] `docs/adr/ADR-007-trade-governance.md`
- [ ] Policy engine in `backend/governance/`
- [ ] Approval workflow implementatie
- [ ] Audit logging voor trades

---

### ADR-008: Data Lifecycle: Retention, Replay, Privacy
**Priority**: Medium
**Impact**: Compliance & kosten
**Scope**: Storage

**Vereisten**:
- Retention policy per datastore:
  - PostgreSQL: 7 jaar trades
  - ClickHouse: 1 jaar analytics
  - ChromaDB: 30 dagen memory
- Replay/debug procedures
- Privacy-by-design (GDPR)
- Source of truth definities

**Deliverables**:
- [ ] `docs/adr/ADR-008-data-lifecycle.md`
- [ ] Retention policies in code
- [ ] Data cleanup jobs
- [ ] GDPR deletion procedures

---

### ADR-009: Release/Rollback Strategy per Environment
**Priority**: Medium
**Impact**: Deployment betrouwbaarheid
**Scope**: DevOps

**Strategie**:
- Blue/green of canary deployments
- Health check criteria
- Automatische rollback triggers
- Database migratie strategie

**Deliverables**:
- [ ] `docs/adr/ADR-009-release-strategy.md`
- [ ] Helm chart updates voor blue/green
- [ ] Health check endpoints
- [ ] Rollback automation

---

### ADR-010: Performance Budget & Load Testing Plan
**Priority**: Medium
**Impact**: Schaalbaarheid
**Scope**: Performance

**Vereisten**:
- Performance budgets per component
- Load test plan:
  - WS fanout (1000+ clients)
  - Order throughput (100/sec)
  - ClickHouse query concurrency
- CI/CD gates

**Deliverables**:
- [ ] `docs/adr/ADR-010-performance-testing.md`
- [ ] Performance budget document
- [ ] Locust/k6 test scripts
- [ ] CI gates voor performance

---

## Implementatie Roadmap

### Week 1: Fundamentals
- [ ] ADR-001: SLO Model
- [ ] ADR-002: Observability
- [ ] ADR-003: WebSocket Reliability (✅ klaar)

### Week 2: Security & Tenancy
- [ ] ADR-005: Multi-Tenant Isolatie
- [ ] ADR-006: Security Threat Model

### Week 3: Governance & Data
- [ ] ADR-007: Trade Governance
- [ ] ADR-008: Data Lifecycle

### Week 4: Operations & Performance
- [ ] ADR-004: Eventing Strategy
- [ ] ADR-009: Release Strategy
- [ ] ADR-010: Performance Testing

---

## Metrics voor Succes

Na implementatie van alle ADR's:

| Dimensie | Huidig | Doel | Meting |
|----------|--------|------|--------|
| Modulariteit | 9/10 | 9.5/10 | Code review |
| Observability | 8/10 | 9/10 | Dashboard coverage |
| Security | 7/10 | 9/10 | Pentest/threat model |
| Performance | 7.5/10 | 9/10 | SLO compliance |
| **Totaal** | **8/10** | **9/10** | **Weighted avg** |

---

## Directe Volgende Stappen

1. **Review ADR-003** met team
2. **Prioritiseer** ADR-001 en ADR-002 (fundamentals)
3. **Plan** week 1 implementatie
4. **Setup** ADR review proces

---

*Laatste update: 2026-02-20*
