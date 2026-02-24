"""
Structured Logging Configuration

Implements ADR-002: Observability - Metrics, Logs, Traces + Correlation IDs
Provides JSON structured logging with correlation context.

Author: Architecture Team
Date: 2026-02-20
"""

import logging
import logging.handlers
import sys
from typing import Any

# Try to import python-json-logger, fall back to basic if not available
try:
    from pythonjsonlogger import jsonlogger

    JSON_LOGGER_AVAILABLE = True
except ImportError:
    JSON_LOGGER_AVAILABLE = False


class CorrelationFilter(logging.Filter):
    """
    Logging filter that injects correlation context into log records.

    This ensures every log line includes trace_id, span_id, user_id, etc.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            from backend.core.telemetry.correlation import CorrelationContext

            ctx = CorrelationContext.get_current()

            record.trace_id = ctx.trace_id
            record.span_id = ctx.span_id
            record.user_id = ctx.user_id or "anonymous"
            record.tenant_id = ctx.tenant_id or "default"
            record.request_id = ctx.request_id or "none"
            record.parent_span_id = ctx.parent_span_id or "none"
        except Exception:
            # If correlation context fails, use defaults
            record.trace_id = getattr(record, "trace_id", "unknown")
            record.span_id = getattr(record, "span_id", "unknown")
            record.user_id = getattr(record, "user_id", "unknown")
            record.tenant_id = getattr(record, "tenant_id", "unknown")
            record.request_id = getattr(record, "request_id", "unknown")
            record.parent_span_id = getattr(record, "parent_span_id", "unknown")

        return True


class StructuredFormatter(logging.Formatter):
    """
    Standard formatter that can output structured-ish logs even without JSON.

    Format: timestamp [LEVEL] [trace_id] [user_id] message
    """

    def format(self, record: logging.LogRecord) -> str:
        # Ensure correlation fields exist
        if not hasattr(record, "trace_id"):
            CorrelationFilter().filter(record)

        # Build structured prefix
        trace_id = getattr(record, "trace_id", "unknown")[:8]  # Truncate for readability
        user_id = getattr(record, "user_id", "unknown")

        record.structured_prefix = f"[{trace_id}] [{user_id}]"

        return super().format(record)


class JSONFormatter(
    jsonlogger.JsonFormatter if JSON_LOGGER_AVAILABLE else logging.Formatter  # type: ignore[misc]
):
    """
    JSON formatter for structured logging.

    Outputs logs as JSON with standard fields:
    - timestamp, level, logger, message
    - trace_id, span_id, user_id, tenant_id, request_id
    - service, version
    - Any extra fields from record
    """

    def __init__(self, fmt: str | None = None, *args, **kwargs):
        # Define standard fields to include
        standard_fields = [
            "timestamp",
            "level",
            "logger",
            "message",
            "trace_id",
            "span_id",
            "user_id",
            "tenant_id",
            "request_id",
            "parent_span_id",
            "service",
            "version",
            "source_file",
            "source_line",
            "function",
            "thread",
            "process",
        ]

        if JSON_LOGGER_AVAILABLE:
            fmt = fmt or " ".join([f"%({f})" for f in standard_fields])
            super().__init__(fmt, *args, **kwargs)
        else:
            super().__init__(*args, **kwargs)

    def add_fields(
        self,
        log_record: dict[str, Any],
        record: logging.LogRecord,
        message_dict: dict[str, Any],
    ):
        """Add standard and correlation fields to log record."""
        super().add_fields(log_record, record, message_dict)

        # Standard fields
        log_record["timestamp"] = self.formatTime(record)
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["message"] = record.getMessage()
        log_record["service"] = "agentic-trader"
        log_record["version"] = "1.0.0"
        log_record["source_file"] = record.filename
        log_record["source_line"] = record.lineno
        log_record["function"] = record.funcName
        log_record["thread"] = record.thread
        log_record["process"] = record.process

        # Ensure correlation filter ran
        if not hasattr(record, "trace_id"):
            CorrelationFilter().filter(record)

        # Correlation fields
        log_record["trace_id"] = getattr(record, "trace_id", "unknown")
        log_record["span_id"] = getattr(record, "span_id", "unknown")
        log_record["user_id"] = getattr(record, "user_id", "unknown")
        log_record["tenant_id"] = getattr(record, "tenant_id", "unknown")
        log_record["request_id"] = getattr(record, "request_id", "unknown")
        log_record["parent_span_id"] = getattr(record, "parent_span_id", "unknown")

        # Add any extra fields from record
        for key, value in record.__dict__.items():
            if key not in log_record and not key.startswith("_"):
                log_record[key] = value

    def formatTime(self, record: logging.LogRecord, datefmt: str | None = None) -> str:
        """Format timestamp in ISO format."""
        from datetime import datetime

        return datetime.utcfromtimestamp(record.created).isoformat() + "Z"


def configure_logging(
    level: int = logging.INFO,
    json_format: bool = True,
    log_file: str | None = None,
    use_colors: bool = False,
) -> None:
    """
    Configure structured logging for the application.

    Args:
        level: Minimum log level
        json_format: Use JSON formatting (if available)
        log_file: Optional file path for logging
        use_colors: Use colored output (console only)
    """
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create correlation filter
    correlation_filter = CorrelationFilter()

    # Console handler
    if json_format and JSON_LOGGER_AVAILABLE:
        # JSON structured logging
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(JSONFormatter())
    else:
        # Standard formatted logging with correlation
        console_handler = logging.StreamHandler(sys.stdout)
        formatter = StructuredFormatter(
            "%(asctime)s [%(levelname)s] %(structured_prefix)s %(message)s"
        )
        console_handler.setFormatter(formatter)

    console_handler.addFilter(correlation_filter)
    root_logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        if json_format and JSON_LOGGER_AVAILABLE:
            file_handler = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=10_000_000, backupCount=5
            )
            file_handler.setFormatter(JSONFormatter())
        else:
            file_handler = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=10_000_000, backupCount=5
            )
            file_handler.setFormatter(
                StructuredFormatter("%(asctime)s [%(levelname)s] %(structured_prefix)s %(message)s")
            )

        file_handler.addFilter(correlation_filter)
        root_logger.addHandler(file_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)

    # Our modules at configured level
    logging.getLogger("backend").setLevel(level)

    root_logger.info(
        "Logging configured",
        extra={
            "level": logging.getLevelName(level),
            "json_format": json_format,
            "log_file": log_file,
        },
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get logger with correlation context support.

    Usage:
        logger = get_logger(__name__)
        logger.info("Processing order", extra={'order_id': '123'})
    """
    return logging.getLogger(name)


# Convenience functions for common log patterns
def log_request(
    logger: logging.Logger,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    **extra,
) -> None:
    """Log HTTP request with standard fields."""
    logger.info(
        f"{method} {path} - {status_code}",
        extra={
            "http_method": method,
            "http_path": path,
            "http_status": status_code,
            "duration_ms": duration_ms,
            **extra,
        },
    )


def log_error(logger: logging.Logger, message: str, error: Exception, **extra) -> None:
    """Log error with exception info."""
    logger.error(
        message,
        extra={
            "error_type": type(error).__name__,
            "error_message": str(error),
            **extra,
        },
        exc_info=True,
    )


def log_performance(
    logger: logging.Logger,
    operation: str,
    duration_ms: float,
    threshold_ms: float | None = None,
    **extra,
) -> None:
    """Log performance metric with optional threshold warning."""
    level = logging.WARNING if threshold_ms and duration_ms > threshold_ms else logging.INFO

    logger.log(
        level,
        f"Performance: {operation} took {duration_ms:.2f}ms",
        extra={
            "operation": operation,
            "duration_ms": duration_ms,
            "threshold_ms": threshold_ms,
            "slow": threshold_ms and duration_ms > threshold_ms,
            **extra,
        },
    )
