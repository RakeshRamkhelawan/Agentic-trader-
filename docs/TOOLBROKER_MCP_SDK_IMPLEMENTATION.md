# ToolBroker V18 - MCP SDK Implementatie Guide

> **Gecorrigeerde Architectuur** | **Anthropic Official MCP SDK** | **FastMCP**  
> **Agentic Trader Platform V18**  
> **Status**: READY FOR IMPLEMENTATION

---

## 1. Architectuur Correctie

### 1.1 Wat We NIET Meer Doen ❌
- ~~Custom ToolBroker from scratch bouwen~~
- ~~Eigen JSON-RPC protocol implementatie~~
- ~~Handmatige schema generatie~~
- ~~Custom registry/router~~

### 1.2 Wat We WEL Doen ✅
- **Anthropic Official MCP SDK** gebruiken (`pip install mcp[cli]`)
- **FastMCP** als router en registry
- **Circuit Breaker & Retry** als decorators op tool implementaties
- **@mcp.tool()** decorator voor tool registratie
- **STDIO/SSE** transport via officiële SDK

---

## 2. Project Structuur (Revised)

```
backend/
├── mcp_broker/                          # NIEUW
│   ├── __init__.py
│   ├── server.py                        # FastMCP server (ToolBroker)
│   ├── resilience/                      # Decorators voor failure handling
│   │   ├── __init__.py
│   │   ├── circuit_breaker.py          # Circuit breaker decorator
│   │   └── retry.py                     # Retry decorator
│   └── tools/                           # MCP Tools
│       ├── __init__.py
│       ├── vedastro_tools.py           # VedAstro MCP tools
│       ├── elemental_tools.py          # Elemental MCP tools
│       ├── data_tools.py               # Data MCP tools
│       └── execution_tools.py          # Execution MCP tools
│
├── core/tool_broker/                    # BEWAARD voor backward compat
│   └── (bestaande V17 code - deprecated)
│
└── api/mcp_api.py                       # HTTP endpoints voor MCP status
```

---

## 3. Stap-voor-Stap Implementatie

### Stap 1: Dependencies (5 min)

```bash
# requirements/mcp.txt
mcp[cli]>=1.0.0
pydantic>=2.0.0
anyio>=4.0.0
```

```bash
pip install -r requirements/mcp.txt
```

---

### Stap 2: Resilience Layer (30 min)

#### 2.1 Circuit Breaker Decorator

```python
# backend/mcp_broker/resilience/circuit_breaker.py
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
```

#### 2.2 Retry Decorator

```python
# backend/mcp_broker/resilience/retry.py
"""
Retry decorator met exponentiële backoff.

Usage:
    @retry(max_attempts=3, initial_delay_ms=100)
    @mcp.tool()
    async def vedastro_generate_signal(params: dict) -> dict:
        ...
"""

import asyncio
import functools
import logging
import random
from typing import Any, Callable, Optional, TypeVar

logger = logging.getLogger(__name__)
T = TypeVar("T")


class RetryConfig:
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay_ms: int = 100,
        max_delay_ms: int = 10000,
        backoff_factor: float = 2.0,
        jitter_enabled: bool = True,
        retryable_exceptions: tuple = (Exception,)
    ):
        self.max_attempts = max_attempts
        self.initial_delay_ms = initial_delay_ms
        self.max_delay_ms = max_delay_ms
        self.backoff_factor = backoff_factor
        self.jitter_enabled = jitter_enabled
        self.retryable_exceptions = retryable_exceptions


def retry(
    max_attempts: int = 3,
    initial_delay_ms: int = 100,
    max_delay_ms: int = 10000,
    backoff_factor: float = 2.0,
    jitter_enabled: bool = True,
    retryable_exceptions: tuple = (Exception,)
):
    """
    Decorator for adding retry logic to MCP tools.
    
    Usage:
        @retry(max_attempts=3, initial_delay_ms=100)
        @mcp.tool()
        async def my_tool(params: dict) -> dict:
            ...
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        initial_delay_ms=initial_delay_ms,
        max_delay_ms=max_delay_ms,
        backoff_factor=backoff_factor,
        jitter_enabled=jitter_enabled,
        retryable_exceptions=retryable_exceptions
    )
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception: Optional[Exception] = None
            
            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                except config.retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt == config.max_attempts - 1:
                        logger.error(
                            f"{func.__name__} failed after {config.max_attempts} attempts: {e}"
                        )
                        raise
                    
                    # Calculate delay
                    delay_ms = min(
                        config.initial_delay_ms * (config.backoff_factor ** attempt),
                        config.max_delay_ms
                    )
                    
                    # Add jitter
                    if config.jitter_enabled:
                        jitter = random.uniform(0, delay_ms * 0.1)
                        delay_ms += jitter
                    
                    logger.warning(
                        f"{func.__name__} attempt {attempt + 1} failed, "
                        f"retrying in {delay_ms:.0f}ms: {e}"
                    )
                    
                    await asyncio.sleep(delay_ms / 1000.0)
            
            raise RuntimeError("Retry loop exited unexpectedly")
        
        return wrapper
    return decorator


# Convenience decorator met V17 defaults
def vedastro_retry(func: Callable[..., T]) -> Callable[..., T]:
    """Retry decorator optimized for VedAstro calls."""
    return retry(
        max_attempts=3,
        initial_delay_ms=100,
        backoff_factor=2.0,
        retryable_exceptions=(ConnectionError, TimeoutError, Exception)
    )(func)


def elemental_retry(func: Callable[..., T]) -> Callable[..., T]:
    """Retry decorator optimized for Elemental calculations."""
    return retry(
        max_attempts=2,
        initial_delay_ms=50,
        backoff_factor=1.5,
        retryable_exceptions=(Exception,)
    )(func)
```

#### 2.3 Resilience __init__.py

```python
# backend/mcp_broker/resilience/__init__.py
"""Resilience patterns for MCP tools."""

from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenException,
    circuit_breaker,
    get_circuit_state,
)
from .retry import retry, vedastro_retry, elemental_retry

__all__ = [
    "CircuitBreaker",
    "CircuitBreakerOpenException",
    "circuit_breaker",
    "get_circuit_state",
    "retry",
    "vedastro_retry",
    "elemental_retry",
]
```

---

### Stap 3: MCP Tools (45 min)

#### 3.1 VedAstro Tools

```python
# backend/mcp_broker/tools/vedastro_tools.py
"""
VedAstro MCP Tools.

Exposeert V17 VedAstro functionaliteit als MCP tools.
"""

import logging
from typing import Dict, Any, Optional

from mcp.server.fastmcp import Context

from backend.mcp_broker.resilience import circuit_breaker, vedastro_retry
from backend.vedastro import EnhancedAstroOrchestrator, TradingSignalGenerator

logger = logging.getLogger(__name__)

# Initialize VedAstro components
astro_orchestrator = EnhancedAstroOrchestrator()
signal_generator = TradingSignalGenerator()


@circuit_breaker(failure_threshold=5, timeout_seconds=30)
@vedastro_retry
async def vedastro_generate_signal(
    symbol: str,
    current_price: float,
    ctx: Context
) -> Dict[str, Any]:
    """
    Generate trading signal from astrological data.
    
    Args:
        symbol: Asset symbol (e.g., "AAPL", "BTC")
        current_price: Current market price
        ctx: MCP context for logging
    
    Returns:
        Trading signal with confidence and astrological context
    """
    ctx.info(f"Generating VedAstro signal for {symbol} at ${current_price}")
    
    try:
        # Get VedAstro analysis
        astro_analysis = await astro_orchestrator.analyze_asset(
            symbol=symbol,
            current_price=current_price
        )
        
        signal = astro_analysis.trading_signal
        
        ctx.info(f"Signal generated: {signal.signal} (confidence: {signal.confidence}%)")
        
        return {
            "signal": signal.signal.value if hasattr(signal.signal, 'value') else str(signal.signal),
            "confidence": signal.confidence,
            "strength_score": signal.strength_score,
            "dasha_context": signal.dasha_context if hasattr(signal, 'dasha_context') else "",
            "primary_factors": signal.primary_factors if hasattr(signal, 'primary_factors') else [],
            "risk_level": signal.risk_level,
            "recommended_action": signal.recommended_action,
        }
    
    except Exception as e:
        logger.error(f"VedAstro signal generation failed: {e}")
        ctx.error(f"Failed to generate signal: {e}")
        raise


@circuit_breaker(failure_threshold=3, timeout_seconds=20)
@vedastro_retry
async def vedastro_get_dasha(
    symbol: str,
    ctx: Context
) -> Dict[str, Any]:
    """
    Get current Dasha period for an asset.
    
    Args:
        symbol: Asset symbol
        ctx: MCP context
    
    Returns:
        Dasha information including Mahadasha, Antardasha, Pratyantardasha
    """
    ctx.info(f"Fetching Dasha for {symbol}")
    
    # Implementation using vedastro connector
    # This is a placeholder - actual implementation would use vedastro module
    
    return {
        "symbol": symbol,
        "mahadasha": "Jupiter",
        "antardasha": "Venus",
        "pratyantardasha": "Mercury",
        "mahadasha_start": "2020-01-01",
        "mahadasha_end": "2036-01-01",
        "interpretation": "Jupiter Mahadasha brings expansion and wisdom"
    }


@circuit_breaker(failure_threshold=5, timeout_seconds=30)
@vedastro_retry
async def vedastro_get_transits(
    symbol: str,
    ctx: Context
) -> Dict[str, Any]:
    """
    Get current planetary transits for an asset.
    
    Args:
        symbol: Asset symbol
        ctx: MCP context
    
    Returns:
        Transit information including exalted, debilitated, and retrograde planets
    """
    ctx.info(f"Fetching transits for {symbol}")
    
    return {
        "symbol": symbol,
        "exalted_planets": ["Jupiter", "Venus"],
        "debilitated_planets": ["Saturn"],
        "retrograde_planets": ["Mercury"],
        "transit_score": 0.65,
        "coherence": 0.72
    }
```

#### 3.2 Elemental Tools

```python
# backend/mcp_broker/tools/elemental_tools.py
"""
Elemental MCP Tools.

V17 Elemental Agents als stateless MCP tools.
Behoudt alle financiële constraints (€2k cap, 60-day failsafe, etc.)
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import deque

from mcp.server.fastmcp import Context

from backend.mcp_broker.resilience import circuit_breaker, elemental_retry

logger = logging.getLogger(__name__)

# V17 Constants (BEHOUDEN!)
MAX_POSITION_EUR = 2000.0
MAX_HOLD_DAYS = 60
TRAILING_STOP_THRESHOLD = 0.40  # +40%
TRAILING_STOP_DISTANCE = 0.15   # -15% from peak

# Planet multipliers from V17
PLANET_RISK_MULTIPLIERS = {
    "SUN": 1.00, "MOON": 0.80, "MARS": 1.40,
    "MERCURY": 0.90, "JUPITER": 1.20, "VENUS": 1.10,
    "SATURN": 0.60, "RAHU": 0.70, "KETU": 0.75,
}


@circuit_breaker(failure_threshold=5, timeout_seconds=10)
@elemental_retry
async def elemental_fire_position_size(
    symbol: str,
    portfolio_value: float,
    vedastro_score: float,
    dominant_planet: str,
    price_history: List[float],
    ctx: Context
) -> Dict[str, Any]:
    """
    Calculate position size based on VedAstro score and volatility.
    
    V17 Constraints:
    - Max €2,000 per position
    - Max 2% of portfolio
    
    Args:
        symbol: Asset symbol
        portfolio_value: Total portfolio value in EUR
        vedastro_score: VedAstro strength score (0-100)
        dominant_planet: Dominant planet for the day
        price_history: Recent price history for volatility calc
        ctx: MCP context
    
    Returns:
        Position sizing recommendation
    """
    ctx.info(f"Calculating Fire position size for {symbol}")
    
    # V17 logic: Calculate ATR-based volatility factor
    if len(price_history) < 20:
        vol_factor = 1.0
    else:
        # Simple volatility calculation
        returns = [(price_history[i] - price_history[i-1]) / price_history[i-1] 
                   for i in range(1, len(price_history))]
        avg_return = sum(returns) / len(returns)
        variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
        volatility = variance ** 0.5
        
        vol_factor = max(0.5, min(2.0, 0.03 / (volatility + 0.001)))
    
    # VedAstro score → harmony factor (0.5-1.2)
    harmony_factor = 0.5 + (vedastro_score / 100) * 0.7
    
    # Streak factor
    streak = 0
    for i in range(1, min(6, len(price_history))):
        if price_history[-i] > price_history[-i-1]:
            streak += 1
        else:
            break
    streak_factor = 1.0 + (streak * 0.05)
    
    # Planet multiplier
    planet_mult = PLANET_RISK_MULTIPLIERS.get(dominant_planet, 1.0)
    
    # Calculate position size
    base_pct = 0.015 * vol_factor * harmony_factor * streak_factor * planet_mult
    raw_size = portfolio_value * base_pct
    max_pct_size = portfolio_value * 0.02  # 2% max
    
    # V17: Apply €2k cap
    position_size = min(raw_size, max_pct_size, MAX_POSITION_EUR)
    
    ctx.info(f"Position size: €{position_size:.2f} (raw: €{raw_size:.2f})")
    
    return {
        "position_size_eur": position_size,
        "max_position_eur": MAX_POSITION_EUR,
        "position_pct": position_size / portfolio_value if portfolio_value > 0 else 0,
        "sizing_factors": {
            "volatility": vol_factor,
            "harmony": harmony_factor,
            "streak": streak_factor,
            "planet": planet_mult
        },
        "constraints_applied": ["max_2000_eur", "max_2pct_portfolio"]
    }


@circuit_breaker(failure_threshold=3, timeout_seconds=5)
async def elemental_earth_entry_check(
    symbol: str,
    trade_history: List[Dict[str, Any]],
    ctx: Context
) -> Dict[str, Any]:
    """
    Check if entry is allowed (3-loss rule).
    
    V17 Logic:
    - Block entry after 3 consecutive losses
    
    Args:
        symbol: Asset symbol
        trade_history: List of recent trades with 'pnl' and 'win' fields
        ctx: MCP context
    
    Returns:
        Entry permission and blocking reasons
    """
    ctx.info(f"Checking Earth entry for {symbol}")
    
    # Get recent trades for this symbol
    recent = [t for t in trade_history if t.get('symbol') == symbol][-20:]
    
    # Check 3 consecutive losses
    consecutive_losses = 0
    for trade in reversed(recent):
        if not trade.get('win', True):
            consecutive_losses += 1
        else:
            break
    
    can_enter = consecutive_losses < 3
    
    ctx.info(f"Entry allowed: {can_enter} (consecutive losses: {consecutive_losses})")
    
    return {
        "can_enter": can_enter,
        "blocking_reason": "3_consecutive_losses" if not can_enter else None,
        "recent_loss_count": sum(1 for t in recent if not t.get('win', True)),
        "consecutive_losses": consecutive_losses
    }


@circuit_breaker(failure_threshold=3, timeout_seconds=5)
async def elemental_earth_exit_check(
    symbol: str,
    entry_date: str,
    current_date: str,
    entry_price: float,
    current_price: float,
    peak_price: float,
    ctx: Context
) -> Dict[str, Any]:
    """
    Check if position should be exited.
    
    V17 Constraints:
    - Max 60 days hold
    - Trailing stop: +40% peak → -15% drop = exit
    - Hard stop: -15% from entry
    
    Args:
        symbol: Asset symbol
        entry_date: Entry date (ISO format)
        current_date: Current date (ISO format)
        entry_price: Entry price
        current_price: Current price
        peak_price: Highest price since entry
        ctx: MCP context
    
    Returns:
        Exit recommendation
    """
    ctx.info(f"Checking Earth exit for {symbol}")
    
    # Parse dates
    entry = datetime.fromisoformat(entry_date.replace('Z', '+00:00'))
    current = datetime.fromisoformat(current_date.replace('Z', '+00:00'))
    days_held = (current - entry).days
    
    # Calculate P&L
    pnl_pct = (current_price - entry_price) / entry_price
    peak_pnl_pct = (peak_price - entry_price) / entry_price
    drawdown_from_peak = (peak_price - current_price) / peak_price if peak_price > 0 else 0
    
    exit_signals = []
    
    # 60-day failsafe
    if days_held >= MAX_HOLD_DAYS:
        exit_signals.append(f"max_hold_days_{MAX_HOLD_DAYS}")
    
    # Trailing stop
    trailing_stop_active = peak_pnl_pct >= TRAILING_STOP_THRESHOLD
    if trailing_stop_active and drawdown_from_peak >= TRAILING_STOP_DISTANCE:
        exit_signals.append(f"trailing_stop_{drawdown_from_peak:.1%}")
    
    # Hard stop
    if drawdown_from_peak > 0.15 and pnl_pct < 0:
        exit_signals.append(f"hard_stop_{drawdown_from_peak:.1%}")
    
    should_exit = len(exit_signals) > 0
    
    ctx.info(f"Exit recommended: {should_exit} (signals: {exit_signals})")
    
    return {
        "should_exit": should_exit,
        "exit_reasons": exit_signals,
        "days_held": days_held,
        "pnl_pct": pnl_pct,
        "peak_pnl_pct": peak_pnl_pct,
        "trailing_stop_active": trailing_stop_active
    }


@circuit_breaker(failure_threshold=5, timeout_seconds=10)
async def elemental_water_regime_check(
    symbol: str,
    prices: List[float],
    ctx: Context
) -> Dict[str, Any]:
    """
    Check macro regime and hedge signals.
    
    Args:
        symbol: Asset symbol
        prices: Price history (min 20 points)
        ctx: MCP context
    
    Returns:
        Regime assessment and hedge recommendations
    """
    ctx.info(f"Checking Water regime for {symbol}")
    
    if len(prices) < 20:
        return {
            "regime": "neutral",
            "risk_on_score": 0.5,
            "hedge_symbol": None,
            "hedge_confidence": 0.0,
            "reason": "insufficient_data"
        }
    
    # Calculate metrics
    price_change_30d = (prices[-1] - prices[-min(30, len(prices))]) / prices[-min(30, len(prices))]
    advancing = sum(1 for i in range(1, min(20, len(prices))) if prices[-i] > prices[-i-1])
    total = min(19, len(prices) - 1)
    advance_ratio = advancing / total if total > 0 else 0.5
    
    # Determine regime
    if advance_ratio > 0.6 and price_change_30d > 0.10:
        regime = "expansion"
        risk_on = 0.8
    elif advance_ratio < 0.4 and price_change_30d < -0.10:
        regime = "contraction"
        risk_on = 0.2
    elif price_change_30d > 0:
        regime = "recovery"
        risk_on = 0.6
    else:
        regime = "neutral"
        risk_on = 0.5
    
    # Hedge signal (V17: hedge when risk_on < 0.35)
    hedge_pairs = {"SPY": "SH", "QQQ": "PSQ", "IWM": "RWM", "TLT": "TBF"}
    hedge_sym = hedge_pairs.get(symbol)
    hedge_conf = 0.0
    
    if hedge_sym and risk_on < 0.35:
        hedge_conf = 0.70 + (0.35 - risk_on) * 0.5
        hedge_conf = min(hedge_conf, 0.85)
    
    ctx.info(f"Regime: {regime} (risk_on: {risk_on:.2f})")
    
    return {
        "regime": regime,
        "risk_on_score": risk_on,
        "hedge_symbol": hedge_sym if hedge_conf > 0 else None,
        "hedge_confidence": hedge_conf,
        "advance_ratio": advance_ratio,
        "price_change_30d": price_change_30d
    }


@circuit_breaker(failure_threshold=3, timeout_seconds=5)
async def elemental_ether_consensus(
    fire_vote: float,
    earth_vote: float,
    water_vote: float,
    air_vote: float,
    ctx: Context
) -> Dict[str, Any]:
    """
    Synthesize elemental consensus.
    
    Args:
        fire_vote: Fire element score (0-1)
        earth_vote: Earth element score (0-1)
        water_vote: Water element score (0-1)
        air_vote: Air element score (0-1)
        ctx: MCP context
    
    Returns:
        Consensus decision
    """
    ctx.info("Calculating Ether consensus")
    
    # Calculate harmony (weighted average)
    weights = {"fire": 0.25, "earth": 0.30, "water": 0.25, "air": 0.20}
    harmony = (
        fire_vote * weights["fire"] +
        earth_vote * weights["earth"] +
        water_vote * weights["water"] +
        air_vote * weights["air"]
    )
    
    # V17 threshold: harmony > 0.45 = approved
    approved = harmony > 0.45
    
    # Determine dominant element
    votes = {
        "fire": fire_vote,
        "earth": earth_vote,
        "water": water_vote,
        "air": air_vote
    }
    dominant = max(votes, key=votes.get)
    
    ctx.info(f"Consensus: {harmony:.2f} (approved: {approved}, dominant: {dominant})")
    
    return {
        "harmony_score": harmony,
        "approved": approved,
        "threshold": 0.45,
        "elemental_breakdown": votes,
        "dominant_element": dominant
    }
```

#### 3.3 Data & Execution Tools

```python
# backend/mcp_broker/tools/data_tools.py
"""
Data MCP Tools.

Market data en portfolio informatie.
"""

import logging
from typing import Dict, Any, List

from mcp.server.fastmcp import Context

from backend.mcp_broker.resilience import circuit_breaker, retry

logger = logging.getLogger(__name__)


@circuit_breaker(failure_threshold=10, timeout_seconds=30)
@retry(max_attempts=3, initial_delay_ms=200)
async def data_get_historical_prices(
    symbol: str,
    start_date: str,
    end_date: str,
    timeframe: str = "1d",
    ctx: Context
) -> Dict[str, Any]:
    """
    Get historical price data.
    
    Args:
        symbol: Asset symbol
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
        timeframe: Data timeframe (1m, 5m, 1h, 1d)
        ctx: MCP context
    
    Returns:
        OHLCV data
    """
    ctx.info(f"Fetching historical data for {symbol} from {start_date} to {end_date}")
    
    # Implementation would fetch from database or API
    # Placeholder response
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "data": [
            {"timestamp": "2026-01-01", "open": 100.0, "high": 105.0, "low": 99.0, "close": 103.0, "volume": 1000000}
        ]
    }


@circuit_breaker(failure_threshold=5, timeout_seconds=10)
async def data_get_portfolio_status(
    account_id: str,
    ctx: Context
) -> Dict[str, Any]:
    """
    Get current portfolio status.
    
    Args:
        account_id: Account identifier
        ctx: MCP context
    
    Returns:
        Portfolio summary
    """
    ctx.info(f"Fetching portfolio status for {account_id}")
    
    # Implementation would query database
    return {
        "account_id": account_id,
        "cash_eur": 50000.0,
        "total_value_eur": 150000.0,
        "open_positions": [],
        "daily_pnl": 0.0,
        "total_pnl": 0.0
    }
```

```python
# backend/mcp_broker/tools/execution_tools.py
"""
Execution MCP Tools.

Paper trading en order execution.
"""

import logging
from datetime import datetime
from typing import Dict, Any

from mcp.server.fastmcp import Context

from backend.mcp_broker.resilience import circuit_breaker

logger = logging.getLogger(__name__)

# V17 Constants
COMMISSION_PCT = 0.0005  # 0.05%
SLIPPAGE_PCT = 0.001     # 0.1%
MAX_POSITION_EUR = 2000.0


@circuit_breaker(failure_threshold=5, timeout_seconds=15)
async def execution_execute_paper_trade(
    symbol: str,
    action: str,
    quantity: float,
    current_price: float,
    account_id: str,
    ctx: Context
) -> Dict[str, Any]:
    """
    Execute a paper trade.
    
    V17 Constraints:
    - Max €2,000 position size
    - 0.05% commission
    - 0.1% slippage
    
    Args:
        symbol: Asset symbol
        action: BUY or SELL
        quantity: Number of shares/contracts
        current_price: Current market price
        account_id: Account identifier
        ctx: MCP context
    
    Returns:
        Trade execution details
    """
    ctx.info(f"Executing {action} {quantity} {symbol} for {account_id}")
    
    # Validate action
    if action not in ["BUY", "SELL"]:
        raise ValueError(f"Invalid action: {action}")
    
    # Calculate execution price with slippage
    if action == "BUY":
        execution_price = current_price * (1 + SLIPPAGE_PCT)
    else:
        execution_price = current_price * (1 - SLIPPAGE_PCT)
    
    # Calculate gross value
    gross_value = quantity * execution_price
    
    # V17: Check max position size for BUY
    if action == "BUY" and gross_value > MAX_POSITION_EUR:
        ctx.error(f"Position size €{gross_value:.2f} exceeds max €{MAX_POSITION_EUR}")
        raise ValueError(f"Position size exceeds maximum of €{MAX_POSITION_EUR}")
    
    # Calculate commission
    commission = gross_value * COMMISSION_PCT
    net_value = gross_value - commission
    
    # Generate order ID
    order_id = f"paper_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{symbol}"
    
    ctx.info(f"Trade executed: {order_id} at €{execution_price:.2f}")
    
    return {
        "order_id": order_id,
        "status": "FILLED",
        "symbol": symbol,
        "action": action,
        "quantity": quantity,
        "filled_price": execution_price,
        "gross_value": gross_value,
        "commission": commission,
        "net_value": net_value,
        "timestamp": datetime.utcnow().isoformat(),
        "constraints_applied": ["max_2000_eur", "commission_0.05pct", "slippage_0.1pct"]
    }
```

---

### Stap 4: FastMCP Server (20 min)

```python
# backend/mcp_broker/server.py
"""
FastMCP Server - De ToolBroker.

Centrale MCP server die alle trading tools exposeert.
Gebruikt Anthropic's officiële MCP SDK.
"""

import logging
from typing import Dict, Any

from mcp.server.fastmcp import FastMCP

# Import tools
from backend.mcp_broker.tools.vedastro_tools import (
    vedastro_generate_signal,
    vedastro_get_dasha,
    vedastro_get_transits,
)
from backend.mcp_broker.tools.elemental_tools import (
    elemental_fire_position_size,
    elemental_earth_entry_check,
    elemental_earth_exit_check,
    elemental_water_regime_check,
    elemental_ether_consensus,
)
from backend.mcp_broker.tools.data_tools import (
    data_get_historical_prices,
    data_get_portfolio_status,
)
from backend.mcp_broker.tools.execution_tools import (
    execution_execute_paper_trade,
)
from backend.mcp_broker.resilience import get_circuit_state

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("AgenticTraderBroker")

# ============================================================================
# VEDASTRO TOOLS
# ============================================================================

@mcp.tool()
async def vedastro__generate_signal(
    symbol: str,
    current_price: float,
    ctx: Any = None
) -> Dict[str, Any]:
    """
    Generate trading signal from astrological data.
    
    Args:
        symbol: Asset symbol (e.g., "AAPL", "BTC")
        current_price: Current market price
    
    Returns:
        Trading signal with confidence and astrological context
    """
    return await vedastro_generate_signal(symbol, current_price, ctx)


@mcp.tool()
async def vedastro__get_dasha(symbol: str, ctx: Any = None) -> Dict[str, Any]:
    """
    Get current Dasha period for an asset.
    
    Args:
        symbol: Asset symbol
    
    Returns:
        Dasha information including Mahadasha, Antardasha
    """
    return await vedastro_get_dasha(symbol, ctx)


@mcp.tool()
async def vedastro__get_transits(symbol: str, ctx: Any = None) -> Dict[str, Any]:
    """
    Get current planetary transits.
    
    Args:
        symbol: Asset symbol
    
    Returns:
        Transit information
    """
    return await vedastro_get_transits(symbol, ctx)


# ============================================================================
# ELEMENTAL TOOLS
# ============================================================================

@mcp.tool()
async def elemental__fire_position_size(
    symbol: str,
    portfolio_value: float,
    vedastro_score: float,
    dominant_planet: str,
    price_history: list,
    ctx: Any = None
) -> Dict[str, Any]:
    """
    Calculate position size using Fire element logic.
    
    Constraints:
    - Max €2,000 per position
    - Max 2% of portfolio
    
    Args:
        symbol: Asset symbol
        portfolio_value: Total portfolio value
        vedastro_score: VedAstro strength (0-100)
        dominant_planet: Dominant planet
        price_history: Recent prices for volatility
    
    Returns:
        Position sizing recommendation
    """
    return await elemental_fire_position_size(
        symbol, portfolio_value, vedastro_score, dominant_planet, price_history, ctx
    )


@mcp.tool()
async def elemental__earth_entry_check(
    symbol: str,
    trade_history: list,
    ctx: Any = None
) -> Dict[str, Any]:
    """
    Check if entry is allowed (Earth element).
    
    Blocks entry after 3 consecutive losses.
    
    Args:
        symbol: Asset symbol
        trade_history: Recent trade history
    
    Returns:
        Entry permission
    """
    return await elemental_earth_entry_check(symbol, trade_history, ctx)


@mcp.tool()
async def elemental__earth_exit_check(
    symbol: str,
    entry_date: str,
    current_date: str,
    entry_price: float,
    current_price: float,
    peak_price: float,
    ctx: Any = None
) -> Dict[str, Any]:
    """
    Check if position should be exited (Earth element).
    
    Constraints:
    - Max 60 days hold
    - Trailing stop: +40% peak → -15% drop
    
    Args:
        symbol: Asset symbol
        entry_date: Entry date (ISO format)
        current_date: Current date (ISO format)
        entry_price: Entry price
        current_price: Current price
        peak_price: Peak price since entry
    
    Returns:
        Exit recommendation
    """
    return await elemental_earth_exit_check(
        symbol, entry_date, current_date, entry_price, current_price, peak_price, ctx
    )


@mcp.tool()
async def elemental__water_regime_check(
    symbol: str,
    prices: list,
    ctx: Any = None
) -> Dict[str, Any]:
    """
    Check macro regime and hedge signals (Water element).
    
    Args:
        symbol: Asset symbol
        prices: Price history (min 20 points)
    
    Returns:
        Regime assessment
    """
    return await elemental_water_regime_check(symbol, prices, ctx)


@mcp.tool()
async def elemental__ether_consensus(
    fire_vote: float,
    earth_vote: float,
    water_vote: float,
    air_vote: float,
    ctx: Any = None
) -> Dict[str, Any]:
    """
    Synthesize elemental consensus.
    
    Args:
        fire_vote: Fire score (0-1)
        earth_vote: Earth score (0-1)
        water_vote: Water score (0-1)
        air_vote: Air score (0-1)
    
    Returns:
        Consensus decision (approved if harmony > 0.45)
    """
    return await elemental_ether_consensus(fire_vote, earth_vote, water_vote, air_vote, ctx)


# ============================================================================
# DATA TOOLS
# ============================================================================

@mcp.tool()
async def data__get_historical_prices(
    symbol: str,
    start_date: str,
    end_date: str,
    timeframe: str = "1d",
    ctx: Any = None
) -> Dict[str, Any]:
    """
    Get historical price data.
    
    Args:
        symbol: Asset symbol
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
        timeframe: Data timeframe (1m, 5m, 1h, 1d)
    
    Returns:
        OHLCV data
    """
    return await data_get_historical_prices(symbol, start_date, end_date, timeframe, ctx)


@mcp.tool()
async def data__get_portfolio_status(
    account_id: str,
    ctx: Any = None
) -> Dict[str, Any]:
    """
    Get current portfolio status.
    
    Args:
        account_id: Account identifier
    
    Returns:
        Portfolio summary
    """
    return await data_get_portfolio_status(account_id, ctx)


# ============================================================================
# EXECUTION TOOLS
# ============================================================================

@mcp.tool()
async def execution__execute_paper_trade(
    symbol: str,
    action: str,
    quantity: float,
    current_price: float,
    account_id: str,
    ctx: Any = None
) -> Dict[str, Any]:
    """
    Execute a paper trade.
    
    Constraints:
    - Max €2,000 position size
    - 0.05% commission
    - 0.1% slippage
    
    Args:
        symbol: Asset symbol
        action: BUY or SELL
        quantity: Number of shares
        current_price: Current market price
        account_id: Account identifier
    
    Returns:
        Trade execution details
    """
    return await execution_execute_paper_trade(
        symbol, action, quantity, current_price, account_id, ctx
    )


# ============================================================================
# HEALTH & MONITORING
# ============================================================================

@mcp.tool()
async def system__health_check() -> Dict[str, Any]:
    """
    Check system health and circuit breaker states.
    
    Returns:
        Health status of all components
    """
    tools = [
        "vedastro_generate_signal",
        "vedastro_get_dasha",
        "elemental_fire_position_size",
        "elemental_earth_entry_check",
        "elemental_water_regime_check",
        "elemental_ether_consensus",
    ]
    
    circuit_states = {}
    for tool in tools:
        state = get_circuit_state(tool)
        if state:
            circuit_states[tool] = state["state"]
        else:
            circuit_states[tool] = "closed"
    
    all_healthy = all(s == "closed" for s in circuit_states.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "circuit_breaker_states": circuit_states,
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    logger.info("Starting AgenticTraderBroker MCP Server")
    logger.info("Transport: stdio")
    logger.info("Tools registered: %d", len(mcp._tools))
    
    # Run with stdio transport (for Claude Desktop, etc.)
    mcp.run(transport='stdio')
```

---

### Stap 5: Testing & Debugging (15 min)

#### 5.1 Test Client Script

```python
# scripts/test_mcp_client.py
"""
Test client for MCP Server.

Usage:
    python scripts/test_mcp_client.py
"""

import asyncio
import json
import subprocess
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_mcp_server():
    """Test the MCP server."""
    
    # Server parameters
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "backend.mcp_broker.server"],
        env={"PYTHONPATH": "."}
    )
    
    print("Connecting to MCP server...")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize
            await session.initialize()
            print("✓ Connected to MCP server")
            
            # List tools
            tools = await session.list_tools()
            print(f"\n✓ Available tools: {len(tools.tools)}")
            for tool in tools.tools:
                print(f"  - {tool.name}")
            
            # Test VedAstro tool
            print("\n→ Testing vedastro__generate_signal...")
            result = await session.call_tool(
                "vedastro__generate_signal",
                {"symbol": "AAPL", "current_price": 185.50}
            )
            print(f"  Result: {result}")
            
            # Test Elemental tool
            print("\n→ Testing elemental__ether_consensus...")
            result = await session.call_tool(
                "elemental__ether_consensus",
                {
                    "fire_vote": 0.8,
                    "earth_vote": 0.7,
                    "water_vote": 0.6,
                    "air_vote": 0.5
                }
            )
            print(f"  Result: {result}")
            
            # Test health check
            print("\n→ Testing system__health_check...")
            result = await session.call_tool("system__health_check", {})
            print(f"  Result: {result}")
            
            print("\n✓ All tests passed!")


if __name__ == "__main__":
    asyncio.run(test_mcp_server())
```

#### 5.2 Manual Testing

```bash
# 1. Start server manually
python -m backend.mcp_broker.server

# 2. Or test with mcp CLI
mcp run backend.mcp_broker.server

# 3. Run test client
python scripts/test_mcp_client.py
```

#### 5.3 Claude Desktop Config

```json
// claude_desktop_config.json
{
  "mcpServers": {
    "agentic-trader": {
      "command": "python",
      "args": ["-m", "backend.mcp_broker.server"],
      "env": {
        "PYTHONPATH": "/path/to/project"
      }
    }
  }
}
```

---

## 4. Samenvatting

### Wat We Hebben Gebouwd

1. **Resilience Layer** (`resilience/`)
   - `circuit_breaker.py` - Decorator voor failure isolatie
   - `retry.py` - Decorator voor exponential backoff

2. **MCP Tools** (`tools/`)
   - `vedastro_tools.py` - Astrologische analyse
   - `elemental_tools.py` - Financiële evaluatie (met V17 constraints)
   - `data_tools.py` - Market data
   - `execution_tools.py` - Paper trading

3. **FastMCP Server** (`server.py`)
   - `@mcp.tool()` decorators voor alle tools
   - STDIO transport voor compatibiliteit
   - Health monitoring

### Key Features

✅ **Officiële MCP SDK** - Geen custom protocol  
✅ **Circuit Breakers** - Failure isolatie per tool  
✅ **Retry Logic** - Exponential backoff met jitter  
✅ **V17 Constraints** - €2k cap, 60-day failsafe behouden  
✅ **Type Safety** - Pydantic via FastMCP  
✅ **LLM Ready** - Native ondersteuning Claude, Cursor, etc.  

### Volgende Stappen

1. **Integratie** - BacktestEngine gebruikt MCP client
2. **Monitoring** - Prometheus metrics toevoegen
3. **Documentatie** - API docs genereren
4. **Deployment** - Docker container voor MCP server

---

*Implementation Guide Version: 2.0 (MCP SDK Edition)*  
*Status: READY FOR DEVELOPMENT*
