import functools
from typing import Callable, Optional

from .multi_level_cache import MultiLevelCache


def cached(
    cache: MultiLevelCache,
    namespace: str,
    ttls: Optional[list[int]] = None,
    key_builder: Optional[Callable] = None,
):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if key_builder:
                cache_args = key_builder(*args, **kwargs)
            else:
                cache_args = args[1:] if args else []

            return await cache.get_or_compute(
                namespace, func, *cache_args, ttls=ttls, **kwargs
            )

        return wrapper

    return decorator
