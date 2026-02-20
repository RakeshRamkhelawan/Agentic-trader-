"""
SLO (Service Level Objective) Tracking

Implements ADR-001: SLO/SLI Model per Kritieke Flow
Tracks latency, success rates, and error budgets for critical flows.

Author: Architecture Team
Date: 2026-02-20
"""

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict, Optional

from prometheus_client import Counter, Gauge, Histogram

logger = logging.getLogger(__name__)


class FlowType(str, Enum):
    """Critical flows as defined in ADR-001."""

    MARKET_DATA_STREAMING = "market_data_streaming"
    ORDER_EXECUTION = "order_execution"
    AGENT_DECISION = "agent_decision"


@dataclass
class SLOConfig:
    """Configuration for a Service Level Objective."""

    target: float  # e.g., 0.999 for 99.9%
    latency_p99_ms: int
    latency_p95_ms: int
    error_budget: float  # percentage (e.g., 0.001 for 0.1%)
    window: str  # e.g., "1m", "1h", "30d"


# SLO Definitions from ADR-001
SLO_DEFINITIONS: Dict[FlowType, SLOConfig] = {
    FlowType.MARKET_DATA_STREAMING: SLOConfig(
        target=0.999,
        latency_p99_ms=100,
        latency_p95_ms=50,
        error_budget=0.001,
        window="30d",
    ),
    FlowType.ORDER_EXECUTION: SLOConfig(
        target=0.9995,
        latency_p99_ms=500,
        latency_p95_ms=200,
        error_budget=0.0005,
        window="30d",
    ),
    FlowType.AGENT_DECISION: SLOConfig(
        target=0.995,
        latency_p99_ms=200,
        latency_p95_ms=100,
        error_budget=0.005,
        window="30d",
    ),
}


class SLITracker:
    """
    Prometheus-based SLI (Service Level Indicator) tracker.

    Measures:
    - Latency (p50, p95, p99)
    - Success rates
    - Error budgets
    - Throughput
    """

    def __init__(self):
        # Latency histograms per flow and stage
        self.latency = Histogram(
            "slo_latency_seconds",
            "Request latency by flow and stage",
            ["flow", "stage"],
            buckets=[
                0.001,
                0.005,
                0.01,
                0.025,
                0.05,
                0.1,
                0.25,
                0.5,
                1.0,
                2.5,
                5.0,
                10.0,
            ],
        )

        # Request counters by status
        self.requests = Counter(
            "slo_requests_total",
            "Total requests by flow and status",
            ["flow", "status"],  # status: success, error, timeout
        )

        # Error budget tracking
        self.error_budget_remaining = Gauge(
            "slo_error_budget_remaining", "Remaining error budget (0-1)", ["flow"]
        )

        # Current SLO compliance ratio
        self.compliance = Gauge(
            "slo_compliance_ratio", "Current SLO compliance (0-1)", ["flow"]
        )

        # Throughput
        self.throughput = Counter(
            "slo_throughput_total", "Request throughput", ["flow"]
        )

        # In-flight requests
        self.in_flight = Gauge(
            "slo_in_flight", "Currently processing requests", ["flow"]
        )

        # Initialize error budgets
        self._init_error_budgets()

    def _init_error_budgets(self):
        """Initialize error budget gauges."""
        for flow in FlowType:
            slo = SLO_DEFINITIONS[flow]
            self.error_budget_remaining.labels(flow=flow.value).set(slo.error_budget)
            self.compliance.labels(flow=flow.value).set(1.0)

    def track_latency(
        self, flow: FlowType, latency_seconds: float, stage: str = "total"
    ) -> None:
        """
        Record latency for a flow.

        Args:
            flow: The critical flow being tracked
            latency_seconds: Measured latency
            stage: Specific stage (e.g., "risk_check", "execution")
        """
        self.latency.labels(flow=flow.value, stage=stage).observe(latency_seconds)

    def track_request(
        self, flow: FlowType, success: bool, timeout: bool = False
    ) -> None:
        """
        Record request outcome.

        Args:
            flow: The critical flow
            success: Whether request succeeded
            timeout: Whether request timed out
        """
        if timeout:
            status = "timeout"
        else:
            status = "success" if success else "error"

        self.requests.labels(flow=flow.value, status=status).inc()
        self.throughput.labels(flow=flow.value).inc()

        # Update compliance
        self._update_compliance(flow)

    def _update_compliance(self, flow: FlowType):
        """Recalculate SLO compliance."""
        # This is a simplified calculation; in production use recording rules
        pass

    def record_market_data_delivery(self, latency_ms: float, delivered: bool) -> None:
        """
        Track market data delivery SLI.

        Args:
            latency_ms: Delivery latency in milliseconds
            delivered: Whether message was delivered
        """
        self.track_latency(
            FlowType.MARKET_DATA_STREAMING, latency_ms / 1000, "delivery"
        )
        self.track_request(FlowType.MARKET_DATA_STREAMING, delivered)

    def record_order_execution(
        self, latency_ms: float, success: bool, stage: Optional[str] = None
    ) -> None:
        """
        Track order execution SLI.

        Args:
            latency_ms: Execution latency
            success: Whether execution succeeded
            stage: Specific stage ("risk_check", "routing", "execution")
        """
        self.track_latency(
            FlowType.ORDER_EXECUTION, latency_ms / 1000, stage or "total"
        )
        self.track_request(FlowType.ORDER_EXECUTION, success)

    def record_agent_decision(
        self, latency_ms: float, quality_score: float, llm_success: bool = True
    ) -> None:
        """
        Track agent decision SLI.

        Args:
            latency_ms: Decision latency
            quality_score: Decision quality (0-1)
            llm_success: Whether LLM call succeeded
        """
        self.track_latency(FlowType.AGENT_DECISION, latency_ms / 1000, "total")

        # Quality above 0.9 is considered success
        quality_ok = quality_score >= 0.9 and llm_success
        self.track_request(FlowType.AGENT_DECISION, quality_ok)

    def check_slo_breach(self, flow: FlowType) -> Optional[str]:
        """
        Check if SLO is currently breached.

        Returns:
            Reason for breach, or None if compliant
        """
        _ = SLO_DEFINITIONS[flow]  # Placeholder for SLO config access

        # In real implementation, query Prometheus for actual metrics
        # This is a placeholder for the concept

        return None

    def get_slo_summary(self) -> Dict[str, Dict]:
        """Get summary of all SLOs and current status."""
        return {
            flow.value: {
                "target": slo.target,
                "latency_p99_target_ms": slo.latency_p99_ms,
                "latency_p95_target_ms": slo.latency_p95_ms,
                "error_budget": slo.error_budget,
                "window": slo.window,
            }
            for flow, slo in SLO_DEFINITIONS.items()
        }


class SLITimer:
    """Context manager for timing operations and auto-recording to SLO tracker."""

    def __init__(
        self,
        tracker: SLITracker,
        flow: FlowType,
        stage: str = "total",
        success_on_exit: bool = True,
    ):
        self.tracker = tracker
        self.flow = flow
        self.stage = stage
        self.success_on_exit = success_on_exit
        self.start_time: Optional[float] = None
        self.success = True

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            latency_ms = (time.time() - self.start_time) * 1000

            if exc_type:
                self.success = False
            elif self.success_on_exit:
                self.success = True

            self.tracker.track_latency(self.flow, latency_ms / 1000, self.stage)
            self.tracker.track_request(self.flow, self.success)

    def set_failure(self):
        """Manually mark operation as failed."""
        self.success = False


# Global instance
slo_tracker = SLITracker()


def track_latency(flow: FlowType, stage: str = "total"):
    """Decorator for tracking function latency."""

    def decorator(func: Callable) -> Callable:
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                slo_tracker.track_latency(flow, time.time() - start, stage)
                slo_tracker.track_request(flow, True)
                return result
            except Exception:
                slo_tracker.track_latency(flow, time.time() - start, stage)
                slo_tracker.track_request(flow, False)
                raise

        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                slo_tracker.track_latency(flow, time.time() - start, stage)
                slo_tracker.track_request(flow, True)
                return result
            except Exception:
                slo_tracker.track_latency(flow, time.time() - start, stage)
                slo_tracker.track_request(flow, False)
                raise

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
