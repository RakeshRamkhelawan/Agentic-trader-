"""
Enterprise Retry Logic with Exponential Backoff
"""

import asyncio
import logging
import random
from functools import wraps
from typing import Callable, Optional, TypeVar, Tuple

logger = logging.getLogger("Retry")
T = TypeVar("T")


class RetryConfig:
    """Configuration for retry logic"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        exceptions: Tuple[type, ...] = (Exception,)
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.exceptions = exceptions


def calculate_delay(attempt: int, config: RetryConfig) -> float:
    """Calculate delay with exponential backoff and jitter"""
    delay = config.base_delay * (config.exponential_base ** (attempt - 1))
    delay = min(delay, config.max_delay)
    
    if config.jitter:
        # Add randomness to prevent thundering herd
        delay = delay * (0.5 + random.random() * 0.5)
    
    return delay


def retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: Tuple[type, ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int, float], None]] = None
):
    """
    Retry decorator with exponential backoff
    
    Usage:
        @retry(max_attempts=3, base_delay=1.0)
        async def fetch_data():
            return await api.get_data()
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        exponential_base=exponential_base,
        jitter=jitter,
        exceptions=exceptions
    )
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(1, config.max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except config.exceptions as e:
                    last_exception = e
                    
                    if attempt == config.max_attempts:
                        logger.error(f"[{func.__name__}] All {config.max_attempts} attempts failed: {e}")
                        raise
                    
                    delay = calculate_delay(attempt, config)
                    logger.warning(f"[{func.__name__}] Attempt {attempt} failed: {e}. Retrying in {delay:.2f}s...")
                    
                    if on_retry:
                        try:
                            on_retry(e, attempt, delay)
                        except Exception as callback_error:
                            logger.error(f"[{func.__name__}] Retry callback failed: {callback_error}")
                    
                    await asyncio.sleep(delay)
            
            # Should never reach here
            raise last_exception or Exception("Unexpected retry loop exit")
        
        return async_wrapper
    
    return decorator


class RetryableOperation:
    """Class-based retryable operation for more control"""
    
    def __init__(self, config: RetryConfig):
        self.config = config
        self.attempts = 0
        self.successes = 0
        self.failures = 0
    
    async def execute(self, operation: Callable[[], T]) -> T:
        """Execute operation with retry logic"""
        last_exception = None
        
        for attempt in range(1, self.config.max_attempts + 1):
            self.attempts += 1
            
            try:
                result = await operation()
                self.successes += 1
                return result
            except self.config.exceptions as e:
                self.failures += 1
                last_exception = e
                
                if attempt == self.config.max_attempts:
                    raise
                
                delay = calculate_delay(attempt, self.config)
                await asyncio.sleep(delay)
        
        raise last_exception or Exception("Unexpected retry exit")
