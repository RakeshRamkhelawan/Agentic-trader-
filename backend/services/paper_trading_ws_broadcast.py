"""
Broadcast functionality for Paper Trading WebSocket
"""

import logging
from datetime import datetime
from typing import Any

from backend.api.paper_trading_ws_simple import broadcast_to_clients

logger = logging.getLogger(__name__)


async def broadcast_trade(trade_data: dict[str, Any]):
    """Broadcast a trade to all connected WebSocket clients."""
    message = {
        "type": "trade",
        "data": {**trade_data, "timestamp": datetime.utcnow().isoformat()},
    }
    await broadcast_to_clients(message)
    logger.debug(f"Broadcasted trade: {trade_data.get('symbol')}")


async def broadcast_portfolio(
    cash: float, total_value: float, pnl: float, pnl_pct: float, positions: dict
):
    """Broadcast portfolio update."""
    message = {
        "type": "portfolio",
        "data": {
            "cash": cash,
            "total_value": total_value,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
            "positions": positions,
            "timestamp": datetime.utcnow().isoformat(),
        },
    }
    await broadcast_to_clients(message)


async def broadcast_agent_decision(
    agent: str,
    strategy: str,
    symbol: str,
    decision: str,
    confidence: float,
    reason: str,
    executed: bool,
):
    """Broadcast agent decision to all connected clients."""
    message = {
        "type": "agent_decision",
        "data": {
            "timestamp": datetime.utcnow().isoformat(),
            "agent": agent,
            "strategy": strategy,
            "symbol": symbol,
            "decision": decision,
            "confidence": confidence,
            "reason": reason,
            "executed": executed,
        },
    }
    await broadcast_to_clients(message)
    logger.debug(f"Broadcasted agent decision: {agent} {decision} {symbol}")


async def broadcast_triad_update(
    agents: list,
    meta_agents: list,
    memory_banks: list,
    consensus_reached: int,
    disputes: int,
    total_decisions: int,
):
    """Broadcast federated triad state update."""
    message = {
        "type": "triad_update",
        "data": {
            "agents": agents,
            "meta_agents": meta_agents,
            "memory_banks": memory_banks,
            "consensus_reached": consensus_reached,
            "disputes": disputes,
            "total_decisions": total_decisions,
            "timestamp": datetime.utcnow().isoformat(),
        },
    }
    await broadcast_to_clients(message)
    logger.debug(f"Broadcasted triad update: {total_decisions} decisions")


async def broadcast_stats(
    total_trades: int, symbols_traded: int, buy_sell_ratio: str, agent_performance: dict
):
    """Broadcast stats update."""
    message = {
        "type": "stats",
        "data": {
            "total_trades": total_trades,
            "symbols_traded": symbols_traded,
            "buy_sell_ratio": buy_sell_ratio,
            "agent_performance": agent_performance,
            "timestamp": datetime.utcnow().isoformat(),
        },
    }
    await broadcast_to_clients(message)


async def broadcast_cognitive_insight(insight_data: dict[str, Any]):
    """Broadcast a cognitive AI decision insight to all connected clients."""
    message = {
        "type": "cognitive_insight",
        "data": {**insight_data, "broadcast_at": datetime.utcnow().isoformat()},
    }
    await broadcast_to_clients(message)
    logger.debug(
        f"Broadcasted cognitive insight: {insight_data.get('symbol')} -> {insight_data.get('final_decision')}"
    )


async def broadcast_tuning_update(tuning_data: dict[str, Any]):
    """Broadcast current adaptive weights and tuning stats to all connected clients."""
    message = {
        "type": "tuning_update",
        "data": {**tuning_data, "timestamp": datetime.utcnow().isoformat()},
    }
    await broadcast_to_clients(message)
    logger.debug(f"Broadcasted tuning update: {list(tuning_data.keys())}")
