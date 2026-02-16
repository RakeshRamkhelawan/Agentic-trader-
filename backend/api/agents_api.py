from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from backend.services.cognitive_orchestrator import CognitiveOrchestrator

router = APIRouter()


# Dependency to get Orchestrator from App State
def get_orchestrator(request: Request) -> CognitiveOrchestrator:
    if (
        not hasattr(request.app.state, "orchestrator")
        or not request.app.state.orchestrator
    ):
        raise HTTPException(
            status_code=503, detail="Cognitive Orchestrator not initialized"
        )
    return request.app.state.orchestrator


@router.get("/status")
async def get_agents_status(
    orchestrator: CognitiveOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    Get the status of all agents managed by the Cognitive Orchestrator.
    Returns their current state, prana (if applicable), and activity.
    """
    agents_status = {}

    for agent_id, agent in orchestrator.agents.items():
        # Basic Info
        status = {
            "id": agent_id,
            "type": agent.__class__.__name__,
            "is_active": True,  # Simplified for now
        }

        # Try to get Prana/Element
        if hasattr(agent, "prana"):
            status["prana"] = agent.prana

        # Try to get specific state
        if hasattr(agent, "state"):
            status["state"] = agent.state

        agents_status[agent_id] = status

    return {
        "agents": agents_status,
        "count": len(agents_status),
        "orchestrator_state": {
            "guna_balance": orchestrator.current_guna_balance.to_dict(),
            "global_coherence": 0.95,  # Placeholder until SystemIdentity integration
        },
    }
