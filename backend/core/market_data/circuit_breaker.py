import time
from enum import Enum
from typing import Any, Dict


class CircuitState(str, Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit is broken (failures exceed threshold)
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """
    Protects the system from cascading failures by stopping requests
    when error rates exceed a threshold.
    """

    def __init__(
        self,
        name: str,
        fail_threshold: int = 5,
        recovery_timeout: float = 60.0,
    ):
        self.name = name
        self.fail_threshold = fail_threshold
        self.recovery_timeout = recovery_timeout

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.last_success_time = 0.0

    async def record_failure(self):
        """Record a failure and potentially trip the circuit."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.CLOSED:
            if self.failure_count >= self.fail_threshold:
                self._trip_circuit()
        elif self.state == CircuitState.HALF_OPEN:
            # If we fail in half-open, trip immediately
            self._trip_circuit()

    async def record_success(self):
        """Record a success and potentially close the circuit."""
        self.last_success_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            self._close_circuit()
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success in closed state (optional, or rely on time decay)
            self.failure_count = 0

    def _trip_circuit(self):
        """Transition to OPEN state."""
        self.state = CircuitState.OPEN
        print(
            f"Content-Type: application/json\n\nCircuit {self.name} TRIPPED to OPEN state."
        )

    def _close_circuit(self):
        """Transition back to CLOSED state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        print(
            f"Content-Type: application/json\n\nCircuit {self.name} CLOSED (Recovered)."
        )

    def allow_request(self) -> bool:
        """Check if request is allowed."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                print(f"Circuit {self.name} transitioned to HALF-OPEN.")
                return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            # Only allow one probe request (or limited rate)
            # For simplicity, we allow it, but next failure trips it back
            return True

        return False

    def get_status(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time,
        }
