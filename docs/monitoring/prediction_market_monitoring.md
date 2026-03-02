# Prediction Market Intelligence - Monitoring Guide

**Version:** 1.0
**Last Updated:** 2026-02-13
**Status:** ✅ READY

---

## Overview

The Prediction Market Intelligence service is monitored via Prometheus metrics exposed at `/metrics` endpoint. Metrics track:

- **Request Performance** - Latency and count by endpoint
- **Analysis Jobs** - Execution time and success rate
- **Signal Quality** - Confidence distribution and volume
- **External Services** - Kalshi API and DuckDB performance
- **Health Indicators** - Circuit breaker state, cache hits/misses

---

## Metrics Endpoints

| Endpoint | Port | Path | Purpose |
|----------|------|------|---------|
| Prediction Service | 8002 | `/metrics` | Prometheus metrics |
| Main API | 8001 | `/metrics` | Aggregated metrics |
| Prometheus | 9090 | `/graph` | Metrics dashboard |
| Grafana | 3000 | `/` | Visualization (optional) |

---

## Key Metrics

### Request Performance

```
prediction_requests_total{method="GET",endpoint="/api/v1/signals",status="200"}
prediction_request_duration_seconds{method="GET",endpoint="/api/v1/signals"}
```

**Interpretation:**
- `_total` = Counter (cumulative)
- `_duration_seconds` = Histogram (percentiles: p50, p95, p99)

**Healthy Ranges:**
- P50 < 10ms (typical signal request)
- P95 < 50ms
- P99 < 100ms

### Analysis Jobs

```
prediction_analysis_jobs_total{analysis_type="maker_taker",status="completed"}
prediction_analysis_duration_seconds{analysis_type="maker_taker"}
```

**Healthy Ranges:**
- Success rate > 95%
- Average duration < 60s
- P99 < 120s

### Signal Quality

```
prediction_signals_generated_total{market="kalshi",category="crypto",signal_type="bullish"}
prediction_signal_confidence{market="kalshi"}
```

**Healthy Indicators:**
- Signals spreading across confidence ranges (not all 0.5+)
- Consistent signal generation per market
- Balanced signal types

### Circuit Breaker

```
prediction_circuit_breaker_state{service="kalshi_api"}
prediction_circuit_breaker_transitions_total{service="kalshi_api",from_state="closed",to_state="open"}
```

**Healthy State:**
- `state = 0` (closed) - Normal operation
- `state = 1` (open) - Service temporarily degraded
- `state = 2` (half-open) - Recovery in progress

---

## Alerting Rules

### Critical Alerts

1. **Service Down (HTTP 503)**
   - Metric: `up{job="prediction-intelligence"} == 0`
   - Action: Immediate page
   - Resolution: Check service logs, restart if necessary

2. **High Error Rate**
   - Metric: `rate(prediction_requests_total{status=~"5..|4[0-9]."}[5m]) > 0.10`
   - Threshold: > 10% errors
   - Action: Investigate error logs

3. **High Latency**
   - Metric: `prediction_request_duration_seconds{quantile="0.95"} > 1`
   - Threshold: P95 > 1s
   - Action: Check upstream services, circuit breaker state

### Warning Alerts

1. **Circuit Breaker Open**
   - Metric: `prediction_circuit_breaker_state > 0`
   - Action: Monitor recovery, prepare incident response

2. **Cache Hit Rate Degradation**
   - Metric: `rate(prediction_cache_hits_total[5m]) / (rate(prediction_cache_hits_total[5m]) + rate(prediction_cache_misses_total[5m])) < 0.8`
   - Threshold: < 80% hit rate
   - Action: Review cache policy, check for memory pressure

---

## Verification Commands

### Check Metrics Endpoint

```bash
# Direct endpoint check
curl http://localhost:8002/metrics | grep prediction_requests_total

# Expected output (example)
prediction_requests_total{method="GET",endpoint="/api/v1/signals",status="200"} 1523
```

### Check Prometheus Scraping

```bash
# Check if prediction-intelligence target is healthy
curl http://localhost:9090/api/v1/targets | jq '.data | map(select(.labels.job == "prediction-intelligence"))'

# Expected: State = "up" or "down"
```

### Query Metrics in Prometheus

```bash
# Check request rate (requests per second)
curl 'http://localhost:9090/api/v1/query?query=rate(prediction_requests_total%5B1m%5D)'

# Check P95 latency
curl 'http://localhost:9090/api/v1/query?query=histogram_quantile(0.95, prediction_request_duration_seconds)'

# Check error rate
curl 'http://localhost:9090/api/v1/query?query=rate(prediction_requests_total{status=~"5.."}%5B5m%5D)'
```

### Grafana Dashboard (if available)

1. Navigate to http://localhost:3000
2. Login (default: admin/admin)
3. Import dashboard or create from Prometheus queries
4. Key visualizations:
   - Request rate and latency
   - Error rate and top errors
   - Analysis job performance
   - Signal confidence distribution

---

## Troubleshooting

### Metrics Not Appearing in Prometheus

**Symptom:** `/metrics` endpoint returns data, but not in Prometheus

**Investigation:**
```bash
# Check if Prometheus can reach the service
curl http://prediction-intelligence:8002/health

# Check Prometheus logs for scrape errors
docker-compose logs prometheus | grep prediction-intelligence

# View target status in Prometheus
curl http://localhost:9090/api/v1/targets | jq '.data[] | select(.labels.job == "prediction-intelligence")'
```

**Solutions:**
1. Verify network connectivity between Prometheus and service
2. Check `/metrics` endpoint returns valid Prometheus format
3. Verify service is actually running
4. Check scrape interval hasn't been overridden

### High Cardinality Metrics

**Symptom:** Prometheus performance degrading, memory usage increasing

**Issue:** Too many label combinations (e.g., unique endpoint values)

**Prevention:**
- Limit endpoint paths in metrics (use regex in Prometheus config)
- Avoid including user IDs, request IDs in labels
- Use metric relabeling to normalize paths

**Fix:**
```yaml
# In prometheus.yml, add metric_relabel_configs
metric_relabel_configs:
  - source_labels: [__name__]
    regex: 'prediction_request_duration_seconds'
    action: keep
```

### Missing Metrics Categories

**Symptom:** Some metrics not being recorded (e.g., signal metrics)

**Causes:**
1. Code path not executed (no signals generated yet)
2. Middleware or metric code not loaded
3. Conditional metrics (only recorded on certain events)

**Investigation:**
```bash
# Check which metrics are available
curl http://localhost:8002/metrics | grep prediction_signals

# If empty, check:
# 1. Analysis jobs are running
# 2. Signal generation code is called
# 3. Metrics are imported in the code path
```

---

## Best Practices

### For Operators

1. **Alert on Business Metrics**
   - High error rate (>10%)
   - Very high latency (P99 > 1s)
   - Service unavailability

2. **Monitor Dependencies**
   - Kalshi API availability
   - DuckDB connection status
   - Circuit breaker state

3. **Regular Reviews**
   - Weekly metric review
   - Trend analysis (performance degradation)
   - Anomaly detection setup

### For Developers

1. **Add Metrics for New Features**
   - Define metrics in `metrics.py`
   - Use helper functions like `record_request()`
   - Document metric purpose

2. **Avoid High Cardinality**
   - Use fixed label values when possible
   - Normalize dynamic values (e.g., endpoint paths)
   - Document label values

3. **Test Metrics**
   - Verify metrics appear after code execution
   - Check metric values make sense
   - Test in staging environment

---

## Configuration

### Enable Metrics Collection

Metrics are automatically enabled when:
1. Prometheus dependencies installed (`prometheus_client`)
2. MetricsMiddleware added to FastAPI app
3. `/metrics` endpoint registered

### Disable Metrics (For Development)

```python
# In backend/api/main.py, comment out:
# app.add_middleware(MetricsMiddleware)
# app.add_route("/metrics", metrics_endpoint)
```

### Custom Scrape Intervals

Edit `infrastructure/prometheus/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'prediction-intelligence'
    scrape_interval: 30s  # Slower collection
    scrape_timeout: 10s   # Timeout per scrape
```

---

## References

- [Prometheus Documentation](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Python Prometheus Client](https://github.com/prometheus/client_python)
- [Histogram Percentiles](https://prometheus.io/docs/practices/histograms/)
- [Metric Naming](https://prometheus.io/docs/practices/naming/)

---

**Document Location:** `docs/monitoring/prediction_market_monitoring.md`

**Last Verified:** 2026-02-13
**Status:** ✅ All metrics operational
