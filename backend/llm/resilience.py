import logging
import time
from enum import Enum
from typing import Any, Callable

_logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service is back


class CircuitBreakerOpenException(Exception):
    pass


class CircuitBreaker:
    """
    Circuit Breaker pattern implementation.
    Prevents cascading failures when a service (e.g. DeepSeek) is down.
    """

    def __init__(
        self, name: str, failure_threshold: int = 5, recovery_timeout: int = 60
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Call usage: await breaker.call(client.chat.completions.create, messages=...)"""

        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                _logger.info(f"Circuit {self.name} checking recovery (HALF-OPEN)...")
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpenException(f"Circuit {self.name} is OPEN")

        try:
            result = await func(*args, **kwargs)

            if self.state == CircuitState.HALF_OPEN:
                _logger.info(f"Circuit {self.name} recovered (CLOSED).")
                self.state = CircuitState.CLOSED
                self.failure_count = 0

            return result

        except Exception as e:
            self._handle_failure()
            raise e

    def _handle_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()

        if (
            self.state == CircuitState.HALF_OPEN
            or self.failure_count >= self.failure_threshold
        ):
            if self.state != CircuitState.OPEN:
                _logger.error(f"Circuit {self.name} opened due to failures!")
                self.state = CircuitState.OPEN
