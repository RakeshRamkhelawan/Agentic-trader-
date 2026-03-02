"""
Unit tests for Optimized System Identity (Sprint 2 Tattva optimizations).
"""

import time
from unittest.mock import patch

import numpy as np
import pytest

from backend.core.system_identity_optimized import (
    SystemIdentityOptimized,
    TraversalMode,
    TattvaMetrics,
)


@pytest.fixture
def system_identity():
    """Create a SystemIdentityOptimized instance."""
    with patch("backend.core.system_identity_optimized.NavagrahaService"):
        with patch("backend.core.system_identity_optimized.SensoryProcessor"):
            with patch("backend.core.system_identity_optimized.MemorySystem"):
                with patch("backend.core.system_identity_optimized.DecisionDiscriminator"):
                    si = SystemIdentityOptimized(
                        coherence_threshold=0.8,
                        enable_metrics=False,  # Disable for tests
                    )
                    return si


class TestTraversalMode:
    """Test cases for traversal mode selection."""

    def test_sparse_mode_high_coherence(self, system_identity):
        """Test that high coherence selects sparse mode."""
        system_identity.system_state["coherence"] = 0.9
        mode = system_identity._select_traversal_mode(0.9)
        assert mode == TraversalMode.SPARSE

    def test_full_mode_low_coherence(self, system_identity):
        """Test that low coherence selects full mode."""
        system_identity.system_state["coherence"] = 0.5
        mode = system_identity._select_traversal_mode(0.5)
        assert mode == TraversalMode.FULL

    def test_threshold_boundary(self, system_identity):
        """Test threshold boundary (0.8)."""
        # Exactly at threshold -> sparse mode
        mode = system_identity._select_traversal_mode(0.8)
        assert mode == TraversalMode.SPARSE

        # Just below threshold -> full mode
        mode = system_identity._select_traversal_mode(0.79)
        assert mode == TraversalMode.FULL


class TestLayerMasks:
    """Test cases for pre-computed layer masks."""

    def test_sparse_mask_length(self, system_identity):
        """Test that sparse mask has correct length."""
        assert len(system_identity._sparse_mask) == 36

    def test_sparse_mask_true_count(self, system_identity):
        """Test that sparse mask has 8 True values."""
        assert np.sum(system_identity._sparse_mask) == 8

    def test_sparse_layers_array(self, system_identity):
        """Test that sparse layers array has 8 elements."""
        assert len(SystemIdentityOptimized.SPARSE_LAYERS) == 8
        assert list(SystemIdentityOptimized.SPARSE_LAYERS) == [1, 2, 3, 14, 15, 16, 17, 36]

    def test_full_layers_array(self, system_identity):
        """Test that full layers array has 36 elements."""
        assert len(SystemIdentityOptimized.FULL_LAYERS) == 36
        assert list(SystemIdentityOptimized.FULL_LAYERS) == list(range(1, 37))


class TestVectorizedTraversal:
    """Test cases for vectorized layer traversal."""

    def test_traverse_ascend(self, system_identity):
        """Test ascend phase traversal."""
        layers = np.array([1, 2, 3, 4, 5])
        result = system_identity._traverse_layers_vectorized(layers, "ascend")

        assert len(result) == 5
        # Ascend phase should have perfect coherence
        for coherence in result.values():
            assert coherence == 1.0

    def test_traverse_filter(self, system_identity):
        """Test filter phase traversal."""
        layers = np.array([6, 7, 8, 9, 10, 11, 12])
        result = system_identity._traverse_layers_vectorized(layers, "filter")

        assert len(result) == 7
        # Filter phase has reduced coherence (0.95)
        for layer, coherence in result.items():
            if 6 <= layer <= 12:
                assert coherence == 0.95

    def test_traverse_interface(self, system_identity):
        """Test interface phase traversal."""
        system_identity.system_state["confidence"] = 0.75

        layers = np.array([13, 14, 15])
        result = system_identity._traverse_layers_vectorized(layers, "interface")

        assert len(result) == 3
        # Buddhi (14) uses system confidence
        assert result[14] == 0.75

    def test_traverse_sense_with_context(self, system_identity):
        """Test sense phase with perception context."""
        layers = np.array([16, 17, 18])
        context = {"coherence": 0.85}
        result = system_identity._traverse_layers_vectorized(layers, "sense", context)

        assert len(result) == 3
        # Should use context coherence * 0.9
        for coherence in result.values():
            assert coherence == 0.85 * 0.9

    def test_traverse_act_with_context(self, system_identity):
        """Test act phase with action context."""
        layers = np.array([26, 27, 28])
        context = {"confidence": 0.9}
        result = system_identity._traverse_layers_vectorized(layers, "act", context)

        assert len(result) == 3
        # Should use context confidence
        for coherence in result.values():
            assert coherence == 0.9


class TestPerformanceTargets:
    """Test cases for performance targets."""

    def test_sparse_traversal_latency(self, system_identity):
        """Test that sparse mode traversal meets < 80μs target."""
        system_identity.system_state["coherence"] = 0.9  # Force sparse mode

        # Warm up
        for _ in range(10):
            system_identity._traverse_layers_vectorized(
                SystemIdentityOptimized.SPARSE_LAYERS, "ascend"
            )

        # Measure
        latencies = []
        for _ in range(100):
            start = time.perf_counter_ns()
            system_identity._traverse_layers_vectorized(
                SystemIdentityOptimized.SPARSE_LAYERS, "ascend"
            )
            end = time.perf_counter_ns()
            latencies.append((end - start) / 1000.0)  # Convert to μs

        p99 = np.percentile(latencies, 99)
        mean = np.mean(latencies)

        print(f"\nSparse mode latency - Mean: {mean:.2f}μs, P99: {p99:.2f}μs")
        assert p99 < 80, f"Sparse mode P99 {p99:.2f}μs exceeds 80μs target"

    def test_full_traversal_latency(self, system_identity):
        """Test that full mode traversal meets < 200μs target."""
        system_identity.system_state["coherence"] = 0.5  # Force full mode

        # Warm up
        for _ in range(10):
            system_identity._traverse_layers_vectorized(
                SystemIdentityOptimized.FULL_LAYERS, "ascend"
            )

        # Measure
        latencies = []
        for _ in range(100):
            start = time.perf_counter_ns()
            system_identity._traverse_layers_vectorized(
                SystemIdentityOptimized.FULL_LAYERS, "ascend"
            )
            end = time.perf_counter_ns()
            latencies.append((end - start) / 1000.0)

        p99 = np.percentile(latencies, 99)
        mean = np.mean(latencies)

        print(f"\nFull mode latency - Mean: {mean:.2f}μs, P99: {p99:.2f}μs")
        assert p99 < 200, f"Full mode P99 {p99:.2f}μs exceeds 200μs target"

    def test_layer_selection_performance(self, system_identity):
        """Test layer selection overhead."""
        latencies = []
        for _ in range(1000):
            start = time.perf_counter_ns()
            system_identity._select_traversal_mode(0.85)
            end = time.perf_counter_ns()
            latencies.append((end - start) / 1000.0)

        p99 = np.percentile(latencies, 99)
        # Layer selection should be sub-microsecond
        assert p99 < 1.0, f"Layer selection too slow: {p99:.2f}μs"


class TestPhilosophicalIntegrity:
    """Test that philosophical integrity is maintained."""

    def test_all_36_layers_represented(self, system_identity):
        """Test that all 36 layers are represented in the system."""
        assert len(system_identity.tattva_config.layers) == 36

        layer_numbers = [layer.layer_number for layer in system_identity.tattva_config.layers]
        assert set(layer_numbers) == set(range(1, 37))

    def test_sparse_mode_preserves_philosophy(self, system_identity):
        """Test that sparse mode doesn't break philosophy.

        The 8 critical layers represent:
        - Pure Consciousness (1-3)
        - Decision making (14-15)
        - Input processing (16-17)
        - Manifestation (36)
        """
        sparse = SystemIdentityOptimized.SPARSE_LAYERS

        # Should include pure consciousness layers
        assert 1 in sparse  # Shiva
        assert 2 in sparse  # Sadashiva
        assert 3 in sparse  # Ishvara

        # Should include decision layers
        assert 14 in sparse  # Buddhi
        assert 15 in sparse  # Ahamkara

        # Should include input layers
        assert 16 in sparse  # Manas
        assert 17 in sparse  # Prana

        # Should include manifestation
        assert 36 in sparse  # Prithvi

    def test_coherence_tracking_preserved(self, system_identity):
        """Test that coherence tracking is maintained for all layers."""
        for i in range(1, 37):
            assert i in system_identity.system_state["tattva_coherence"]


class TestMetricsAndStatistics:
    """Test cases for performance metrics."""

    def test_performance_statistics_structure(self, system_identity):
        """Test that performance statistics have correct structure."""
        # Add some mock data
        system_identity.performance_history["traversal_latencies"] = [50, 60, 55]
        system_identity.performance_history["tattva_traversals"] = [
            {"mode": "sparse"},
            {"mode": "full"},
            {"mode": "sparse"},
        ]

        stats = system_identity.get_performance_statistics()

        assert "total_cycles" in stats
        assert "all_modes" in stats
        assert "sparse_mode" in stats
        assert "full_mode" in stats
        assert "configuration" in stats

    def test_sparse_statistics(self, system_identity):
        """Test sparse mode statistics."""
        system_identity.performance_history["traversal_latencies"] = [50, 55, 60, 200]
        system_identity.performance_history["tattva_traversals"] = [
            {"mode": "sparse"},
            {"mode": "sparse"},
            {"mode": "sparse"},
            {"mode": "full"},
        ]

        stats = system_identity.get_performance_statistics()

        assert stats["sparse_mode"]["count"] == 3
        assert stats["sparse_mode"]["target_met"]  # All < 80

    def test_full_statistics(self, system_identity):
        """Test full mode statistics."""
        system_identity.performance_history["traversal_latencies"] = [50, 150, 180, 250]
        system_identity.performance_history["tattva_traversals"] = [
            {"mode": "sparse"},
            {"mode": "full"},
            {"mode": "full"},
            {"mode": "full"},
        ]

        stats = system_identity.get_performance_statistics()

        assert stats["full_mode"]["count"] == 3
        assert not stats["full_mode"]["target_met"]  # One > 200


class TestTattvaMetrics:
    """Test cases for TattvaMetrics dataclass."""

    def test_metrics_creation(self):
        """Test TattvaMetrics creation."""
        metrics = TattvaMetrics(
            mode=TraversalMode.SPARSE,
            layers_traversed=8,
            latency_us=65.5,
            coherence_threshold=0.8,
        )

        assert metrics.mode == TraversalMode.SPARSE
        assert metrics.layers_traversed == 8
        assert metrics.latency_us == 65.5
        assert metrics.coherence_threshold == 0.8


class TestSystemStateUpdate:
    """Test cases for system state updates."""

    def test_coherence_update(self, system_identity):
        """Test that coherence is updated correctly."""
        initial_coherence = system_identity.system_state["coherence"]

        perception = {"coherence": 0.9}
        system_identity._update_system_state(perception, 0.8, 1, None)

        # Coherence should move towards perception coherence
        new_coherence = system_identity.system_state["coherence"]
        assert new_coherence > initial_coherence
        assert new_coherence < 0.9  # But not all the way

    def test_exploration_rate_adaptation(self, system_identity):
        """Test that exploration rate adapts to coherence."""
        # High coherence -> more exploration
        system_identity.system_state["coherence"] = 0.9
        system_identity._update_system_state({"coherence": 0.9}, 0.8, 1, None)

        # Should use higher exploration rate
        assert system_identity.system_state["exploration_rate"] == min(0.15, 0.1)

        # Low coherence -> less exploration
        system_identity.system_state["coherence"] = 0.5
        system_identity._update_system_state({"coherence": 0.5}, 0.6, 0, None)

        # Should use lower exploration rate
        assert system_identity.system_state["exploration_rate"] == max(0.05, 0.1)
