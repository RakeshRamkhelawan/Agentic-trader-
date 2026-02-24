"""
Correlation Context Management for Distributed Tracing

Implements ADR-002: Observability - Metrics, Logs, Traces + Correlation IDs
Provides correlation ID propagation across services.

Author: Architecture Team
Date: 2026-02-20
"""

import contextvars
import logging
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# Context variables (per-async-task storage)
_trace_id: contextvars.ContextVar[str] = contextvars.ContextVar("trace_id")
_span_id: contextvars.ContextVar[str] = contextvars.ContextVar("span_id")
_user_id: contextvars.ContextVar[str | None] = contextvars.ContextVar("user_id", default=None)
_tenant_id: contextvars.ContextVar[str | None] = contextvars.ContextVar("tenant_id", default=None)
_request_id: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)
_parent_span_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "parent_span_id", default=None
)


@dataclass
class CorrelationContext:
    """
    Immutable correlation context for distributed tracing.

    Contains:
    - trace_id: Root identifier for entire request chain
    - span_id: Current operation identifier
    - user_id: Authenticated user (if available)
    - tenant_id: Multi-tenant identifier
    - request_id: HTTP request identifier
    - parent_span_id: Parent operation (for nested spans)
    """

    trace_id: str
    span_id: str
    user_id: str | None = None
    tenant_id: str | None = None
    request_id: str | None = None
    parent_span_id: str | None = None

    @classmethod
    def create(
        cls,
        user_id: str | None = None,
        tenant_id: str | None = None,
        parent_context: Optional["CorrelationContext"] = None,
    ) -> "CorrelationContext":
        """
        Create new correlation context.

        If parent_context is provided, inherits trace_id and sets parent_span_id.
        Otherwise creates new trace_id.
        """
        if parent_context:
            return cls(
                trace_id=parent_context.trace_id,
                span_id=str(uuid.uuid4()),
                user_id=user_id or parent_context.user_id,
                tenant_id=tenant_id or parent_context.tenant_id,
                request_id=parent_context.request_id,
                parent_span_id=parent_context.span_id,
            )

        return cls(
            trace_id=str(uuid.uuid4()),
            span_id=str(uuid.uuid4()),
            user_id=user_id,
            tenant_id=tenant_id,
            request_id=str(uuid.uuid4()),
        )

    @classmethod
    def get_current(cls) -> "CorrelationContext":
        """Get current correlation context from async context."""
        try:
            return cls(
                trace_id=_trace_id.get(),
                span_id=_span_id.get(),
                user_id=_user_id.get(),
                tenant_id=_tenant_id.get(),
                request_id=_request_id.get(),
                parent_span_id=_parent_span_id.get(),
            )
        except LookupError:
            # No context set, create default
            return cls.create()

    def set_current(self) -> None:
        """Set this context as current for async task."""
        _trace_id.set(self.trace_id)
        _span_id.set(self.span_id)
        _user_id.set(self.user_id)
        _tenant_id.set(self.tenant_id)
        _request_id.set(self.request_id)
        _parent_span_id.set(self.parent_span_id)

    def to_dict(self) -> dict[str, str | None]:
        """Convert to dictionary for logging/headers."""
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "request_id": self.request_id,
            "parent_span_id": self.parent_span_id,
        }

    def to_headers(self) -> dict[str, str]:
        """Convert to HTTP headers (excluding None values)."""
        headers = {
            "X-Trace-ID": self.trace_id,
            "X-Span-ID": self.span_id,
        }
        if self.user_id:
            headers["X-User-ID"] = self.user_id
        if self.tenant_id:
            headers["X-Tenant-ID"] = self.tenant_id
        if self.request_id:
            headers["X-Request-ID"] = self.request_id
        if self.parent_span_id:
            headers["X-Parent-Span-ID"] = self.parent_span_id
        return headers

    @classmethod
    def from_headers(cls, headers: dict[str, str]) -> "CorrelationContext":
        """Create context from HTTP headers."""
        # Support both X-Trace-ID and X-Request-ID for trace_id
        trace_id = headers.get("X-Trace-ID") or headers.get("X-Request-ID") or str(uuid.uuid4())

        return cls(
            trace_id=trace_id,
            span_id=str(uuid.uuid4()),  # Always create new span
            user_id=headers.get("X-User-ID"),
            tenant_id=headers.get("X-Tenant-ID"),
            request_id=headers.get("X-Request-ID"),
            parent_span_id=headers.get("X-Span-ID"),  # Incoming span becomes parent
        )


class CorrelationManager:
    """
        Manager for correlation context lifecycle.

        Provides convenience methods for creating, propagating and using
    correlation contexts across service boundaries.
    """

    @staticmethod
    def new_context(user_id: str | None = None, tenant_id: str | None = None) -> CorrelationContext:
        """Create and activate new correlation context."""
        ctx = CorrelationContext.create(user_id, tenant_id)
        ctx.set_current()
        return ctx

    @staticmethod
    def from_headers(headers: dict[str, str]) -> CorrelationContext:
        """Create and activate context from HTTP headers."""
        ctx = CorrelationContext.from_headers(headers)
        ctx.set_current()
        return ctx

    @staticmethod
    def to_headers() -> dict[str, str]:
        """Get current context as HTTP headers."""
        try:
            ctx = CorrelationContext.get_current()
            return ctx.to_headers()
        except Exception:
            return {"X-Trace-ID": str(uuid.uuid4())}

    @staticmethod
    def new_span(span_name: str) -> "SpanContext":
        """Create new child span from current context."""
        parent = CorrelationContext.get_current()
        span_ctx = CorrelationContext.create(parent_context=parent)
        span_ctx.set_current()
        return SpanContext(span_ctx, span_name)

    @staticmethod
    def get_current() -> CorrelationContext:
        """Get current correlation context."""
        return CorrelationContext.get_current()

    @staticmethod
    def set_current(ctx: CorrelationContext) -> None:
        """Set correlation context as current."""
        ctx.set_current()


class SpanContext:
    """
    Context manager for operation spans with automatic logging.

    Usage:
        with CorrelationManager.new_span("order_execution") as span:
            result = execute_order()
            span.set_tag("order_id", result.id)
    """

    def __init__(self, ctx: CorrelationContext, name: str):
        self.ctx = ctx
        self.name = name
        self.start_time: float | None = None
        self.tags: dict[str, str] = {}
        self.error: Exception | None = None

    def set_tag(self, key: str, value: str) -> None:
        """Add metadata tag to span."""
        self.tags[key] = value

    def __enter__(self) -> "SpanContext":
        """Start span and log entry."""
        self.start_time = time.time()

        logger.info(
            f"Span started: {self.name}",
            extra={
                "span_name": self.name,
                "span_event": "start",
                "trace_id": self.ctx.trace_id,
                "span_id": self.ctx.span_id,
                "parent_span_id": self.ctx.parent_span_id,
                **self.tags,
            },
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """End span and log completion with timing."""
        duration_ms = (time.time() - self.start_time) * 1000 if self.start_time else 0
        status = "error" if exc_type else "success"

        if exc_val:
            self.error = exc_val
            logger.error(
                f"Span failed: {self.name}",
                extra={
                    "span_name": self.name,
                    "span_event": "end",
                    "duration_ms": duration_ms,
                    "status": status,
                    "error_type": exc_type.__name__ if exc_type else None,
                    "error_message": str(exc_val) if exc_val else None,
                    "trace_id": self.ctx.trace_id,
                    "span_id": self.ctx.span_id,
                    **self.tags,
                },
                exc_info=(exc_type, exc_val, exc_tb) if exc_type else None,
            )
        else:
            logger.info(
                f"Span completed: {self.name}",
                extra={
                    "span_name": self.name,
                    "span_event": "end",
                    "duration_ms": duration_ms,
                    "status": status,
                    "trace_id": self.ctx.trace_id,
                    "span_id": self.ctx.span_id,
                    **self.tags,
                },
            )


@contextmanager
def traced_operation(operation_name: str, **tags):
    """
    Decorator-style context manager for tracing operations.

    Usage:
        @traced_operation("risk_check", component="risk_engine")
        async def check_risk(order):
            # ... logic ...
            return result
    """
    with CorrelationManager.new_span(operation_name) as span:
        for key, value in tags.items():
            span.set_tag(key, str(value))
        yield span


def get_correlation_logger(name: str) -> logging.Logger:
    """
    Get logger that automatically includes correlation context.

    Usage:
        logger = get_correlation_logger(__name__)
        logger.info("Processing order")  # Automatically includes trace_id, etc.
    """
    return logging.getLogger(name)


# Convenience function for quick span creation
def trace_span(name: str):
    """Decorator for tracing function execution."""

    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            with CorrelationManager.new_span(name) as span:
                span.set_tag("function", func.__name__)
                return await func(*args, **kwargs)

        def sync_wrapper(*args, **kwargs):
            with CorrelationManager.new_span(name) as span:
                span.set_tag("function", func.__name__)
                return func(*args, **kwargs)

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
