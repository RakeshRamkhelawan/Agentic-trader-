import hashlib
import json
from typing import Any, List, Optional

from .adapters import CacheAdapter


class MultiLevelCache:
    def __init__(self, adapters: List[CacheAdapter], default_ttls: List[int]):
        if len(adapters) != len(default_ttls):
            raise ValueError("Number of adapters must match number of TTLs")

        self._adapters = adapters
        self._default_ttls = default_ttls
        self._levels = len(adapters)

    def _generate_key(self, namespace: str, *args, **kwargs) -> str:
        key_parts = [namespace] + [str(arg) for arg in args]
        if kwargs:
            key_parts.append(json.dumps(kwargs, sort_keys=True))

        key_string = ":".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()[:16]

    async def get(self, namespace: str, *args, **kwargs) -> Optional[Any]:
        key = self._generate_key(namespace, *args, **kwargs)

        for level, adapter in enumerate(self._adapters):
            try:
                value = await adapter.get(key)
                if value is not None:
                    await self._backfill(key, value, level)
                    return value
            except Exception:
                continue

        return None

    async def set(
        self,
        namespace: str,
        value: Any,
        *args,
        ttls: Optional[List[int]] = None,
        **kwargs
    ) -> bool:
        key = self._generate_key(namespace, *args, **kwargs)
        ttls = ttls or self._default_ttls

        success = True
        for level, (adapter, ttl) in enumerate(zip(self._adapters, ttls)):
            try:
                await adapter.set(key, value, ttl)
            except Exception:
                success = False

        return success

    async def delete(self, namespace: str, *args, **kwargs) -> bool:
        key = self._generate_key(namespace, *args, **kwargs)

        success = True
        for adapter in self._adapters:
            try:
                await adapter.delete(key)
            except Exception:
                success = False

        return success

    async def clear(self, level: Optional[int] = None) -> bool:
        if level is not None:
            try:
                return await self._adapters[level].clear()
            except Exception:
                return False

        success = True
        for adapter in self._adapters:
            try:
                await adapter.clear()
            except Exception:
                success = False

        return success

    async def _backfill(self, key: str, value: Any, found_at_level: int):
        for level in range(found_at_level):
            try:
                ttl = self._default_ttls[level]
                await self._adapters[level].set(key, value, ttl)
            except Exception:
                continue

    async def get_or_compute(
        self,
        namespace: str,
        compute_fn,
        *args,
        ttls: Optional[List[int]] = None,
        **kwargs
    ) -> Any:
        value = await self.get(namespace, *args, **kwargs)

        if value is not None:
            return value

        value = await compute_fn(*args, **kwargs)

        if value is not None:
            await self.set(namespace, value, *args, ttls=ttls, **kwargs)

        return value
