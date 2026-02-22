"""
Circuit Breaker decorator voor MCP tools.

Usage:
    @circuit_breaker(failure_threshold=5, timeout_seconds=30)
    @mcp.tool()
    async def vedastro_generate_signal(params: dict) -> dict:
        ...
"""

import asyncio
import functools
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Optional, TypeVar

logger = logging.getLogger(__name__)
T = TypeVar("T")


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    failure_window_seconds: int = 60
    timeout_seconds: int = 30
    reset_timeout_seconds: int = 60
    half_open_requests: int = 3


class CircuitBreaker:
    """Circuit breaker state machine per tool."""
    
    _instances: dict = {}
    _lock = asyncio.Lock()
    
    def __new__(cls, name: str, config: CircuitBreakerConfig = None):
        if name not in cls._instances:
            cls._instances[name] = super().__new__(cls)
            cls._instances[name]._initialized = False
        return cls._instances[name]
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        if self._initialized:
            return
        
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state_change_time: Optional[datetime] = None
        self.half_open_request_count = 0
        self._initialized = True
        
        logger.info(f"CircuitBreaker '{name}' initialized in {self.state.value} state")
    
    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function through circuit breaker."""
        async with CircuitBreaker._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    logger.info(f"Circuit '{self.name}' transitioning to HALF_OPEN")
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    self.half_open_request_count = 0
                    self.state_change_time = datetime.utcnow()
                else:
                    raise CircuitBreakerOpenException(f"Circuit '{self.name}' is OPEN")
            
            if self.state == CircuitState.HALF_OPEN:
                if self.half_open_request_count >= self.config.half_open_requests:
                    raise CircuitBreakerOpenException(
                        f"Circuit '{self.name}' half-open limit reached"
                    )
                self.half_open_request_count += 1
        
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception:
            await self._on_failure()
            raise
    
    async def _on_success(self):
        async with CircuitBreaker._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= 2:
                    logger.info(f"Circuit '{self.name}' transitioning to CLOSED")
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
                    self.state_change_time = datetime.utcnow()
            elif self.state == CircuitState.CLOSED:
                self.failure_count = max(0, self.failure_count - 1)
    
    async def _on_failure(self):
        async with CircuitBreaker._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()
            
            if self.state == CircuitState.HALF_OPEN:
                logger.warning(f"Circuit '{self.name}' failed during recovery, reopening")
                self.state = CircuitState.OPEN
                self.state_change_time = datetime.utcnow()
            elif self.state == CircuitState.CLOSED:
                if self.failure_count >= self.config.failure_threshold:
                    logger.error(f"Circuit '{self.name}' opening after {self.failure_count} failures")
                    self.state = CircuitState.OPEN
                    self.state_change_time = datetime.utcnow()
    
    def _should_attempt_reset(self) -> bool:
        if not self.last_failure_time:
            return True
        elapsed = datetime.utcnow() - self.last_failure_time
        return elapsed >= timedelta(seconds=self.config.reset_timeout_seconds)
    
    def get_state(self) -> dict:
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
        }


class CircuitBreakerOpenException(Exception):
    """Raised when circuit breaker is open."""
    pass


def circuit_breaker(
    failure_threshold: int = 5,
    failure_window_seconds: int = 60,
    timeout_seconds: int = 30,
    reset_timeout_seconds: int = 60
):
    """
    Decorator for adding circuit breaker to MCP tools.
    
    Usage:
        @circuit_breaker(failure_threshold=3)
        @mcp.tool()
        async def my_tool(params: dict) -> dict:
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        breaker_name = f"cb_{func.__name__}"
        config = CircuitBreakerConfig(
            failure_threshold=failure_threshold,
            failure_window_seconds=failure_window_seconds,
            timeout_seconds=timeout_seconds,
            reset_timeout_seconds=reset_timeout_seconds
        )
        breaker = CircuitBreaker(breaker_name, config)
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await breaker.call(func, *args, **kwargs)
        
        # Attach circuit breaker to function for introspection
        wrapper._circuit_breaker = breaker
        return wrapper
    return decorator


def get_circuit_state(tool_name: str) -> Optional[dict]:
    """Get circuit breaker state for a tool."""
    breaker_name = f"cb_{tool_name}"
    if breaker_name in CircuitBreaker._instances:
        return CircuitBreaker._instances[breaker_name].get_state()
    return None
