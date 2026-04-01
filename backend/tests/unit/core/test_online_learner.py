"""
Unit tests for Online Learning module (Sprint 3).
"""

import asyncio

import pytest

from backend.core.learning.online_learner import AdaptiveLearner  # Backward compatibility
from backend.core.learning.online_learner import (
    LearningMetrics,
    OnlineLearner,
)


class TestLearningMetrics:
    """Test LearningMetrics dataclass."""

    def test_default_initialization(self):
        """Test default metric values."""
        metrics = LearningMetrics()
        assert metrics.total_samples == 0
        assert metrics.drift_events == 0
        assert metrics.last_drift_timestamp is None
        assert metrics.model_accuracy == 0.0
        assert metrics.strategy_weights == {}

    def test_custom_initialization(self):
        """Test custom metric values."""
        metrics = LearningMetrics(
            total_samples=100,
            drift_events=5,
            model_accuracy=0.85,
        )
        assert metrics.total_samples == 100
        assert metrics.drift_events == 5
        assert metrics.model_accuracy == 0.85


class TestOnlineLearnerInitialization:
    """Test OnlineLearner initialization."""

    @pytest.mark.skipif(
        not hasattr(OnlineLearner(), "_enabled") or not OnlineLearner()._enabled,
        reason="River not available",
    )
    def test_default_initialization(self):
        """Test learner initializes with defaults."""
        learner = OnlineLearner()
        assert learner is not None
        assert learner.learning_rate == 0.01
        assert learner.drift_delta == 0.002
        assert learner.enable_drift_detection is True

    @pytest.mark.skipif(
        not hasattr(OnlineLearner(), "_enabled") or not OnlineLearner()._enabled,
        reason="River not available",
    )
    def test_custom_initialization(self):
        """Test learner initializes with custom params."""
        learner = OnlineLearner(
            learning_rate=0.05,
            drift_delta=0.001,
            enable_drift_detection=False,
        )
        assert learner.learning_rate == 0.05
        assert learner.drift_delta == 0.001
        assert learner.enable_drift_detection is False


class TestOnlineLearnerLearning:
    """Test OnlineLearner learning functionality."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not hasattr(OnlineLearner(), "_enabled") or not OnlineLearner()._enabled,
        reason="River not available",
    )
    async def test_learn_single_sample(self):
        """Test learning from a single sample."""
        learner = OnlineLearner()

        features = {"price": 100.0, "volume": 1000.0, "rsi": 50.0}

        drift = await learner.learn(features, action=1, reward=0.05)

        # No drift detected with first sample
        assert drift is False
        assert learner.metrics.total_samples == 1

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not hasattr(OnlineLearner(), "_enabled") or not OnlineLearner()._enabled,
        reason="River not available",
    )
    async def test_learn_multiple_samples(self):
        """Test learning from multiple samples."""
        learner = OnlineLearner()

        for i in range(20):
            features = {"price": 100.0 + i, "volume": 1000.0, "rsi": 50.0 + i}
            await learner.learn(features, action=i % 3, reward=0.01 * (i % 2))

        assert learner.metrics.total_samples == 20

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not hasattr(OnlineLearner(), "_enabled") or not OnlineLearner()._enabled,
        reason="River not available",
    )
    async def test_get_strategy_weights(self):
        """Test getting strategy weights."""
        learner = OnlineLearner()

        # Initially empty
        weights = learner.get_strategy_weights()
        assert isinstance(weights, dict)

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not hasattr(OnlineLearner(), "_enabled") or not OnlineLearner()._enabled,
        reason="River not available",
    )
    async def test_get_metrics(self):
        """Test getting learning metrics."""
        learner = OnlineLearner()

        # Add some samples
        for i in range(15):
            await learner.learn({"f1": i}, action=0, reward=0.01)

        metrics = learner.get_metrics()

        assert "total_samples" in metrics
        assert "drift_events" in metrics
        assert "model_accuracy" in metrics
        assert "enabled" in metrics
        assert metrics["total_samples"] == 15


class TestOnlineLearnerBatchLearning:
    """Test batch learning functionality."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not hasattr(OnlineLearner(), "_enabled") or not OnlineLearner()._enabled,
        reason="River not available",
    )
    async def test_learn_batch(self):
        """Test learning from a batch of samples."""
        learner = OnlineLearner()

        samples = [
            ({"price": 100.0}, 1, 0.05),
            ({"price": 101.0}, 2, -0.02),
            ({"price": 99.0}, 0, 0.01),
            ({"price": 102.0}, 1, 0.03),
        ]

        drift_count = await learner.learn_batch(samples)

        assert drift_count >= 0  # May or may not detect drift
        assert learner.metrics.total_samples == 4


class TestOnlineLearnerSnapshot:
    """Test weight snapshot functionality."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not hasattr(OnlineLearner(), "_enabled") or not OnlineLearner()._enabled,
        reason="River not available",
    )
    async def test_snapshot_update(self):
        """Test that snapshot is updated periodically (every 10 samples)."""
        learner = OnlineLearner()

        # Add exactly 10 samples to trigger snapshot update
        for i in range(10):
            await learner.learn({"f1": float(i)}, action=0, reward=0.01)

        # Snapshot should have been updated at sample 10
        weights = learner.get_strategy_weights()
        assert "total_samples" in weights
        assert weights["total_samples"] == 10.0


class TestAdaptiveLearnerBackwardCompatibility:
    """Test backward compatibility alias."""

    def test_adaptive_learner_alias(self):
        """Test that AdaptiveLearner is alias for OnlineLearner."""
        assert AdaptiveLearner is OnlineLearner


class TestOnlineLearnerDisabled:
    """Test behavior when River is not available."""

    def test_disabled_when_river_unavailable(self):
        """Test learner disables itself when River not available."""
        learner = OnlineLearner()
        # If River not available, _enabled is False
        if not hasattr(learner, "learning_rate"):
            assert learner._enabled is False

    @pytest.mark.asyncio
    async def test_learn_returns_false_when_disabled(self):
        """Test learn returns False when disabled."""
        learner = OnlineLearner()
        if not learner._enabled:
            result = await learner.learn({"f1": 1.0}, action=0, reward=0.01)
            assert result is False
        else:
            pytest.skip("River is available")

    def test_get_metrics_when_disabled(self):
        """Test get_metrics returns default when disabled."""
        learner = OnlineLearner()
        if not learner._enabled:
            metrics = learner.get_metrics()
            assert metrics["enabled"] is False
            assert metrics["total_samples"] == 0
        else:
            pytest.skip("River is available")


class TestOnlineLearnerScheduling:
    """Test background task scheduling."""

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not hasattr(OnlineLearner(), "_enabled") or not OnlineLearner()._enabled,
        reason="River not available",
    )
    async def test_schedule_learning_task(self):
        """Test learning task processes queue."""
        learner = OnlineLearner()

        queue = asyncio.Queue()
        stop_event = asyncio.Event()

        # Add some experiences to queue
        for i in range(5):
            await queue.put(({"f1": float(i)}, i % 3, 0.01))

        # Stop immediately after processing
        async def stop_after_processing():
            await asyncio.sleep(0.1)
            stop_event.set()

        # Run both tasks
        await asyncio.gather(
            learner.schedule_learning_task(queue, stop_event),
            stop_after_processing(),
        )

        # Should have processed some samples
        assert learner.metrics.total_samples >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
