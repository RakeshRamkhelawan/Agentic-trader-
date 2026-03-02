# Phase 15: Hardware Metrics Integration - Implementation Guide

**Phase:** 15 (Hardware Metrics & Adaptive Coherence)
**Status:** 🟡 TDD Phase - Stubs & Framework Complete
**Session Date:** February 4, 2026

---

## 📋 Overview

Phase 15 integrates real-time hardware metrics collection into the Mahabhutas physical layer, enabling dynamic coherence adaptation based on actual system conditions.

### What This Phase Does

**Before (Phase 14):**

```python
# Static, config-driven
akasha_coherence = config.akasha.default_coherence  # Fixed 1.0
agni_coherence = config.agni.default_coherence      # Fixed 1.0
```

**After Phase 15:**

```python
# Dynamic, hardware-driven
network_latency = measure_real_ping()  # 123ms actual
akasha_coherence = 1.0 - (latency * 0.00015)  # 0.92 adaptive

cpu_usage = measure_real_cpu()  # 78% actual
agni_coherence = 1.0 - (cpu * 0.01)  # 0.22 adaptive
```

### Key Benefits

✅ **Self-Aware System** - Knows its own hardware constraints
✅ **Adaptive Behavior** - Changes strategy based on real conditions
✅ **Early Warning** - Detects problems before they cause crashes
✅ **Cost Optimization** - Scales resources based on real metrics
✅ **Realistic Deployments** - Works with actual infrastructure

---

## 📁 Files Created

### 1. Test File

**Location:** `backend/tests/test_phase_15_hardware_metrics.py` (1500+ lines)

**Contents:**

- 50+ comprehensive test stubs
- 8 test classes organized by concern
- 6 fixtures for metrics and system setup
- Expected behavior documentation for each test

**Test Classes:**

1. `TestPhase15MetricsCollection` - Basic metrics collection (8 tests)
2. `TestPhase15AkashaNetworkAdaptation` - Network coherence (7 tests)
3. `TestPhase15AgniComputeAdaptation` - CPU/memory coherence (7 tests)
4. `TestPhase15ApasDataFlowAdaptation` - Queue/dataflow coherence (7 tests)
5. `TestPhase15PrithviStorageAdaptation` - Disk/storage coherence (7 tests)
6. `TestPhase15AdaptiveCoherence` - Overall coherence system (8 tests)
7. `TestPhase15SystemResilience` - Error handling & recovery (6 tests)
8. `TestPhase15PerformanceAndMonitoring` - Monitoring & efficiency (8 tests)

### 2. Implementation Framework

**Location:** `backend/observability/hardware_metrics.py` (500+ lines)

**Classes:**

#### `HardwareMetricsCollector` (Abstract)

Collects real-time hardware metrics using platform-specific APIs.

```python
Methods:
- collect_network_metrics() -> NetworkMetrics
- collect_compute_metrics() -> ComputeMetrics
- collect_storage_metrics() -> StorageMetrics
- collect_dataflow_metrics() -> DataFlowMetrics
- collect_all_metrics() -> AggregatedMetrics
- async stream_metrics() -> AsyncGenerator
```

**Implementation Hints:**

- Use `psutil.cpu_percent()` for CPU metrics
- Use `psutil.virtual_memory()` for memory
- Use `psutil.disk_usage()` for disk space
- Use `ping3` or `socket` for network latency
- Query Redis for queue depth
- Check database connection pools

#### `MetricsAggregator`

Maintains rolling window of metrics history and calculates statistics.

```python
Methods:
- add_metrics(metrics) - Add to history
- get_network_stats() -> Dict[str, float]
- get_compute_stats() -> Dict[str, float]
- get_storage_stats() -> Dict[str, float]
- get_dataflow_stats() -> Dict[str, float]
- detect_trend(metric_type) -> str
- get_metric_correlation(m1, m2) -> float
```

**Implementation Hints:**

- Use `deque` with maxlen for rolling windows
- Calculate mean, std, percentiles from history
- Track trends (improving/stable/degrading)
- Thread-safe with RLock

#### `AdaptiveCoherenceCalculator`

Maps metrics to coherence values for each layer.

```python
Methods:
- calculate_akasha_coherence(network_metrics) -> float
- calculate_vayu_coherence(config_state) -> float
- calculate_agni_coherence(compute_metrics) -> float
- calculate_apas_coherence(dataflow_metrics) -> float
- calculate_prithvi_coherence(storage_metrics) -> float
- apply_damping(layer, new_coherence) -> float
```

**Coherence Formulas (to implement):**

**Akasha (Layer 32) - Network:**

```
base = 1.0
coherence = base - (latency_ms * 0.00015) - (packet_loss_percent * 0.01)
coherence = max(0.3, min(1.0, coherence))  # Clamp to [0.3, 1.0]
```

**Agni (Layer 34) - Computation:**

```
base = 1.0
cpu_penalty = max(0, (cpu_percent - 50) * 0.01)
memory_penalty = max(0, (memory_percent - 70) * 0.01)
thermal_penalty = 0.25 if thermal_throttling else 0
coherence = base - cpu_penalty - memory_penalty - thermal_penalty
coherence = max(0.3, min(1.0, coherence))
```

**Apas (Layer 35) - DataFlow:**

```
base = 1.0
queue_penalty = max(0, (queue_depth - 10) * 0.01)
latency_penalty = msg_latency_ms * 0.0001
cache_bonus = max(0, (cache_hit_rate - 50) * 0.005)
coherence = base - queue_penalty - latency_penalty + cache_bonus
coherence = max(0.3, min(1.0, coherence))
```

**Prithvi (Layer 36) - Storage:**

```
base = 1.0
disk_penalty = max(0, (50 - disk_free_gb) * 0.01)
io_penalty = write_latency_ms * 0.005
backup_penalty = 0.3 if backup_stale else 0
coherence = base - disk_penalty - io_penalty - backup_penalty
coherence = max(0.3, min(1.0, coherence))
```

**Damping (Smoothing):**

```
damped = old_coherence * (1 - damping_factor) + new_coherence * damping_factor
# damping_factor typically 0.7 (70% old, 30% new)
```

#### `MetricsMonitor`

Detects anomalies and generates alerts.

```python
Methods:
- update_baseline(metrics) - Record baseline statistics
- check_for_anomalies(metrics) -> List[str]
- generate_alerts(metrics, coherence) -> List[str]
```

**Implementation Hints:**

- Collect first 100 samples for baseline
- Detect > 2σ deviations as anomalies
- Generate alerts for:
  - Coherence < 0.5
  - Latency > 2000ms
  - Disk free < 50GB
  - Queue depth > 100

#### `Phase15MetricsIntegration`

High-level integration helper for SystemIdentity.

```python
Methods:
- get_adaptive_coherence() -> Dict[int, float]
- get_system_health_report() -> Dict[str, Any]
```

**Integration Points:**

- Called from `SystemIdentity._process_layer_materialize()`
- Returns {32: 0.95, 33: 0.92, 34: 0.88, 35: 0.90, 36: 0.85}
- Replaces static config-based coherence

---

## 🚀 Implementation Roadmap

### Step 1: Implement Test Fixtures (1-2 hours)

**File:** `backend/tests/test_phase_15_hardware_metrics.py`

```python
@pytest.fixture
def mock_metrics_collector():
    """Create a mock collector with controllable values"""
    collector = MockHardwareMetricsCollector()
    # Can set values: set_latency(ms), set_cpu(%), etc.
    return collector
```

**Fixtures to implement:**

1. `tattva_config` - TattvaConfig with Mahabhutas enabled
2. `system_identity` - SystemIdentity instance
3. `mock_metrics_collector` - Controllable mock metrics
4. `mock_network_conditions` - Network metric controls
5. `mock_compute_conditions` - Compute metric controls
6. `async_metrics_stream` - Async generator for testing

### Step 2: Implement HardwareMetricsCollector (3-4 hours)

**File:** `backend/observability/hardware_metrics.py`

Start with concrete implementation class:

```python
class RealHardwareMetricsCollector(HardwareMetricsCollector):
    """Real implementation using psutil and system APIs"""

    def collect_network_metrics(self):
        import psutil
        import ping3

        latency = ping3.ping('api.binance.com') * 1000  # to ms
        net_io = psutil.net_io_counters()

        return NetworkMetrics(
            latency_ms=latency,
            bandwidth_mbps=calculate_bandwidth(net_io),
            packet_loss_percent=measure_packet_loss(),
            ...
        )
```

**Metrics to collect:**

- Network: latency, bandwidth, packet loss to exchange APIs
- Compute: CPU%, memory%, thermal throttling, cores
- Storage: disk I/O, free space, write latency, backup age
- DataFlow: Redis queue depth, DB pool usage, cache hits

### Step 3: Implement MetricsAggregator (2-3 hours)

```python
def get_network_stats(self):
    """Calculate rolling averages and percentiles"""
    latencies = [m.latency_ms for m in self.network_history]
    return {
        'avg_latency': mean(latencies),
        'p95_latency': percentile(latencies, 95),
        'p99_latency': percentile(latencies, 99),
        'min_latency': min(latencies),
        'max_latency': max(latencies),
    }
```

Use `numpy` or implement percentile calculation manually.

### Step 4: Implement AdaptiveCoherenceCalculator (3-4 hours)

```python
def calculate_akasha_coherence(self, network_metrics):
    """Map network metrics to coherence"""
    base = 1.0
    latency_penalty = network_metrics.latency_ms * 0.00015
    packet_loss_penalty = network_metrics.packet_loss_percent * 0.01

    coherence = base - latency_penalty - packet_loss_penalty
    coherence = max(0.3, min(1.0, coherence))  # Clamp

    # Apply damping for smoothing
    return self.apply_damping(32, coherence)
```

Implement all 5 coherence calculation methods with appropriate formulas.

### Step 5: Implement MetricsMonitor (2-3 hours)

```python
def check_for_anomalies(self, metrics):
    """Detect unusual patterns"""
    alerts = []

    if not self.baseline:
        self.update_baseline(metrics)
        return alerts

    # Check if metric deviates > 2 sigma
    if metrics.compute.cpu_percent > baseline_cpu_mean + 2*baseline_cpu_std:
        alerts.append("High CPU anomaly detected")

    return alerts
```

### Step 6: Integration with SystemIdentity (2-3 hours)

**File:** `backend/core/system_identity.py`

Modify `_process_layer_materialize()`:

```python
def _process_layer_materialize(self, layer, context):
    """Materialize layer with adaptive hardware metrics"""

    # Get adaptive coherence from Phase 15
    if layer in [32, 33, 34, 35, 36]:  # Mahabhutas
        metrics_integration = Phase15MetricsIntegration(...)
        coherence_values = metrics_integration.get_adaptive_coherence()
        layer_coherence = coherence_values.get(layer, 1.0)
    else:
        layer_coherence = calculate_default_coherence(layer, context)

    return layer_coherence
```

---

## ✅ Implementation Checklist

**Before running tests:**

- [ ] Fixtures implemented (6 fixtures)
- [ ] HardwareMetricsCollector concrete implementation
- [ ] MetricsAggregator with all stat methods
- [ ] AdaptiveCoherenceCalculator with all 5 coherence functions
- [ ] MetricsMonitor with baseline and anomaly detection
- [ ] Phase15MetricsIntegration integration helper
- [ ] SystemIdentity integration point modified

**Test Execution:**

```bash
# First test run (should fail initially - TDD style)
pytest backend/tests/test_phase_15_hardware_metrics.py -v

# Expected: All tests fail (implementations are stubs)
# Run: 0 passed, 50 failed

# After each implementation step, re-run to see progress
```

---

## 📊 Expected Test Results

### Phase 1 (Fixtures & Imports)

```
FAILED backend/tests/test_phase_15_hardware_metrics.py::...
ERROR in conftest or fixtures
```

### Phase 2 (After Collector Implementation)

```
PASSED TestPhase15MetricsCollection::test_network_latency_collection
FAILED TestPhase15AkashaNetworkAdaptation::test_akasha_low_latency_coherence
```

### Phase 3 (After Coherence Calculator)

```
PASSED TestPhase15MetricsCollection (all 8)
PASSED TestPhase15AkashaNetworkAdaptation (all 7)
PASSED TestPhase15AgniComputeAdaptation (all 7)
... continuing...
```

### Final Result

```
===================== 50 passed in 2.3s =====================
✅ All Phase 15 tests passing
```

---

## 🔧 Key Implementation Details

### Thread Safety

All classes need thread-safety for concurrent access:

```python
from threading import RLock

class MetricsAggregator:
    def __init__(self):
        self._lock = RLock()

    def add_metrics(self, metrics):
        with self._lock:
            self.network_history.append(metrics.network)
```

### Error Handling

Graceful degradation when metrics fail to collect:

```python
def collect_network_metrics(self):
    try:
        latency = ping3.ping(host)
    except Exception as e:
        logger.warning(f"Network latency collection failed: {e}")
        return NetworkMetrics(latency_ms=float('inf'))  # Treated as down
```

### Async Support

For real-time streaming:

```python
async def stream_metrics(self, interval_seconds=1.0):
    while True:
        await asyncio.sleep(interval_seconds)
        yield self.collect_all_metrics()
```

### Data Persistence

Store metrics history for trending:

```python
# In system_state
{
    'tattva_coherence': {
        'layer_32': {
            'value': 0.92,
            'history': [0.94, 0.93, 0.92, ...],  # Last 1000
            'timestamp': datetime.now(),
        }
    }
}
```

---

## 🎯 Success Criteria

- ✅ All 50 tests passing
- ✅ Sub-100ms metrics collection overhead
- ✅ Coherence values stay in [0.3, 1.0] range
- ✅ No memory leaks over sustained operation
- ✅ Thread-safe concurrent access
- ✅ Graceful degradation on metric failures
- ✅ Real hardware metrics integrated with SystemIdentity
- ✅ OpenTelemetry export of all metrics

---

## 📚 References

- **psutil Documentation:** Hardware metrics library
- **Phase 14:** Mahabhutas baseline (layers 32-36)
- **SystemIdentity:** Layer materialization algorithm
- **TDD Pattern:** Test-first development (from Phase 12)

---

## 🚀 Next Phase

After Phase 15 is complete:

- **Phase 16:** Frontend UI with real-time metrics visualization
- **Phase 17:** LLM provider integration (Gemini, OpenAI, Ollama)
- **Phase 18:** Production deployment (Docker, Kubernetes)

---

**Ready to start implementing? Begin with Step 1: Fixtures**
