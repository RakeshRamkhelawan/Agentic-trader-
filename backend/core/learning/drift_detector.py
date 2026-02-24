"""
ADWIN Drift Detector - Adaptive Windowing for concept drift detection.

ADWIN (ADaptive WINdowing) is an adaptive sliding window algorithm that
detects change in data streams by comparing statistical properties of
two sub-windows.

Philosophy:
Like the mind's ability to recognize when a situation has fundamentally
changed (requiring new learning), ADWIN detects when the market regime
has shifted and old strategies may no longer work.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass

try:
    from river.drift import ADWIN as RiverADWIN

    RIVER_AVAILABLE = True
except ImportError:
    RIVER_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class DriftEvent:
    """Represents a detected drift event."""

    timestamp: float
    sample_index: int
    severity: str  # "low", "medium", "high"
    affected_metric: str
    old_value: float
    new_value: float


class ADWINDriftDetector:
    """
    ADWIN-based drift detector with multiple sensitivity levels.

    Features:
    - Automatic drift detection on data streams
    - Multiple detectors for different metrics
    - Severity classification
    - Callback system for drift events

    Usage:
        detector = ADWINDriftDetector(delta=0.002)
        for value in data_stream:
            if detector.update(value):
                print("Drift detected!")
    """

    def __init__(
        self,
        delta: float = 0.002,
        min_samples: int = 30,
        name: str = "default",
    ):
        """
        Initialize ADWIN drift detector.

        Args:
            delta: Sensitivity parameter (lower = more sensitive)
            min_samples: Minimum samples before drift detection
            name: Detector name for logging
        """
        self.name = name
        self.delta = delta
        self.min_samples = min_samples

        if not RIVER_AVAILABLE:
            logger.warning(f"River not available. Drift detector '{name}' disabled.")
            self._enabled = False
            return

        self._enabled = True
        self.detector = RiverADWIN(delta=delta)

        # Statistics
        self.sample_count = 0
        self.drift_count = 0
        self._callbacks: list[Callable[[DriftEvent], None]] = []

        logger.info(f"ADWIN detector '{name}' initialized: delta={delta}")

    def update(self, value: float) -> bool:
        """
        Update detector with new value.

        Args:
            value: New data point

        Returns:
            True if drift was detected
        """
        if not self._enabled:
            return False

        self.sample_count += 1

        # Don't detect drift until we have enough samples
        if self.sample_count < self.min_samples:
            self.detector.update(value)
            return False

        # Check for drift
        drift_detected = self.detector.update(value)

        if drift_detected:
            self.drift_count += 1
            self._handle_drift(value)

        return drift_detected

    def _handle_drift(self, current_value: float) -> None:
        """Handle drift detection event."""
        import time

        # Determine severity based on magnitude of change
        # This is a simplified approach - in production, compare distributions
        severity = "medium"  # Default

        event = DriftEvent(
            timestamp=time.time(),
            sample_index=self.sample_count,
            severity=severity,
            affected_metric=self.name,
            old_value=0.0,  # Would be computed from before/after windows
            new_value=current_value,
        )

        logger.warning(
            f"Drift detected in '{self.name}' at sample {self.sample_count}, "
            f"severity={severity}"
        )

        # Trigger callbacks
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Drift callback error: {e}")

        # Reset detector after drift
        self.detector.reset()

    def register_callback(self, callback: Callable[[DriftEvent], None]) -> None:
        """Register callback for drift events."""
        self._callbacks.append(callback)

    def get_statistics(self) -> dict:
        """Get detector statistics."""
        return {
            "name": self.name,
            "enabled": self._enabled,
            "sample_count": self.sample_count,
            "drift_count": self.drift_count,
            "delta": self.delta,
        }

    def reset(self) -> None:
        """Reset detector state."""
        if self._enabled:
            self.detector.reset()
        self.sample_count = 0
        self.drift_count = 0


class MultiMetricDriftDetector:
    """
    Manage multiple ADWIN detectors for different metrics.

    Example:
        - Price volatility drift
        - Win rate drift
        - Market regime drift
    """

    def __init__(self):
        """Initialize multi-metric detector."""
        self.detectors: dict[str, ADWINDriftDetector] = {}
        self._drift_history: list[DriftEvent] = []

    def add_detector(
        self,
        name: str,
        delta: float = 0.002,
        min_samples: int = 30,
    ) -> ADWINDriftDetector:
        """Add a new detector for a metric."""
        detector = ADWINDriftDetector(
            delta=delta,
            min_samples=min_samples,
            name=name,
        )
        detector.register_callback(self._on_drift)
        self.detectors[name] = detector
        return detector

    def update(self, metric_name: str, value: float) -> bool:
        """Update a specific metric detector."""
        if metric_name not in self.detectors:
            # Auto-create detector with default settings
            self.add_detector(metric_name)

        return self.detectors[metric_name].update(value)

    def _on_drift(self, event: DriftEvent) -> None:
        """Internal drift handler."""
        self._drift_history.append(event)
        logger.info(f"Multi-metric drift recorded: {event.affected_metric}")

    def get_all_statistics(self) -> dict:
        """Get statistics for all detectors."""
        return {name: detector.get_statistics() for name, detector in self.detectors.items()}

    def get_drift_history(
        self,
        limit: int = 100,
    ) -> list[DriftEvent]:
        """Get recent drift events."""
        return self._drift_history[-limit:]
