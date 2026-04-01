"""
Unit tests for FastConfig - Hot/Cold path configuration bridge.

TDD approach: Tests define the contract for FastConfig behavior.
"""

import os
import tempfile
import time
from pathlib import Path

import pytest

from backend.execution.fast_config import (
    ConfigSerializer,
    ConfigValidator,
    FastConfigManager,
)

pytestmark = pytest.mark.unit


class TestConfigSerializer:
    """Test binary serialization/deserialization of configuration."""

    def test_serialize_basic_config(self):
        """Should serialize config dict to binary format."""
        config = {
            "action": 1,
            "confidence": 0.85,
            "exploration_rate": 0.05,
            "quantity": 0.5,
        }

        serializer = ConfigSerializer()
        binary = serializer.serialize(config)

        assert isinstance(binary, bytes)
        assert len(binary) == ConfigSerializer.SIZE

    def test_deserialize_binary_config(self):
        """Should deserialize binary back to dict."""
        config = {
            "action": 2,
            "confidence": 0.72,
            "exploration_rate": 0.08,
            "quantity": 10.5,
        }

        serializer = ConfigSerializer()
        binary = serializer.serialize(config)

        restored, version = serializer.deserialize(binary)

        assert restored["action"] == 2
        assert abs(restored["confidence"] - 0.72) < 0.01
        assert abs(restored["exploration_rate"] - 0.08) < 0.01
        assert abs(restored["quantity"] - 10.5) < 0.01

    def test_serialization_preserves_types(self):
        """Serialization should preserve integer and float types."""
        config = {
            "action": 0,
            "confidence": 0.5,
            "exploration_rate": 0.1,
            "quantity": 1.0,
        }
        serializer = ConfigSerializer()
        binary = serializer.serialize(config)
        restored, version = serializer.deserialize(binary)

        assert isinstance(restored["action"], int)
        assert isinstance(restored["confidence"], float)
        assert isinstance(restored["exploration_rate"], float)
        assert isinstance(restored["quantity"], float)

    def test_serialization_handles_edge_cases(self):
        """Should handle edge values (0, 1, boundary values)."""
        edge_cases = [
            {"action": 0, "confidence": 0.0, "exploration_rate": 0.0, "quantity": 0.0},
            {
                "action": 2,
                "confidence": 1.0,
                "exploration_rate": 1.0,
                "quantity": 1000.0,
            },
            {
                "action": 1,
                "confidence": 0.5,
                "exploration_rate": 0.5,
                "quantity": 0.0001,
            },
        ]

        serializer = ConfigSerializer()
        for config in edge_cases:
            binary = serializer.serialize(config)
            restored, version = serializer.deserialize(binary)
            assert restored["action"] == config["action"]
            assert abs(restored["confidence"] - config["confidence"]) < 0.01


class TestFastConfigManager:
    """Test memory-mapped configuration manager."""

    @pytest.fixture
    def temp_config_file(self):
        """Create temporary config file."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as f:
            temp_path = f.name
        # Delete it so FastConfigManager can create fresh
        os.unlink(temp_path)
        yield temp_path
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_manager_initialization(self, temp_config_file):
        """FastConfigManager should initialize with file path."""
        manager = FastConfigManager(temp_config_file)
        assert manager.config_path == Path(temp_config_file)
        assert os.path.exists(temp_config_file)  # Should create file

    def test_write_config_atomically(self, temp_config_file):
        """Should write config atomically (all or nothing)."""
        config = {
            "action": 1,
            "confidence": 0.9,
            "exploration_rate": 0.05,
            "quantity": 1.0,
        }

        manager = FastConfigManager(temp_config_file)
        manager.write_atomic(config)

        # File should exist and contain valid data
        assert os.path.exists(temp_config_file)
        assert os.path.getsize(temp_config_file) > 0

    def test_read_config_fast(self, temp_config_file):
        """Should read config quickly."""
        config = {
            "action": 2,
            "confidence": 0.75,
            "exploration_rate": 0.1,
            "quantity": 0.5,
        }

        manager = FastConfigManager(temp_config_file)
        manager.write_atomic(config)

        # Read should be fast
        read_config, version = manager.read_fast()
        assert read_config["action"] == 2
        assert abs(read_config["confidence"] - 0.75) < 0.01

    def test_multiple_writes_are_atomic(self, temp_config_file):
        """Multiple writes should not corrupt file (atomicity)."""
        manager = FastConfigManager(temp_config_file)

        configs = [
            {"action": 1, "confidence": 0.8, "exploration_rate": 0.05, "quantity": 0.1},
            {
                "action": 2,
                "confidence": 0.85,
                "exploration_rate": 0.06,
                "quantity": 0.2,
            },
            {"action": 0, "confidence": 0.9, "exploration_rate": 0.04, "quantity": 0.0},
        ]

        for config in configs:
            manager.write_atomic(config)

        # Last config should be readable
        # Last config should be readable
        final, version = manager.read_fast()
        assert final["action"] == 0
        assert abs(final["confidence"] - 0.9) < 0.01

    def test_read_during_write_isolation(self, temp_config_file):
        """Reader should not see partial writes (isolation)."""
        manager = FastConfigManager(temp_config_file)

        # Write initial config
        # Write initial config
        initial = {
            "action": 1,
            "confidence": 0.8,
            "exploration_rate": 0.05,
            "quantity": 0.1,
        }
        manager.write_atomic(initial)

        # Reader always sees consistent state
        # Reader always sees consistent state
        for _ in range(5):
            read_config, version = manager.read_fast()
            # Should see valid config, never partial
            assert "action" in read_config
            assert "confidence" in read_config


class TestFastConfigHotPath:
    """Test hot path optimization - ultra-low latency reads."""

    @pytest.fixture
    def fast_config_manager(self, tmp_path):
        """Create FastConfigManager with temp file."""
        config_file = tmp_path / "config.bin"
        manager = FastConfigManager(str(config_file))
        return manager

    def test_hot_path_latency_reasonable(self, fast_config_manager):
        """Hot path read should be reasonably fast."""
        fast_config_manager.write_atomic(
            {"action": 1, "confidence": 0.9, "exploration_rate": 0.05, "quantity": 1.0}
        )

        # Measure read latency
        times = []
        for _ in range(100):
            start = time.perf_counter()
            config, version = fast_config_manager.read_fast()
            elapsed = time.perf_counter() - start
            times.append(elapsed)

        # Average should be reasonable (<1ms)
        avg_latency = sum(times) / len(times)
        assert avg_latency < 0.001  # <1ms
        assert config["action"] == 1

    def test_fallback_on_unreadable_file(self, tmp_path):
        """Hot path should fallback if file unreadable."""
        config_file = tmp_path / "config.bin"
        manager = FastConfigManager(str(config_file))

        # Write initial config
        manager.write_atomic(
            {"action": 1, "confidence": 0.8, "exploration_rate": 0.05, "quantity": 0.1}
        )

        # Delete file to simulate error
        os.unlink(str(config_file))

        # Should return fallback
        # Should return fallback
        config, version = manager.read_fast()
        assert config is not None
        assert "action" in config


class TestFastConfigColdPath:
    """Test cold path - LLM agents updating config."""

    @pytest.fixture
    def fast_config_manager(self, tmp_path):
        """Create FastConfigManager with temp file."""
        config_file = tmp_path / "config.bin"
        manager = FastConfigManager(str(config_file))
        return manager

    def test_cold_path_write_reasonably_fast(self, fast_config_manager):
        """Cold path write should complete quickly (<100ms)."""
        config = {
            "action": 1,
            "confidence": 0.85,
            "exploration_rate": 0.05,
            "quantity": 0.5,
        }

        start = time.time()
        fast_config_manager.write_atomic(config)
        elapsed = time.time() - start

        assert elapsed < 0.1  # <100ms

    def test_version_increments_on_write(self, fast_config_manager):
        """Version should increment with each write."""
        v1 = fast_config_manager.get_version()

        fast_config_manager.write_atomic(
            {"action": 1, "confidence": 0.8, "exploration_rate": 0.05, "quantity": 0.1}
        )
        v2 = fast_config_manager.get_version()

        fast_config_manager.write_atomic(
            {"action": 2, "confidence": 0.85, "exploration_rate": 0.06, "quantity": 0.2}
        )
        v3 = fast_config_manager.get_version()

        assert v2 > v1
        assert v3 > v2


class TestConfigSchemaValidation:
    """Test config schema and validation."""

    def test_required_fields_enforced(self):
        """Config must have all required fields."""
        with pytest.raises(KeyError):
            ConfigValidator.validate({"action": 1})  # Missing confidence, exploration_rate

    def test_field_types_validated(self):
        """Config fields must have correct types."""
        # Wrong type for action (should be int)
        with pytest.raises(TypeError):
            ConfigValidator.validate(
                {
                    "action": "buy",
                    "confidence": 0.9,
                    "exploration_rate": 0.05,
                    "quantity": 0.1,
                }
            )

        # Wrong type for confidence (should be float)
        with pytest.raises(TypeError):
            ConfigValidator.validate(
                {
                    "action": 1,
                    "confidence": "high",
                    "exploration_rate": 0.05,
                    "quantity": 0.1,
                }
            )

    def test_field_value_ranges(self):
        """Config fields must be in valid ranges."""
        # action should be 0-2
        with pytest.raises(ValueError):
            ConfigValidator.validate(
                {
                    "action": -1,
                    "confidence": 0.9,
                    "exploration_rate": 0.05,
                    "quantity": 0.1,
                }
            )

        # confidence should be 0-1
        with pytest.raises(ValueError):
            ConfigValidator.validate(
                {
                    "action": 1,
                    "confidence": 1.5,
                    "exploration_rate": 0.05,
                    "quantity": 0.1,
                }
            )

        # exploration_rate should be 0-1
        with pytest.raises(ValueError):
            ConfigValidator.validate(
                {
                    "action": 1,
                    "confidence": 0.9,
                    "exploration_rate": -0.1,
                    "quantity": 0.1,
                }
            )

    def test_valid_config_passes(self):
        """Valid configs should pass validation."""
        valid_configs = [
            {"action": 0, "confidence": 0.0, "exploration_rate": 0.0, "quantity": 0.0},
            {"action": 1, "confidence": 0.5, "exploration_rate": 0.5, "quantity": 0.5},
            {"action": 2, "confidence": 1.0, "exploration_rate": 1.0, "quantity": 1.0},
        ]

        for config in valid_configs:
            ConfigValidator.validate(config)  # Should not raise


class TestFastConfigIntegration:
    """Integration tests - FastConfig with hot/cold paths."""

    def test_hot_path_reads_cold_path_writes(self, tmp_path):
        """Hot path should immediately see cold path writes."""
        config_file = tmp_path / "config.bin"
        manager = FastConfigManager(str(config_file))

        # Cold path writes config
        cold_config = {
            "action": 2,
            "confidence": 0.88,
            "exploration_rate": 0.07,
            "quantity": 0.5,
        }
        manager.write_atomic(cold_config)

        # Hot path reads immediately
        # Hot path reads immediately
        hot_config, version = manager.read_fast()
        assert hot_config["action"] == 2
        assert abs(hot_config["confidence"] - 0.88) < 0.01

    def test_config_fallback_on_error(self, tmp_path):
        """Hot path should have fallback config if file unreadable."""
        manager = FastConfigManager(str(tmp_path / "config.bin"))

        # Get fallback
        fallback = manager.get_fallback_config()

        # Fallback should be valid
        assert "action" in fallback
        assert fallback["action"] in [0, 1, 2]

    def test_config_versioning(self, tmp_path):
        """Config should have version for consistency checks."""
        config_file = tmp_path / "config.bin"
        manager = FastConfigManager(str(config_file))

        config1 = {
            "action": 1,
            "confidence": 0.8,
            "exploration_rate": 0.05,
            "quantity": 0.1,
        }
        manager.write_atomic(config1)
        version1 = manager.get_version()

        config2 = {
            "action": 2,
            "confidence": 0.85,
            "exploration_rate": 0.06,
            "quantity": 0.2,
        }
        manager.write_atomic(config2)
        version2 = manager.get_version()

        assert version2 > version1


class TestFastConfigPerformance:
    """Performance benchmarks for FastConfig."""

    def test_serialization_efficiency(self):
        """Serialized config should be small."""
        config = {
            "action": 1,
            "confidence": 0.85,
            "exploration_rate": 0.05,
            "quantity": 0.5,
        }
        serializer = ConfigSerializer()
        binary = serializer.serialize(config)

        # Binary should be exactly 13 bytes (version:4 + action:1 + confidence:4 + exploration_rate:4)
        assert len(binary) == ConfigSerializer.SIZE
        assert len(binary) < 100  # Very compact

    def test_binary_round_trip_precision(self):
        """Binary serialization should preserve precision."""
        configs = [
            {"action": 0, "confidence": 0.0, "exploration_rate": 0.0, "quantity": 0.0},
            {
                "action": 1,
                "confidence": 0.333,
                "exploration_rate": 0.667,
                "quantity": 0.333,
            },
            {
                "action": 2,
                "confidence": 1.0,
                "exploration_rate": 1.0,
                "quantity": 100.0,
            },
        ]

        serializer = ConfigSerializer()
        for original in configs:
            binary = serializer.serialize(original)
            restored, version = serializer.deserialize(binary)

            # Float precision should be within 1%
            assert abs(restored["confidence"] - original["confidence"]) < 0.001
            assert abs(restored["exploration_rate"] - original["exploration_rate"]) < 0.001


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
