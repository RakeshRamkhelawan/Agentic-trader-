from typing import Optional

from fastapi import APIRouter, Depends, Query

from backend.core.navagraha.models import NavagrahaState
from backend.core.navagraha.service import NavagrahaService

router = APIRouter()


# Dependency
def get_navagraha_service():
    return NavagrahaService()


@router.get("/current-state", response_model=NavagrahaState)
async def get_current_navagraha_state(
    lat: float = Query(28.61, description="Latitude (default: New Delhi)"),
    lon: float = Query(77.20, description="Longitude (default: New Delhi)"),
    service: NavagrahaService = Depends(get_navagraha_service),
):
    """
    Get the current Navagraha (9 Planets) state, including positions, retrogrades, and Guna context.
    Default location is New Delhi for Vedic accuracy unless specified.
    """
    return await service.get_current_state(lat, lon)
