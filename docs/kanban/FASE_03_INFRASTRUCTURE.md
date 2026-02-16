# Fase 3: Infrastructure (K8s, Docker, Monitoring)

> **Prioriteit**: 🟡 HIGH
> **Afhankelijkheden**: Fase 2 (Vault → K8s init container)
> **Geschatte effort**: 5-7 dagen
> **Master document**: [SAMKHYA_MASTER_KANBAN_TDD.md](./SAMKHYA_MASTER_KANBAN_TDD.md)

---

## Overzicht

Complete infrastructuur: productie-grade Kubernetes deployment, multi-stage Docker images met ephemeris data, en Prometheus/Grafana monitoring met Samkhya-specifieke dashboards.

```
Helm Chart (agentic-platform)
├── StatefulSet (backend + ephemeris .se1 files)
├── Service (ClusterIP + Ingress)
├── NetworkPolicy (tenant isolation)
├── CronJob (key rotation via Vault)
├── ConfigMap (Prometheus scrape config)
└── Grafana Dashboards (OODA + Navagraha + Guna)
```

---

## Bestaande Code Referenties

| Bestand | Regels | Status |
|---------|--------|--------|
| [docker-compose.yml](../../docker-compose.yml) | 300 | Redpanda, ClickHouse, Redis, PG, Prom, Grafana |
| [infrastructure/docker/Dockerfile](../../infrastructure/docker/Dockerfile) | 31 | Basis Python image |
| [infrastructure/k8s/charts/](../../infrastructure/k8s/charts/) | — | Helm chart met 8 templates |
| [infrastructure/prometheus/prometheus.yml](../../infrastructure/prometheus/prometheus.yml) | 15 | Basis scrape config |
| [backend/observability/metrics.py](../../backend/observability/metrics.py) | 75 | Prometheus counters |
| [backend/observability/hardware_metrics.py](../../backend/observability/hardware_metrics.py) | 459 | Hardware monitoring |

---

## Taken & Microtaken

---

### TAAK 3.1: Kubernetes Hardening

**Doel**: Production-ready Helm chart met health checks, resource limits, HPA.

**Bestanden te wijzigen**:
- `infrastructure/k8s/charts/agentic-platform/values.yaml`
- `infrastructure/k8s/charts/agentic-platform/templates/statefulset.yaml`

**Bestanden te creëren**:
- `infrastructure/k8s/charts/agentic-platform/templates/hpa.yaml`
- `infrastructure/k8s/charts/agentic-platform/templates/pdb.yaml`
- `tests/integration/test_k8s_deployments.py` (uitbreiden)

---

#### Microtaak 3.1.1: Resource Limits & Health Probes

**Masterprompt**:
```
Voeg resource limits toe aan statefulset.yaml:
- Backend: requests 256Mi/250m, limits 1Gi/1000m
- Liveness probe: /api/health, period 30s
- Readiness probe: /api/health?ready=true, period 10s
- Startup probe: /api/health, failure threshold 30, period 10s
Bestaand: statefulset.yaml template in infrastructure/k8s/charts/
```

**Test FIRST**:
```python
# tests/integration/test_k8s_deployments.py

class TestK8sHealthChecks:

    def test_liveness_probe_defined(self):
        """Happy: StatefulSet heeft liveness probe."""
        pass

    def test_readiness_probe_defined(self):
        """Happy: StatefulSet heeft readiness probe."""
        pass

    def test_resource_limits_set(self):
        """Happy: Memory en CPU limits zijn gedefinieerd."""
        pass

    def test_startup_probe_gives_enough_time(self):
        """Happy: Startup probe = 30 * 10s = 300s max startup."""
        pass

    def test_helm_template_renders_valid_yaml(self):
        """Happy: helm template --debug renders zonder errors."""
        pass

    def test_invalid_values_caught_by_schema(self):
        """Unhappy: Ongeldige values.yaml → helm lint error."""
        pass
```

---

#### Microtaak 3.1.2: HPA (Horizontal Pod Autoscaler)

**Masterprompt**:
```
HorizontalPodAutoscaler voor backend:
- Min replicas: 2 (HA)
- Max replicas: 10
- Target CPU utilization: 70%
- Target memory utilization: 80%
- Scale-down stabilization: 300s
```

**Test FIRST**:
```python
class TestHPA:

    def test_hpa_min_replicas_at_least_2(self):
        """Happy: Minimaal 2 pods voor HA."""
        pass

    def test_hpa_scales_on_cpu(self):
        """Happy: CPU > 70% → scale up."""
        pass

    def test_hpa_scale_down_stabilization(self):
        """Happy: Scale-down wacht 300s voordat pods verwijderd."""
        pass
```

#### Microtaak 3.1.3: Vault Init Container + Sidecar

**Masterprompt**:
```
Vault agent als init container voor secret injection.
Springt CronJob key-rotation (bestaand: cronjob-key-rotation.yaml).
Vault annotations op StatefulSet:
  vault.hashicorp.com/agent-inject: "true"
  vault.hashicorp.com/role: "agentic-trader"
  vault.hashicorp.com/agent-inject-secret-db-creds: "database/creds/trader"
```

---

### TAAK 3.2: Docker Multi-Stage Build

**Doel**: Optimized Docker image met ephemeris bestanden en alle dependencies.

**Bestanden te wijzigen**:
- `infrastructure/docker/Dockerfile` (31 regels — uitbreiden)
- `infrastructure/docker/.dockerignore`

**Bestanden te creëren**:
- `infrastructure/docker/Dockerfile.test`
- `tests/integration/test_docker_build.py` (uitbreiden)

---

#### Microtaak 3.2.1: Multi-Stage Dockerfile

**Masterprompt**:
```
Multi-stage build:
Stage 1 (builder): Install dependencies, compile wheels
Stage 2 (runtime): Copy wheels + app code
- Python 3.12-slim als base
- Ephemeris bestanden: Swiss Ephemeris .se1 files bundelen (Kerykeion bundelt deze al)
- Non-root user: uid 1000
- Health check: HEALTHCHECK CMD curl -f http://localhost:8000/api/health
Bestaand: Dockerfile is 31 regels basis Python image.
```

**Test FIRST**:
```python
class TestDockerBuild:

    def test_image_builds_successfully(self):
        """Happy: docker build slaagt zonder errors."""
        pass

    def test_image_runs_and_health_passes(self):
        """Happy: Container start, /api/health returnt 200."""
        pass

    def test_image_has_non_root_user(self):
        """Happy: Process draait als non-root (uid 1000)."""
        pass

    def test_ephemeris_files_present(self):
        """Happy: .se1 ephemeris bestanden aanwezig in image."""
        pass

    def test_image_size_under_500mb(self):
        """Happy: Image < 500MB (slim base)."""
        pass

    def test_no_dev_dependencies_in_runtime(self):
        """Unhappy: pytest/dev tools NIET in runtime image."""
        pass
```

---

### TAAK 3.3: Prometheus + Grafana Monitoring

**Doel**: Complete observability met Samkhya-specifieke dashboards.

**Bestanden te wijzigen**:
- `infrastructure/prometheus/prometheus.yml` (15 regels — uitbreiden)

**Bestanden te creëren**:
- `infrastructure/grafana/dashboards/ooda_loop.json`
- `infrastructure/grafana/dashboards/navagraha.json`
- `infrastructure/grafana/dashboards/guna_balance.json`
- `infrastructure/grafana/provisioning/dashboards.yml`
- `backend/observability/navagraha_metrics.py`
- `backend/tests/unit/test_navagraha_metrics.py`

**Bestaande referenties**:
- `backend/observability/metrics.py:1-75` (PrometheusMiddleware, counters)
- `backend/services/intent_monitor.py:1-53` (guna Prometheus gauges bestaand)

---

#### Microtaak 3.3.1: Navagraha Prometheus Metrics

**Masterprompt**:
```
Nieuwe Prometheus metrics voor Navagraha layer:
- navagraha_rahu_kala_active (Gauge) — 0/1
- navagraha_trading_gate_open (Gauge) — 0/1
- navagraha_dominant_element (Info) — label element
- navagraha_guna_sattva_delta (Gauge) — from guna_modulation
- navagraha_guna_rajas_delta (Gauge)
- navagraha_guna_tamas_delta (Gauge)
- navagraha_dasha_mahadasha_lord (Info) — label graha
- navagraha_hora_ruling_planet (Info) — label graha
- navagraha_assess_duration_seconds (Histogram) — ephem calc latency
- navagraha_cache_hit_total (Counter) — caching effectiveness
Bestaand: intent_monitor.py heeft al guna gauges (global_guna_sattva, etc.)
```

**Test FIRST**:
```python
class TestNavagrahaMetrics:

    def test_rahu_kala_gauge_updates(self):
        """Happy: Rahu Kala gauge reflecteert engine state."""
        pass

    def test_trading_gate_gauge_synced_with_rahu_kala(self):
        """Happy: Gate = inverse van Rahu Kala."""
        pass

    def test_assess_histogram_records_latency(self):
        """Happy: Elke assess() call wordt gemeten."""
        pass

    def test_cache_hit_counter_increments(self):
        """Happy: Cache hits tellen op."""
        pass

    def test_metrics_endpoint_returns_prometheus_format(self):
        """Happy: /metrics endpoint retourneert text/plain."""
        pass
```

#### Microtaak 3.3.2: Grafana Dashboards

**Masterprompt**:
```
3 Grafana dashboard JSON files:
1. OODA Loop Dashboard: cycle duration, phase timings, decision counts, error rate
2. Navagraha Dashboard: planetary positions (polar chart), Rahu Kala timeline,
   Hora sequence, Dasha progress bar, trading gate status
3. Guna Balance Dashboard: 3-axis (sattva/rajas/tamas) real-time,
   modulation deltas, agent prana levels, harmony score
Provisioning via Grafana datasource + dashboard YAML.
```

**Taak-afronding integratie test**:
```python
async def test_integration_3_3_prometheus_scrape_all_metrics():
    """
    Integratie: Prometheus scraped alle targets, Grafana dashboards laden.
    """
    # 1. Start app met Prometheus middleware
    # 2. Trigger OODA cycle
    # 3. Verify /metrics bevat navagraha_* metrics
    # 4. Verify dashboard JSON is valid Grafana format
```

---

## Fase 3 Productie Test

```python
@pytest.mark.e2e
async def test_production_phase3_infrastructure():
    """
    PRODUCTIE TEST:
    1. Helm chart renders valid YAML
    2. Docker image bouwt en start
    3. Health checks passeren
    4. Prometheus scrapes succesvol
    5. Ephemeris bestanden beschikbaar in container
    """
    pass
```

---

## Kruisverwijzingen

- **← Fase 1**: Docker image moet ephemeris .se1 bestanden bundelen
- **← Fase 2**: Vault init container voor secret injection
- **→ Fase 4**: Prometheus metrics voor broker latency (Taak 4.1)
- **→ Fase 5**: Grafana dashboards embedded in frontend (Taak 5.2)
- **→ Fase 7**: Prometheus alerting voor circuit breaker trips (Taak 7.4)
