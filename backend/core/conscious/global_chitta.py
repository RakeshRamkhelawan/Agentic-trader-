"""
Global Chitta - Shared Consciousness Across All Agents (v12 MetaOrchestrator)

Synchronizes learning across all 27+ agents for collective intelligence.
"""

import asyncio
import json
import logging
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.core.conscious.chitta_memory import ChittaMemory, TradeExperience

logger = logging.getLogger(__name__)


class GlobalChitta:
    """
    Global consciousness shared across all agents.

    Features:
    - Cross-agent learning sync
    - Collective winrate tracking
    - Global market regime detection
    - Meta-decision optimization
    """

    def __init__(self, storage_path: str = "backend/data/conscious_memory/global"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Global trade memory (anonymized)
        self.global_trades: List[Dict] = []

        # Per-agent performance tracking
        self.agent_winrates: Dict[str, Dict] = defaultdict(
            lambda: {
                "wins": 0,
                "losses": 0,
                "total_pnl": 0.0,
                "avg_harmony": 0.0,
                "trades": [],
            }
        )

        # Collective insights
        self.collective_insights: List[Dict] = []

        # Market regime memory
        self.regime_memory: Dict[str, List] = defaultdict(list)

        self._load_global_memory()
        logger.info(f"GlobalChitta initialized | Trades: {len(self.global_trades)}")

    def sync_from_agent(self, agent_name: str, agent_chitta: ChittaMemory):
        """Sync agent's Chitta into global consciousness."""
        try:
            # Get agent's trades
            agent_trades = [
                {
                    "agent": agent_name,
                    "timestamp": trade.timestamp,
                    "symbol": trade.symbol,
                    "action": trade.action,
                    "pnl": trade.pnl,
                    "confidence": trade.confidence,
                    "market_regime": trade.market_regime,
                    "reasoning": trade.reasoning,
                }
                for trade in agent_chitta.trades
            ]

            # Update global trades
            self.global_trades.extend(agent_trades)

            # Update agent winrate
            wins = sum(1 for t in agent_trades if t["pnl"] > 0)
            losses = sum(1 for t in agent_trades if t["pnl"] <= 0)
            total_pnl = sum(t["pnl"] for t in agent_trades)

            self.agent_winrates[agent_name]["wins"] += wins
            self.agent_winrates[agent_name]["losses"] += losses
            self.agent_winrates[agent_name]["total_pnl"] += total_pnl
            self.agent_winrates[agent_name]["trades"].extend(agent_trades)

            logger.info(f"Synced {len(agent_trades)} trades from {agent_name}")
            self._save_global_memory()

        except Exception as e:
            logger.error(f"Failed to sync from {agent_name}: {e}")

    def sync_to_agent(self, agent_name: str, agent_chitta: ChittaMemory):
        """Sync global insights to specific agent."""
        try:
            # Get similar trades from other agents
            other_trades = [t for t in self.global_trades if t["agent"] != agent_name]

            # Add to agent's memory (cross-agent learning)
            for trade_data in other_trades[-100:]:  # Last 100 only
                experience = TradeExperience(
                    timestamp=trade_data["timestamp"],
                    symbol=trade_data["symbol"],
                    action=trade_data["action"],
                    confidence=trade_data["confidence"],
                    pnl=trade_data["pnl"],
                    market_regime=trade_data["market_regime"],
                    reasoning=f"[Global] {trade_data['reasoning']}",
                )
                agent_chitta.store_trade(experience)

            logger.info(f"Synced {len(other_trades[-100:])} global trades to {agent_name}")

        except Exception as e:
            logger.error(f"Failed to sync to {agent_name}: {e}")

    def get_collective_consensus(self, symbol: str, market_state: Dict) -> Dict[str, Any]:
        """
        Get collective consensus from all agents for a symbol.

        Returns:
            {
                "consensus_action": "BUY|SELL|HOLD",
                "confidence": float,
                "supporting_agents": [str],
                "harmony_score": float,
                "collective_reasoning": str
            }
        """
        try:
            # Get relevant trades for symbol
            symbol_trades = [t for t in self.global_trades if t["symbol"] == symbol]

            if not symbol_trades:
                return {
                    "consensus_action": "HOLD",
                    "confidence": 0.5,
                    "supporting_agents": [],
                    "harmony_score": 0.0,
                    "collective_reasoning": "No historical data",
                }

            # Count actions
            buy_votes = sum(1 for t in symbol_trades if t["action"] == "BUY")
            sell_votes = sum(1 for t in symbol_trades if t["action"] == "SELL")
            hold_votes = sum(1 for t in symbol_trades if t["action"] == "HOLD")

            total = len(symbol_trades)

            # Determine consensus
            if buy_votes > sell_votes and buy_votes > hold_votes:
                action = "BUY"
                confidence = buy_votes / total
            elif sell_votes > buy_votes and sell_votes > hold_votes:
                action = "SELL"
                confidence = sell_votes / total
            else:
                action = "HOLD"
                confidence = hold_votes / total

            # Get supporting agents
            recent_trades = symbol_trades[-20:]
            supporting = list(set(t["agent"] for t in recent_trades))

            # Calculate harmony (winrate correlation)
            winning_trades = [t for t in symbol_trades if t["pnl"] > 0]
            harmony = len(winning_trades) / len(symbol_trades) if symbol_trades else 0.5

            return {
                "consensus_action": action,
                "confidence": confidence,
                "supporting_agents": supporting,
                "harmony_score": harmony,
                "collective_reasoning": f"{action} consensus from {len(supporting)} agents ({confidence:.0%} confidence)",
            }

        except Exception as e:
            logger.error(f"Failed to get consensus: {e}")
            return {
                "consensus_action": "HOLD",
                "confidence": 0.5,
                "supporting_agents": [],
                "harmony_score": 0.0,
                "collective_reasoning": f"Error: {e}",
            }

    def get_agent_rankings(self) -> List[Dict]:
        """Get ranked list of agents by performance."""
        rankings = []
        for agent_name, stats in self.agent_winrates.items():
            total = stats["wins"] + stats["losses"]
            if total > 0:
                winrate = stats["wins"] / total
                rankings.append(
                    {
                        "agent": agent_name,
                        "winrate": winrate,
                        "total_pnl": stats["total_pnl"],
                        "total_trades": total,
                        "wins": stats["wins"],
                        "losses": stats["losses"],
                    }
                )

        return sorted(rankings, key=lambda x: x["winrate"], reverse=True)

    def reflect_collective(self, n_trades: int = 50) -> Dict[str, Any]:
        """Reflect on collective performance."""
        try:
            recent = self.global_trades[-n_trades:]

            if not recent:
                return {"insight": "No trades to reflect on", "action": "continue"}

            # Analyze patterns
            winning = [t for t in recent if t["pnl"] > 0]

            winrate = len(winning) / len(recent)
            avg_pnl = sum(t["pnl"] for t in recent) / len(recent)

            # Best performing regime
            regimes = defaultdict(lambda: {"pnl": 0, "count": 0})
            for trade in recent:
                regimes[trade["market_regime"]]["pnl"] += trade["pnl"]
                regimes[trade["market_regime"]]["count"] += 1

            best_regime = (
                max(regimes.items(), key=lambda x: x[1]["pnl"]) if regimes else ("unknown", {})
            )

            # Generate insight
            if winrate < 0.4:
                insight = (
                    f"Low winrate ({winrate:.0%}). Consider pausing. Best regime: {best_regime[0]}"
                )
                action = "pause"
            elif winrate > 0.6:
                insight = f"Strong performance ({winrate:.0%}). Continue strategy."
                action = "continue"
            else:
                insight = f"Mixed results ({winrate:.0%}). Monitor closely."
                action = "caution"

            return {
                "insight": insight,
                "action": action,
                "winrate": winrate,
                "avg_pnl": avg_pnl,
                "best_regime": best_regime[0],
                "total_trades": len(recent),
            }

        except Exception as e:
            logger.error(f"Collective reflection failed: {e}")
            return {"insight": f"Error: {e}", "action": "pause"}

    def should_pause_global_trading(self, drawdown_limit: float = 0.1) -> tuple[bool, str]:
        """Check if ALL trading should pause based on collective performance."""
        try:
            recent = self.global_trades[-100:]  # Last 100 trades
            if not recent:
                return False, "No recent trades"

            # Calculate collective drawdown
            cumulative_pnl = sum(t["pnl"] for t in recent)

            if cumulative_pnl < -drawdown_limit:
                return True, f"Collective drawdown: {cumulative_pnl:.2%} exceeds limit"

            # Check consecutive losses
            consecutive_losses = 0
            max_consecutive = 0
            for trade in reversed(recent):
                if trade["pnl"] <= 0:
                    consecutive_losses += 1
                    max_consecutive = max(max_consecutive, consecutive_losses)
                else:
                    break

            if consecutive_losses >= 5:
                return True, "5+ consecutive losses detected"

            return (
                False,
                f"Trading OK (drawdown: {cumulative_pnl:.2%}, max streak: {max_consecutive})",
            )

        except Exception as e:
            logger.error(f"Global pause check failed: {e}")
            return True, f"Error: {e}"

    def _load_global_memory(self):
        """Load global memory from disk."""
        memory_file = self.storage_path / "global_memory.json"
        if memory_file.exists():
            try:
                with open(memory_file, "r") as f:
                    data = json.load(f)
                    self.global_trades = data.get("trades", [])
                    self.agent_winrates = defaultdict(
                        lambda: {
                            "wins": 0,
                            "losses": 0,
                            "total_pnl": 0.0,
                            "avg_harmony": 0.0,
                            "trades": [],
                        }
                    )
                    self.agent_winrates.update(data.get("winrates", {}))
                    self.collective_insights = data.get("insights", [])
                logger.info(f"Loaded {len(self.global_trades)} global trades")
            except Exception as e:
                logger.error(f"Failed to load global memory: {e}")

    def _save_global_memory(self):
        """Save global memory to disk."""
        try:
            memory_file = self.storage_path / "global_memory.json"
            with open(memory_file, "w") as f:
                json.dump(
                    {
                        "trades": self.global_trades[-10000:],  # Keep last 10k
                        "winrates": dict(self.agent_winrates),
                        "insights": self.collective_insights[-100:],
                        "last_updated": datetime.now(UTC).isoformat(),
                    },
                    f,
                    indent=2,
                )
        except Exception as e:
            logger.error(f"Failed to save global memory: {e}")


# Singleton instance
_global_chitta: Optional[GlobalChitta] = None


def get_global_chitta() -> GlobalChitta:
    """Get global chitta singleton."""
    global _global_chitta
    if _global_chitta is None:
        _global_chitta = GlobalChitta()
    return _global_chitta
