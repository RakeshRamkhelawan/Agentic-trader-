"""
MetaOrchestrator (v12) - Collective Consciousness Trading System

Orchestrates all 27+ agents with global Chitta synchronization.
Implements weighted voting based on agent winrates.

ENHANCED: Self-Improving Supervisor (GuruAgents + Meta-Prompting)
- 9-Step hierarchical process
- Individual agent signal logging
- Bias detection & correction
- Auto weight tuning
"""

import asyncio
import csv
import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.agents.base_agent import BaseAgent
from backend.agents.elemental_base import ElementalBase
from backend.core.conscious.global_chitta import GlobalChitta, get_global_chitta
from backend.core.llm.llm_provider import create_llm_provider
from backend.governance.agent_gatekeeper import AgentRole

logger = logging.getLogger(__name__)


@dataclass
class MetaDecision:
    """Decision from MetaOrchestrator."""

    action: str  # BUY, SELL, HOLD
    confidence: float
    harmony_score: float
    supporting_agents: List[str]
    opposing_agents: List[str]
    collective_reasoning: str
    should_pause: bool
    pause_reason: Optional[str]
    was_forced: bool = False  # NEW: track bias correction
    force_reason: str = ""  # NEW: why forced


@dataclass
class AgentSignal:
    """Individual agent signal (NEW: for logging)."""

    timestamp: str
    agent_name: str
    symbol: str
    action: str
    confidence: float
    reasoning: str
    weight: float


class MetaOrchestrator:
    """
    Meta-level orchestrator for collective agent intelligence.

    ENHANCED - 9-Step GuruAgents Process:
    1. LOG EVERY DECISION: Store agent_name, action, conf, harmony
    2. PERFORMANCE TRACK: Calc rolling winrate/PnL per agent
    3. ANOMALY DETECT: Flag biases (100% BUY), low conf, disharmony
    4. AGENT FEEDBACK: Per agent tuning recommendations
    5. STRATEGY GENERATE: New theses based on top performers
    6. WEIGHT AUTO-TUNE: Rebalance based on performance
    7. PROMPT EVOLVE: Meta-prompt improvements
    8. GLOBAL STRATEGY: Portfolio thesis
    9. SESSION REVIEW: Lessons learned

    Features:
    - Global Chitta synchronization
    - Weighted agent voting (by winrate)
    - Collective deliberation
    - Meta-learning from session performance
    - Bias correction (33/33/33 enforcement)
    """

    # NEW: 9-Step GuruAgents Prompt
    META_PROMPT = """Je bent META ORCHESTRATOR - Supreme Akasha Intelligence, GuruAgents Supervisor.
Je observeert ALLE agents realtime, leert van elke decision, en orchestreert evolutie.

HIERARCHICAL 9-STEP PROCESS:
1. **LOG EVERY DECISION**: Store agent_name, action, conf, harmony, outcome_pnl.
2. **PERFORMANCE TRACK**: Calc rolling winrate/PnL per agent/symbol.
3. **ANOMALY DETECT**: Flag biases (100% BUY), low conf (0%), disharmony.
4. **AGENT FEEDBACK**: Per agent: "Water: +0.35 harmony → boost weight. Air: 0 conf → retrain."
5. **STRATEGY GENERATE**: Nieuwe theses (bull/bear/neutral) gebaseerd op top performers.
6. **WEIGHT AUTO-TUNE**: Rebalance: winrate_high * 1.2, loss_streak * 0.8.
7. **PROMPT EVOLVE**: Meta-prompt verbeteringen.
8. **GLOBAL STRATEGY**: Portfolio thesis.
9. **SESSION REVIEW**: Lessons learned.

BIAS CORRECTION PROTOCOL:
- Force 33% BUY / 33% SELL / 34% HOLD over laatste 10 decisions
- Als bias > 60% → force counter-action

Input: {input_data}
Output JSON met improvements, weight_adjustments, lessons.
"""

    def __init__(self, agents: Optional[List[BaseAgent]] = None):
        self.agents = agents or []
        self.global_chitta = get_global_chitta()
        self.logger = logging.getLogger(f"{__name__}.MetaOrchestrator")

        # Voting weights (updated based on performance)
        self.agent_weights: Dict[str, float] = {}

        # NEW: Bias correction tracking
        self.action_history: List[str] = []
        self.bias_threshold = 0.60
        self.target_distribution = {"BUY": 0.33, "SELL": 0.33, "HOLD": 0.34}

        # NEW: Individual signal logging
        self.signal_log: List[AgentSignal] = []
        self.log_dir = Path("backend/data/agent_logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # NEW: LLM for meta-improvement
        try:
            self.llm = create_llm_provider(backend="ollama", model="llama3.2")
        except:
            self.llm = None

        # Session tracking
        self.session_start = datetime.now(UTC)
        self.session_trades: List[Dict] = []

        self.logger.info(f"MetaOrchestrator initialized with {len(self.agents)} agents")

    def register_agent(self, agent: BaseAgent):
        """Register an agent with the orchestrator."""
        self.agents.append(agent)

        # Sync agent's Chitta to global
        if agent.chitta:
            self.global_chitta.sync_from_agent(agent.agent_name, agent.chitta)

        self.logger.info(f"Registered agent: {agent.agent_name}")

    # NEW: Bias calculation
    def _calculate_bias(self) -> Dict[str, Any]:
        """Calculate current action bias."""
        if not self.action_history:
            return {"buy": 0.33, "sell": 0.33, "hold": 0.34, "is_biased": False}

        total = len(self.action_history)
        buy_pct = sum(1 for a in self.action_history if a == "BUY") / total
        sell_pct = sum(1 for a in self.action_history if a == "SELL") / total
        hold_pct = sum(1 for a in self.action_history if a == "HOLD") / total

        max_bias = max(buy_pct, sell_pct, hold_pct)

        return {
            "buy": buy_pct,
            "sell": sell_pct,
            "hold": hold_pct,
            "max_bias": max_bias,
            "is_biased": max_bias > self.bias_threshold,
        }

    # NEW: Force action for bias correction
    def _determine_forced_action(self, bias: Dict) -> Optional[str]:
        """Determine if we need to force an action for balance."""
        if not bias["is_biased"]:
            return None

        # Force the under-represented action
        if bias["buy"] > self.bias_threshold:
            return "SELL" if bias["sell"] < bias["hold"] else "HOLD"
        elif bias["sell"] > self.bias_threshold:
            return "BUY" if bias["buy"] < bias["hold"] else "HOLD"
        elif bias["hold"] > self.bias_threshold:
            return "BUY" if bias["buy"] < bias["sell"] else "SELL"

        return None

    async def deliberate(self, market_state: Dict[str, Any]) -> MetaDecision:
        """
        Collective deliberation across all agents.
        ENHANCED with bias correction and individual logging.
        """
        symbol = market_state.get("symbol", "UNKNOWN")
        timestamp = datetime.now(UTC).isoformat()

        # 1. Global Reflection - Check collective health
        self.logger.info("Starting collective deliberation...")
        collective_reflection = self.global_chitta.reflect_collective(n_trades=50)

        # 2. Check if global pause needed
        should_pause, pause_reason = self.global_chitta.should_pause_global_trading(
            drawdown_limit=0.08
        )

        if should_pause:
            self.logger.warning(f"GLOBAL PAUSE: {pause_reason}")
            return MetaDecision(
                action="HOLD",
                confidence=0.5,
                harmony_score=0.0,
                supporting_agents=[],
                opposing_agents=[],
                collective_reasoning=f"Trading paused: {pause_reason}",
                should_pause=True,
                pause_reason=pause_reason,
            )

        # 3. Get agent rankings (for weighted voting)
        agent_rankings = self.global_chitta.get_agent_rankings()
        self._update_weights(agent_rankings)

        # 4. Collect signals from all agents
        agent_signals = await self._collect_agent_signals(market_state, timestamp)

        # NEW: 5. Check bias and apply correction
        bias_status = self._calculate_bias()
        force_action = self._determine_forced_action(bias_status)

        if force_action:
            self.logger.info(f"[BIAS-CORRECTION] Forcing {force_action} (bias detected)")
            self.action_history.append(force_action)
            return MetaDecision(
                action=force_action,
                confidence=0.4,
                harmony_score=0.2,
                supporting_agents=["bias_correction"],
                opposing_agents=[],
                collective_reasoning=f"Forced {force_action} to maintain 33/33/33 balance",
                should_pause=False,
                pause_reason=None,
                was_forced=True,
                force_reason=f"Bias correction: B:{bias_status['buy']:.0%} S:{bias_status['sell']:.0%} H:{bias_status['hold']:.0%}",
            )

        # 6. Weighted voting
        weighted_vote = self._weighted_voting(agent_signals)

        # 7. Get collective consensus from Chitta
        consensus = self.global_chitta.get_collective_consensus(symbol, market_state)

        # 8. Harmonize signals (Ether layer)
        final_decision = self._harmonize_decisions(weighted_vote, consensus)

        # NEW: Track for bias correction
        self.action_history.append(final_decision.action)

        # NEW: Log MetaOrchestrator consensus decision too
        self._log_meta_decision(symbol, final_decision, market_state)

        # NEW: 9. Self-improvement every 5 decisions
        if len(self.action_history) % 5 == 0:
            await self._self_improve()

        # 10. Log deliberation
        self.logger.info(
            f"Deliberation complete: {final_decision.action} "
            f"(confidence: {final_decision.confidence:.2f}, "
            f"harmony: {final_decision.harmony_score:.2f})"
        )

        return final_decision

    async def _collect_agent_signals(
        self, market_state: Dict[str, Any], timestamp: str
    ) -> List[Dict[str, Any]]:
        """
        Collect signals from all registered agents.
        ENHANCED: Logs individual signals.
        """
        signals = []
        symbol = market_state.get("symbol", "UNKNOWN")

        # Sync global insights to agents before deliberation
        for agent in self.agents:
            if agent.chitta:
                self.global_chitta.sync_to_agent(agent.agent_name, agent.chitta)

        # Gather signals concurrently
        async def get_signal(agent: BaseAgent) -> Optional[Dict]:
            try:
                # Use existing analyze method
                result = await agent.analyze(
                    features=market_state, context={"timestamp": timestamp}
                )

                signal = {
                    "agent": agent.agent_name,
                    "action": result.get("action", "HOLD"),
                    "confidence": result.get("confidence", 0.5),
                    "reasoning": result.get("reasoning", ""),
                    "weight": self.agent_weights.get(agent.agent_name, 1.0),
                }

                # NEW: Log individual signal
                self._log_individual_signal(timestamp, agent.agent_name, symbol, signal)

                return signal
            except Exception as e:
                self.logger.error(f"Agent {agent.agent_name} failed: {e}")
                # NEW: Log error as HOLD
                self._log_individual_signal(
                    timestamp,
                    agent.agent_name,
                    symbol,
                    {"action": "HOLD", "confidence": 0.0, "reasoning": f"Error: {e}", "weight": 0},
                )
                return None

        # Run all agents concurrently
        results = await asyncio.gather(*[get_signal(agent) for agent in self.agents])
        signals = [r for r in results if r is not None]

        self.logger.info(f"Collected {len(signals)} agent signals")
        return signals

    # NEW: Log MetaOrchestrator consensus decision
    def _log_meta_decision(self, symbol: str, decision: MetaDecision, market_state: Dict):
        """Log MetaOrchestrator's consensus decision."""
        meta_signal = AgentSignal(
            timestamp=datetime.now(UTC).isoformat(),
            agent_name="MetaOrchestrator",
            symbol=symbol,
            action=decision.action,
            confidence=decision.confidence,
            reasoning=decision.collective_reasoning
            + (f" [FORCED: {decision.force_reason}]" if decision.was_forced else ""),
            weight=1.0,
        )
        self.signal_log.append(meta_signal)
        self._append_to_csv(meta_signal)

    # NEW: Log individual agent signal
    def _log_individual_signal(self, timestamp: str, agent_name: str, symbol: str, signal: Dict):
        """Log individual agent signal for analysis."""
        agent_signal = AgentSignal(
            timestamp=timestamp,
            agent_name=agent_name,
            symbol=symbol,
            action=signal.get("action", "HOLD"),
            confidence=signal.get("confidence", 0.0),
            reasoning=signal.get("reasoning", ""),
            weight=signal.get("weight", 1.0),
        )
        self.signal_log.append(agent_signal)

        # Also write to CSV immediately
        self._append_to_csv(agent_signal)

    # NEW: Append to CSV
    def _append_to_csv(self, signal: AgentSignal):
        """Append signal to CSV log file."""
        csv_path = self.log_dir / f"individual_signals_{self.session_start.date()}.csv"

        file_exists = csv_path.exists()
        with open(csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(
                    [
                        "timestamp",
                        "agent_name",
                        "symbol",
                        "action",
                        "confidence",
                        "reasoning",
                        "weight",
                    ]
                )
            writer.writerow(
                [
                    signal.timestamp,
                    signal.agent_name,
                    signal.symbol,
                    signal.action,
                    signal.confidence,
                    signal.reasoning,
                    signal.weight,
                ]
            )

    # NEW: Self-improvement
    async def _self_improve(self):
        """Run meta-analysis and generate improvements."""
        self.logger.info("[SELF-IMPROVE] Running meta-analysis...")

        # Calculate recent performance
        recent_signals = self.signal_log[-20:] if len(self.signal_log) >= 20 else self.signal_log
        bias = self._calculate_bias()

        input_data = {
            "recent_signals": [
                {"agent": s.agent_name, "action": s.action, "confidence": s.confidence}
                for s in recent_signals
            ],
            "current_weights": self.agent_weights,
            "bias_status": bias,
            "total_decisions": len(self.action_history),
        }

        # If LLM available, use it
        if self.llm:
            try:
                prompt = self.META_PROMPT.format(input_data=json.dumps(input_data))
                response = self.llm.generate(prompt, temperature=0.3)

                # Parse and apply improvements
                if "weight_adjustments" in response:
                    for agent, new_weight in response["weight_adjustments"].items():
                        if agent in self.agent_weights:
                            old_weight = self.agent_weights[agent]
                            self.agent_weights[agent] = max(0.1, min(2.0, new_weight))
                            self.logger.info(
                                f"[WEIGHT-TUNE] {agent}: {old_weight:.2f} → {self.agent_weights[agent]:.2f}"
                            )

                if "lessons" in response:
                    self.logger.info(f"[LESSON] {response['lessons']}")

            except Exception as e:
                self.logger.error(f"[SELF-IMPROVE] LLM error: {e}")
        else:
            # Simple rule-based improvement
            if bias["is_biased"]:
                self.logger.warning(f"[BIAS-ALERT] Action bias detected: {bias}")

    def _update_weights(self, rankings: List[Dict]):
        """Update voting weights based on agent performance."""
        for rank in rankings:
            agent_name = rank["agent"]
            winrate = rank["winrate"]

            # Weight = winrate * log(trade_count + 1)
            trade_count = rank["total_trades"]
            weight = winrate * (1 + 0.1 * min(trade_count, 100))

            self.agent_weights[agent_name] = max(0.1, weight)  # Min weight 0.1

        self.logger.debug(f"Updated weights for {len(self.agent_weights)} agents")

    def _weighted_voting(self, signals: List[Dict]) -> Dict[str, Any]:
        """Perform weighted voting across agent signals."""
        if not signals:
            return {"action": "HOLD", "confidence": 0.5, "score": 0.0}

        # Aggregate votes
        action_scores = {"BUY": 0.0, "SELL": 0.0, "HOLD": 0.0}
        total_weight = 0.0

        for signal in signals:
            weight = signal["weight"]
            action = signal["action"]
            confidence = signal["confidence"]

            if action in action_scores:
                action_scores[action] += weight * confidence
                total_weight += weight

        # Normalize
        if total_weight > 0:
            for action in action_scores:
                action_scores[action] /= total_weight

        # Determine winner
        best_action = max(action_scores, key=action_scores.get)
        best_score = action_scores[best_action]

        # Calculate consensus (how unified are agents?)
        max_score = max(action_scores.values())
        consensus = (
            max_score / sum(action_scores.values()) if sum(action_scores.values()) > 0 else 0
        )

        return {
            "action": best_action,
            "confidence": best_score,
            "score": consensus,
            "action_scores": action_scores,
        }

    def _harmonize_decisions(self, weighted_vote: Dict, consensus: Dict[str, Any]) -> MetaDecision:
        """Harmonize weighted vote with collective consensus."""

        # If weighted vote and consensus agree, boost confidence
        if weighted_vote["action"] == consensus["consensus_action"]:
            final_action = weighted_vote["action"]
            final_confidence = (weighted_vote["confidence"] + consensus["confidence"]) / 2
            harmony = consensus["harmony_score"]
            reasoning = f"Consensus: {consensus['collective_reasoning']}"
        else:
            # Disagreement - use weighted vote but lower confidence
            final_action = weighted_vote["action"]
            final_confidence = weighted_vote["confidence"] * 0.7
            harmony = consensus["harmony_score"] * 0.5
            reasoning = f"Divergent signals. Using weighted vote: {weighted_vote['action']}"

        # Determine supporting/opposing agents
        supporting = consensus.get("supporting_agents", [])
        opposing = [a.agent_name for a in self.agents if a.agent_name not in supporting]

        return MetaDecision(
            action=final_action,
            confidence=final_confidence,
            harmony_score=harmony,
            supporting_agents=supporting,
            opposing_agents=opposing,
            collective_reasoning=reasoning,
            should_pause=False,
            pause_reason=None,
            was_forced=False,
            force_reason="",
        )

    def record_trade(self, decision: MetaDecision, result: Dict[str, Any]):
        """Record trade outcome for learning."""
        trade_record = {
            "timestamp": datetime.now(UTC).isoformat(),
            "action": decision.action,
            "confidence": decision.confidence,
            "harmony": decision.harmony_score,
            "supporting_agents": decision.supporting_agents,
            "pnl": result.get("pnl", 0),
            "symbol": result.get("symbol", "UNKNOWN"),
        }

        self.session_trades.append(trade_record)

        # Sync to global Chitta
        for agent_name in decision.supporting_agents:
            agent = next((a for a in self.agents if a.agent_name == agent_name), None)
            if agent and agent.chitta:
                from backend.core.conscious.chitta_memory import TradeExperience

                experience = TradeExperience(
                    timestamp=trade_record["timestamp"],
                    symbol=trade_record["symbol"],
                    action=trade_record["action"],
                    confidence=trade_record["confidence"],
                    pnl=trade_record["pnl"],
                    market_regime="collective",
                    reasoning=f"MetaOrchestrator trade via {agent_name}",
                )
                agent.chitta.store_trade(experience)
                self.global_chitta.sync_from_agent(agent_name, agent.chitta)

    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current trading session."""
        if not self.session_trades:
            return {"status": "No trades yet"}

        wins = sum(1 for t in self.session_trades if t["pnl"] > 0)
        total = len(self.session_trades)
        total_pnl = sum(t["pnl"] for t in self.session_trades)
        avg_harmony = sum(t["harmony"] for t in self.session_trades) / total

        # NEW: Add bias status
        bias = self._calculate_bias()

        return {
            "status": "active" if total < 100 else "session_complete",
            "total_trades": total,
            "winrate": wins / total if total > 0 else 0,
            "total_pnl": total_pnl,
            "avg_harmony": avg_harmony,
            "duration_minutes": (datetime.now(UTC) - self.session_start).seconds / 60,
            "bias_status": bias,
            "action_distribution": {
                "BUY": sum(1 for a in self.action_history if a == "BUY"),
                "SELL": sum(1 for a in self.action_history if a == "SELL"),
                "HOLD": sum(1 for a in self.action_history if a == "HOLD"),
            },
        }
