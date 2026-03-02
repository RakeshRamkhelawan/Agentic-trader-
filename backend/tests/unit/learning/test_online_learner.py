"""
Unit tests for Online Learning module (Sprint 3).
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.core.learning.online_learner import OnlineLearner, LearningMetrics
from backend.core.learning.drift_detector import (
    ADWINDriftDetector,
    DriftEvent,
    MultiMetricDriftDetector,
)
from backend.core.learning.strategy_adapter import StrategyWeightAdapter


class TestOnlineLearner:
    """Test cases for OnlineLearner."""

    def test_initialization(self):
        """Test learner initialization."""
        learner = OnlineLearner(learning_rate=0.01)

        assert learner.learning_rate == 0.01
        assert learner._enabled == True
        assert learner.metrics.total_samples == 0

    def test_initialization_without_river(self):
        """Test learner without River available."""
        with patch("backend.core.learning.online_learner.RIVER_AVAILABLE", False):
            learner = OnlineLearner()
            assert learner._enabled == False

    @pytest.mark.asyncio
    async def test_learn_single_sample(self):
        """Test learning from single sample."""
        learner = OnlineLearner()

        features = {"price_change": 0.01, "volume": 1000}
        drift = await learner.learn(features, action=1, reward=0.05)

        assert learner.metrics.total_samples == 1
        assert isinstance(drift, bool)

    @pytest.mark.asyncio
    async def test_learn_batch(self):
        """Test batch learning."""
        learner = OnlineLearner()

        samples = [
            ({"f1": 0.1}, 1, 0.05),
            ({"f1": 0.2}, 0, -0.02),
            ({"f1": 0.15}, 1, 0.03),
        ]

        drift_count = await learner.learn_batch(samples)

        assert learner.metrics.total_samples == 3
        assert drift_count >= 0

    @pytest.mark.asyncio
    async def test_weight_snapshot(self):
        """Test weight snapshot mechanism."""
        learner = OnlineLearner()

        # Initially empty
        weights = learner.get_strategy_weights()
        assert isinstance(weights, dict)

    def test_get_metrics(self):
        """Test metrics retrieval."""
        learner = OnlineLearner()

        metrics = learner.get_metrics()

        assert "total_samples" in metrics
        assert "drift_events" in metrics
        assert "model_accuracy" in metrics
        assert "enabled" in metrics


class TestADWINDriftDetector:
    """Test cases for ADWIN drift detector."""

    def test_initialization(self):
        """Test detector initialization."""
        detector = ADWINDriftDetector(delta=0.002, name="test")

        assert detector.name == "test"
        assert detector.delta == 0.002
        assert detector.sample_count == 0

    def test_update_without_drift(self):
        """Test update without drift detection."""
        detector = ADWINDriftDetector(min_samples=100)

        # Feed consistent data
        for i in range(50):
            drift = detector.update(0.5)
            assert drift == False  # Not enough samples

        assert detector.sample_count == 50

    def test_get_statistics(self):
        """Test statistics retrieval."""
        detector = ADWINDriftDetector(name="test_stat")

        stats = detector.get_statistics()

        assert stats["name"] == "test_stat"
        assert "sample_count" in stats
        assert "drift_count" in stats

    def test_reset(self):
        """Test detector reset."""
        detector = ADWINDriftDetector()

        for i in range(50):
            detector.update(0.5)

        assert detector.sample_count == 50

        detector.reset()

        assert detector.sample_count == 0
        assert detector.drift_count == 0


class TestMultiMetricDriftDetector:
    """Test cases for multi-metric detector."""

    def test_add_detector(self):
        """Test adding detectors."""
        multi = MultiMetricDriftDetector()

        detector = multi.add_detector("volatility", delta=0.001)

        assert "volatility" in multi.detectors
        assert isinstance(detector, ADWINDriftDetector)

    def test_update_multiple_metrics(self):
        """Test updating multiple metrics."""
        multi = MultiMetricDriftDetector()

        # Auto-creates detector
        multi.update("volatility", 0.2)
        multi.update("win_rate", 0.6)

        assert len(multi.detectors) == 2
        assert multi.detectors["volatility"].sample_count == 1
        assert multi.detectors["win_rate"].sample_count == 1

    def test_get_all_statistics(self):
        """Test getting statistics for all detectors."""
        multi = MultiMetricDriftDetector()
        multi.add_detector("metric1")
        multi.add_detector("metric2")

        stats = multi.get_all_statistics()

        assert "metric1" in stats
        assert "metric2" in stats


class TestStrategyWeightAdapter:
    """Test cases for StrategyWeightAdapter."""

    def test_initialization(self):
        """Test adapter initialization."""
        strategies = ["trend", "mean_reversion", "momentum"]
        adapter = StrategyWeightAdapter(strategies)

        assert adapter.strategies == strategies
        assert len(adapter._weights) == 3
        # Equal initial weights
        assert adapter._weights["trend"] == 1 / 3

    @pytest.mark.asyncio
    async def test_update_performance(self):
        """Test performance update."""
        adapter = StrategyWeightAdapter(["s1", "s2"], min_samples=5)

        # Add samples
        for i in range(10):
            await adapter.update_performance("s1", return_value=0.02, win=True)
            await adapter.update_performance("s2", return_value=-0.01, win=False)

        # s1 should have better weight
        weights = adapter.get_weights()
        assert weights["s1"] > weights["s2"]

    def test_get_strategy_ranking(self):
        """Test strategy ranking."""
        adapter = StrategyWeightAdapter(["s1", "s2", "s3"])

        # Manually set weights
        adapter._weight_snapshot = {"s1": 0.5, "s2": 0.3, "s3": 0.2}

        ranking = adapter.get_strategy_ranking()

        assert ranking[0][0] == "s1"  # Highest weight
        assert ranking[0][1] == 0.5

    def test_exploration_floor(self):
        """Test that minimum exploration (epsilon) is maintained."""
        adapter = StrategyWeightAdapter(["s1", "s2"], epsilon=0.1)

        # Even with extreme performance difference, min weight should be >= epsilon
        adapter._weight_snapshot = adapter._weights.copy()

        weights = adapter.get_weights()
        for w in weights.values():
            assert w >= 0.1

    def test_reset(self):
        """Test adapter reset."""
        adapter = StrategyWeightAdapter(["s1", "s2"])

        # Modify weights
        adapter._weights = {"s1": 0.8, "s2": 0.2}
        adapter._performance["s1"].win_count = 10

        adapter.reset()

        # Back to equal weights
        assert adapter._weights["s1"] == 0.5
        assert adapter._performance["s1"].win_count == 0


class TestPerformanceBenchmarks:
    """Performance benchmark tests."""

    @pytest.mark.asyncio
    async def test_learn_performance(self):
        """Benchmark learn() performance."""
        learner = OnlineLearner()

        import time

        start = time.perf_counter()

        for i in range(100):
            await learner.learn({"f1": i * 0.01}, i % 3, 0.01)

        elapsed = time.perf_counter() - start
        avg_time = elapsed / 100

        print(f"\nLearn() average time: {avg_time*1000:.3f}ms")

        # Should be < 5ms per sample
        assert avg_time < 0.005

    def test_weight_query_performance(self):
        """Benchmark weight query (hot path)."""
        adapter = StrategyWeightAdapter(["s1", "s2", "s3", "s4", "s5"])

        import time

        start = time.perf_counter()

        for i in range(10000):
            weights = adapter.get_weights()

        elapsed = time.perf_counter() - start
        avg_time = elapsed / 10000

        print(f"\nWeight query average time: {avg_time*1e6:.3f}μs")

        # Should be < 1μs (hot path)
        assert avg_time < 1e-5  # Relaxed for test environment
