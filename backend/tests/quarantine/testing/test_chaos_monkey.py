"""
Unit tests for ChaosMonkey (Sprint 4 S4-2).
"""

import asyncio
import os
from unittest.mock import patch

import pytest

from backend.testing.chaos.monkey import (
    ChaosMode,
    ChaosMonkey,
    get_chaos_monkey,
    reset_chaos_monkey,
)


class TestChaosMonkeyInitialization:
    """Test ChaosMonkey initialization."""

    def test_disabled_by_default(self):
        """Test that chaos is disabled by default."""
        with patch.dict(os.environ, {}, clear=True):
            monkey = ChaosMonkey()
            assert monkey.enabled is False
            assert monkey.mode == ChaosMode.DISABLED

    def test_enabled_in_testing_env(self):
        """Test that chaos enables in testing environment."""
        with patch.dict(os.environ, {"ENV": "testing"}):
            monkey = ChaosMonkey()
            assert monkey.enabled is True
            assert monkey.mode == ChaosMode.FULL

    def test_enabled_with_chaos_mode(self):
        """Test that chaos enables with CHAOS_MODE=1."""
        with patch.dict(os.environ, {"CHAOS_MODE": "1"}):
            monkey = ChaosMonkey()
            assert monkey.enabled is True

    def test_latency_mode(self):
        """Test latency-only mode."""
        with patch.dict(os.environ, {"CHAOS_MODE": "latency"}):
            monkey = ChaosMonkey()
            assert monkey.mode == ChaosMode.LATENCY

    def test_failure_mode(self):
        """Test failure-only mode."""
        with patch.dict(os.environ, {"CHAOS_MODE": "failure"}):
            monkey = ChaosMonkey()
            assert monkey.mode == ChaosMode.FAILURE


class TestChaosMonkeyLatency:
    """Test latency injection."""

    @pytest.mark.asyncio
    async def test_latency_injection(self):
        """Test that latency is injected when enabled."""
        monkey = ChaosMonkey(mode=ChaosMode.LATENCY)

        start = asyncio.get_event_loop().time()
        await monkey.inject_latency("test", delay_ms=50, probability=1.0)
        elapsed = asyncio.get_event_loop().time() - start

        assert elapsed >= 0.05  # At least 50ms

    @pytest.mark.asyncio
    async def test_latency_disabled_when_mode_mismatch(self):
        """Test that latency is not injected in wrong mode."""
        monkey = ChaosMonkey(mode=ChaosMode.FAILURE)

        start = asyncio.get_event_loop().time()
        await monkey.inject_latency("test", delay_ms=100, probability=1.0)
        elapsed = asyncio.get_event_loop().time() - start

        assert elapsed < 0.05  # Should be instant

    @pytest.mark.asyncio
    async def test_probability_zero(self):
        """Test that probability=0 prevents injection."""
        monkey = ChaosMonkey(mode=ChaosMode.LATENCY)

        start = asyncio.get_event_loop().time()
        await monkey.inject_latency("test", delay_ms=100, probability=0.0)
        elapsed = asyncio.get_event_loop().time() - start

        assert elapsed < 0.01  # Should be instant


class TestChaosMonkeyFailure:
    """Test service failure simulation."""

    def test_should_fail_service(self):
        """Test service failure determination."""
        monkey = ChaosMonkey(mode=ChaosMode.FAILURE)
        monkey._failure_probability = 1.0  # Force failure

        should_fail = monkey.should_fail_service("redis")
        assert should_fail is True

    def test_should_not_fail_when_disabled(self):
        """Test no failure when chaos disabled."""
        monkey = ChaosMonkey(mode=ChaosMode.DISABLED)

        should_fail = monkey.should_fail_service("redis")
        assert should_fail is False

    def test_should_not_fail_unknown_service(self):
        """Test no failure for unknown services."""
        monkey = ChaosMonkey(mode=ChaosMode.FAILURE)

        should_fail = monkey.should_fail_service("unknown_service")
        assert should_fail is False

    def test_simulate_service_failure_raises(self):
        """Test that failure simulation raises exception."""
        monkey = ChaosMonkey(mode=ChaosMode.FAILURE)
        monkey._failure_probability = 1.0  # Force failure

        with pytest.raises(ConnectionError) as exc_info:
            monkey.simulate_service_failure("redis")

        assert "ChaosMonkey" in str(exc_info.value)
        assert "redis" in str(exc_info.value)


class TestChaosMonkeyTattva:
    """Test Tattva disruption."""

    def test_disrupt_coherence(self):
        """Test coherence disruption."""
        monkey = ChaosMonkey(mode=ChaosMode.TATTVA)

        original = 0.85
        disrupted = monkey.disrupt_tattva_coherence(original, target_coherence=0.1)

        assert disrupted < original
        assert disrupted <= 0.1

    def test_no_disruption_when_disabled(self):
        """Test no disruption when chaos disabled."""
        monkey = ChaosMonkey(mode=ChaosMode.DISABLED)

        original = 0.85
        result = monkey.disrupt_tattva_coherence(original)

        assert result == original

    def test_no_disruption_in_wrong_mode(self):
        """Test no disruption in wrong chaos mode."""
        monkey = ChaosMonkey(mode=ChaosMode.LATENCY)

        original = 0.85
        result = monkey.disrupt_tattva_coherence(original)

        assert result == original


class TestChaosMonkeyWrap:
    """Test function wrapping."""

    @pytest.mark.asyncio
    async def test_wrap_async_with_latency(self):
        """Test async function wrapping with latency."""
        monkey = ChaosMonkey(mode=ChaosMode.LATENCY)

        async def test_func():
            return "success"

        wrapped = monkey.wrap_async(test_func, "test", latency_probability=1.0)

        start = asyncio.get_event_loop().time()
        result = await wrapped()
        elapsed = asyncio.get_event_loop().time() - start

        assert result == "success"
        assert elapsed >= 0.05  # Latency injected

    @pytest.mark.asyncio
    async def test_wrap_async_with_failure(self):
        """Test async function wrapping with failure."""
        monkey = ChaosMonkey(mode=ChaosMode.FAILURE)
        monkey._failure_probability = 1.0  # Force failure

        async def test_func():
            return "success"

        wrapped = monkey.wrap_async(test_func, "redis")

        with pytest.raises(ConnectionError):
            await wrapped()


class TestChaosMonkeyStats:
    """Test statistics and state."""

    def test_get_stats(self):
        """Test statistics retrieval."""
        monkey = ChaosMonkey(mode=ChaosMode.FULL)
        stats = monkey.get_stats()

        assert "enabled" in stats
        assert "mode" in stats
        assert "target_services" in stats
        assert stats["enabled"] is True

    def test_reset(self):
        """Test state reset."""
        monkey = ChaosMonkey(mode=ChaosMode.FAILURE)
        monkey._failure_probability = 1.0

        # Trigger a failure
        monkey.should_fail_service("redis")
        assert "redis" in monkey._injected_failures

        # Reset
        monkey.reset()
        assert len(monkey._injected_failures) == 0


class TestChaosMonkeyGlobal:
    """Test global instance management."""

    def test_get_chaos_monkey_singleton(self):
        """Test global singleton pattern."""
        reset_chaos_monkey()

        monkey1 = get_chaos_monkey()
        monkey2 = get_chaos_monkey()

        assert monkey1 is monkey2

    def test_reset_chaos_monkey(self):
        """Test global instance reset."""
        reset_chaos_monkey()

        monkey1 = get_chaos_monkey()
        reset_chaos_monkey()
        monkey2 = get_chaos_monkey()

        assert monkey1 is not monkey2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
