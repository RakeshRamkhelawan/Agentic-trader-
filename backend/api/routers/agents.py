"""
Agents Router

API endpoints for AI agents management and interaction.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List

router = APIRouter(prefix="/agents", tags=["Agents"])


@router.get("/status")
async def get_agents_status() -> Dict[str, Any]:
    """Get status of all AI agents."""
    return {
        "agents": {
            "elemental_fire": {
                "type": "elemental",
                "is_active": True,
                "prana": 85.5,
                "state": {"last_signal": "buy", "confidence": 0.82}
            },
            "elemental_water": {
                "type": "elemental",
                "is_active": True,
                "prana": 78.2,
                "state": {"last_signal": "hold", "confidence": 0.65}
            },
            "elemental_earth": {
                "type": "elemental",
                "is_active": True,
                "prana": 92.1,
                "state": {"last_signal": "accumulate", "confidence": 0.91}
            },
            "elemental_air": {
                "type": "elemental",
                "is_active": True,
                "prana": 71.3,
                "state": {"last_signal": "distribute", "confidence": 0.74}
            },
            "elemental_ether": {
                "type": "consensus",
                "is_active": True,
                "prana": 88.7,
                "state": {"consensus": "buy", "agreement": 0.78}
            }
        },
        "count": 5,
        "orchestrator_state": {
            "global_coherence": 0.83,
            "coherence": {
                "harmony": 85,
                "performance": 100,
                "total_coherence": 83,
                "factors": {
                    "active_agents": "5/5",
                    "avg_prana": 83.16,
                    "total_trades": 42
                }
            }
        }
    }


@router.post("/chat")
async def chat_with_advisor(message: str, history: List[Dict[str, str]] = None) -> Dict[str, str]:
    """Chat with AI trading advisor."""
    if history is None:
        history = []

    # Simple mock response
    responses = {
        "market": "Based on current market conditions and VedAstro analysis, I see a bullish trend emerging. The elemental consensus suggests accumulating positions.",
        "trade": "Consider a measured approach. The Fire agent indicates strong momentum, but Water suggests caution. A 60% position size might be optimal.",
        "risk": "Current portfolio risk is within acceptable limits. VaR is at 2.3% with a Sharpe ratio of 1.8. Consider diversifying into BTC-EUR.",
    }

    # Find best matching response
    response_text = responses.get("market")
    for key, value in responses.items():
        if key in message.lower():
            response_text = value
            break

    return {"response": response_text}


@router.post("/run-cycle")
async def run_agent_cycle() -> Dict[str, Any]:
    """Trigger a full agent analysis cycle."""
    return {
        "insights": "Market analysis complete. Elemental consensus indicates bullish sentiment with 78% confidence. Fire and Earth agents strongly favor accumulation.",
        "market_data": {
            "gainers": [
                {"symbol": "BTC-EUR", "change_24h": 2.5},
                {"symbol": "ETH-EUR", "change_24h": 1.8}
            ],
            "losers": [
                {"symbol": "ADA-EUR", "change_24h": -0.5}
            ]
        },
        "agents_triggered": 5,
        "trades_generated": 2
    }


@router.get("/trades")
async def get_agent_trades() -> Dict[str, Any]:
    """Get AI-generated trade history."""
    return {
        "trades": [
            {
                "id": "agent-trade-001",
                "symbol": "BTC-EUR",
                "side": "buy",
                "amount": 0.1,
                "price": 67234.50,
                "timestamp": "2026-02-22T14:30:00Z",
                "agent": "elemental_fire",
                "confidence": 0.82
            },
            {
                "id": "agent-trade-002",
                "symbol": "ETH-EUR",
                "side": "buy",
                "amount": 1.5,
                "price": 3456.78,
                "timestamp": "2026-02-22T13:15:00Z",
                "agent": "elemental_ether",
                "confidence": 0.78
            }
        ],
        "count": 2
    }
