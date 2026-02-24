import logging
from datetime import datetime

from backend.core.cache_layer import get_cache
from backend.core.navagraha.models import NavagrahaState

logger = logging.getLogger(__name__)


class NavagrahaCache:
    CACHE_KEY_PREFIX = "navagraha:state"
    TTL_SECONDS = 300  # 5 minutes

    def __init__(self):
        self.cache = get_cache()

    def _generate_key(self, lat: float, lon: float, dt: datetime) -> str:
        # Bucket time to nearest 5 minutes to align with cache TTL and avoid infinite keys
        # Timestamp format: YYYYMMDDHHmm
        # We round down minutes to nearest 5
        minute = (dt.minute // 5) * 5
        timestamp = dt.strftime(f"%Y%m%d%H{minute:02d}")
        # Round lat/lon to 2 decimal places to avoid float precision issues in keys
        return f"{self.CACHE_KEY_PREFIX}:{lat:.2f}-{lon:.2f}:{timestamp}"

    async def get_state(self, lat: float, lon: float, dt: datetime) -> NavagrahaState | None:
        key = self._generate_key(lat, lon, dt)
        data = await self.cache.get(key)
        if data:
            try:
                return NavagrahaState.model_validate(data)
            except Exception as e:
                logger.error(f"Failed to deserialize NavagrahaState from cache: {e}")
                return None
        return None

    async def set_state(self, state: NavagrahaState):
        key = self._generate_key(state.location_lat, state.location_lon, state.calculated_at)
        # Convert to dict with ISO formatted datetimes
        data = state.model_dump(mode="json")
        await self.cache.set(key, data, ttl=self.TTL_SECONDS)
