# ADR-001: SLO/SLI Model per Kritieke Flow

**Status**: Proposed  
**Date**: 2026-02-20  
**Author**: Architecture Team  
**Scope**: Alle kritieke gebruikersflows  

---

## Context

Het Agentic Trader Platform heeft drie kritieke flows die directe impact hebben op gebruikerservaring en trading resultaten:

1. **Market Data → UI**: Real-time prijsupdates via WebSocket
2. **Order Intake → Execution**: Order plaatsing en uitvoering
3. **Agent Decision Loop**: OODA cyclus voor AI beslissingen

Huidige situatie:
- Latency filosofie aanwezig (hot path <1ms, cognitive 50-200ms)
- Geen concrete meetbare doelen
- Geen error budgets
- Geen degrade mode gedocumenteerd

---

## Decision

### 1. Definieer 3 Kritieke Flows

#### Flow A: Market Data → UI (WebSocket)
**User Impact**: Traders zien real-time prijzen; vertraging = verlies

| SLI | Meetmethode | SLO | Window |
|-----|-------------|-----|--------|
| Latency (p99) | WS publish → client receive | <100ms | 1m |
| Latency (p95) | WS publish → client receive | <50ms | 1m |
| Availability | Verbinding succes rate | >99.9% | 1h |
| Message Delivery | Geleverd / gepubliceerd | >99.99% (high priority) | 1m |
| Error Rate | WS errors / totaal | <0.1% | 5m |

**Error Budget**: 0.1% downtime per maand = 43min

**Degrade Mode**:
- Bij >p99 latency: switch naar 1s updates (niet realtime)
- Bij >1% drop rate: force resync + REST fallback
- Bij connectie verlies: toon "delayed data" indicator

---

#### Flow B: Order Intake → Execution
**User Impact**: Orders moeten betrouwbaar en snel uitgevoerd worden

| SLI | Meetmethode | SLO | Window |
|-----|-------------|-----|--------|
| End-to-end Latency (p99) | Order request → confirm | <500ms | 1m |
| End-to-end Latency (p95) | Order request → confirm | <200ms | 1m |
| Success Rate | Succesvolle orders / totaal | >99.95% | 1h |
| Risk Check Latency (p99) | Order → risk decision | <50ms | 1m |
| Execution Latency (p99) | Risk approve → exchange | <100ms | 1m |

**Error Budget**: 0.05% failed orders = 1 op 2000

**Degrade Mode**:
- Bij >p99 latency: async processing + "pending" status
- Bij risk engine overload: reject nieuwe orders (circuit breaker)
- Bij exchange downtime: queue orders (max 5min)

---

#### Flow C: Agent Decision Loop (OODA)
**User Impact**: AI agents moeten tijdig beslissingen maken

| SLI | Meetmethode | SLO | Window |
|-----|-------------|-----|--------|
| Decision Latency (p99) | Trigger → decision output | <200ms | 1m |
| Decision Latency (p95) | Trigger → decision output | <100ms | 1m |
| Decision Quality | Goedgekeurde beslissingen / totaal | >90% | 1h |
| LLM Availability | Succesvolle LLM calls / totaal | >99.5% | 1h |
| Memory Retrieval (p99) | Query → resultaat | <20ms | 1m |

**Error Budget**: 0.5% LLM failures = fallback naar rule-based

**Degrade Mode**:
- Bij LLM timeout (>2s): gebruik cached strategy
- Bij >10% quality drop: human approval verplicht
- Bij memory outage: operate zonder context (conservatief)

---

### 2. Error Budget Policy

```
Error Budget = 100% - SLO target

Als error budget op is:
1. Stop feature development voor deze flow
2. Prioritiseer reliability fixes
3. Escaleer naar on-call engineer
4. Overweeg manual overrides
```

**Voorbeeld**: Market Data SLO 99.9% → 0.1% error budget
- Per maand: 43 minuten downtime toegestaan
- Als bereikt: alleen critical fixes tot reset

---

### 3. Alerting Thresholds

| Severity | Condition | Response |
|----------|-----------|----------|
| **Critical** | SLO breach | PagerDuty + auto-degrade |
| **Warning** | 5% van error budget in 1h | Slack alert + investigation |
| **Info** | Latency p95 > 2x baseline | Metric dashboard highlight |

---

## Implementation

### 1. SLO Configuratie

```python
# backend/core/config/slo.py
from dataclasses import dataclass

@dataclass
class SLOConfig:
    target: float  # 0.999 = 99.9%
    latency_p99_ms: int
    latency_p95_ms: int
    error_budget: float  # percentage
    window: str  # "1m", "1h", "30d"

SLO_DEFINITIONS = {
    "market_data_streaming": SLOConfig(
        target=0.999,
        latency_p99_ms=100,
        latency_p95_ms=50,
        error_budget=0.001,
        window="30d"
    ),
    "order_execution": SLOConfig(
        target=0.9995,
        latency_p99_ms=500,
        latency_p95_ms=200,
        error_budget=0.0005,
        window="30d"
    ),
    "agent_decision": SLOConfig(
        target=0.995,
        latency_p99_ms=200,
        latency_p95_ms=100,
        error_budget=0.005,
        window="30d"
    )
}
```

### 2. SLI Measurement Code

```python
# backend/core/telemetry/slo_tracker.py
from prometheus_client import Counter, Histogram, Gauge
import time

class SLITracker:
    """Track SLIs for SLO compliance."""
    
    def __init__(self):
        # Latency histograms per flow
        self.latency = Histogram(
            'slo_latency_seconds',
            'Latency per flow',
            ['flow', 'stage'],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
        )
        
        # Success counters
        self.requests = Counter(
            'slo_requests_total',
            'Total requests',
            ['flow', 'status']  # status: success, error, timeout
        )
        
        # Error budget tracking
        self.error_budget_remaining = Gauge(
          'slo_error_budget_remaining',
            'Remaining error budget (0-1)',
            ['flow']
        )
        
        # SLO compliance ratio
        self.compliance = Gauge(
            'slo_compliance_ratio',
            'Current SLO compliance (0-1)',
            ['flow']
        )
    
    def track_latency(self, flow: str, latency_seconds: float, stage: str = "total"):
        """Record latency for a flow."""
        self.latency.labels(flow=flow, stage=stage).observe(latency_seconds)
    
    def track_request(self, flow: str, success: bool, timeout: bool = False):
        """Record request outcome."""
        if timeout:
            status = "timeout"
        else:
            status = "success" if success else "error"
        self.requests.labels(flow=flow, status=status).inc()
    
    def record_order_execution(self, latency_ms: float, success: bool):
        """Track order execution SLI."""
        self.track_latency("order_execution", latency_ms / 1000, "total")
        self.track_request("order_execution", success)
    
    def record_market_data_delivery(self, latency_ms: float, delivered: bool):
        """Track market data delivery SLI."""
        self.track_latency("market_data_streaming", latency_ms / 1000, "delivery")
        self.track_request("market_data_streaming", delivered)
    
    def record_agent_decision(self, latency_ms: float, quality_score: float):
        """Track agent decision SLI."""
        self.track_latency("agent_decision", latency_ms / 1000, "total")
        quality_ok = quality_score >= 0.9
        self.track_request("agent_decision", quality_ok)

# Global instance
slo_tracker = SLITracker()
```

### 3. Integration Points

**WebSocket Manager** (ADR-003):
```python
# In websocket_manager_v2.py
async def broadcast(self, stream: str, data: dict):
    start_time = time.time()
    
    # ... broadcast logic ...
    
    latency = time.time() - start_time
    slo_tracker.record_market_data_delivery(
        latency_ms=latency * 1000,
        delivered=(stats["dropped"] == 0)
    )
```

**Order Execution**:
```python
# In backend/execution/smart_order_router.py
async def route_order(self, order: OrderRequest):
    start_time = time.time()
    
    try:
        # ... execution logic ...
        success = True
    except Exception:
        success = False
        raise
    finally:
        latency = time.time() - start_time
        slo_tracker.record_order_execution(
            latency_ms=latency * 1000,
            success=success
        )
```

**Agent Decision**:
```python
# In backend/core/cognitive_mind_service.py
async def make_decision(self, context: DecisionContext):
    start_time = time.time()
    
    decision = await self._generate_decision(context)
    
    latency = time.time() - start_time
    slo_tracker.record_agent_decision(
        latency_ms=latency * 1000,
        quality_score=decision.confidence
    )
    
    return decision
```

---

## Monitoring

### Grafana Dashboard: "SLO Compliance"

**Panels**:
1. **SLO Compliance Overview**: 3 gauges (99.9%, 99.95%, 99.5%)
2. **Error Budget Burn**: Burn rate per flow
3. **Latency Percentiles**: p50/p95/p99 per flow
4. **Success Rate**: Real-time success percentages
5. **Alert Status**: Active SLO alerts

### Prometheus Recording Rules

```yaml
# infrastructure/prometheus/rules/slo.yml
groups:
  - name: slo_rules
    interval: 1m
    rules:
      # Market Data SLO
      - record: slo:market_data:availability
        expr: |
          sum(rate(slo_requests_total{flow="market_data_streaming",status="success"}[5m]))
          /
          sum(rate(slo_requests_total{flow="market_data_streaming"}[5m]))
      
      # Order Execution SLO
      - record: slo:order_execution:success_rate
        expr: |
          sum(rate(slo_requests_total{flow="order_execution",status="success"}[5m]))
          /
          sum(rate(slo_requests_total{flow="order_execution"}[5m]))
      
      # Latency percentiles
      - record: slo:latency:p99
        expr: histogram_quantile(0.99, slo_latency_seconds_bucket)
      
      - record: slo:latency:p95
        expr: histogram_quantile(0.95, slo_latency_seconds_bucket)
```

### Alerts

```yaml
# infrastructure/prometheus/rules/slo_alerts.yml
groups:
  - name: slo_alerts
    rules:
      - alert: SLOBreach_MarketData
        expr: slo:market_data:availability < 0.999
        for: 2m
        labels:
          severity: critical
          team: platform
        annotations:
          summary: "Market Data SLO breach"
          description: "Availability {{ $value }} < 99.9%"
      
      - alert: ErrorBudgetBurn_OrderExecution
        expr: |
          (
            sum(rate(slo_requests_total{flow="order_execution",status!="success"}[1h]))
            /
            sum(rate(slo_requests_total{flow="order_execution"}[1h]))
          ) > 0.0005 * 14.4  # 2% van maandelijks budget in 1h
        for: 5m
        labels:
          severity: warning
          team: trading
        annotations:
          summary: "Order execution error budget burning fast"
```

---

## Consequences

### Positief
- Meetbare betrouwbaarheid
- Duidelijke degrade scenarios
- Data-driven beslissingen
- Klantverwachtingen duidelijk

### Negatief
- Extra complexiteit in code
- Monitoring overhead
- Team moet SLOs begrijpen
- Error budget management vereist discipline

---

## References

- [Google SRE Book - SLOs](https://sre.google/sre-book/service-level-objectives/)
- [Prometheus SLO Best Practices](https://prometheus.io/docs/practices/)

---

## Decision Log

| Date | Change | Author |
|------|--------|--------|
| 2026-02-20 | Initial draft | Architecture Team |
