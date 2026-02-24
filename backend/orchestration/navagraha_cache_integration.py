from datetime import datetime
from typing import Any

from backend.core.cache.decorators import cached
from backend.core.cache.multi_level_cache import MultiLevelCache


class NavagrahaCache:
    def __init__(self, cache: MultiLevelCache):
        self._cache = cache
        self._position_ttls = [300, 900, 3600]
        self._aspect_ttls = [900, 1800, 7200]
        self._rahu_kala_ttls = [3600, 7200, 86400]

    @cached(cache=None, namespace="navagraha:positions", ttls=[300, 900, 3600])
    async def get_planetary_positions(
        self, timestamp: datetime, location: tuple[float, float]
    ) -> dict[str, Any]:
        pass

    @cached(cache=None, namespace="navagraha:aspects", ttls=[900, 1800, 7200])
    async def get_planetary_aspects(
        self, timestamp: datetime, location: tuple[float, float]
    ) -> dict[str, Any]:
        pass

    @cached(
        cache=None,
        namespace="navagraha:rahu_kala",
        ttls=[3600, 7200, 86400],
        key_builder=lambda ts, loc: (ts.date(), loc),
    )
    async def get_rahu_kala_window(
        self, timestamp: datetime, location: tuple[float, float]
    ) -> dict[str, datetime]:
        pass

    async def invalidate_positions(
        self,
        timestamp: datetime | None = None,
        location: tuple[float, float] | None = None,
    ):
        if timestamp and location:
            await self._cache.delete("navagraha:positions", timestamp, location)
        else:
            await self._cache.clear(level=0)

    async def invalidate_all(self):
        await self._cache.clear()

    async def warm_cache(self, timestamps: list[datetime], location: tuple[float, float]):
        for ts in timestamps:
            await self.get_planetary_positions(ts, location)
            await self.get_planetary_aspects(ts, location)
