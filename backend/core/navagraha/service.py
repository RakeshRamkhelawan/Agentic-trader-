from datetime import datetime, timezone
from typing import Optional
from backend.core.navagraha.ephemeris import EphemerisCalculator
from backend.core.navagraha.cache import NavagrahaCache
from backend.core.navagraha.models import NavagrahaState

class NavagrahaService:
    def __init__(self, calculator: Optional[EphemerisCalculator] = None, cache: Optional[NavagrahaCache] = None):
        self.calculator = calculator or EphemerisCalculator()
        self.cache = cache or NavagrahaCache()

    async def get_current_state(self, lat: float, lon: float, dt: Optional[datetime] = None) -> NavagrahaState:
        if dt is None:
            dt = datetime.now(timezone.utc)
            
        # Try Cache
        cached_state = await self.cache.get_state(lat, lon, dt)
        if cached_state:
            return cached_state

        # Calculate
        state = self.calculator.calculate_navagraha_state(dt, lat, lon)

        # Cache
        await self.cache.set_state(state)

        return state
