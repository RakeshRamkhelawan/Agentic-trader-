# ADR-003: WebSocket Reliability & Backpressure

**Status**: Proposed
**Date**: 2026-02-20
**Author**: Architecture Team
**Scope**: `/ws`, `/ws/paper-trading`, WebSocket Manager, Frontend WS Layer

---

## Context

Het Agentic Trader Platform gebruikt WebSockets intensief voor:
- Real-time marktdata (ticks, orderboeken)
- Paper trading updates (fills, P&L)
- Agent signalen en OODA cycle updates
- Portfolio wijzigingen

Huidige componenten:
- `backend/api/websocket_endpoints.py` - WS endpoints
- `backend/api/websocket_manager.py` - Centrale WS broker
- `backend/services/signal_bridge.py` - Signal distributie
- `backend/services/market_data_streamer.py` - Data streaming
- `frontend/src/hooks/useWebSocket.ts` - Client WS hook
- `frontend/src/store/wsStore.ts` - WS state management

### Problemen die opgelost moeten worden
1. Geen heartbeat → half-open connections blijven hangen
2. Geen backpressure → memory bij hoge load
3. Geen reconnect strategie → UI blijft "dood" na disconnect
4. Geen delivery semantics → onduidelijk of updates gemist zijn
5. Geen observability → we weten niet hoe WS presteert

---

## Decision

### 1. Delivery Semantics: "Best-Effort Realtime + Eventual Resync"

WebSocket is primair voor live updates, maar clients moeten altijd kunnen resyncen via REST.

```
WS: Live updates (ticks, fills) → snel maar best-effort
REST: Snapshot + history → betrouwbaar voor recovery
```

### 2. Message Contract

Elk WS event bevat verplichte metadata:

```typescript
interface WSMessage {
  type: string;           // Event type
  stream: string;         // Channel (e.g., "ticker.BTC-EUR")
  ts: string;            // ISO timestamp (server genereert)
  seq?: number;          // Optionele sequence per stream
  tenant_id?: string;    // Voor multi-tenant routing
  correlation_id?: string; // Voor tracing
  priority: 'high' | 'low'; // Backpressure hint
  data: unknown;         // Payload
}
```

### 3. Backpressure Policy

Per-connection bounded queue (max 1000 messages):
- **High priority**: fills, errors, heartbeats → nooit droppen
- **Low priority**: ticks, volume updates → droppen bij overflow
- Bij overflow: stuur `resync_required` event naar client

### 4. Heartbeat Protocol

```
Client ←→ Server
  |        |
  |<──ping──|  elke 30s
  |──pong──>|  binnen 5s
  |        |
  |<──data──|  normaal verkeer reset timer
```

Server sluit verbinding na 3 gemiste heartbeats (90s timeout).

### 5. Reconnect Strategy (Client)

```
Disconnect detected
       ↓
Exponential backoff: 1s → 2s → 4s → 8s → max 30s
       ↓
Jitter: +0-30% random delay
       ↓
On connect:
  1. Authenticate (JWT in query param)
  2. Fetch REST snapshot
  3. Subscribe WS channels
  4. Resume live updates
```

### 6. AuthZ bij Handshake

- JWT validatie bij WS connect (via query param `?token=...`)
- Koppel verbinding aan user/tenant
- Channel subscriptions gebaseerd op permissions
- Auto-disconnect bij token expiry

---

## Consequences

### Positief
- Voorspelbare UX: geen "bevroren" dashboards meer
- Betrouwbare paper trading: geen gemiste fills
- Meetbaar: we zien WS performance in Grafana
- Schaalbaar: backpressure voorkomt cascade failures

### Negatief
- Extra complexiteit in frontend (reconnect logica)
- Meer server resources (heartbeat handling)
- Sequence numbers vereisen state per stream

---

## Implementation

### Backend Changes

#### 1. WebSocketManager (`backend/api/websocket_manager.py`)

```python
class WebSocketManager:
    def __init__(self):
        self.connections: Dict[str, ConnectionState] = {}
        self.metrics = WSMetrics()  # Prometheus metrics

    async def connect(self, websocket: WebSocket, user: User):
        """Handle new connection with auth."""
        conn_id = generate_uuid()
        await websocket.accept()

        self.connections[conn_id] = ConnectionState(
            websocket=websocket,
            user=user,
            queue=asyncio.Queue(maxsize=1000),
            last_pong=time.time(),
            subscriptions=set()
        )

        # Start heartbeat handler
        asyncio.create_task(self._heartbeat_loop(conn_id))

        # Start message processor
        asyncio.create_task(self._message_processor(conn_id))

        self.metrics.connections.inc()

    async def _heartbeat_loop(self, conn_id: str):
        """Send pings, expect pongs."""
        while conn_id in self.connections:
            try:
                conn = self.connections[conn_id]

                # Check last pong
                if time.time() - conn.last_pong > 90:
                    logger.warning(f"Heartbeat timeout for {conn_id}")
                    await self.disconnect(conn_id, reason="heartbeat_timeout")
                    break

                # Send ping
                await conn.websocket.send_json({
                    "type": "ping",
                    "ts": datetime.utcnow().isoformat()
                })

                await asyncio.sleep(30)

            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                break

    async def broadcast(self, stream: str, message: dict, priority: str = "low"):
        """Broadcast with backpressure handling."""
        msg = {
            "type": message.get("type"),
            "stream": stream,
            "ts": datetime.utcnow().isoformat(),
            "seq": self._get_next_seq(stream),
            "priority": priority,
            "data": message.get("data")
        }

        for conn_id, conn in self.connections.items():
            if stream in conn.subscriptions:
                try:
                    conn.queue.put_nowait((priority, msg))
                except asyncio.QueueFull:
                    if priority == "high":
                        # Force resync for critical messages
                        asyncio.create_task(self._send_resync_required(conn_id))
                    self.metrics.dropped_messages.inc()
```

#### 2. Metrics (`backend/observability/ws_metrics.py`)

```python
from prometheus_client import Counter, Gauge, Histogram

class WSMetrics:
    def __init__(self):
        self.connections = Gauge('ws_connections_current', 'Active WS connections')
        self.connect_rate = Counter('ws_connect_total', 'Total connections', ['status'])
        self.disconnect_reason = Counter('ws_disconnect_total', 'Disconnect reasons', ['reason'])
        self.messages_sent = Counter('ws_messages_sent', 'Messages sent', ['stream', 'priority'])
        self.messages_dropped = Counter('ws_messages_dropped', 'Messages dropped', ['stream'])
        self.queue_depth = Gauge('ws_queue_depth', 'Queue depth per connection', ['conn_id'])
        self.latency = Histogram('ws_latency_seconds', 'Publish to receive latency')
```

### Frontend Changes

#### 1. useWebSocket Hook (`frontend/src/hooks/useWebSocket.ts`)

```typescript
interface WSConfig {
  url: string;
  token: string;
  onMessage: (msg: WSMessage) => void;
  onConnect?: () => void;
  onDisconnect?: (reason: string) => void;
  reconnect?: boolean;
}

export function useWebSocket(config: WSConfig) {
  const [status, setStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');
  const [reconnectCount, setReconnectCount] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const connect = useCallback(() => {
    setStatus('connecting');

    const ws = new WebSocket(`${config.url}?token=${config.token}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setStatus('connected');
      setReconnectCount(0);
      config.onConnect?.();

      // Subscribe to channels
      ws.send(JSON.stringify({
        type: 'subscribe',
        streams: ['ticker.*', 'portfolio', 'trades']
      }));
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);

      // Handle ping/pong
      if (msg.type === 'ping') {
        ws.send(JSON.stringify({ type: 'pong', ts: new Date().toISOString() }));
        return;
      }

      // Handle resync required
      if (msg.type === 'resync_required') {
        triggerResync();
        return;
      }

      config.onMessage(msg);
    };

    ws.onclose = (event) => {
      setStatus('disconnected');
      config.onDisconnect?.(event.reason);

      if (config.reconnect !== false) {
        scheduleReconnect();
      }
    };

    ws.onerror = (error) => {
      console.error('WS error:', error);
      ws.close();
    };
  }, [config]);

  const scheduleReconnect = () => {
    const baseDelay = Math.min(1000 * Math.pow(2, reconnectCount), 30000);
    const jitter = Math.random() * 0.3 * baseDelay;
    const delay = baseDelay + jitter;

    setReconnectCount(prev => prev + 1);

    reconnectTimeoutRef.current = setTimeout(() => {
      connect();
    }, delay);
  };

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    wsRef.current?.close();
  }, []);

  useEffect(() => {
    connect();
    return disconnect;
  }, [connect, disconnect]);

  return { status, reconnectCount, disconnect, reconnect: connect };
}
```

---

## SLO Targets

| Metric | SLI | SLO | Window |
|--------|-----|-----|--------|
| Connection success rate | successful / total connects | >99.5% | 1h |
| Message delivery | delivered / published | >99.9% (high priority) | 1m |
| Latency (p99) | publish → receive | <100ms | 1m |
| Uptime | connected time / total | >99.9% | 24h |
| Resync frequency | resync events / total connections | <1% | 1h |

---

## Monitoring

### Grafana Dashboard: "WebSocket Reliability"

Panels:
1. **Connections**: Current active, connect rate, disconnect reasons
2. **Message Flow**: Sent/dropped per stream, queue depth
3. **Latency**: p50/p95/p99 publish-to-receive
4. **Errors**: Auth failures, heartbeat timeouts, parse errors
5. **Client Experience**: Reconnect rate, resync frequency

### Alerts

```yaml
- alert: WSHighDropRate
  expr: rate(ws_messages_dropped[1m]) / rate(ws_messages_sent[1m]) > 0.01
  for: 2m
  severity: warning

- alert: WSHeartbeatTimeout
  expr: rate(ws_disconnect_total{reason="heartbeat_timeout"}[5m]) > 10
  for: 1m
  severity: critical

- alert: WSHighLatency
  expr: histogram_quantile(0.99, ws_latency_seconds) > 0.5
  for: 2m
  severity: warning
```

---

## Migration Plan

### Phase 1: Backend (Week 1)
1. Implement heartbeat in WebSocketManager
2. Add metrics collection
3. Implement backpressure (bounded queues)
4. Update message contract

### Phase 2: Frontend (Week 1-2)
1. Update useWebSocket hook
2. Add reconnect logic
3. Implement resync flow
4. Update wsStore

### Phase 3: Observability (Week 2)
1. Deploy Grafana dashboard
2. Configure alerts
3. Document runbook

### Phase 4: Validation (Week 3)
1. Load test WS layer
2. Verify SLOs
3. Fine-tune backpressure limits

---

## References

- [RFC 6455 - WebSocket Protocol](https://tools.ietf.org/html/rfc6455)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- Existing code: `websocket_manager.py`, `useWebSocket.ts`

---

## Decision Log

| Date | Change | Author |
|------|--------|--------|
| 2026-02-20 | Initial draft | Architecture Team |
