from functools import lru_cache
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from backend.services.cognitive_orchestrator import CognitiveOrchestrator

router = APIRouter()


# ---------------------------------------------------------------------------
# LLM service singleton (created lazily on first chat request)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _get_llm_service():
    from backend.llm.service import LLMService
    return LLMService.create_from_env()


# ---------------------------------------------------------------------------
# Chat schemas
# ---------------------------------------------------------------------------

class ChatHistoryEntry(BaseModel):
    type: str   # "user" | "ai" | "system"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[ChatHistoryEntry] = []


class ChatResponse(BaseModel):
    response: str


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


@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(body: ChatRequest) -> ChatResponse:
    """
    Conversational AI endpoint for the trading terminal.
    Routes the user message (with optional history context) through the
    configured LLM provider (Ollama / OpenAI / Gemini / DeepSeek).
    """
    llm = _get_llm_service()

    system_prompt = (
        "You are an expert AI trading assistant for the Agentic Trader platform. "
        "You help users analyze markets, manage portfolios, and make informed trading decisions. "
        "Keep responses concise and actionable. Use bullet points where appropriate. "
        "When asked about live prices or portfolio values, advise the user to check "
        "the live dashboard, as you do not have real-time data access."
    )

    # Build conversational context from the last 10 history entries
    history_text = ""
    for entry in body.history[-10:]:
        role = "User" if entry.type == "user" else "Assistant"
        history_text += f"{role}: {entry.content}\n"

    full_prompt = f"{history_text}User: {body.message}"

    try:
        response_text = await llm.circuit_breaker.call(
            llm.provider.generate_text,
            full_prompt,
            system_instruction=system_prompt,
        )
    except Exception:
        if llm.fallback_provider:
            try:
                response_text = await llm.fallback_provider.generate_text(
                    full_prompt,
                    system_instruction=system_prompt,
                )
            except Exception:
                response_text = (
                    "I'm having trouble connecting to the AI service right now. "
                    "Please try again in a moment."
                )
        else:
            response_text = (
                "I'm having trouble connecting to the AI service right now. "
                "Please try again in a moment."
            )

    return ChatResponse(response=response_text)
