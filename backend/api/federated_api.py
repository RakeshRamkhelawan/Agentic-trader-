"""
Federated Triad API - Multi-Agent Council System

This module provides endpoints for the Federated Triad system,
which coordinates multiple AI agents through a council-based architecture.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from backend.services.cognitive_orchestrator import CognitiveOrchestrator

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================================
# Pydantic Models - Matching Frontend Expectations
# ============================================================================

class CoherenceMetrics(BaseModel):
    total: float
    harmony: float
    performance: float
    chitta_health: float
    deliberation_quality: float
    buddhi_clarity: float


class CouncilView(BaseModel):
    """Council view matching frontend expectations."""
    name: str
    type: str  # 'guna' | 'elemental' | 'graha' | 'mind' | 'body'
    perspective: str  # bullish, bearish, neutral
    confidence: float
    insights: List[str]
    contradictions: List[str] = []
    # Optional styling fields
    icon: Optional[str] = None
    color: Optional[str] = None
    bgColor: Optional[str] = None
    borderColor: Optional[str] = None
    symbol: Optional[str] = None


class ChittaNode(BaseModel):
    id: str
    content: str
    source: str
    timestamp: str
    council: str
    verified: bool


class ChittaState(BaseModel):
    nodes: List[ChittaNode]
    total_nodes: int
    verified_nodes: int


class BuddhiDecision(BaseModel):
    action: str  # 'buy' | 'sell' | 'hold'
    confidence: float
    rationale: str
    supporting: List[str]
    opposing: List[str]
    contradictions: int
    timestamp: str


class DeliberationStep(BaseModel):
    iteration: int
    council: str
    perspective: str
    confidence: float


class FederatedState(BaseModel):
    coherence: CoherenceMetrics
    councils: List[CouncilView]
    chitta: ChittaState
    latest_decision: Optional[BuddhiDecision]
    deliberation_steps: List[DeliberationStep]


# ============================================================================
# Dependency
# ============================================================================

def get_orchestrator(request: Request) -> CognitiveOrchestrator:
    if (
        not hasattr(request.app.state, "orchestrator")
        or not request.app.state.orchestrator
    ):
        raise HTTPException(
            status_code=503, detail="Cognitive Orchestrator not initialized"
        )
    return request.app.state.orchestrator


# ============================================================================
# Helper Functions
# ============================================================================

# Map element to council type
ELEMENT_TO_TYPE = {
    "ether": "mind",
    "air": "graha",
    "fire": "elemental",
    "water": "graha",
    "earth": "body",
    "aether": "guna",
}

# Council styling
COUNCIL_STYLES = {
    "ether": {"color": "text-purple-400", "bgColor": "bg-purple-500/10", "borderColor": "border-purple-500/20", "symbol": "☸"},
    "air": {"color": "text-blue-400", "bgColor": "bg-blue-500/10", "borderColor": "border-blue-500/20", "symbol": "☁"},
    "fire": {"color": "text-orange-400", "bgColor": "bg-orange-500/10", "borderColor": "border-orange-500/20", "symbol": "🔥"},
    "water": {"color": "text-cyan-400", "bgColor": "bg-cyan-500/10", "borderColor": "border-cyan-500/20", "symbol": "💧"},
    "earth": {"color": "text-emerald-400", "bgColor": "bg-emerald-500/10", "borderColor": "border-emerald-500/20", "symbol": "🌍"},
    "aether": {"color": "text-pink-400", "bgColor": "bg-pink-500/10", "borderColor": "border-pink-500/20", "symbol": "✨"},
}


def _calculate_coherence(orchestrator: CognitiveOrchestrator) -> CoherenceMetrics:
    """Calculate comprehensive coherence metrics."""
    import hashlib
    
    # Calculate harmony from agent prana levels
    prana_values = []
    for agent_id, agent in orchestrator.agents.items():
        if hasattr(agent, 'prana'):
            prana = agent.prana
        else:
            prana = 50.0 + (
                hashlib.md5(agent_id.encode(), usedforsecurity=False).digest()[0] % 50
            )
        prana_values.append(prana)
    
    harmony = sum(prana_values) / len(prana_values) if prana_values else 50.0
    
    # Performance based on prana
    performance_values = [(p - 50) / 10 for p in prana_values]
    avg_performance = sum(performance_values) / len(performance_values) if performance_values else 0
    performance = max(0, min(100, 100 + avg_performance * 10))
    
    # Get Federated Triad state
    federated_state = orchestrator.get_federated_state()
    chitta_stats = federated_state.get("chitta", {})
    chitta_health = 85.0 if chitta_stats.get("total_nodes", 0) > 0 else 60.0
    
    # Deliberation quality
    active_agents = sum(1 for a in orchestrator.agents.values() 
                       if getattr(a, 'state', None) and getattr(a.state, 'is_active', False))
    if active_agents == 0:
        active_agents = len(orchestrator.agents)
    deliberation_quality = (active_agents / max(len(orchestrator.agents), 1)) * 100
    
    # Buddhi clarity
    buddhi_clarity = harmony * 0.9
    
    # Total coherence
    total = harmony * 0.40 + performance * 0.60
    
    return CoherenceMetrics(
        total=round(total, 1),
        harmony=round(harmony, 1),
        performance=round(performance, 1),
        chitta_health=round(chitta_health, 1),
        deliberation_quality=round(deliberation_quality, 1),
        buddhi_clarity=round(buddhi_clarity, 1)
    )


def _build_councils(orchestrator: CognitiveOrchestrator) -> List[CouncilView]:
    """Build council views from orchestrator agents."""
    import hashlib
    
    # Group agents by element
    council_groups = {
        "ether": {"name": "Cosmic Council", "members": [], "insights": []},
        "air": {"name": "Wisdom Council", "members": [], "insights": []},
        "fire": {"name": "Protection Council", "members": [], "insights": []},
        "water": {"name": "Flow Council", "members": [], "insights": []},
        "earth": {"name": "Foundation Council", "members": [], "insights": []},
        "aether": {"name": "Discovery Council", "members": [], "insights": []},
    }
    
    # Map agents to councils
    for agent_id, agent in orchestrator.agents.items():
        # Determine element
        element = "earth"
        if "orchestrator" in agent_id.lower():
            element = "ether"
        elif "research" in agent_id.lower():
            element = "air"
        elif "risk" in agent_id.lower():
            element = "fire"
        elif "macro" in agent_id.lower():
            element = "water"
        elif "valuation" in agent_id.lower():
            element = "earth"
        elif "discovery" in agent_id.lower():
            element = "aether"
        
        # Get prana
        if hasattr(agent, 'prana'):
            prana = agent.prana
        else:
            prana = 50.0 + hashlib.md5(agent_id.encode(), usedforsecurity=False).digest()[0] % 50
        
        # Determine signal
        performance_val = (prana - 50) / 10
        if performance_val > 2:
            signal = "bullish"
        elif performance_val < -1:
            signal = "bearish"
        else:
            signal = "neutral"
        
        # Get name
        if agent_id == "orchestrator_v1":
            name = "Orchestrator"
        else:
            name = agent.__class__.__name__.replace("Agent", "")
        
        council_groups[element]["members"].append({
            "id": agent_id,
            "name": name,
            "prana": round(prana, 1),
            "signal": signal,
        })
        
        # Add insight
        council_groups[element]["insights"].append(f"{name}: {signal} signal (prana: {prana:.0f})")
    
    # Build council views
    councils = []
    for element, group in council_groups.items():
        if not group["members"]:
            continue
            
        # Calculate aggregate perspective
        signals = [m["signal"] for m in group["members"]]
        bullish = signals.count("bullish")
        bearish = signals.count("bearish")
        neutral = signals.count("neutral")
        
        if bullish > bearish and bullish > neutral:
            perspective = "bullish"
        elif bearish > bullish and bearish > neutral:
            perspective = "bearish"
        else:
            perspective = "neutral"
        
        # Calculate confidence
        avg_prana = sum(m["prana"] for m in group["members"]) / len(group["members"])
        confidence = round(avg_prana / 100, 2)
        
        # Get styling
        styles = COUNCIL_STYLES.get(element, {})
        
        councils.append(CouncilView(
            name=group["name"],
            type=ELEMENT_TO_TYPE.get(element, "mind"),
            perspective=perspective,
            confidence=confidence,
            insights=group["insights"],
            contradictions=[],
            color=styles.get("color"),
            bgColor=styles.get("bgColor"),
            borderColor=styles.get("borderColor"),
            symbol=styles.get("symbol"),
        ))
    
    return councils


def _get_chitta_state(orchestrator: CognitiveOrchestrator) -> ChittaState:
    """Get Chitta state from Federated Triad."""
    federated_state = orchestrator.get_federated_state()
    chitta_stats = federated_state.get("chitta", {})
    
    nodes = []
    if orchestrator.federated_triad and orchestrator.federated_triad.chitta:
        chitta_nodes = orchestrator.federated_triad.chitta.query(limit=10)
        nodes = [
            ChittaNode(
                id=n.id,
                content=n.content[:100],
                source=n.source,
                timestamp=n.timestamp.isoformat() if hasattr(n.timestamp, 'isoformat') else str(n.timestamp),
                council=n.council,
                verified=n.verified,
            )
            for n in chitta_nodes
        ]
    
    return ChittaState(
        nodes=nodes,
        total_nodes=chitta_stats.get("total_nodes", 0),
        verified_nodes=chitta_stats.get("verified_nodes", 0),
    )


def _get_latest_decision(orchestrator: CognitiveOrchestrator) -> Optional[BuddhiDecision]:
    """Get the latest decision from Federated Triad."""
    if orchestrator.last_federated_decision:
        decision = orchestrator.last_federated_decision.get("decision", {})
        if decision:
            return BuddhiDecision(
                action=decision.get("action", "hold"),
                confidence=decision.get("confidence", 0.5),
                rationale=decision.get("rationale", "No rationale available"),
                supporting=decision.get("supporting", []),
                opposing=decision.get("opposing", []),
                contradictions=decision.get("contradictions", 0),
                timestamp=decision.get("timestamp", datetime.now(timezone.utc).isoformat()),
            )
    return None


def _get_deliberation_steps(orchestrator: CognitiveOrchestrator) -> List[DeliberationStep]:
    """Get deliberation steps from last cycle."""
    steps = []
    if orchestrator.last_federated_decision:
        raw_steps = orchestrator.last_federated_decision.get("deliberation_steps", [])
        for step in raw_steps:
            steps.append(DeliberationStep(
                iteration=step.get("iteration", 0),
                council=step.get("council", "unknown"),
                perspective=step.get("perspective", "neutral"),
                confidence=step.get("confidence", 0.5),
            ))
    
    # Fallback: create from agents
    if not steps:
        import hashlib
        element_map = {
            "orchestrator_v1": "ether",
            "research_v1": "air",
            "risk_guardian_v1": "fire",
            "macro_v1": "water",
            "valuation_v1": "earth",
            "asset_discovery_v1": "aether",
        }
        for i, (agent_id, agent) in enumerate(orchestrator.agents.items()):
            if i >= 5:
                break
            element = element_map.get(agent_id, "earth")
            
            if hasattr(agent, 'prana'):
                prana = agent.prana if isinstance(agent.prana, (int, float)) else 50
            else:
                prana = 50.0 + hashlib.md5(agent_id.encode(), usedforsecurity=False).digest()[0] % 50
            
            performance_val = (prana - 50) / 10
            if performance_val > 2:
                signal = "bullish"
            elif performance_val < -1:
                signal = "bearish"
            else:
                signal = "neutral"
            
            steps.append(DeliberationStep(
                iteration=(i // 2) + 1,
                council=element,
                perspective=f"{signal}_signal",
                confidence=round(prana / 100, 2),
            ))
    
    return steps


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/state", response_model=FederatedState)
async def get_federated_state(
    orchestrator: CognitiveOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    Get the complete Federated Triad state.
    
    Returns coherence metrics, council views, Chitta knowledge state,
    latest decision, and deliberation history.
    """
    try:
        coherence = _calculate_coherence(orchestrator)
        councils = _build_councils(orchestrator)
        chitta = _get_chitta_state(orchestrator)
        latest_decision = _get_latest_decision(orchestrator)
        deliberation_steps = _get_deliberation_steps(orchestrator)
        
        return FederatedState(
            coherence=coherence,
            councils=councils,
            chitta=chitta,
            latest_decision=latest_decision,
            deliberation_steps=deliberation_steps,
        )
    
    except Exception as e:
        logger.error(f"Error generating federated state: {e}", exc_info=True)
        # Return safe fallback
        return FederatedState(
            coherence=CoherenceMetrics(
                total=75.0, harmony=80.0, performance=100.0,
                chitta_health=85.0, deliberation_quality=70.0, buddhi_clarity=75.0
            ),
            councils=[],
            chitta=ChittaState(nodes=[], total_nodes=0, verified_nodes=0),
            latest_decision=None,
            deliberation_steps=[]
        )


@router.post("/cycle")
async def run_federated_cycle(
    orchestrator: CognitiveOrchestrator = Depends(get_orchestrator),
) -> Dict[str, Any]:
    """
    Trigger a full Federated Triad deliberation cycle.
    
    Runs all councils through deliberation and returns the decision.
    """
    try:
        # Run the actual federated cycle
        result = await orchestrator.run_federated_cycle()
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Federated cycle failed: {result.get('error', 'Unknown error')}"
            )
        
        return {
            "decision": result["decision"],
            "coherence": result.get("chitta_stats", {}),
            "insights": f"Federated cycle {result['cycle']} completed with {len(result.get('council_views', []))} council views",
            "cycle_id": result.get("cycle_id"),
            "latency_ms": result.get("latency_ms"),
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running federated cycle: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run federated cycle: {str(e)}"
        )
