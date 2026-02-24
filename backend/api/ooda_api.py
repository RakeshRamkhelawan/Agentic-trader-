from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from backend.core.system_identity import SystemIdentity

router = APIRouter()


# Dependency to get SystemIdentity from App State
def get_system_identity(request: Request) -> SystemIdentity:
    if not hasattr(request.app.state, "system_identity") or not request.app.state.system_identity:
        raise HTTPException(status_code=503, detail="System Identity not initialized")
    return request.app.state.system_identity


@router.get("/current-cycle")
async def get_current_ooda_cycle(
    system: SystemIdentity = Depends(get_system_identity),
) -> dict[str, Any]:
    """
    Get the current OODA Loop Cycle state from the System Identity.
    Includes Phase (Orient/Decide/etc.), Coherence, and Tattva Metrics.
    """
    stats = system.get_system_statistics()

    # Map SystemIdentity stats to OODA Cycle format expected by Frontend
    return {
        "phase": "ORIENT",  # Infer from last active Tattva or maintain explicit phase state
        "cycle_id": f"cycle_{stats['system_state']['total_experiences']}",
        "coherence": stats["system_state"]["coherence"],
        "confidence": stats["system_state"]["confidence"],
        "tattva_metrics": stats.get("tattva_metrics", {}),
        "last_update": "2024-01-01T00:00:00Z",  # TODO: Add timestamp to system stats
    }
