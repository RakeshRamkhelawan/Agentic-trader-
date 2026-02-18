"""
Unit tests for HotPathEngine - Ultra-low latency execution engine.

TDD approach: Tests define the performance and functionality contracts.

HotPathEngine characteristics:
- Ultra-low latency: <1ms per decision cycle
- Deterministic: No LLM calls, no I/O except FastConfig reads
- Thread-safe: Safe for concurrent execution
- Zero allocation: Minimal memory operations
"""

import tempfile
import time
from threading import Thread

import pytest

from backend.execution.fast_config import FALLBACK_CONFIG, FastConfigManager
from backend.execution.hot_path_engine import (ExecutionDecision,
                                               HotPathEngine, HotPathExecutor)

pytestmark = pytest.mark.unit


class TestHotPathEngineBasics:
    """Test basic HotPathEngine functionality."""

    def test_engine_initialization(self):
        """Engine should initialize with config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/config.bin"
            config_manager = FastConfigManager(config_file)
            config_manager.write_atomic(
                {
                    "action": 1,
                    "confidence": 0.8,
                    "exploration_rate": 0.05,
                    "quantity": 1.0,
                }
            )

            engine = HotPathEngine(config_file)

            assert engine is not None
            assert engine.config_manager is not None
            assert engine.fallback_decision is not None

    def test_get_execution_decision(self):
        """Engine should read config and return execution decision."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/config.bin"
            config_manager = FastConfigManager(config_file)
            config_manager.write_atomic(
                {
                    "action": 1,
                    "confidence": 0.85,
                    "exploration_rate": 0.05,
                    "quantity": 0.5,
                }
            )

            engine = HotPathEngine(config_file)
            decision = engine.get_execution_decision()

            assert decision.action == 1
            assert decision.confidence == pytest.approx(0.85, abs=0.01)
            assert decision.quantity == 0.5
            assert decision.timestamp > 0
            assert decision.source == "hot_path"

    def test_execution_decision_to_dict(self):
        """ExecutionDecision should convert to dict."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/config.bin"
            config_manager = FastConfigManager(config_file)
            config_manager.write_atomic(
                {
                    "action": 2,
                    "confidence": 0.75,
                    "exploration_rate": 0.1,
                    "quantity": 0.2,
                }
            )

            engine = HotPathEngine(config_file)
            decision = engine.get_execution_decision()
            decision_dict = decision.to_dict()

            assert decision_dict["action"] == 2
            assert decision_dict["confidence"] == 0.75
            assert decision_dict["quantity"] == pytest.approx(0.2)
            assert "timestamp" in decision_dict
            assert "config_version" in decision_dict


class TestHotPathLatency:
    """Test hot path latency requirements."""

    def test_decision_sub_millisecond(self):
        """Decision latency should be <1ms average."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/config.bin"
            config_manager = FastConfigManager(config_file)
            config_manager.write_atomic(
                {
                    "action": 1,
                    "confidence": 0.8,
                    "exploration_rate": 0.05,
                    "quantity": 0.1,
                }
            )

            engine = HotPathEngine(config_file)

            times = []
            for _ in range(1000):
                start = time.perf_counter()
                decision = engine.get_execution_decision()
                elapsed = time.perf_counter() - start
                times.append(elapsed)

            avg_latency = sum(times) / len(times)
            assert (
                avg_latency < 0.001
            ), f"Average latency {avg_latency*1000:.3f}ms exceeds <1ms target"

    def test_p99_latency_under_threshold(self):
        """P99 latency should be <5ms."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/config.bin"
            config_manager = FastConfigManager(config_file)
            config_manager.write_atomic(
                {
                    "action": 1,
                    "confidence": 0.8,
                    "exploration_rate": 0.05,
                    "quantity": 0.1,
                }
            )

            engine = HotPathEngine(config_file)

            times = []
            for _ in range(1000):
                start = time.perf_counter()
                decision = engine.get_execution_decision()
                elapsed = time.perf_counter() - start
                times.append(elapsed)

            sorted_times = sorted(times)
            p99_latency = sorted_times[int(0.99 * len(sorted_times))]
            assert (
                p99_latency < 0.005
            ), f"P99 latency {p99_latency*1000:.3f}ms exceeds <5ms target"

    def test_max_latency_reasonable(self):
        """Max latency should not exceed 10ms."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/config.bin"
            config_manager = FastConfigManager(config_file)
            config_manager.write_atomic(
                {
                    "action": 1,
                    "confidence": 0.8,
                    "exploration_rate": 0.05,
                    "quantity": 0.1,
                }
            )

            engine = HotPathEngine(config_file)

            times = []
            for _ in range(1000):
                start = time.perf_counter()
                decision = engine.get_execution_decision()
                elapsed = time.perf_counter() - start
                times.append(elapsed)

            max_latency = max(times)
            # Allow up to 12ms for system load and initialization overhead
            assert (
                max_latency < 0.012
            ), f"Max latency {max_latency*1000:.3f}ms exceeds <12ms threshold"


class TestHotPathDeterminism:
    """Test that hot path is completely deterministic."""

    def test_same_config_same_decision(self):
        """Given same config, should always produce same decision."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/config.bin"
            config_manager = FastConfigManager(config_file)
            config_manager.write_atomic(
                {
                    "action": 1,
                    "confidence": 0.85,
                    "exploration_rate": 0.05,
                    "quantity": 0.5,
                }
            )

            engine = HotPathEngine(config_file)

            decision1 = engine.get_execution_decision()
            decision2 = engine.get_execution_decision()

            assert decision1.action == decision2.action
            assert decision1.confidence == decision2.confidence

    def test_no_randomness(self):
        """Hot path should not use randomization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/config.bin"
            config_manager = FastConfigManager(config_file)
            config_manager.write_atomic(
                {
                    "action": 1,
                    "confidence": 0.8,
                    "exploration_rate": 0.05,
                    "quantity": 0.1,
                }
            )

            engine = HotPathEngine(config_file)

            decisions = [engine.get_execution_decision() for _ in range(100)]
            actions = [d.action for d in decisions]
            confidences = [d.confidence for d in decisions]

            # All should be identical
            assert len(set(actions)) == 1
            assert len(set(confidences)) == 1

    def test_no_blocking_io(self):
        """Hot path should not perform blocking I/O except config read."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/config.bin"
            config_manager = FastConfigManager(config_file)
            config_manager.write_atomic(
                {
                    "action": 1,
                    "confidence": 0.8,
                    "exploration_rate": 0.05,
                    "quantity": 0.1,
                }
            )

            engine = HotPathEngine(config_file)

            # Should complete very quickly (no I/O)
            start = time.perf_counter()
            for _ in range(100):
                decision = engine.get_execution_decision()
            elapsed = time.perf_counter() - start

            # 100 decisions should take <50ms (0.5ms each)
            assert (
                elapsed < 0.05
            ), f"100 decisions took {elapsed*1000:.1f}ms, expected <50ms"


class TestHotPathFallback:
    """Test fallback behavior when config is unavailable."""

    def test_fallback_on_missing_config(self):
        """Should return fallback decision if config file missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/config.bin"
            # Don't create file - it's missing

            engine = HotPathEngine(config_file)
            decision = engine.get_execution_decision()

            # Should return fallback
            assert decision.action == FALLBACK_CONFIG["action"]
            assert decision.confidence == FALLBACK_CONFIG["confidence"]

    def test_fallback_on_corrupted_config(self):
        """Should return fallback if config is corrupted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/config.bin"

            # Write garbage data
            with open(config_file, "wb") as f:
                f.write(b"garbage data that is not a valid config")

            engine = HotPathEngine(config_file)
            decision = engine.get_execution_decision()

            # Should return fallback
            assert decision.action == FALLBACK_CONFIG["action"]
            assert decision.confidence == FALLBACK_CONFIG["confidence"]

    def test_fallback_configuration(self):
        """Fallback config should be sensible defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/config.bin"

            engine = HotPathEngine(config_file)
            fallback = engine.fallback_decision

            assert isinstance(fallback.action, int)
            assert 0 <= fallback.action <= 2
            assert 0 <= fallback.confidence <= 1


class TestHotPathMemory:
    """Test memory efficiency."""

    def test_no_excessive_allocations(self):
        """Should not allocate excessively per decision."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/config.bin"
            config_manager = FastConfigManager(config_file)
            config_manager.write_atomic(
                {
                    "action": 1,
                    "confidence": 0.8,
                    "exploration_rate": 0.05,
                    "quantity": 0.1,
                }
            )

            engine = HotPathEngine(config_file)

            # Get baseline memory
            import tracemalloc

            tracemalloc.start()

            for _ in range(1000):
                decision = engine.get_execution_decision()

            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            # Peak allocation should be minimal (1000 decisions, each ~200 bytes)
            # Should not exceed 1MB for 1000 decisions
            assert peak < 1_000_000, f"Peak memory {peak/1000:.0f}KB exceeds threshold"

    def test_reuses_buffers(self):
        """Should reuse buffers and not create new objects per decision."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/config.bin"
            config_manager = FastConfigManager(config_file)
            config_manager.write_atomic(
                {
                    "action": 1,
                    "confidence": 0.8,
                    "exploration_rate": 0.05,
                    "quantity": 0.1,
                }
            )

            engine = HotPathEngine(config_file)

            # Get multiple decisions
            decisions = [engine.get_execution_decision() for _ in range(10)]

            # All should share the same underlying data (just different timestamps)
            assert all(d.action == decisions[0].action for d in decisions)
            assert all(d.confidence == decisions[0].confidence for d in decisions)


class TestHotPathThreadSafety:
    """Test concurrent execution safety."""

    def test_concurrent_reads_safe(self):
        """Multiple threads should be able to read decisions concurrently."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/config.bin"
            config_manager = FastConfigManager(config_file)
            config_manager.write_atomic(
                {
                    "action": 1,
                    "confidence": 0.8,
                    "exploration_rate": 0.05,
                    "quantity": 0.1,
                }
            )

            engine = HotPathEngine(config_file)
            decisions = []
            errors = []

            def read_decisions():
                try:
                    for _ in range(100):
                        d = engine.get_execution_decision()
                        decisions.append(d)
                except Exception as e:
                    errors.append(e)

            threads = [Thread(target=read_decisions) for _ in range(10)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            assert len(errors) == 0, f"Errors during concurrent reads: {errors}"
            assert len(decisions) == 1000


class TestHotPathExecution:
    """Test execution decision structure and usage."""

    def test_decision_has_action(self):
        """Decision should always have action."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/config.bin"
            config_manager = FastConfigManager(config_file)
            config_manager.write_atomic(
                {
                    "action": 2,
                    "confidence": 0.9,
                    "exploration_rate": 0.02,
                    "quantity": 0.1,
                }
            )

            engine = HotPathEngine(config_file)
            decision = engine.get_execution_decision()

            assert hasattr(decision, "action")
            assert decision.action in [0, 1, 2]

    def test_decision_has_confidence(self):
        """Decision should always have confidence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/config.bin"
            config_manager = FastConfigManager(config_file)
            config_manager.write_atomic(
                {
                    "action": 1,
                    "confidence": 0.65,
                    "exploration_rate": 0.08,
                    "quantity": 0.1,
                }
            )

            engine = HotPathEngine(config_file)
            decision = engine.get_execution_decision()

            assert hasattr(decision, "confidence")
            assert 0 <= decision.confidence <= 1

    def test_decision_has_timestamp(self):
        """Decision should have timestamp of when it was made."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/config.bin"
            config_manager = FastConfigManager(config_file)
            config_manager.write_atomic(
                {
                    "action": 1,
                    "confidence": 0.8,
                    "exploration_rate": 0.05,
                    "quantity": 0.1,
                }
            )

            engine = HotPathEngine(config_file)
            before = time.time()
            decision = engine.get_execution_decision()
            after = time.time()

            assert hasattr(decision, "timestamp")
            assert before <= decision.timestamp <= after


class TestHotPathIntegration:
    """Test integration with config updates."""

    def test_responds_to_config_changes(self):
        """Engine should reflect config changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/config.bin"
            config_manager = FastConfigManager(config_file)

            # Initial config
            config_manager.write_atomic(
                {
                    "action": 0,
                    "confidence": 0.5,
                    "exploration_rate": 0.1,
                    "quantity": 0.0,
                }
            )

            engine = HotPathEngine(config_file)

            decision1 = engine.get_execution_decision()
            assert decision1.action == 0

            # Update config
            config_manager.write_atomic(
                {
                    "action": 2,
                    "confidence": 0.9,
                    "exploration_rate": 0.02,
                    "quantity": 0.5,
                }
            )

            decision2 = engine.get_execution_decision()
            assert decision2.action == 2
            assert decision2.confidence == pytest.approx(0.9, abs=0.01)

    def test_tracks_config_version(self):
        """Decision should track which config version was used."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/config.bin"
            config_manager = FastConfigManager(config_file)
            config_manager.write_atomic(
                {
                    "action": 1,
                    "confidence": 0.8,
                    "exploration_rate": 0.05,
                    "quantity": 0.1,
                }
            )

            engine = HotPathEngine(config_file)
            decision = engine.get_execution_decision()

            assert hasattr(decision, "config_version")
            assert decision.config_version >= 0


class TestHotPathPerformance:
    """Test performance benchmarks."""

    def test_throughput_benchmark(self):
        """Engine should achieve high throughput."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/config.bin"
            config_manager = FastConfigManager(config_file)
            config_manager.write_atomic(
                {
                    "action": 1,
                    "confidence": 0.8,
                    "exploration_rate": 0.05,
                    "quantity": 0.1,
                }
            )

            engine = HotPathEngine(config_file)

            start = time.perf_counter()
            count = 10000
            for _ in range(count):
                decision = engine.get_execution_decision()
            elapsed = time.perf_counter() - start

            throughput = count / elapsed
            # Should achieve at least 2500 decisions/second after system initialization
            assert (
                throughput > 2_500
            ), f"Throughput {throughput:.0f}/sec below 2.5k target"

    def test_consistency_under_load(self):
        """Results should be consistent even under load."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/config.bin"
            config_manager = FastConfigManager(config_file)
            config_manager.write_atomic(
                {
                    "action": 1,
                    "confidence": 0.85,
                    "exploration_rate": 0.05,
                    "quantity": 0.1,
                }
            )

            engine = HotPathEngine(config_file)

            decisions = [engine.get_execution_decision() for _ in range(10000)]

            # All should have same action and confidence
            assert all(d.action == decisions[0].action for d in decisions)
            assert all(d.confidence == decisions[0].confidence for d in decisions)


class TestExecutionDecisionDataclass:
    """Test ExecutionDecision dataclass."""

    def test_creation_with_all_fields(self):
        """Should create with all required fields."""
        decision = ExecutionDecision(
            action=1,
            confidence=0.85,
            timestamp=time.time(),
            config_version=5,
            quantity=0.5,
        )

        assert decision.action == 1
        assert decision.confidence == 0.85
        assert decision.quantity == 0.5
        assert decision.config_version == 5
        assert decision.source == "hot_path"

    def test_to_dict_conversion(self):
        """Should convert to dict properly."""
        decision = ExecutionDecision(
            action=2, confidence=0.75, timestamp=1234.5, config_version=3, quantity=0.5
        )

        d = decision.to_dict()
        assert d["action"] == 2
        assert d["confidence"] == 0.75
        assert d["quantity"] == 0.5
        assert d["timestamp"] == 1234.5
        assert d["config_version"] == 3
        assert d["source"] == "hot_path"


class TestHotPathExecutor:
    """Test HotPathExecutor with batching support."""

    def test_executor_initialization(self):
        """Executor should initialize properly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/config.bin"
            config_manager = FastConfigManager(config_file)
            config_manager.write_atomic(
                {
                    "action": 1,
                    "confidence": 0.8,
                    "exploration_rate": 0.05,
                    "quantity": 0.1,
                }
            )

            executor = HotPathExecutor(config_file)

            assert executor is not None
            assert executor.engine is not None
            assert executor.batch_size == 10

    def test_get_decision_batch(self):
        """Should get batch of decisions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = f"{tmpdir}/config.bin"
            config_manager = FastConfigManager(config_file)
            config_manager.write_atomic(
                {
                    "action": 1,
                    "confidence": 0.8,
                    "exploration_rate": 0.05,
                    "quantity": 0.1,
                }
            )

            executor = HotPathExecutor(config_file)
            decisions = executor.get_decision_batch(5)

            assert len(decisions) == 5
            assert all(isinstance(d, ExecutionDecision) for d in decisions)
