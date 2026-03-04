# ADR-002: Observability - Metrics, Logs, Traces + Correlation IDs

**Status**: Proposed
**Date**: 2026-02-20
**Author**: Architecture Team
**Scope**: Alle services (API, Execution, Agents, Storage)

---

## Context

Het platform heeft meerdere lagen die samenwerken:
- Frontend (React) → API (FastAPI)
- API → Services → Execution
- Events (Redis/Kafka)
- Storage (PostgreSQL, ClickHouse, ChromaDB)

Huidige situatie:
- Prometheus metrics aanwezig
- Logging bestaat maar niet gestructureerd
- Geen distributed tracing
- Geen correlation IDs → debugging is moeilijk
- Geen "golden signals" definitie

---

## Decision

### 1. Observability Pillars

```
┌─────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY STACK                      │
├─────────────────────────────────────────────────────────────┤
│  METRICS          LOGS              TRACES                  │
│  ───────          ────              ──────                  │
│  Prometheus    Structured JSON   OpenTelemetry              │
│  (Counters,    (timestamp,       (Spans,                   │
│   Gauges,      level, message,   correlation)               │
│   Histograms)  context)                                     │
├─────────────────────────────────────────────────────────────┤
│  CORRELATION: trace_id → request_id → user_id → tenant_id   │
├─────────────────────────────────────────────────────────────┤
│  VISUALIZATION: Grafana (metrics) + Jaeger (traces)         │
└─────────────────────────────────────────────────────────────┘
```

### 2. Correlation ID Propagation

**Flow**:
```
Frontend Request
      ↓ X-Request-ID: abc-123
API Gateway (FastAPI)
      ↓ trace_id: abc-123
WebSocket / Service Call
      ↓ trace_id: abc-123
Redis Event
      ↓ correlation_id: abc-123
Database Query
      ↓ comment: 'trace_id=abc-123'
```

**Headers/Context**:
- `X-Request-ID`: HTTP request identifier
- `trace_id`: OpenTelemetry trace identifier
- `span_id`: Current span identifier
- `user_id`: Authenticated user
- `tenant_id`: Multi-tenant isolation

### 3. Structured Logging Schema

**JSON Format**:
```json
{
  "timestamp": "2026-02-20T10:30:00.000Z",
  "level": "INFO",
  "logger": "backend.api.trading",
  "message": "Order executed",
  "trace_id": "abc-123-def",
  "span_id": "span-456",
  "user_id": "user-789",
  "tenant_id": "tenant-abc",
  "service": "trading-api",
  "version": "1.2.3",
  "context": {
    "order_id": "order-xyz",
    "symbol": "BTC-EUR",
    "quantity": 0.5,
    "price": 85000.00
  },
  "duration_ms": 45.2,
  "http": {
    "method": "POST",
    "path": "/api/v1/orders",
    "status_code": 200,
    "client_ip": "10.0.0.1"
  }
}
```

### 4. Golden Signals per Service

| Service | Latency | Traffic | Errors | Saturation |
|---------|---------|---------|--------|------------|
| **API Gateway** | p99 request duration | RPS | 5xx rate | CPU/memory |
| **WebSocket** | msg delivery time | connections | drop rate | queue depth |
| **Execution** | order confirm time | orders/sec | reject rate | pending queue |
| **Risk Engine** | check latency | checks/sec | timeout rate | rule eval queue |
| **Agent** | decision time | decisions/hr | failure rate | LLM quota |
| **Storage** | query time | queries/sec | error rate | connection pool |

---

## Implementation

### 1. Correlation Context Manager

```python
# backend/core/telemetry/correlation.py
import contextvars
from typing import Optional, Dict
from dataclasses import dataclass
import uuid

# Context variables (per-async-task)
_trace_id: contextvars.ContextVar[str] = contextvars.ContextVar('trace_id')
_span_id: contextvars.ContextVar[str] = contextvars.ContextVar('span_id')
_user_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('user_id', default=None)
_tenant_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('tenant_id', default=None)
_request_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar('request_id', default=None)

@dataclass
class CorrelationContext:
    trace_id: str
    span_id: str
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    request_id: Optional[str] = None

    @classmethod
    def create(cls, user_id: Optional[str] = None, tenant_id: Optional[str] = None) -> "CorrelationContext":
        """Create new correlation context."""
        return cls(
            trace_id=str(uuid.uuid4()),
            span_id=str(uuid.uuid4()),
            user_id=user_id,
            tenant_id=tenant_id,
            request_id=str(uuid.uuid4())
        )

    @classmethod
    def get_current(cls) -> "CorrelationContext":
        """Get current correlation context."""
        return cls(
            trace_id=_trace_id.get(),
            span_id=_span_id.get(),
            user_id=_user_id.get(),
            tenant_id=_tenant_id.get(),
            request_id=_request_id.get()
        )

    def set_current(self):
        """Set as current context."""
        _trace_id.set(self.trace_id)
        _span_id.set(self.span_id)
        _user_id.set(self.user_id)
        _tenant_id.set(self.tenant_id)
        _request_id.set(self.request_id)

    def to_dict(self) -> Dict[str, Optional[str]]:
        """Convert to dictionary for logging/headers."""
        return {
            'trace_id': self.trace_id,
            'span_id': self.span_id,
            'user_id': self.user_id,
            'tenant_id': self.tenant_id,
            'request_id': self.request_id
        }


class CorrelationManager:
    """Manage correlation context lifecycle."""

    @staticmethod
    def new_context(user_id: Optional[str] = None, tenant_id: Optional[str] = None) -> CorrelationContext:
        """Create and set new context."""
        ctx = CorrelationContext.create(user_id, tenant_id)
        ctx.set_current()
        return ctx

    @staticmethod
    def from_headers(headers: Dict[str, str]) -> CorrelationContext:
        """Create context from HTTP headers."""
        ctx = CorrelationContext(
            trace_id=headers.get('X-Trace-ID') or headers.get('X-Request-ID') or str(uuid.uuid4()),
            span_id=str(uuid.uuid4()),
            user_id=headers.get('X-User-ID'),
            tenant_id=headers.get('X-Tenant-ID'),
            request_id=headers.get('X-Request-ID')
        )
        ctx.set_current()
        return ctx

    @staticmethod
    def to_headers() -> Dict[str, str]:
        """Get current context as HTTP headers."""
        ctx = CorrelationContext.get_current()
        return {
            'X-Trace-ID': ctx.trace_id,
            'X-Span-ID': ctx.span_id,
            'X-User-ID': ctx.user_id or '',
            'X-Tenant-ID': ctx.tenant_id or '',
            'X-Request-ID': ctx.request_id or ''
        }

    @staticmethod
    def new_span(span_name: str) -> "SpanContext":
        """Create new child span."""
        parent = CorrelationContext.get_current()
        span = CorrelationContext(
            trace_id=parent.trace_id,
            span_id=str(uuid.uuid4()),
            user_id=parent.user_id,
            tenant_id=parent.tenant_id,
            request_id=parent.request_id
        )
        span.set_current()
        return SpanContext(span, span_name)


class SpanContext:
    """Context manager for spans."""

    def __init__(self, ctx: CorrelationContext, name: str):
        self.ctx = ctx
        self.name = name
        self.start_time: Optional[float] = None

    def __enter__(self):
        self.start_time = time.time()
        logger.info(f"Span started: {self.name}", extra={
            'span_name': self.name,
            'span_kind': 'start'
        })
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time if self.start_time else 0
        status = 'error' if exc_type else 'success'

        logger.info(f"Span ended: {self.name}", extra={
            'span_name': self.name,
            'span_kind': 'end',
            'duration_ms': duration * 1000,
            'status': status,
            'error': str(exc_val) if exc_val else None
        })
```

### 2. FastAPI Middleware

```python
# backend/core/telemetry/middleware.py
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging

logger = logging.getLogger(__name__)

class CorrelationMiddleware(BaseHTTPMiddleware):
    """Inject correlation IDs into request context."""

    async def dispatch(self, request: Request, call_next):
        # Extract/create correlation context from headers
        ctx = CorrelationManager.from_headers(dict(request.headers))

        # Add to request state
        request.state.correlation = ctx

        # Process request
        start_time = time.time()

        try:
            response = await call_next(request)

            # Add correlation headers to response
            for key, value in CorrelationManager.to_headers().items():
                if value:
                    response.headers[key] = value

            # Log request
            duration = time.time() - start_time
            logger.info(
                f"{request.method} {request.url.path} - {response.status_code}",
                extra={
                    'http_method': request.method,
                    'http_path': request.url.path,
                    'http_status': response.status_code,
                    'duration_ms': duration * 1000,
                    'client_ip': request.client.host if request.client else None,
                    **ctx.to_dict()
                }
            )

            return response

        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"{request.method} {request.url.path} - ERROR: {e}",
                extra={
                    'http_method': request.method,
                    'http_path': request.url.path,
                    'duration_ms': duration * 1000,
                    'error': str(e),
                    **ctx.to_dict()
                },
                exc_info=True
            )
            raise


class MetricsMiddleware(BaseHTTPMiddleware):
    """Collect golden signals."""

    def __init__(self, app):
        super().__init__(app)
        from backend.observability.metrics import request_count, request_duration
        self.request_count = request_count
        self.request_duration = request_duration

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        response = await call_next(request)

        duration = time.time() - start_time

        # Record metrics
        self.request_count.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()

        self.request_duration.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(duration)

        return response
```

### 3. Structured Logger

```python
# backend/core/telemetry/structured_logger.py
import logging
import json
from pythonjsonlogger import jsonlogger
from typing import Any, Dict

class CorrelationFilter(logging.Filter):
    """Add correlation context to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            from backend.core.telemetry.correlation import CorrelationContext
            ctx = CorrelationContext.get_current()

            record.trace_id = ctx.trace_id
            record.span_id = ctx.span_id
            record.user_id = ctx.user_id or 'anonymous'
            record.tenant_id = ctx.tenant_id or 'default'
            record.request_id = ctx.request_id or 'none'
        except Exception:
            record.trace_id = 'unknown'
            record.span_id = 'unknown'
            record.user_id = 'unknown'
            record.tenant_id = 'unknown'
            record.request_id = 'unknown'

        return True


class StructuredFormatter(jsonlogger.JsonFormatter):
    """JSON formatter with correlation context."""

    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]):
        super().add_fields(log_record, record, message_dict)

        # Add standard fields
        log_record['timestamp'] = record.created
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['service'] = 'agentic-trader'
        log_record['version'] = '1.0.0'

        # Add correlation fields
        log_record['trace_id'] = getattr(record, 'trace_id', 'unknown')
        log_record['span_id'] = getattr(record, 'span_id', 'unknown')
        log_record['user_id'] = getattr(record, 'user_id', 'unknown')
        log_record['tenant_id'] = getattr(record, 'tenant_id', 'unknown')
        log_record['request_id'] = getattr(record, 'request_id', 'unknown')

        # Rename fields for consistency
        if 'message' not in log_record:
            log_record['message'] = record.getMessage()


def setup_structured_logging():
    """Configure structured logging for the application."""

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler with JSON formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(StructuredFormatter())

    # Add correlation filter
    console_handler.addFilter(CorrelationFilter())

    root_logger.addHandler(console_handler)

    # Reduce noise from libraries
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
```

### 4. WebSocket Correlation

```python
# In websocket_manager_v2.py
async def handle_client_message(self, connection_id: str, message: Dict):
    """Handle message with correlation context."""

    # Extract or create correlation from message
    trace_id = message.get('trace_id') or str(uuid.uuid4())

    # Set context
    ctx = CorrelationContext.create()
    ctx.trace_id = trace_id
    ctx.set_current()

    # Log with correlation
    logger.info(f"WS message received: {message.get('type')}", extra={
        'connection_id': connection_id,
        'message_type': message.get('type'),
        'stream': message.get('stream'),
        **ctx.to_dict()
    })

    # Process message
    # ...
```

### 5. Event Bus Correlation

```python
# backend/events/event_bus.py
class TracedEventBus:
    """Event bus with correlation propagation."""

    async def publish(self, event: Event):
        """Publish event with correlation context."""
        from backend.core.telemetry.correlation import CorrelationContext

        ctx = CorrelationContext.get_current()

        # Add correlation to event
        event.metadata['trace_id'] = ctx.trace_id
        event.metadata['user_id'] = ctx.user_id
        event.metadata['tenant_id'] = ctx.tenant_id

        # Publish with tracing
        with CorrelationManager.new_span(f"publish_{event.type}"):
            await self._publish(event)

    async def consume(self, event: Event):
        """Consume event with restored correlation."""
        # Restore correlation from event
        ctx = CorrelationContext(
            trace_id=event.metadata.get('trace_id', str(uuid.uuid4())),
            span_id=str(uuid.uuid4()),
            user_id=event.metadata.get('user_id'),
            tenant_id=event.metadata.get('tenant_id')
        )
        ctx.set_current()

        # Process with tracing
        with CorrelationManager.new_span(f"consume_{event.type}"):
            await self._process(event)
```

---

## Monitoring

### Grafana Dashboard: "Distributed Tracing"

**Panels**:
1. **Trace Timeline**: Waterfall view per request
2. **Service Dependencies**: Graph van service calls
3. **Latency by Service**: Heatmap
4. **Error Traces**: Gefilterde fouten traces

### Jaeger Integration

```python
# backend/core/telemetry/tracing.py
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

def setup_tracing(service_name: str):
    """Setup OpenTelemetry tracing."""

    # Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name="jaeger-agent",
        agent_port=6831,
    )

    # Tracer provider
    provider = TracerProvider()
    processor = BatchSpanProcessor(jaeger_exporter)
    provider.add_span_processor(processor)

    # Set global provider
    trace.set_tracer_provider(provider)

    return trace.get_tracer(service_name)
```

---

## Consequences

### Positief
- End-to-end traceability
- Snellere debugging
- Betere performance insights
- Compliance audit trails

### Negatief
- Performance overhead (5-10%)
- Storage kosten voor logs/traces
- Complexere code

---

## Migration Plan

### Week 1: Foundation
1. Implementeer correlation context
2. Update logging configuratie
3. Add FastAPI middleware

### Week 2: Integration
1. Update WebSocket manager
2. Instrument event bus
3. Add database query comments

### Week 3: Visualization
1. Deploy Jaeger
2. Create Grafana dashboards
3. Document runbooks

---

## References

- [OpenTelemetry](https://opentelemetry.io/)
- [Distributed Tracing](https://microservices.io/patterns/observability/distributed-tracing.html)
- [Google Dapper Paper](https://research.google/pubs/pub36356/)

---

## Decision Log

| Date | Change | Author |
|------|--------|--------|
| 2026-02-20 | Initial draft | Architecture Team |
