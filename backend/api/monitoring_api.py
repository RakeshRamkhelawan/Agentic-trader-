"""
Monitoring API — FastAPI router for consciousness architecture observability (Spec §5.4).

Endpoints:
- GET /health — Layer health status
- GET /soul-context — Current soul context
- GET /karma-summary — Karma episode statistics
- POST /kill-switch — Emergency halt
"""

import json
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.monitoring.soul_observer import SoulObserver

logger = logging.getLogger(__name__)

router = APIRouter()

# Shared observer instance (initialized without Redis for testability)
_observer = SoulObserver()

# Kill switch state
_kill_switch_active = False


class KillSwitchRequest(BaseModel):
    confirm: bool = False


@router.get("/health")
async def get_health():
    """Return health status for all 3 consciousness layers."""
    health = await _observer.get_health()
    return health


@router.get("/soul-context")
async def get_soul_context():
    """Return current soul context from Redis."""
    try:
        if _observer.redis_client:
            ctx_json = await _observer.redis_client.get("soul:context")
            if ctx_json:
                return json.loads(ctx_json)
        return {"warning": "No soul context available"}
    except Exception as e:
        return {"warning": f"Error fetching soul context: {e}"}


@router.get("/karma-summary")
async def get_karma_summary():
    """Return karma episode statistics."""
    return {
        "episode_count": 0,
        "avg_karma": 0.0,
        "recent_regime": "unknown",
    }


@router.post("/kill-switch")
async def activate_kill_switch(req: KillSwitchRequest):
    """Emergency halt — requires confirmation."""
    global _kill_switch_active

    if not req.confirm:
        raise HTTPException(
            status_code=400, detail="Confirmation required: set confirm=true"
        )

    _kill_switch_active = True
    logger.warning("KILL SWITCH ACTIVATED")
    return {"status": "activated", "kill_switch": True}
