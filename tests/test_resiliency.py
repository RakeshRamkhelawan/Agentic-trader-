"""
Enterprise Resiliency Tests
Tests for circuit breakers, retry logic, and health checks
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from backend.core.resiliency import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    CircuitState,
    circuit_breaker,
    get_circuit_breaker_registry,
)
from backend.core.resiliency.retry import retry, RetryConfig


class TestCircuitBreaker:
    """Test suite for Circuit Breaker pattern"""

    @pytest.mark.asyncio
    async def test_circuit_starts_closed(self):
        """Circuit should start in CLOSED state"""
        cb = CircuitBreaker("test")
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_opens_after_failures(self):
        """Circuit should open after failure threshold"""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker("test", config)

        @cb.protect
        async def failing_operation():
            raise Exception("Test error")

        # First 3 failures
        for _ in range(3):
            with pytest.raises(Exception):
                await failing_operation()

        # Circuit should now be open
        assert cb.state == CircuitState.OPEN

        # Next call should fail fast with CircuitBreakerOpenError
        with pytest.raises(CircuitBreakerOpenError):
            await failing_operation()

    @pytest.mark.asyncio
    async def test_circuit_closes_after_recovery(self):
        """Circuit should close after successful recovery"""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=0.1,  # Fast for testing
            success_threshold=1
        )
        cb = CircuitBreaker("test", config)

        call_count = 0

        @cb.protect
        async def flaky_operation():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("Fail")
            return "success"

        # Fail twice to open circuit
        for _ in range(2):
            with pytest.raises(Exception):
                await flaky_operation()

        assert cb.state == CircuitState.OPEN

        # Wait for recovery timeout
        await asyncio.sleep(0.15)

        # Circuit should be half-open now
        # Next success should close it
        result = await flaky_operation()
        assert result == "success"
        assert cb.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_circuit_records_metrics(self):
        """Circuit should track metrics"""
        cb = CircuitBreaker("test")

        @cb.protect
        async def operation():
            return "ok"

        await operation()
        await operation()

        metrics = cb.get_metrics()
        assert metrics["name"] == "test"
        assert metrics["total_calls"] == 2
        assert metrics["total_successes"] == 2
        assert metrics["state"] == "closed"

    @pytest.mark.asyncio
    async def test_circuit_decorator(self):
        """Test decorator-style circuit breaker"""
        registry = get_circuit_breaker_registry()

        @circuit_breaker("my_service", failure_threshold=2)
        async def my_service_call():
            raise Exception("Service down")

        # Fail twice
        for _ in range(2):
            with pytest.raises(Exception):
                await my_service_call()

        # Check circuit is registered and open
        cb = registry.get("my_service")
        assert cb is not None
        assert cb.state == CircuitState.OPEN

    @pytest.mark.asyncio
    async def test_circuit_state_callback(self):
        """Test state change callback"""
        transitions = []

        def on_state_change(old: str, new: str):
            transitions.append((old, new))

        config = CircuitBreakerConfig(failure_threshold=1)
        cb = CircuitBreaker("test", config, on_state_change=on_state_change)

        @cb.protect
        async def failing_operation():
            raise Exception("Fail")

        with pytest.raises(Exception):
            await failing_operation()

        assert ("closed", "open") in transitions


class TestRetryLogic:
    """Test suite for retry logic"""

    @pytest.mark.asyncio
    async def test_retry_succeeds_eventually(self):
        """Retry should succeed on subsequent attempts"""
        call_count = 0

        @retry(max_attempts=3, base_delay=0.01)
        async def flaky_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception(f"Attempt {call_count} failed")
            return "success"

        result = await flaky_operation()
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_exhausts_attempts(self):
        """Retry should fail after max attempts"""
        call_count = 0

        @retry(max_attempts=2, base_delay=0.01)
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise Exception("Always fails")

        with pytest.raises(Exception):
            await always_fails()

        assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_respects_exception_types(self):
        """Retry should only retry specified exceptions"""
        call_count = 0

        @retry(max_attempts=3, base_delay=0.01, exceptions=(ValueError,))
        async def mixed_exceptions():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise TypeError("Should not retry")
            return "success"

        with pytest.raises(TypeError):
            await mixed_exceptions()

        assert call_count == 1  # Did not retry


class TestCircuitBreakerRegistry:
    """Test suite for Circuit Breaker Registry"""

    def test_registry_creates_breaker(self):
        """Registry should create and store circuit breaker"""
        registry = get_circuit_breaker_registry()

        cb = registry.register("test_service")
        assert cb.name == "test_service"

        # Should return same instance
        cb2 = registry.register("test_service")
        assert cb is cb2

    def test_registry_get_metrics(self):
        """Registry should aggregate metrics"""
        registry = get_circuit_breaker_registry()

        registry.register("service1")
        registry.register("service2")

        metrics = registry.get_all_metrics()
        assert "service1" in metrics
        assert "service2" in metrics

    @pytest.mark.asyncio
    async def test_registry_health_check(self):
        """Registry should provide health status"""
        registry = get_circuit_breaker_registry()

        cb = registry.register("healthy_service")

        health = await registry.health_check()
        assert "healthy_service" in health
        assert health["healthy_service"]["healthy"] is True
        assert health["healthy_service"]["state"] == "closed"


class TestIntegration:
    """Integration tests for resiliency patterns"""

    @pytest.mark.asyncio
    async def test_circuit_breaker_with_retry(self):
        """Circuit breaker and retry can work together"""
        cb = CircuitBreaker("integration_test", CircuitBreakerConfig(failure_threshold=5))

        call_count = 0
        fail_count = 0

        @cb.protect
        @retry(max_attempts=2, base_delay=0.01)
        async def protected_operation():
            nonlocal call_count, fail_count
            call_count += 1
            fail_count += 1
            if fail_count <= 1:  # Fail once, then succeed
                raise Exception("Transient error")
            return "success"

        # First call: retry succeeds on 2nd attempt
        result = await protected_operation()
        assert result == "success"
        assert call_count == 2  # Initial + 1 retry

        # Reset fail_count for second call
        fail_count = 0

        # Second call: retry pattern repeats
        result = await protected_operation()
        assert result == "success"
        assert call_count == 4  # 2 more calls (initial + 1 retry)
