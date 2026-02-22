# ToolBroker Implementatie Guide

> **Agentic Trader Platform V18**
> **Step-by-Step Technical Implementation**
> **Status**: Ready for Development

---

## 1. Quick Start Checklist

### Pre-requisites
- [ ] Python 3.13+ geïnstalleerd
- [ ] Huidige V17 build draait zonder errors
- [ ] Alle V17 tests passing
- [ ] Git branch `feature/v18-toolbroker` aangemaakt

### Files Created
```
docs/
├── TOOLBROKER_ARCHITECTURE_AUDIT.md    # Architecture overview
├── PRD_TOOLBROKER_V18.md               # Detailed PRD
└── TOOLBROKER_IMPLEMENTATION_GUIDE.md  # This file
```

---

## 2. Project Structuur

### 2.1 Nieuwe Directory Structuur
```
backend/
├── core/
│   └── tool_broker/                    # NIEUW
│       ├── __init__.py
│       ├── broker.py                   # Core ToolBroker class
│       ├── circuit_breaker.py          # Circuit breaker implementation
│       ├── retry.py                    # Retry engine
│       ├── registry.py                 # Tool registry
│       ├── schemas.py                  # Pydantic models
│       ├── mcp_adapter.py              # MCP protocol handling
│       ├── exceptions.py               # Custom exceptions
│       └── metrics.py                  # Metrics collection
│
├── tools/                              # NIEUW - Tool implementations
│   ├── __init__.py
│   ├── base.py                         # Base tool class
│   ├── registry.py                     # Tool registry decorator
│   │
│   ├── vedastro/                       # VedAstro tools
│   │   ├── __init__.py
│   │   ├── server.py                   # MCP server wrapper
│   │   └── tools.py                    # VedAstro tool implementations
│   │
│   ├── elemental/                      # Elemental tools
│   │   ├── __init__.py
│   │   ├── server.py
│   │   ├── fire_tools.py               # Position sizing
│   │   ├── earth_tools.py              # Entry/exit checks
│   │   ├── water_tools.py              # Regime detection
│   │   └── ether_tools.py              # Consensus
│   │
│   ├── data/                           # Data tools
│   │   ├── __init__.py
│   │   ├── server.py
│   │   └── market_data_tools.py
│   │
│   └── execution/                      # Execution tools
│       ├── __init__.py
│       ├── server.py
│       └── paper_trading_tools.py
│
└── api/
    └── toolbroker_api.py               # NIEUW - API endpoints
```

---

## 3. Stap-voor-Stap Implementatie

### Stap 1: Basis Structuur (30 min)

#### 1.1 Creëer directories
```bash
mkdir -p backend/core/tool_broker
mkdir -p backend/tools/vedastro
mkdir -p backend/tools/elemental
mkdir -p backend/tools/data
mkdir -p backend/tools/execution
touch backend/core/tool_broker/__init__.py
touch backend/tools/__init__.py
```

#### 1.2 Initiële `__init__.py` files
```python
# backend/core/tool_broker/__init__.py
"""ToolBroker - MCP-enabled tool orchestration for Agentic Trader Platform."""

from .broker import ToolBroker
from .schemas import ToolExecutionRequest, ToolExecutionResponse
from .exceptions import ToolBrokerException, CircuitBreakerOpenException

__all__ = [
    "ToolBroker",
    "ToolExecutionRequest",
    "ToolExecutionResponse",
    "ToolBrokerException",
    "CircuitBreakerOpenException",
]

__version__ = "1.0.0"
```

---

### Stap 2: Exceptions (15 min)

```python
# backend/core/tool_broker/exceptions.py
"""ToolBroker exception hierarchy."""


class ToolBrokerException(Exception):
    """Base exception for ToolBroker."""

    def __init__(self, message: str, original_error: Exception = None):
        super().__init__(message)
        self.message = message
        self.original_error = original_error


class CircuitBreakerOpenException(ToolBrokerException):
    """Raised when circuit breaker is open."""

    def __init__(self, tool_name: str, original_error: Exception = None):
        super().__init__(
            f"Circuit breaker is OPEN for tool '{tool_name}'",
            original_error
        )
        self.tool_name = tool_name


class ToolExecutionException(ToolBrokerException):
    """Raised when tool execution fails."""

    def __init__(self, tool_name: str, error_detail: str, original_error: Exception = None):
        super().__init__(
            f"Tool '{tool_name}' execution failed: {error_detail}",
            original_error
        )
        self.tool_name = tool_name
        self.error_detail = error_detail


class ToolNotFoundException(ToolBrokerException):
    """Raised when tool is not in registry."""

    def __init__(self, tool_name: str):
        super().__init__(f"Tool '{tool_name}' not found in registry")
        self.tool_name = tool_name


class MCPConnectionException(ToolBrokerException):
    """Raised when MCP connection fails."""

    def __init__(self, server_name: str, original_error: Exception = None):
        super().__init__(
            f"MCP connection to '{server_name}' failed",
            original_error
        )
        self.server_name = server_name


class RetryExhaustedException(ToolBrokerException):
    """Raised when all retry attempts are exhausted."""

    def __init__(self, tool_name: str, attempts: int, original_error: Exception = None):
        super().__init__(
            f"Tool '{tool_name}' failed after {attempts} retry attempts",
            original_error
        )
        self.tool_name = tool_name
        self.attempts = attempts
```

---

### Stap 3: Schemas (20 min)

```python
# backend/core/tool_broker/schemas.py
"""Pydantic schemas for ToolBroker."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CircuitBreakerState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class ToolExecutionRequest(BaseModel):
    """Request to execute a tool."""

    tool_name: str = Field(
        ...,
        description="Tool name in format 'server__tool_name'",
        examples=["vedastro__generate_signal"]
    )
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Tool parameters"
    )
    timeout_seconds: Optional[int] = Field(
        default=30,
        ge=1,
        le=300,
        description="Execution timeout"
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Optional request ID for tracing"
    )

    @field_validator("tool_name")
    @classmethod
    def validate_tool_name(cls, v: str) -> str:
        if "__" not in v:
            raise ValueError("Tool name must be in format 'server__tool_name'")
        return v

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "tool_name": "vedastro__generate_signal",
            "params": {"symbol": "AAPL", "current_price": 185.50},
            "timeout_seconds": 30,
            "request_id": "req_12345"
        }
    })


class ToolExecutionResponse(BaseModel):
    """Response from tool execution."""

    success: bool = Field(..., description="Whether execution succeeded")
    result: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Tool result on success"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message on failure"
    )
    execution_time_ms: float = Field(
        ...,
        ge=0,
        description="Execution duration in milliseconds"
    )
    circuit_breaker_state: Optional[CircuitBreakerState] = Field(
        default=None,
        description="Circuit breaker state after execution"
    )
    retry_count: int = Field(
        default=0,
        ge=0,
        description="Number of retry attempts"
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Request ID for tracing"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response timestamp"
    )


class ToolInfo(BaseModel):
    """Information about a registered tool."""

    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    version: str = Field(default="1.0.0", description="Tool version")
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parameter schema"
    )
    returns: Dict[str, Any] = Field(
        default_factory=dict,
        description="Return schema"
    )
    circuit_state: CircuitBreakerState = Field(
        default=CircuitBreakerState.CLOSED,
        description="Current circuit breaker state"
    )
    execution_count: int = Field(
        default=0,
        description="Total execution count"
    )
    success_rate: float = Field(
        default=1.0,
        ge=0,
        le=1,
        description="Success rate (0-1)"
    )
    avg_latency_ms: float = Field(
        default=0,
        ge=0,
        description="Average latency in milliseconds"
    )


class CircuitBreakerConfig(BaseModel):
    """Configuration for circuit breaker."""

    failure_threshold: int = Field(default=5, ge=1, description="Failures before opening")
    failure_window_seconds: int = Field(default=60, ge=1, description="Window for failure count")
    timeout_seconds: int = Field(default=30, ge=1, description="Reset timeout")
    reset_timeout_seconds: int = Field(default=60, ge=1, description="Time before half-open")
    half_open_requests: int = Field(default=3, ge=1, description="Requests in half-open state")


class RetryConfig(BaseModel):
    """Configuration for retry mechanism."""

    max_attempts: int = Field(default=3, ge=1, description="Maximum retry attempts")
    initial_delay_ms: int = Field(default=100, ge=0, description="Initial delay")
    max_delay_ms: int = Field(default=10000, ge=0, description="Maximum delay")
    backoff_factor: float = Field(default=2.0, ge=1.0, description="Backoff multiplier")
    jitter_enabled: bool = Field(default=True, description="Add random jitter")


class ResilienceMetrics(BaseModel):
    """Resilience metrics."""

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    circuit_breaker_opens: int = 0
    circuit_breaker_resets: int = 0
    total_retry_attempts: int = 0
    successful_retries: int = 0

    @property
    def success_rate(self) -> float:
        if self.total_calls == 0:
            return 1.0
        return self.successful_calls / self.total_calls

    @property
    def retry_success_rate(self) -> float:
        if self.total_retry_attempts == 0:
            return 0.0
        return self.successful_retries / self.total_retry_attempts


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Overall status: healthy/degraded/unhealthy")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    service_name: str = Field(default="ToolBroker")
    version: str = Field(default="1.0.0")
    components: Dict[str, str] = Field(default_factory=dict)
    metrics: Optional[ResilienceMetrics] = None
```

---

### Stap 4: Circuit Breaker (30 min)

```python
# backend/core/tool_broker/circuit_breaker.py
"""Circuit breaker implementation for failure isolation."""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, Optional, TypeVar

from .schemas import CircuitBreakerConfig, CircuitBreakerState

logger = logging.getLogger(__name__)
T = TypeVar("T")


class CircuitBreaker:
    """
    Circuit breaker for failure isolation.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Service failing, requests rejected immediately
    - HALF_OPEN: Testing if service recovered, limited requests allowed
    """

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state_change_time: Optional[datetime] = None
        self.half_open_request_count = 0
        self.lock = asyncio.Lock()

        logger.info(f"Circuit breaker '{name}' initialized in {self.state.value} state")

    async def call(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """Execute function through circuit breaker."""
        async with self.lock:
            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    logger.info(f"Circuit '{self.name}' transitioning to HALF_OPEN")
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.success_count = 0
                    self.half_open_request_count = 0
                    self.state_change_time = datetime.utcnow()
                else:
                    raise CircuitBreakerOpenException(
                        f"Circuit breaker '{self.name}' is OPEN"
                    )

            if self.state == CircuitBreakerState.HALF_OPEN:
                if self.half_open_request_count >= self.config.half_open_requests:
                    raise CircuitBreakerOpenException(
                        f"Circuit '{self.name}' half-open request limit reached"
                    )
                self.half_open_request_count += 1

        # Execute outside lock
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise

    async def _on_success(self):
        """Handle successful call."""
        async with self.lock:
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= 2:  # Configurable threshold
                    logger.info(f"Circuit '{self.name}' transitioning to CLOSED")
                    self.state = CircuitBreakerState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
                    self.state_change_time = datetime.utcnow()
            elif self.state == CircuitBreakerState.CLOSED:
                self.failure_count = 0

    async def _on_failure(self):
        """Handle failed call."""
        async with self.lock:
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()

            if self.state == CircuitBreakerState.HALF_OPEN:
                logger.warning(f"Circuit '{self.name}' failed during recovery, reopening")
                self.state = CircuitBreakerState.OPEN
                self.state_change_time = datetime.utcnow()
            elif self.state == CircuitBreakerState.CLOSED:
                if self.failure_count >= self.config.failure_threshold:
                    logger.error(
                        f"Circuit '{self.name}' threshold reached ({self.failure_count}), "
                        "opening circuit"
                    )
                    self.state = CircuitBreakerState.OPEN
                    self.state_change_time = datetime.utcnow()

    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt to reset."""
        if not self.last_failure_time:
            return True
        elapsed = datetime.utcnow() - self.last_failure_time
        return elapsed >= timedelta(seconds=self.config.reset_timeout_seconds)

    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "state_change_time": self.state_change_time.isoformat() if self.state_change_time else None,
            "half_open_requests": self.half_open_request_count,
        }


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers."""

    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()

    async def get_or_create(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """Get or create a circuit breaker."""
        async with self._lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(name, config)
            return self._breakers[name]

    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name."""
        return self._breakers.get(name)

    def get_all_states(self) -> Dict[str, Dict[str, Any]]:
        """Get states of all circuit breakers."""
        return {name: breaker.get_state() for name, breaker in self._breakers.items()}

    async def reset_all(self):
        """Reset all circuit breakers to CLOSED."""
        async with self._lock:
            for breaker in self._breakers.values():
                breaker.state = CircuitBreakerState.CLOSED
                breaker.failure_count = 0
                breaker.success_count = 0


class CircuitBreakerOpenException(Exception):
    """Raised when circuit breaker is open."""
    pass
```

---

### Stap 5: Retry Engine (20 min)

```python
# backend/core/tool_broker/retry.py
"""Retry mechanism with exponential backoff."""

import asyncio
import logging
import random
from typing import Any, Callable, Optional, TypeVar

from .exceptions import RetryExhaustedException
from .schemas import RetryConfig

logger = logging.getLogger(__name__)
T = TypeVar("T")


async def async_retry(
    func: Callable[..., Any],
    *args,
    config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable[[int, Exception], Any]] = None,
    **kwargs
) -> Any:
    """
    Execute async function with retry logic.

    Args:
        func: Async function to execute
        config: Retry configuration
        on_retry: Optional callback on retry (attempt_number, exception)
        *args, **kwargs: Arguments for func

    Returns:
        Function result

    Raises:
        RetryExhaustedException: If all retries fail
        Original exception: Last error encountered
    """
    config = config or RetryConfig()
    last_exception: Optional[Exception] = None

    for attempt in range(config.max_attempts):
        try:
            result = await func(*args, **kwargs)
            logger.debug(f"Function succeeded on attempt {attempt + 1}")
            return result
        except Exception as e:
            last_exception = e

            if attempt == config.max_attempts - 1:
                # Last attempt failed
                logger.error(
                    f"Function failed after {config.max_attempts} attempts: {e}"
                )
                raise RetryExhaustedException(
                    func.__name__,
                    config.max_attempts,
                    last_exception
                ) from last_exception

            # Calculate delay with exponential backoff
            delay_ms = min(
                config.initial_delay_ms * (config.backoff_factor ** attempt),
                config.max_delay_ms
            )

            # Add jitter to prevent thundering herd
            if config.jitter_enabled:
                jitter = random.uniform(0, delay_ms * 0.1)
                delay_ms += jitter

            logger.warning(
                f"Attempt {attempt + 1} failed, retrying in {delay_ms:.0f}ms: {e}"
            )

            # Call optional retry callback
            if on_retry:
                try:
                    await on_retry(attempt + 1, e)
                except Exception as callback_error:
                    logger.warning(f"Retry callback failed: {callback_error}")

            # Wait before retry
            await asyncio.sleep(delay_ms / 1000.0)

    # Should never reach here
    raise RuntimeError("Retry loop exited unexpectedly")
```

---

### Stap 6: Tool Registry (25 min)

```python
# backend/core/tool_broker/registry.py
"""Tool registry for managing available tools."""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional

from .schemas import ToolInfo

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for managing tool registrations."""

    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._handlers: Dict[str, Callable] = {}
        self._lock = asyncio.Lock()
        self._metrics: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        name: str,
        handler: Callable,
        description: str = "",
        version: str = "1.0.0",
        parameters: Optional[Dict[str, Any]] = None,
        returns: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register a tool.

        Args:
            name: Tool name (format: "server__tool_name")
            handler: Async function that executes the tool
            description: Tool description
            version: Tool version
            parameters: Parameter schema
            returns: Return schema
        """
        if name in self._tools:
            logger.warning(f"Tool '{name}' already registered, overwriting")

        self._tools[name] = {
            "name": name,
            "description": description,
            "version": version,
            "parameters": parameters or {},
            "returns": returns or {},
        }
        self._handlers[name] = handler
        self._metrics[name] = {
            "execution_count": 0,
            "success_count": 0,
            "failure_count": 0,
            "total_latency_ms": 0,
        }

        logger.info(f"Registered tool: {name}")

    def get(self, name: str) -> Optional[Dict[str, Any]]:
        """Get tool info."""
        return self._tools.get(name)

    def get_handler(self, name: str) -> Optional[Callable]:
        """Get tool handler."""
        return self._handlers.get(name)

    def list_tools(self) -> List[ToolInfo]:
        """List all registered tools with metrics."""
        tools = []
        for name, info in self._tools.items():
            metrics = self._metrics.get(name, {})
            execution_count = metrics.get("execution_count", 0)
            success_count = metrics.get("success_count", 0)

            tools.append(ToolInfo(
                name=name,
                description=info["description"],
                version=info["version"],
                parameters=info["parameters"],
                returns=info["returns"],
                execution_count=execution_count,
                success_rate=success_count / execution_count if execution_count > 0 else 1.0,
                avg_latency_ms=metrics.get("total_latency_ms", 0) / max(execution_count, 1)
            ))
        return tools

    async def record_execution(
        self,
        tool_name: str,
        success: bool,
        latency_ms: float
    ):
        """Record execution metrics."""
        async with self._lock:
            if tool_name in self._metrics:
                self._metrics[tool_name]["execution_count"] += 1
                self._metrics[tool_name]["total_latency_ms"] += latency_ms
                if success:
                    self._metrics[tool_name]["success_count"] += 1
                else:
                    self._metrics[tool_name]["failure_count"] += 1


def tool(
    name: str,
    description: str = "",
    version: str = "1.0.0",
    parameters: Optional[Dict[str, Any]] = None,
    returns: Optional[Dict[str, Any]] = None
):
    """
    Decorator for registering tools.

    Usage:
        @tool("vedastro__generate_signal", description="Generate signal")
        async def generate_signal(params: Dict) -> Dict:
            ...
    """
    def decorator(func: Callable) -> Callable:
        # Registry will be set up later
        func._tool_meta = {
            "name": name,
            "description": description,
            "version": version,
            "parameters": parameters,
            "returns": returns,
        }
        return func
    return decorator
```

---

### Stap 7: Core ToolBroker (30 min)

```python
# backend/core/tool_broker/broker.py
"""Core ToolBroker implementation."""

import logging
import time
from typing import Any, Dict, List, Optional

from .circuit_breaker import CircuitBreakerRegistry
from .exceptions import (
    CircuitBreakerOpenException,
    ToolBrokerException,
    ToolExecutionException,
    ToolNotFoundException,
)
from .registry import ToolRegistry
from .retry import async_retry
from .schemas import (
    CircuitBreakerConfig,
    ResilienceMetrics,
    RetryConfig,
    ToolExecutionRequest,
    ToolExecutionResponse,
    ToolInfo,
)

logger = logging.getLogger(__name__)


class ToolBroker:
    """
    Central tool broker with resilience patterns.

    Features:
    - Tool registration and discovery
    - Circuit breaker protection
    - Automatic retry with exponential backoff
    - Metrics collection
    """

    def __init__(
        self,
        retry_config: Optional[RetryConfig] = None,
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None
    ):
        self.registry = ToolRegistry()
        self.circuit_registry = CircuitBreakerRegistry()
        self.retry_config = retry_config or RetryConfig()
        self.circuit_config = circuit_breaker_config or CircuitBreakerConfig()
        self._metrics = ResilienceMetrics()

        logger.info("ToolBroker initialized")

    def register_tool(
        self,
        name: str,
        handler: callable,
        description: str = "",
        version: str = "1.0.0",
        parameters: Optional[Dict[str, Any]] = None,
        returns: Optional[Dict[str, Any]] = None
    ) -> None:
        """Register a tool with the broker."""
        self.registry.register(
            name=name,
            handler=handler,
            description=description,
            version=version,
            parameters=parameters,
            returns=returns
        )

        # Create circuit breaker for this tool
        asyncio.create_task(
            self.circuit_registry.get_or_create(name, self.circuit_config)
        )

    async def execute_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
        timeout_seconds: Optional[int] = None,
        request_id: Optional[str] = None
    ) -> ToolExecutionResponse:
        """
        Execute a tool with resilience patterns.

        Args:
            tool_name: Tool name (format: "server__tool_name")
            params: Tool parameters
            timeout_seconds: Optional timeout override
            request_id: Optional request ID for tracing

        Returns:
            ToolExecutionResponse with result or error
        """
        start_time = time.time()
        request_id = request_id or f"req_{int(start_time * 1000)}"
        retry_count = 0

        # Check if tool exists
        handler = self.registry.get_handler(tool_name)
        if not handler:
            return ToolExecutionResponse(
                success=False,
                error_message=f"Tool '{tool_name}' not found",
                execution_time_ms=(time.time() - start_time) * 1000,
                request_id=request_id
            )

        # Get or create circuit breaker
        circuit_breaker = await self.circuit_registry.get_or_create(
            tool_name, self.circuit_config
        )

        try:
            # Execute with circuit breaker and retry
            async def execute_with_retry():
                nonlocal retry_count

                async def on_retry(attempt: int, error: Exception):
                    nonlocal retry_count
                    retry_count = attempt
                    self._metrics.total_retry_attempts += 1

                return await async_retry(
                    handler,
                    params,
                    config=self.retry_config,
                    on_retry=on_retry
                )

            result = await circuit_breaker.call(execute_with_retry)

            # Record success
            execution_time_ms = (time.time() - start_time) * 1000
            await self.registry.record_execution(tool_name, True, execution_time_ms)
            self._metrics.total_calls += 1
            self._metrics.successful_calls += 1
            if retry_count > 0:
                self._metrics.successful_retries += 1

            return ToolExecutionResponse(
                success=True,
                result=result,
                execution_time_ms=execution_time_ms,
                circuit_breaker_state=circuit_breaker.state,
                retry_count=retry_count,
                request_id=request_id
            )

        except CircuitBreakerOpenException as e:
            self._metrics.total_calls += 1
            self._metrics.failed_calls += 1
            self._metrics.circuit_breaker_opens += 1

            return ToolExecutionResponse(
                success=False,
                error_message=str(e),
                execution_time_ms=(time.time() - start_time) * 1000,
                circuit_breaker_state=circuit_breaker.state,
                retry_count=retry_count,
                request_id=request_id
            )

        except Exception as e:
            self._metrics.total_calls += 1
            self._metrics.failed_calls += 1

            execution_time_ms = (time.time() - start_time) * 1000
            await self.registry.record_execution(tool_name, False, execution_time_ms)

            logger.error(f"Tool '{tool_name}' execution failed: {e}")

            return ToolExecutionResponse(
                success=False,
                error_message=str(e),
                execution_time_ms=execution_time_ms,
                circuit_breaker_state=circuit_breaker.state,
                retry_count=retry_count,
                request_id=request_id
            )

    def list_tools(self) -> List[ToolInfo]:
        """List all registered tools."""
        return self.registry.list_tools()

    def get_tool_info(self, tool_name: str) -> Optional[ToolInfo]:
        """Get info for a specific tool."""
        tools = self.list_tools()
        for tool in tools:
            if tool.name == tool_name:
                return tool
        return None

    def get_metrics(self) -> ResilienceMetrics:
        """Get resilience metrics."""
        return self._metrics

    def get_circuit_states(self) -> Dict[str, Any]:
        """Get all circuit breaker states."""
        return self.circuit_registry.get_all_states()
```

---

### Stap 8: API Endpoints (20 min)

```python
# backend/api/toolbroker_api.py
"""API endpoints for ToolBroker."""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status

from backend.core.auth.middleware import require_auth
from backend.core.tool_broker import ToolBroker
from backend.core.tool_broker.schemas import (
    HealthCheckResponse,
    ResilienceMetrics,
    ToolExecutionRequest,
    ToolExecutionResponse,
    ToolInfo,
)

router = APIRouter(prefix="/v1/tools", tags=["ToolBroker"])

# Global broker instance (initialized at startup)
_broker: ToolBroker = None


def get_broker() -> ToolBroker:
    """Get ToolBroker instance."""
    if _broker is None:
        raise RuntimeError("ToolBroker not initialized")
    return _broker


def initialize_broker(broker: ToolBroker):
    """Initialize global broker (call at startup)."""
    global _broker
    _broker = broker


@router.post("/execute", response_model=ToolExecutionResponse)
async def execute_tool(
    request: ToolExecutionRequest,
    broker: ToolBroker = Depends(get_broker),
    user: dict = Depends(require_auth)
) -> ToolExecutionResponse:
    """Execute a tool."""
    return await broker.execute_tool(
        tool_name=request.tool_name,
        params=request.params,
        timeout_seconds=request.timeout_seconds,
        request_id=request.request_id
    )


@router.get("/list", response_model=List[ToolInfo])
async def list_tools(
    broker: ToolBroker = Depends(get_broker),
    user: dict = Depends(require_auth)
) -> List[ToolInfo]:
    """List all available tools."""
    return broker.list_tools()


@router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    broker: ToolBroker = Depends(get_broker)
) -> HealthCheckResponse:
    """Health check endpoint."""
    circuit_states = broker.get_circuit_states()

    components = {}
    for name, state in circuit_states.items():
        components[name] = "operational" if state["state"] == "closed" else "degraded"

    all_healthy = all(s == "operational" for s in components.values())

    return HealthCheckResponse(
        status="healthy" if all_healthy else "degraded",
        components=components,
        metrics=broker.get_metrics()
    )


@router.get("/metrics", response_model=ResilienceMetrics)
async def get_metrics(
    broker: ToolBroker = Depends(get_broker),
    user: dict = Depends(require_auth)
) -> ResilienceMetrics:
    """Get resilience metrics."""
    return broker.get_metrics()


@router.get("/circuit-breakers")
async def get_circuit_breaker_states(
    broker: ToolBroker = Depends(get_broker),
    user: dict = Depends(require_auth)
) -> Dict[str, Any]:
    """Get circuit breaker states."""
    return broker.get_circuit_states()
```

---

### Stap 9: Integratie in Main App (10 min)

```python
# backend/api/main.py (update)

from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.api import toolbroker_api
from backend.core.tool_broker import ToolBroker


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    broker = ToolBroker()

    # Register tools (this will be expanded)
    # broker.register_tool("vedastro__generate_signal", vedastro_tool_handler)

    toolbroker_api.initialize_broker(broker)
    app.state.tool_broker = broker

    yield

    # Shutdown
    pass


app = FastAPI(lifespan=lifespan)

# Include routers
app.include_router(toolbroker_api.router)
# ... other routers
```

---

## 4. Testing

### 4.1 Unit Tests
```python
# backend/tests/unit/core/tool_broker/test_circuit_breaker.py
import pytest
from backend.core.tool_broker.circuit_breaker import CircuitBreaker, CircuitBreakerState


@pytest.mark.asyncio
async def test_circuit_opens_after_failures():
    breaker = CircuitBreaker("test", failure_threshold=3)

    async def failing_func():
        raise ValueError("Fail")

    # 3 failures
    for _ in range(3):
        with pytest.raises(ValueError):
            await breaker.call(failing_func)

    # Circuit should be open
    assert breaker.state == CircuitBreakerState.OPEN

    # Next call should raise CircuitBreakerOpenException
    with pytest.raises(Exception) as exc_info:
        await breaker.call(failing_func)
    assert "OPEN" in str(exc_info.value)
```

### 4.2 Run Tests
```bash
# Run ToolBroker tests
pytest backend/tests/unit/core/tool_broker/ -v

# Run with coverage
pytest backend/tests/unit/core/tool_broker/ --cov=backend.core.tool_broker --cov-report=html
```

---

## 5. Volgende Stappen

Na deze basis implementatie:

1. **Tool Implementaties**: Converteer V17 agents naar tools
2. **MCP Protocol**: Voeg MCP server/client mode toe
3. **BacktestEngine Refactor**: Gebruik ToolBroker in backtest
4. **Monitoring**: Voeg Prometheus metrics toe
5. **Documentatie**: API docs en voorbeelden

---

*Implementation Guide Version: 1.0*
*Status: Ready for Development*
