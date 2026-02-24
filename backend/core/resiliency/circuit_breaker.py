"""
Enterprise Circuit Breaker Pattern for LLM and External Services
Prevents cascade failures by failing fast when services are unhealthy
"""

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from functools import wraps
from typing import TypeVar

logger = logging.getLogger("CircuitBreaker")
T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""

    failure_threshold: int = 5  # Failures before opening
    recovery_timeout: float = 30.0  # Seconds before half-open
    half_open_max_calls: int = 3  # Test calls in half-open
    success_threshold: int = 2  # Successes to close


class CircuitBreaker:
    """
    Enterprise Circuit Breaker implementation

    Usage:
        cb = CircuitBreaker("openai", CircuitBreakerConfig())

        @cb.protect
        async def call_llm(prompt: str) -> str:
            return await openai_client.chat.completions.create(...)
    """

    def __init__(
        self,
        name: str,
        config: CircuitBreakerConfig | None = None,
        on_state_change: Callable[[str, str], None] | None = None,
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.on_state_change = on_state_change

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float | None = None
        self._half_open_calls = 0
        self._lock = asyncio.Lock()

        # Metrics
        self.total_calls = 0
        self.total_failures = 0
        self.total_successes = 0
        self.total_rejected = 0

        logger.info(f"[{self.name}] CircuitBreaker initialized (state: {self._state.value})")

    @property
    def state(self) -> CircuitState:
        return self._state

    @property
    def state_label(self) -> str:
        return self._state.value

    def _transition_to(self, new_state: CircuitState):
        """Transition to new state with callback"""
        old_state = self._state
        self._state = new_state

        logger.warning(
            f"[{self.name}] Circuit transitioned: {old_state.value} -> {new_state.value}"
        )

        if self.on_state_change:
            try:
                self.on_state_change(old_state.value, new_state.value)
            except Exception as e:
                logger.error(f"[{self.name}] State change callback failed: {e}")

        # Reset counters on transition
        if new_state == CircuitState.CLOSED:
            self._failure_count = 0
            self._success_count = 0
            self._half_open_calls = 0
        elif new_state == CircuitState.OPEN:
            self._half_open_calls = 0
            self._success_count = 0
        elif new_state == CircuitState.HALF_OPEN:
            self._failure_count = 0
            self._half_open_calls = 0

    async def _can_execute(self) -> bool:
        """Check if request can be executed"""
        async with self._lock:
            if self._state == CircuitState.CLOSED:
                return True

            if self._state == CircuitState.OPEN:
                # Check if recovery timeout passed
                if self._last_failure_time:
                    elapsed = time.time() - self._last_failure_time
                    if elapsed >= self.config.recovery_timeout:
                        logger.info(f"[{self.name}] Recovery timeout passed, entering HALF_OPEN")
                        self._transition_to(CircuitState.HALF_OPEN)
                        return True

                self.total_rejected += 1
                return False

            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls < self.config.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
                return False

            return True

    async def _record_success(self):
        """Record successful call"""
        async with self._lock:
            self.total_successes += 1

            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    logger.info(f"[{self.name}] Success threshold reached, closing circuit")
                    self._transition_to(CircuitState.CLOSED)
            else:
                # Reset failure count on success in CLOSED state
                self._failure_count = 0

    async def _record_failure(self):
        """Record failed call"""
        async with self._lock:
            self.total_failures += 1
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                logger.warning(f"[{self.name}] Failure in HALF_OPEN, opening circuit")
                self._transition_to(CircuitState.OPEN)
            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.config.failure_threshold:
                    logger.warning(f"[{self.name}] Failure threshold reached, opening circuit")
                    self._transition_to(CircuitState.OPEN)

    def protect(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator to protect function with circuit breaker"""

        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            self.total_calls += 1

            if not await self._can_execute():
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN - service unavailable"
                )

            try:
                result = await func(*args, **kwargs)
                await self._record_success()
                return result
            except Exception:
                await self._record_failure()
                raise

        return async_wrapper

    def get_metrics(self) -> dict:
        """Get circuit breaker metrics"""
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "half_open_calls": self._half_open_calls,
            "total_calls": self.total_calls,
            "total_failures": self.total_failures,
            "total_successes": self.total_successes,
            "total_rejected": self.total_rejected,
            "last_failure_time": self._last_failure_time,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "half_open_max_calls": self.config.half_open_max_calls,
                "success_threshold": self.config.success_threshold,
            },
        }


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""

    pass


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers"""

    def __init__(self):
        self._breakers: dict[str, CircuitBreaker] = {}

    def register(self, name: str, config: CircuitBreakerConfig | None = None) -> CircuitBreaker:
        """Register a new circuit breaker"""
        if name in self._breakers:
            logger.warning(f"Circuit breaker '{name}' already registered, returning existing")
            return self._breakers[name]

        breaker = CircuitBreaker(name, config)
        self._breakers[name] = breaker
        return breaker

    def get(self, name: str) -> CircuitBreaker | None:
        """Get circuit breaker by name"""
        return self._breakers.get(name)

    def get_all_metrics(self) -> dict:
        """Get metrics for all circuit breakers"""
        return {name: breaker.get_metrics() for name, breaker in self._breakers.items()}

    async def health_check(self) -> dict:
        """Health check for all circuit breakers"""
        results = {}
        for name, breaker in self._breakers.items():
            state = breaker.state
            results[name] = {
                "healthy": state == CircuitState.CLOSED,
                "state": state.value,
                "degraded": state == CircuitState.HALF_OPEN,
                "unhealthy": state == CircuitState.OPEN,
            }
        return results


# Global registry
_registry = CircuitBreakerRegistry()


def get_circuit_breaker_registry() -> CircuitBreakerRegistry:
    """Get the global circuit breaker registry"""
    return _registry


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 30.0,
    half_open_max_calls: int = 3,
    success_threshold: int = 2,
):
    """
    Decorator to apply circuit breaker to a function

    Usage:
        @circuit_breaker("openai", failure_threshold=3)
        async def call_openai(prompt: str) -> str:
            ...
    """
    config = CircuitBreakerConfig(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        half_open_max_calls=half_open_max_calls,
        success_threshold=success_threshold,
    )

    breaker = _registry.register(name, config)
    return breaker.protect
