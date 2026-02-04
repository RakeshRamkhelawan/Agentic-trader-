# Phase 15: Quick Start Guide

**Start TDD Implementation Now**

---

## 📁 Files to Work With

```
backend/tests/test_phase_15_hardware_metrics.py     ← Read test expectations
backend/observability/hardware_metrics.py            ← Implement here
PHASE_15_INIT_GUIDE.md                              ← Implementation steps
PHASE_15_LAUNCH_SUMMARY.md                          ← Full overview
```

---

## 🎯 Next Steps (In Order)

### Step 1️⃣ Implement Fixtures (~1-2 hours)

**File:** `backend/tests/test_phase_15_hardware_metrics.py`

Replace `pass` with actual implementations:

```python
@pytest.fixture
def mock_metrics_collector():
    """Create a mock with controllable values"""
    class MockCollector(HardwareMetricsCollector):
        def __init__(self):
            self.latency_ms = 100
            self.cpu_percent = 50
            self.queue_depth = 10

        def collect_network_metrics(self):
            return NetworkMetrics(latency_ms=self.latency_ms, ...)

        def set_latency(self, ms):
            self.latency_ms = ms

    return MockCollector()
```

**Check:** After implementing, run:

```bash
pytest backend/tests/test_phase_15_hardware_metrics.py::TestPhase15MetricsCollection -v
```

---

### Step 2️⃣ Implement HardwareMetricsCollector (~3-4 hours)

**File:** `backend/observability/hardware_metrics.py`

```python
class RealHardwareMetricsCollector(HardwareMetricsCollector):
    def collect_network_metrics(self):
        import psutil
        import ping3

        # Measure real network
        latency = ping3.ping('api.binance.com') * 1000
        net_io = psutil.net_io_counters()

        return NetworkMetrics(
            latency_ms=latency or 5000,
            bandwidth_mbps=calculate_bandwidth(),
            packet_loss_percent=0.0,
            timestamp=datetime.now()
        )

    def collect_compute_metrics(self):
        import psutil
        return ComputeMetrics(
            cpu_percent=psutil.cpu_percent(interval=0.1),
            memory_percent=psutil.virtual_memory().percent,
            thermal_throttling=check_thermal_throttling(),
            available_cores=psutil.cpu_count(),
            timestamp=datetime.now()
        )

    # Implement: collect_storage_metrics(), collect_dataflow_metrics()
    # Implement: collect_all_metrics(), async stream_metrics()
```

**Check:**

```bash
pytest backend/tests/test_phase_15_hardware_metrics.py::TestPhase15MetricsCollection -v
# Should now PASS (8/8)
```

---

### Step 3️⃣ Implement MetricsAggregator (~2-3 hours)

**File:** `backend/observability/hardware_metrics.py`

```python
def get_network_stats(self):
    """Calculate rolling statistics"""
    if not self.network_history:
        return {}

    latencies = [m.latency_ms for m in self.network_history]

    return {
        'avg_latency': sum(latencies) / len(latencies),
        'p95_latency': percentile(latencies, 95),
        'max_latency': max(latencies),
    }

def detect_trend(self, metric_type, lookback_samples=10):
    """Detect improving/stable/degrading"""
    history = getattr(self, f'{metric_type}_history')
    if len(history) < 2:
        return 'stable'

    recent = list(history)[-lookback_samples:]
    first_half = recent[:len(recent)//2]
    second_half = recent[len(recent)//2:]

    avg1 = sum(first_half) / len(first_half)
    avg2 = sum(second_half) / len(second_half)

    if avg2 > avg1:
        return 'degrading'
    elif avg2 < avg1:
        return 'improving'
    else:
        return 'stable'
```

---

### Step 4️⃣ Implement AdaptiveCoherenceCalculator (~3-4 hours)

**File:** `backend/observability/hardware_metrics.py`

**Key Formulas (Copy-paste ready):**

```python
def calculate_akasha_coherence(self, network_metrics):
    """L32: Network latency → coherence"""
    base = 1.0
    latency_penalty = network_metrics.latency_ms * 0.00015
    packet_loss_penalty = network_metrics.packet_loss_percent * 0.01

    coherence = base - latency_penalty - packet_loss_penalty
    coherence = max(0.3, min(1.0, coherence))  # Clamp

    return self.apply_damping(32, coherence)

def calculate_agni_coherence(self, compute_metrics):
    """L34: CPU/memory → coherence"""
    base = 1.0
    cpu_penalty = max(0, (compute_metrics.cpu_percent - 50) * 0.01)
    memory_penalty = max(0, (compute_metrics.memory_percent - 70) * 0.01)
    thermal_penalty = 0.25 if compute_metrics.thermal_throttling else 0

    coherence = base - cpu_penalty - memory_penalty - thermal_penalty
    coherence = max(0.3, min(1.0, coherence))

    return self.apply_damping(34, coherence)

def calculate_apas_coherence(self, dataflow_metrics):
    """L35: Queue/latency → coherence"""
    base = 1.0
    queue_penalty = max(0, (dataflow_metrics.queue_depth - 10) * 0.01)
    latency_penalty = dataflow_metrics.avg_message_latency_ms * 0.0001
    cache_bonus = max(0, (dataflow_metrics.cache_hit_rate_percent - 50) * 0.005)

    coherence = base - queue_penalty - latency_penalty + cache_bonus
    coherence = max(0.3, min(1.0, coherence))

    return self.apply_damping(35, coherence)

def calculate_prithvi_coherence(self, storage_metrics):
    """L36: Disk/I/O → coherence"""
    base = 1.0
    disk_penalty = max(0, (50 - storage_metrics.disk_free_gb) * 0.01)
    io_penalty = storage_metrics.write_latency_ms * 0.005
    backup_penalty = 0.3 if storage_metrics.last_backup_hours_ago > 24 else 0

    coherence = base - disk_penalty - io_penalty - backup_penalty
    coherence = max(0.3, min(1.0, coherence))

    return self.apply_damping(36, coherence)

def apply_damping(self, layer, new_coherence):
    """Smooth transitions to prevent jitter"""
    old = self._last_coherence.get(layer, 1.0)
    damped = old * (1 - self._damping_factor) + new_coherence * self._damping_factor
    self._last_coherence[layer] = damped
    return damped
```

---

### Step 5️⃣ Implement MetricsMonitor (~2-3 hours)

```python
def check_for_anomalies(self, metrics):
    """Detect unusual patterns"""
    alerts = []

    if not self.baseline:
        self.update_baseline(metrics)
        return alerts

    # Check CPU anomaly
    cpu = metrics.compute.cpu_percent
    baseline_mean = self.baseline['cpu_mean']
    baseline_std = self.baseline['cpu_std']

    if cpu > baseline_mean + 2 * baseline_std:
        alerts.append(f"High CPU anomaly: {cpu}%")

    return alerts

def generate_alerts(self, metrics, coherence_values):
    """Generate operator alerts"""
    alerts = []

    # Alert if any coherence too low
    for layer, coherence in coherence_values.items():
        if coherence < 0.5:
            element = {32: 'Network', 33: 'Config', 34: 'Compute',
                      35: 'DataFlow', 36: 'Storage'}.get(layer)
            alerts.append(f"⚠️ {element} coherence low: {coherence:.2f}")

    # Alert if latency too high
    if metrics.network.latency_ms > 2000:
        alerts.append(f"⚠️ Network latency critical: {metrics.network.latency_ms:.0f}ms")

    # Alert if disk space low
    if metrics.storage.disk_free_gb < 50:
        alerts.append(f"⚠️ Low disk space: {metrics.storage.disk_free_gb:.1f}GB")

    return alerts
```

---

### Step 6️⃣ Integrate with SystemIdentity (~2-3 hours)

**File:** `backend/core/system_identity.py`

Find `_process_layer_materialize()` and modify:

```python
def _process_layer_materialize(self, layer, context):
    """Materialize layer with adaptive metrics (Phase 15)"""

    # For Mahabhutas layers, use hardware metrics
    if layer in [32, 33, 34, 35, 36]:
        from backend.observability.hardware_metrics import (
            Phase15MetricsIntegration,
            RealHardwareMetricsCollector
        )

        collector = RealHardwareMetricsCollector()
        integration = Phase15MetricsIntegration(collector)
        coherence_values = integration.get_adaptive_coherence()

        layer_coherence = coherence_values.get(layer, 1.0)
    else:
        # Non-Mahabhutas layers use original logic
        layer_coherence = self._calculate_default_coherence(layer, context)

    return layer_coherence
```

---

## ✅ Validation

After each step, run tests:

```bash
# Test specific class
pytest backend/tests/test_phase_15_hardware_metrics.py::TestPhase15MetricsCollection -v

# Test specific method
pytest backend/tests/test_phase_15_hardware_metrics.py::TestPhase15AkashaNetworkAdaptation::test_akasha_low_latency_coherence -v

# Test all Phase 15
pytest backend/tests/test_phase_15_hardware_metrics.py -v

# Final verification
pytest backend/tests/test_phase_15_hardware_metrics.py -v --tb=short
# Expected: 58 passed in ~1-2 seconds
```

---

## 📊 Time Estimate

```
Step 1 (Fixtures)           1-2 hours    ✅ Basic infrastructure
Step 2 (Collector)          3-4 hours    ✅ Hardware measurement
Step 3 (Aggregator)         2-3 hours    ✅ Statistics & trending
Step 4 (Coherence)          3-4 hours    ✅ Core adaptive logic
Step 5 (Monitor)            2-3 hours    ✅ Anomaly detection
Step 6 (Integration)        2-3 hours    ✅ SystemIdentity hookup
─────────────────────────────────────────
TOTAL                      13-20 hours
```

---

## 🎯 Success = All Tests Green

```bash
================================ 58 passed in 1.5s =================================

✅ TestPhase15MetricsCollection (8/8)
✅ TestPhase15AkashaNetworkAdaptation (7/7)
✅ TestPhase15AgniComputeAdaptation (7/7)
✅ TestPhase15ApasDataFlowAdaptation (7/7)
✅ TestPhase15PrithviStorageAdaptation (7/7)
✅ TestPhase15AdaptiveCoherence (8/8)
✅ TestPhase15SystemResilience (6/6)
✅ TestPhase15PerformanceAndMonitoring (8/8)
```

---

## 🚀 Ready? Start with Step 1!

Questions? See PHASE_15_INIT_GUIDE.md for detailed explanations.
