# Phase 16: Frontend Dashboard - Quick Start Guide

## 6-Step Implementation Roadmap

### Step 1: Create REST API Endpoints

**File**: `backend/api/dashboard.py` → `DashboardAPI` class

```python
from fastapi import FastAPI
from backend.api.dashboard import DashboardAPI, MetricsProvider

app = FastAPI()
api = DashboardAPI(metrics_provider)

@app.get("/api/metrics")
def get_metrics():
    """Returns current metrics snapshot."""
    return api.get_metrics()

@app.get("/api/coherence")
def get_coherence():
    """Returns Mahabhutas coherence values."""
    return api.get_coherence()

@app.get("/api/alerts")
def get_alerts(severity: str = None):
    """Returns recent alerts."""
    return api.get_alerts(severity)

@app.get("/api/history")
def get_history(hours: int = 24):
    """Returns historical metrics."""
    return api.get_history(hours)

@app.get("/api/layer/{layer_id}")
def get_layer_status(layer_id: int):
    """Returns status for one layer."""
    return api.get_layer_status(layer_id)

@app.post("/api/config")
def update_config(config: dict):
    """Updates dashboard configuration."""
    return api.update_config(config)

@app.get("/api/health")
def get_health():
    """Returns overall system health."""
    return api.get_health()

@app.get("/api/export/csv")
def export_csv(hours: int = 24):
    """Exports metrics as CSV."""
    return api.export_csv(hours)
```

**Test**: `test_phase_16_frontend_dashboard.py::TestPhase16DashboardAPI`

---

### Step 2: Real-Time Metrics Collection

**File**: `backend/api/dashboard.py` → `RealtimeMetricsService` class

```python
from backend.api.dashboard import RealtimeMetricsService

metrics_service = RealtimeMetricsService(
    metrics_provider=integration,
    refresh_interval_ms=1000
)

# Get current metrics (with caching)
current = metrics_service.get_current_metrics(use_cache=True)

# Validate coherence values are in [0.3, 1.0]
validated = metrics_service.validate_coherence_values(current['coherence'])

# Calculate overall system load
load = metrics_service.calculate_system_load(current)

# Start continuous collection
await metrics_service.start_collection()

# Later: stop collection
await metrics_service.stop_collection()
```

**Expected Behavior**:

- Updates every 1 second (configurable)
- Sub-millisecond latency from hardware
- Caches results within window
- No drops or jitter

**Test**: `test_phase_16_frontend_dashboard.py::TestPhase16RealTimeMetrics`

---

### Step 3: Alert System

**File**: `backend/api/dashboard.py` → `AlertService` class

```python
from backend.api.dashboard import AlertService

alerts = AlertService(retention_hours=24)

# Check and generate alerts based on coherence
coherence_alerts = alerts.check_coherence_thresholds({
    32: 0.95, 33: 1.0, 34: 0.88, 35: 0.92, 36: 0.99
})
# → ["⚠️ Agni coherence degraded: 0.88"]

# Check metrics thresholds
metric_alerts = alerts.check_metric_thresholds({
    'latency_ms': 2500,
    'cpu_percent': 92,
    'disk_free_gb': 30,
    'queue_depth': 150
})
# → ["🔴 Network latency critical: 2500ms",
#    "🟡 CPU high: 92%", ...]

# Add manual alert
alerts.add_alert("Manual intervention needed", severity='critical')

# Get recent alerts
recent = alerts.get_recent_alerts(limit=50, severity='critical')

# Clean up old alerts
cleared = alerts.clear_alerts(older_than_hours=24)

# Periodic cleanup (run hourly)
await alerts.cleanup_old_alerts()
```

**Alert Thresholds**:

- **Coherence**: Warning <0.7, Critical <0.5
- **Network Latency**: Warning >1000ms, Critical >2000ms
- **CPU**: Warning >85%, Critical >95%
- **Disk**: Warning <100GB, Critical <50GB
- **Queue**: Warning >50 items, Critical >100 items

**Test**: `test_phase_16_frontend_dashboard.py::TestPhase16AlertSystem`

---

### Step 4: Historical Analytics

**File**: `backend/api/dashboard.py` → `HistoricalAnalyticsService` class

```python
from backend.api.dashboard import HistoricalAnalyticsService

analytics = HistoricalAnalyticsService(history_size=3600)

# Add metric sample (call every second)
analytics.add_metrics_sample(current_metrics)

# Get history
history_24h = analytics.get_history(hours=24)
all_history = analytics.get_history()

# Analyze trends
cpu_trend = analytics.analyze_trend('cpu_percent', samples=100)
# → 'improving', 'stable', or 'degrading'

# Calculate percentiles
stats = analytics.calculate_percentiles('latency_ms')
# → {'p50': 100, 'p95': 250, 'p99': 500, 'min': 50, 'max': 5000}

# Detect anomalies
anomaly_score = analytics.detect_anomalies(2500, 'latency_ms')
# → 0.85 (highly anomalous)

# Calculate correlations
cpu_coherence_corr = analytics.calculate_metric_correlation(
    'cpu_percent', 'compute_coherence'
)
# → 0.92 (strong correlation)

# Aggregate to coarser intervals
minute_data = analytics.aggregate_to_interval(interval_minutes=1)

# Forecast ahead
forecast = analytics.forecast_metric('cpu_percent', minutes_ahead=5)
# → {'predicted_value': 65.5, 'confidence': 0.87, 'trend': 'increasing'}
```

**Test**: `test_phase_16_frontend_dashboard.py::TestPhase16HistoricalAnalytics`

---

### Step 5: WebSocket Real-Time Updates

**File**: `backend/api/websocket.py` (extend existing)

```python
import websockets
import json
from backend.api.dashboard import DashboardIntegration

@app.websocket("/ws/metrics")
async def websocket_metrics(websocket):
    """Stream metrics via WebSocket."""
    await websocket.accept()

    # Initialize dashboard integration
    integration = DashboardIntegration(
        metrics_provider=Phase15MetricsIntegration(),
        refresh_interval_ms=1000
    )
    await integration.start()

    try:
        # Send initial connection message
        await websocket.send_json({
            'type': 'connected',
            'message': 'Connected to metrics stream'
        })

        # Stream metrics every second
        async for metrics in integration.realtime_service.metrics_stream(1000):
            await websocket.send_json({
                'type': 'metrics',
                'data': metrics
            })

    except websockets.exceptions.ConnectionClosed:
        logger.info("WebSocket client disconnected")
    finally:
        await integration.stop()
```

**Frontend Usage**:

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/metrics");

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  if (message.type === "metrics") {
    updateDashboard(message.data);
  }
};

ws.onerror = (error) => {
  console.error("WebSocket error:", error);
};

ws.onclose = () => {
  console.log("Disconnected from metrics stream");
};
```

**Test**: `test_phase_16_frontend_dashboard.py::TestPhase16WebSocketIntegration`

---

### Step 6: Frontend Components (React)

**File**: `frontend/src/components/Dashboard.tsx`

```typescript
import React, { useEffect, useState } from 'react';
import CoherenceGauges from './CoherenceGauges';
import AlertsList from './AlertsList';
import MetricsChart from './MetricsChart';
import SystemHealthStatus from './SystemHealthStatus';

interface DashboardData {
    coherence: Record<number, number>;
    metrics: any;
    alerts: any[];
    system_load: number;
}

export const Dashboard: React.FC = () => {
    const [data, setData] = useState<DashboardData | null>(null);
    const [connected, setConnected] = useState(false);

    useEffect(() => {
        // Connect to WebSocket
        const ws = new WebSocket('ws://localhost:8000/ws/metrics');

        ws.onopen = () => {
            console.log('Connected to metrics stream');
            setConnected(true);
        };

        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            if (message.type === 'metrics') {
                setData(message.data);
            }
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            setConnected(false);
        };

        return () => ws.close();
    }, []);

    if (!data) {
        return <div className="loading">Connecting to metrics...</div>;
    }

    return (
        <div className="dashboard">
            <header>
                <h1>Mahabhutas Control Panel</h1>
                <div className="status">
                    {connected ? '🟢 Connected' : '🔴 Disconnected'}
                </div>
            </header>

            <div className="grid">
                {/* System Health */}
                <div className="card">
                    <SystemHealthStatus
                        load={data.system_load}
                        status={getHealthStatus(data)}
                    />
                </div>

                {/* Coherence Gauges */}
                <div className="card">
                    <h2>Mahabhutas Coherence</h2>
                    <CoherenceGauges coherence={data.coherence} />
                </div>

                {/* Alerts */}
                <div className="card">
                    <h2>Alerts ({data.alerts.length})</h2>
                    <AlertsList alerts={data.alerts} />
                </div>

                {/* Metrics Chart */}
                <div className="card wide">
                    <h2>Historical Trends</h2>
                    <MetricsChart data={data} />
                </div>
            </div>
        </div>
    );
};

function getHealthStatus(data: DashboardData): string {
    const minCoherence = Math.min(...Object.values(data.coherence));
    if (minCoherence < 0.5) return 'critical';
    if (minCoherence < 0.7) return 'degraded';
    return 'healthy';
}
```

**Component Details**:

**CoherenceGauges.tsx**:

```typescript
// 5 gauge displays for layers 32-36
// Color: green (>0.8), yellow (0.5-0.8), red (<0.5)
// Shows trend arrow: ↑ ↓ →
```

**AlertsList.tsx**:

```typescript
// Scrollable list of recent alerts
// Color by severity: blue (info), yellow (warning), red (critical)
// Auto-scrolls to newest
```

**MetricsChart.tsx**:

```typescript
// Line chart with 4-6 metrics
// X-axis: time, Y-axis: value
// Smooth animations
```

**SystemHealthStatus.tsx**:

```typescript
// Large circular health indicator
// Shows status: healthy/degraded/critical
// Progress bar for system load
```

**Test**: `test_phase_16_frontend_dashboard.py::TestPhase16VisualizationComponents`

---

## Testing the Complete Phase 16

```bash
# Run all Phase 16 tests
pytest backend/tests/test_phase_16_frontend_dashboard.py -v

# Expected output:
# TestPhase16DashboardAPI (8 tests) ✅
# TestPhase16RealTimeMetrics (8 tests) ✅
# TestPhase16VisualizationComponents (8 tests) ✅
# TestPhase16AlertSystem (8 tests) ✅
# TestPhase16HistoricalAnalytics (8 tests) ✅
# TestPhase16WebSocketIntegration (6 tests) ✅
# TestPhase16PerformanceAndUI (6 tests) ✅
#
# ===================== 52 passed in X.XXs =====================
```

---

## Verification Checklist

- [ ] All 52 tests created as stubs in `test_phase_16_frontend_dashboard.py`
- [ ] Fixtures created: MetricsProvider, dashboard_config, mock_websocket_server
- [ ] Implementation skeleton created in `backend/api/dashboard.py`
- [ ] 6 core classes: MetricsProvider, DashboardAPI, RealtimeMetricsService, AlertService, HistoricalAnalyticsService, DashboardIntegration
- [ ] All 52 tests running and passing (as stubs with `pass` statements)
- [ ] Documentation complete with code examples

---

## What's Next

**Phase 16b Implementation**:

1. Implement MetricsProvider → query Phase 15
2. Implement DashboardAPI → REST endpoints
3. Implement RealtimeMetricsService → metrics collection
4. Implement AlertService → threshold checking
5. Implement HistoricalAnalyticsService → time-series analysis
6. Implement Frontend Components → React dashboard

Expected: All 52 tests passing with full implementation

---

## Integration with Phase 15

```python
from backend.observability.hardware_metrics import Phase15MetricsIntegration
from backend.api.dashboard import DashboardIntegration

# Connect Phase 15 metrics to Phase 16 dashboard
metrics_provider = Phase15MetricsIntegration()
dashboard = DashboardIntegration(metrics_provider)

# Get dashboard data
dashboard_data = dashboard.get_dashboard_data()
# {
#     'coherence': {32: 0.95, 33: 1.0, 34: 0.88, ...},
#     'metrics': {...},
#     'alerts': [...],
#     'system_load': 0.45
# }
```

This is the complete Phase 16 TDD setup. Ready to implement! 🚀
