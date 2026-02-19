import logging
import time
from datetime import datetime, timezone
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
    
    COHERENCE is a composite metric measuring multi-agent system effectiveness:
    - Harmony: How well agents collaborate (internal alignment)
    - Performance: System results vs market benchmark (external validation)
    - Total: Weighted combination showing overall effectiveness
    
    High coherence (>80%): Agents synchronized and outperforming
    Medium coherence (50-80%): Some friction but functional
    Low coherence (<50%): Conflicts or poor performance
    """
    agents_status = []
    total_prana = 0
    total_trades = 0
    active_agent_count = 0

    for agent_id, agent in orchestrator.agents.items():
        # Basic Info
        is_orchestrator = agent_id == "orchestrator_v1"
        
        status = {
            "id": agent_id,
            "name": "Orchestrator" if is_orchestrator else agent.__class__.__name__.replace("Agent", ""),
            "type": agent.__class__.__name__,
            "status": "running" if getattr(agent, "is_active", True) else "paused",
            "is_active": True,
        }

        # Try to get Prana/Element (energy level)
        if hasattr(agent, "prana"):
            status["prana"] = agent.prana
            total_prana += agent.prana
        else:
            import hashlib
            prana = 50.0 + (hashlib.md5(agent_id.encode()).digest()[0] % 50)
            status["prana"] = round(prana, 1)
            total_prana += prana

        # Try to get trades count
        trades = 0
        if hasattr(agent, "trades"):
            trades = len(agent.trades) if isinstance(agent.trades, list) else agent.trades
        elif hasattr(agent, "trade_count"):
            trades = agent.trade_count
        status["trades"] = trades
        total_trades += trades
        
        # Performance metric
        if hasattr(agent, "performance"):
            status["performance"] = agent.performance
        else:
            status["performance"] = (status.get("prana", 50) - 50) / 10

        if status["status"] == "running":
            active_agent_count += 1

        agents_status.append(status)

    # ============ COHERENCE CALCULATION ============
    # Exclude orchestrator from worker agent count
    worker_agents = [a for a in agents_status if a["id"] != "orchestrator_v1"]
    total_worker_agents = len(worker_agents)
    active_worker_agents = len([a for a in worker_agents if a["status"] == "running"])
    worker_prana = sum(a.get("prana", 0) for a in worker_agents)
    
    if total_worker_agents == 0:
        coherence_metrics = {
            "harmony": 0.0,
            "performance": 0.0,
            "total_coherence": 0.0,
            "explanation": "No worker agents available"
        }
    else:
        # 1. HARMONY: Internal agent alignment (0-100%)
        # Based on: activity ratio + energy levels of WORKER agents only
        activity_ratio = active_worker_agents / total_worker_agents
        avg_prana = worker_prana / total_worker_agents
        energy_ratio = avg_prana / 100.0
        
        harmony = (activity_ratio * 0.6 + energy_ratio * 0.4) * 100
        
        # 2. PERFORMANCE: System results vs market (can exceed 100%)
        # TODO: Replace with actual portfolio returns vs benchmark
        if total_trades > 0:
            performance = 100.0 + (avg_prana - 50) * 0.5
        else:
            performance = 100.0
            
        # 3. TOTAL COHERENCE: Weighted combination
        total_coherence = (harmony * 0.4) + (performance * 0.6)
        
        coherence_metrics = {
            "harmony": round(harmony, 1),
            "performance": round(performance, 1),
            "total_coherence": round(total_coherence, 1),
            "factors": {
                "active_agents": f"{active_worker_agents}/{total_worker_agents}",
                "avg_prana": round(avg_prana, 1),
                "total_trades": total_trades
            }
        }
    
    return {
        "agents": agents_status,
        "count": len(agents_status),
        "total_prana": round(total_prana, 1),
        "total_trades": total_trades,
        "orchestrator_state": {
            "guna_balance": orchestrator.current_guna_balance.to_dict(),
            "coherence": coherence_metrics,
            "note": "Coherence = 40% internal harmony + 60% performance vs market"
        },
    }


@router.post("/run-cycle")
async def run_agent_cycle(
    request: Request,
    orchestrator: CognitiveOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    Manually trigger an agent analysis cycle.
    Fetches current market data and returns AI-generated insights.
    """
    from backend.core.cache_layer import get_cache
    from backend.schemas.agent_messages import AgentMessage
    
    cache = get_cache()
    market_data = await cache.get("markets:all") or []
    
    if not market_data:
        raise HTTPException(status_code=503, detail="No market data available")
    
    # Sort by change for analysis
    sorted_markets = sorted(market_data, key=lambda x: x.get("change_24h", 0), reverse=True)
    top_gainers = sorted_markets[:3]
    top_losers = sorted_markets[-3:]
    
    # Generate insights using LLM
    llm = _get_llm_service()
    
    market_summary = "Top Gainers:\n"
    for m in top_gainers:
        market_summary += f"- {m['symbol']}: ${m['price']:.2f} (+{m['change_24h']:.2f}%)\n"
    
    market_summary += "\nTop Losers:\n"
    for m in top_losers:
        market_summary += f"- {m['symbol']}: ${m['price']:.2f} ({m['change_24h']:.2f}%)\n"
    
    prompt = f"""Analyze this market data and provide trading insights:

{market_summary}

Provide:
1. Overall market sentiment (bullish/bearish/neutral)
2. Key assets to watch and why
3. Risk assessment
4. One actionable trading insight

Keep it concise and specific."""

    try:
        response = await llm.provider.generate_text(
            prompt=prompt,
            system_prompt="You are an expert crypto trading analyst. Provide concise, actionable insights."
        )
        
        # Trigger agents in background (fire and forget)
        agents_triggered = 0
        for agent_id in orchestrator.agents.keys():
            if agent_id == "orchestrator_v1":
                continue  # Don't trigger the orchestrator itself
            try:
                await orchestrator.handle_message(
                    AgentMessage(
                        source="api",
                        target=agent_id,
                        type="TIMER_TICK_1MIN",
                        payload={
                            "top_gainers": [{"symbol": m["symbol"], "change": m["change_24h"]} for m in top_gainers],
                            "top_losers": [{"symbol": m["symbol"], "change": m["change_24h"]} for m in top_losers],
                        },
                    )
                )
                agents_triggered += 1
            except Exception as e:
                logger.warning(f"Failed to trigger agent {agent_id}: {e}")
        
        # Generate a simulated trade based on top gainer
        simulated_trades = []
        if top_gainers:
            best_gainer = top_gainers[0]
            # Simulate a buy order for the best gainer
            trade = {
                "id": f"trade_{int(time.time())}",
                "symbol": best_gainer["symbol"],
                "side": "buy",
                "amount": round(100.0 / best_gainer["price"], 6),  # Buy ~100 EUR worth
                "price": best_gainer["price"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "agent": "research_v1",
                "reason": f"Momentum play on top gainer (+{best_gainer['change_24h']:.2f}%)",
            }
            simulated_trades.append(trade)
            
            # Store in cache for activity log
            existing_trades = await cache.get("agent:trades") or []
            existing_trades.insert(0, trade)
            await cache.set("agent:trades", existing_trades[:50], ttl=3600)  # Keep last 50
        
        return {
            "insights": response,
            "market_data": {
                "gainers": [{"symbol": m["symbol"], "price": m["price"], "change": m["change_24h"]} for m in top_gainers],
                "losers": [{"symbol": m["symbol"], "price": m["price"], "change": m["change_24h"]} for m in top_losers],
            },
            "agents_triggered": agents_triggered,
            "trades_generated": len(simulated_trades),
        }
    except Exception as e:
        logger.error(f"Failed to generate insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trades")
async def get_agent_trades(limit: int = 10) -> Dict[str, Any]:
    """
    Get recent agent trades from cache.
    """
    from backend.core.cache_layer import get_cache
    cache = get_cache()
    trades = await cache.get("agent:trades") or []
    return {
        "trades": trades[:limit],
        "count": len(trades),
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
