"""
Performance metrics collection and profiling for backtests.

Provides:
- Real-time performance monitoring
- Detailed profiling of MCP tool calls
- Bottleneck identification
- Performance reporting
"""

import asyncio
import time
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ToolMetrics:
    """Metrics for a single MCP tool."""

    tool_name: str
    call_count: int = 0
    total_time_seconds: float = 0.0
    min_time_seconds: float = float("inf")
    max_time_seconds: float = 0.0
    errors: int = 0
    last_called: datetime | None = None

    @property
    def avg_time_seconds(self) -> float:
        if self.call_count == 0:
            return 0.0
        return self.total_time_seconds / self.call_count

    def record_call(self, duration: float, error: bool = False) -> None:
        self.call_count += 1
        self.total_time_seconds += duration
        self.min_time_seconds = min(self.min_time_seconds, duration)
        self.max_time_seconds = max(self.max_time_seconds, duration)
        self.last_called = datetime.now()
        if error:
            self.errors += 1


@dataclass
class BacktestMetrics:
    """Comprehensive backtest performance metrics."""

    backtest_id: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime | None = None
    symbols: list[str] = field(default_factory=list)
    date_range: dict[str, str] = field(default_factory=dict)

    # Timing
    total_time_seconds: float = 0.0
    data_fetch_time_seconds: float = 0.0
    vedastro_time_seconds: float = 0.0
    elemental_time_seconds: float = 0.0
    execution_time_seconds: float = 0.0

    # Counts
    total_days_processed: int = 0
    total_symbols_processed: int = 0
    total_trades_executed: int = 0
    total_signals_generated: int = 0

    # Tool-specific metrics
    tool_metrics: dict[str, ToolMetrics] = field(default_factory=dict)

    # Cache metrics
    cache_hits: int = 0
    cache_misses: int = 0

    # Memory
    peak_memory_mb: float = 0.0

    def get_cache_hit_rate(self) -> float:
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return self.cache_hits / total

    def to_dict(self) -> dict[str, Any]:
        return {
            "backtest_id": self.backtest_id,
            "duration": {
                "start": self.start_time.isoformat() if self.start_time else None,
                "end": self.end_time.isoformat() if self.end_time else None,
                "total_seconds": self.total_time_seconds,
            },
            "scope": {
                "symbols": self.symbols,
                "date_range": self.date_range,
                "total_days": self.total_days_processed,
                "total_trades": self.total_trades_executed,
            },
            "timing_breakdown": {
                "data_fetch": self.data_fetch_time_seconds,
                "vedastro": self.vedastro_time_seconds,
                "elemental": self.elemental_time_seconds,
                "execution": self.execution_time_seconds,
                "other": self.total_time_seconds
                - (
                    self.data_fetch_time_seconds
                    + self.vedastro_time_seconds
                    + self.elemental_time_seconds
                    + self.execution_time_seconds
                ),
            },
            "tools": {
                name: {
                    "calls": m.call_count,
                    "avg_time_ms": m.avg_time_seconds * 1000,
                    "min_time_ms": (
                        m.min_time_seconds * 1000 if m.min_time_seconds != float("inf") else 0
                    ),
                    "max_time_ms": m.max_time_seconds * 1000,
                    "errors": m.errors,
                }
                for name, m in self.tool_metrics.items()
            },
            "cache": {
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "hit_rate": self.get_cache_hit_rate(),
            },
            "memory": {"peak_mb": self.peak_memory_mb},
        }


class PerformanceMetricsCollector:
    """
    Collects and aggregates performance metrics during backtest execution.

    Usage:
        collector = PerformanceMetricsCollector()

        with collector.time_tool_call("vedastro__generate_signal"):
            result = await client.call_tool(...)

        metrics = collector.get_metrics()
    """

    def __init__(self, backtest_id: str | None = None):
        self.backtest_id = backtest_id or f"bt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.metrics = BacktestMetrics(backtest_id=self.backtest_id)
        self._active_timers: dict[str, float] = {}
        self._lock = asyncio.Lock()

    @contextmanager
    def time_tool_call(self, tool_name: str):
        """Context manager to time an MCP tool call."""
        start = time.perf_counter()
        error = False
        try:
            yield self
        except Exception:
            error = True
            raise
        finally:
            duration = time.perf_counter() - start
            self._record_tool_time(tool_name, duration, error)

    @contextmanager
    def time_section(self, section: str):
        """Time a section of code (data_fetch, vedastro, elemental, execution)."""
        start = time.perf_counter()
        try:
            yield self
        finally:
            duration = time.perf_counter() - start
            setattr(
                self.metrics,
                f"{section}_time_seconds",
                getattr(self.metrics, f"{section}_time_seconds", 0) + duration,
            )

    def _record_tool_time(self, tool_name: str, duration: float, error: bool = False) -> None:
        """Record timing for a tool call."""
        if tool_name not in self.metrics.tool_metrics:
            self.metrics.tool_metrics[tool_name] = ToolMetrics(tool_name=tool_name)

        self.metrics.tool_metrics[tool_name].record_call(duration, error)

    async def record_cache_hit(self) -> None:
        """Record a cache hit."""
        async with self._lock:
            self.metrics.cache_hits += 1

    async def record_cache_miss(self) -> None:
        """Record a cache miss."""
        async with self._lock:
            self.metrics.cache_misses += 1

    async def record_trade(self) -> None:
        """Record a trade execution."""
        async with self._lock:
            self.metrics.total_trades_executed += 1

    async def record_signal(self) -> None:
        """Record a signal generation."""
        async with self._lock:
            self.metrics.total_signals_generated += 1

    async def record_day_processed(self) -> None:
        """Record a day processed."""
        async with self._lock:
            self.metrics.total_days_processed += 1

    def set_symbols(self, symbols: list[str]) -> None:
        """Set the symbols being processed."""
        self.metrics.symbols = symbols
        self.metrics.total_symbols_processed = len(symbols)

    def set_date_range(self, start: datetime, end: datetime) -> None:
        """Set the date range."""
        self.metrics.date_range = {"start": start.isoformat(), "end": end.isoformat()}

    def finalize(self) -> BacktestMetrics:
        """Finalize metrics collection."""
        self.metrics.end_time = datetime.now()
        if self.metrics.start_time:
            self.metrics.total_time_seconds = (
                self.metrics.end_time - self.metrics.start_time
            ).total_seconds()
        return self.metrics

    def get_metrics(self) -> dict[str, Any]:
        """Get current metrics as dictionary."""
        return self.metrics.to_dict()

    def get_slowest_tools(self, n: int = 5) -> list[tuple[str, float]]:
        """Get the N slowest tools by average time."""
        tools = [
            (name, metrics.avg_time_seconds) for name, metrics in self.metrics.tool_metrics.items()
        ]
        return sorted(tools, key=lambda x: x[1], reverse=True)[:n]

    def get_most_called_tools(self, n: int = 5) -> list[tuple[str, int]]:
        """Get the N most frequently called tools."""
        tools = [(name, metrics.call_count) for name, metrics in self.metrics.tool_metrics.items()]
        return sorted(tools, key=lambda x: x[1], reverse=True)[:n]

    def identify_bottlenecks(self) -> list[dict[str, Any]]:
        """Identify performance bottlenecks."""
        bottlenecks = []

        # Check for slow tools
        for name, metrics in self.metrics.tool_metrics.items():
            if metrics.avg_time_seconds > 1.0:  # > 1 second
                bottlenecks.append(
                    {
                        "type": "slow_tool",
                        "tool": name,
                        "avg_time_seconds": metrics.avg_time_seconds,
                        "call_count": metrics.call_count,
                        "impact": metrics.avg_time_seconds * metrics.call_count,
                    }
                )

            if metrics.errors > 0:
                bottlenecks.append(
                    {
                        "type": "error_prone_tool",
                        "tool": name,
                        "error_count": metrics.errors,
                        "error_rate": metrics.errors / max(metrics.call_count, 1),
                    }
                )

        # Check cache hit rate
        hit_rate = self.metrics.get_cache_hit_rate()
        if hit_rate < 0.5 and (self.metrics.cache_hits + self.metrics.cache_misses) > 100:
            bottlenecks.append(
                {
                    "type": "low_cache_hit_rate",
                    "hit_rate": hit_rate,
                    "suggestion": "Consider increasing cache TTL or improving cache keys",
                }
            )

        return sorted(bottlenecks, key=lambda x: x.get("impact", 0), reverse=True)


class BacktestProfiler:
    """
    High-level profiler for backtest performance analysis.

    Provides detailed profiling reports and optimization suggestions.
    """

    def __init__(self):
        self.collector: PerformanceMetricsCollector | None = None
        self._snapshots: list[dict[str, Any]] = []

    def start_profiling(self, backtest_id: str | None = None) -> PerformanceMetricsCollector:
        """Start profiling a backtest."""
        self.collector = PerformanceMetricsCollector(backtest_id)
        return self.collector

    def stop_profiling(self) -> BacktestMetrics:
        """Stop profiling and return metrics."""
        if self.collector:
            return self.collector.finalize()
        raise RuntimeError("Profiling not started")

    def take_snapshot(self) -> None:
        """Take a snapshot of current metrics."""
        if self.collector:
            self._snapshots.append(self.collector.get_metrics())

    def generate_report(self) -> dict[str, Any]:
        """Generate comprehensive performance report."""
        if not self.collector:
            return {"error": "No profiling data available"}

        metrics = self.collector.finalize()

        report = {
            "summary": {
                "backtest_id": metrics.backtest_id,
                "duration_seconds": metrics.total_time_seconds,
                "symbols": len(metrics.symbols),
                "trades": metrics.total_trades_executed,
                "trades_per_second": metrics.total_trades_executed
                / max(metrics.total_time_seconds, 0.001),
            },
            "timing_breakdown": {
                "data_fetch_pct": metrics.data_fetch_time_seconds
                / max(metrics.total_time_seconds, 0.001)
                * 100,
                "vedastro_pct": metrics.vedastro_time_seconds
                / max(metrics.total_time_seconds, 0.001)
                * 100,
                "elemental_pct": metrics.elemental_time_seconds
                / max(metrics.total_time_seconds, 0.001)
                * 100,
                "execution_pct": metrics.execution_time_seconds
                / max(metrics.total_time_seconds, 0.001)
                * 100,
            },
            "top_slowest_tools": [
                {"tool": name, "avg_ms": avg * 1000}
                for name, avg in self.collector.get_slowest_tools(5)
            ],
            "most_called_tools": [
                {"tool": name, "calls": count}
                for name, count in self.collector.get_most_called_tools(5)
            ],
            "bottlenecks": self.collector.identify_bottlenecks(),
            "cache_performance": {
                "hit_rate": metrics.get_cache_hit_rate(),
                "hits": metrics.cache_hits,
                "misses": metrics.cache_misses,
            },
            "recommendations": self._generate_recommendations(metrics),
        }

        return report

    def _generate_recommendations(self, metrics: BacktestMetrics) -> list[str]:
        """Generate optimization recommendations."""
        recommendations = []

        # Cache recommendations
        hit_rate = metrics.get_cache_hit_rate()
        if hit_rate < 0.3:
            recommendations.append(
                "Cache hit rate is low (<30%). Consider increasing cache TTL or batching similar requests."
            )
        elif hit_rate > 0.8:
            recommendations.append(
                f"Excellent cache hit rate ({hit_rate:.1%}). Cache configuration is optimal."
            )

        # Tool-specific recommendations
        for name, tool_metrics in metrics.tool_metrics.items():
            if tool_metrics.avg_time_seconds > 2.0:
                recommendations.append(
                    f"Tool '{name}' is slow (avg {tool_metrics.avg_time_seconds:.2f}s). "
                    "Consider caching or optimization."
                )

            if tool_metrics.errors > 0:
                error_rate = tool_metrics.errors / max(tool_metrics.call_count, 1)
                if error_rate > 0.1:
                    recommendations.append(
                        f"Tool '{name}' has high error rate ({error_rate:.1%}). "
                        "Check resilience configuration."
                    )

        # Timing recommendations
        if metrics.vedastro_time_seconds > metrics.total_time_seconds * 0.5:
            recommendations.append(
                "VedAstro calculations dominate runtime (>50%). Consider pre-computing or caching."
            )

        if metrics.data_fetch_time_seconds > metrics.total_time_seconds * 0.3:
            recommendations.append(
                "Data fetching is significant (>30%). Consider batch data loading or prefetching."
            )

        return recommendations


# Decorator for automatic metrics collection


def instrumented_tool_call(metrics_collector: PerformanceMetricsCollector):
    """Decorator to automatically instrument MCP tool calls."""

    def decorator(func: Callable) -> Callable:
        async def wrapper(*args, **kwargs):
            # Extract tool name from function name
            tool_name = func.__name__

            with metrics_collector.time_tool_call(tool_name):
                return await func(*args, **kwargs)

        return wrapper

    return decorator
