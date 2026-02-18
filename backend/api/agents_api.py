import logging
from functools import lru_cache
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from backend.services.cognitive_orchestrator import CognitiveOrchestrator

router = APIRouter()
logger = logging.getLogger(__name__)


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
    type: str  # "user" | "ai" | "system"
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
    Includes live market data context for accurate analysis.
    """
    llm = _get_llm_service()
    
    # Fetch live market data for context
    from backend.core.cache_layer import get_cache
    cache = get_cache()
    market_data = await cache.get("markets:all") or []
    
    # Build market context summary
    market_context = ""
    if market_data:
        # Sort by change to get gainers/losers
        sorted_markets = sorted(market_data, key=lambda x: x.get("change_24h", 0), reverse=True)
        top_gainers = sorted_markets[:3]
        top_losers = sorted_markets[-3:]
        
        market_context = "\n\nLIVE MARKET DATA:\n"
        market_context += "Top Gainers:\n"
        for m in top_gainers:
            market_context += f"- {m['symbol']}: ${m['price']:.2f} ({m['change_24h']:+.2f}%)\n"
        market_context += "\nTop Losers:\n"
        for m in top_losers:
            market_context += f"- {m['symbol']}: ${m['price']:.2f} ({m['change_24h']:+.2f}%)\n"
        market_context += f"\nTotal assets tracked: {len(market_data)}\n"

    system_prompt = (
        "You are an expert AI trading assistant for the Agentic Trader platform. "
        "You help users analyze markets, manage portfolios, and make informed trading decisions. "
        "Keep responses concise and actionable. Use bullet points where appropriate. "
        "Base your analysis on the live market data provided in the context. "
        "Be specific about price movements and percentages when answering."
    )

    # Build conversational context from the last 10 history entries
    history_text = ""
    for entry in body.history[-10:]:
        role = "User" if entry.type == "user" else "Assistant"
        history_text += f"{role}: {entry.content}\n"

    full_prompt = f"{history_text}User: {body.message}{market_context}"

    try:
        response_text = await llm.circuit_breaker.call(
            llm.provider.generate_text,
            prompt=full_prompt,
            system_prompt=system_prompt,
        )
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        if llm.fallback_provider:
            try:
                response_text = await llm.fallback_provider.generate_text(
                    full_prompt,
                    system_prompt=system_prompt,
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
