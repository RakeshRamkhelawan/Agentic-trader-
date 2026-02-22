"""
Chaos Engineering - ChaosMonkey (Sprint 4 S4-2).

Implements controlled chaos injection for resilience testing:
- Latency injection (50ms - 2s delays)
- Service failure simulation (Redis, FAISS down)
- Tattva disruption (coherence corruption)

Usage:
    Only active when ENV=testing or CHAOS_MODE=1
    
    from backend.testing.chaos.monkey import ChaosMonkey
    
    monkey = ChaosMonkey()
    await monkey.inject_latency("exchange_api", delay_ms=100)
    await monkey.simulate_service_failure("redis")
    monkey.disrupt_tattva_coherence(target_coherence=0.1)
"""

import asyncio
import logging
import os
import random
from enum import Enum
from typing import Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class ChaosMode(Enum):
    """Chaos injection modes."""
    DISABLED = "disabled"
    LATENCY = "latency"           # Only latency injection
    FAILURE = "failure"           # Only service failures
    TATTVA = "tattva"             # Only Tattva disruption
    FULL = "full"                 # All chaos types


class ChaosMonkey:
    """
    Chaos Engineering tool for testing system resilience.
    
    Features:
    1. Latency Injection: Random delays in async operations
    2. Service Failure: Simulates downstream service outages
    3. Tattva Disruption: Corrupts consciousness state
    
    Safety:
    - Only active in testing/chaos mode
    - Circuit breakers should catch failures
    - Graceful degradation verification
    """
    
    # Services that can be targeted
    TARGET_SERVICES = {"redis", "faiss", "postgres", "exchange_api", "llm"}
    
    def __init__(self, mode: Optional[ChaosMode] = None):
        """
        Initialize ChaosMonkey.
        
        Args:
            mode: Chaos mode (auto-detected from env if not specified)
        """
        self._mode = mode or self._detect_mode()
        self._enabled = self._mode != ChaosMode.DISABLED
        self._injected_failures: Set[str] = set()
        self._latency_config = {"min_ms": 50, "max_ms": 2000}
        self._failure_probability = 0.1  # 10% failure rate
        
        if self._enabled:
            logger.warning(
                f"🐵 CHAOS MODE ENABLED: {self._mode.value} "
                f"(This should only be in testing!)"
            )
    
    def _detect_mode(self) -> ChaosMode:
        """Detect chaos mode from environment."""
        env = os.environ.get("ENV", "production").lower()
        chaos_env = os.environ.get("CHAOS_MODE", "").lower()
        
        if env == "testing" or chaos_env == "1":
            return ChaosMode.FULL
        elif chaos_env == "latency":
            return ChaosMode.LATENCY
        elif chaos_env == "failure":
            return ChaosMode.FAILURE
        elif chaos_env == "tattva":
            return ChaosMode.TATTVA
        return ChaosMode.DISABLED
    
    @property
    def enabled(self) -> bool:
        """Check if chaos mode is enabled."""
        return self._enabled
    
    @property
    def mode(self) -> ChaosMode:
        """Get current chaos mode."""
        return self._mode
    
    async def inject_latency(
        self,
        target: str,
        delay_ms: Optional[int] = None,
        probability: float = 1.0,
    ) -> None:
        """
        Inject random latency into async operations.
        
        Args:
            target: Target service name
            delay_ms: Specific delay (random if not specified)
            probability: Chance of injection (0.0 - 1.0)
        """
        if not self._enabled:
            return
        if self._mode not in (ChaosMode.LATENCY, ChaosMode.FULL):
            return
        if random.random() > probability:
            return
        
        delay = delay_ms or random.randint(
            self._latency_config["min_ms"],
            self._latency_config["max_ms"]
        )
        
        logger.info(f"🐵 Chaos: Injecting {delay}ms latency into {target}")
        await asyncio.sleep(delay / 1000.0)
    
    def should_fail_service(self, service: str, probability: Optional[float] = None) -> bool:
        """
        Determine if a service call should fail.
        
        Args:
            service: Service name
            probability: Override default failure probability
            
        Returns:
            True if service should fail
        """
        if not self._enabled:
            return False
        if self._mode not in (ChaosMode.FAILURE, ChaosMode.FULL):
            return False
        if service not in self.TARGET_SERVICES:
            return False
        
        prob = probability or self._failure_probability
        should_fail = random.random() < prob
        
        if should_fail:
            self._injected_failures.add(service)
            logger.warning(f"🐵 Chaos: Service failure triggered for {service}")
        
        return should_fail
    
    def simulate_service_failure(
        self,
        service: str,
        exception_type: Optional[type] = None,
    ) -> None:
        """
        Simulate a service failure by raising exception.
        
        Args:
            service: Service to fail
            exception_type: Exception to raise (default: ConnectionError)
            
        Raises:
            ConnectionError: Simulated connection failure
            TimeoutError: Simulated timeout
        """
        if not self.should_fail_service(service):
            return
        
        exc_type = exception_type or ConnectionError
        error_msg = f"🐵 Chaos: Simulated {service} failure"
        
        logger.error(error_msg)
        raise exc_type(f"ChaosMonkey injected failure: {service} unavailable")
    
    def disrupt_tattva_coherence(
        self,
        current_coherence: float,
        target_coherence: Optional[float] = None,
    ) -> float:
        """
        Disrupt Tattva coherence for testing system response.
        
        Args:
            current_coherence: Current coherence value
            target_coherence: Target coherence (random low if not specified)
            
        Returns:
            Disrupted coherence value
        """
        if not self._enabled:
            return current_coherence
        if self._mode not in (ChaosMode.TATTVA, ChaosMode.FULL):
            return current_coherence
        
        target = target_coherence or random.uniform(0.05, 0.3)
        disrupted = min(current_coherence, target)
        
        logger.warning(
            f"🐵 Chaos: Tattva coherence disrupted: "
            f"{current_coherence:.3f} -> {disrupted:.3f}"
        )
        
        return disrupted
    
    def wrap_async(
        self,
        func: Callable,
        target: str,
        latency_probability: float = 0.5,
        failure_probability: Optional[float] = None,
    ) -> Callable:
        """
        Wrap an async function with chaos injection.
        
        Args:
            func: Async function to wrap
            target: Target service name
            latency_probability: Chance of latency injection
            failure_probability: Override default failure rate
            
        Returns:
            Wrapped function
        """
        async def wrapper(*args, **kwargs):
            # Check for failure first
            if self.should_fail_service(target, failure_probability):
                self.simulate_service_failure(target)
            
            # Inject latency
            await self.inject_latency(target, probability=latency_probability)
            
            # Call original function
            return await func(*args, **kwargs)
        
        return wrapper
    
    def reset(self) -> None:
        """Reset chaos state (clear tracked failures)."""
        self._injected_failures.clear()
        logger.info("🐵 Chaos: State reset")
    
    def get_stats(self) -> Dict:
        """Get chaos injection statistics."""
        return {
            "enabled": self._enabled,
            "mode": self._mode.value,
            "injected_failures": list(self._injected_failures),
            "target_services": list(self.TARGET_SERVICES),
        }


# Global instance for easy access
_chaos_monkey: Optional[ChaosMonkey] = None


def get_chaos_monkey() -> ChaosMonkey:
    """Get or create global ChaosMonkey instance."""
    global _chaos_monkey
    if _chaos_monkey is None:
        _chaos_monkey = ChaosMonkey()
    return _chaos_monkey


def reset_chaos_monkey() -> None:
    """Reset global ChaosMonkey instance."""
    global _chaos_monkey
    _chaos_monkey = None


# Convenience decorators
def with_latency(target: str, delay_ms: Optional[int] = None, probability: float = 0.5):
    """Decorator to inject latency into async function."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            monkey = get_chaos_monkey()
            await monkey.inject_latency(target, delay_ms, probability)
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def with_possible_failure(target: str, probability: Optional[float] = None):
    """Decorator to possibly fail function call."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            monkey = get_chaos_monkey()
            if monkey.should_fail_service(target, probability):
                monkey.simulate_service_failure(target)
            return await func(*args, **kwargs)
        return wrapper
    return decorator
