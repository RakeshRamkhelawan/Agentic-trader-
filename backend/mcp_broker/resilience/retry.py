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
from collections.abc import Callable
from typing import TypeVar

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
        retryable_exceptions: tuple = (Exception,),
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
    retryable_exceptions: tuple = (Exception,),
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
        retryable_exceptions=retryable_exceptions,
    )

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception: Exception | None = None

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
                        config.initial_delay_ms * (config.backoff_factor**attempt),
                        config.max_delay_ms,
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
        retryable_exceptions=(ConnectionError, TimeoutError, Exception),
    )(func)


def elemental_retry(func: Callable[..., T]) -> Callable[..., T]:
    """Retry decorator optimized for Elemental calculations."""
    return retry(
        max_attempts=2, initial_delay_ms=50, backoff_factor=1.5, retryable_exceptions=(Exception,)
    )(func)
