"""
MetaOrchestrator V2 - Enhanced with PnL Learning & Adaptive Weights

Verbeteringen:
1. PnL feedback per signaal
2. Symbol-specifieke weights
3. Divergence/conflict detectie
4. Harmony scores
5. Self-improving prompts
"""

import asyncio
import csv
import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from backend.agents.base_agent import BaseAgent
from backend.agents.unified_agent_interface_v2 import EnhancedSignal, SelfImprovingAgentWrapper
from backend.core.conscious.global_chitta import get_global_chitta
from backend.core.llm.llm_provider import create_llm_provider

logger = logging.getLogger(__name__)


@dataclass
class AgentSignalV2:
    """Enhanced agent signal with outcome tracking."""

    timestamp: str
    agent_name: str
    symbol: str
    action: str
    confidence: float
    reasoning: str
    weight: float
    # NEW: Parsed features from reasoning
    rsi: Optional[float] = None
    adx: Optional[float] = None
    regime: Optional[str] = None
    # NEW: Outcome tracking (filled later)
    pnl: Optional[float] = None
    exit_reason: Optional[str] = None
    was_correct: Optional[bool] = None
    # NEW: Harmony/conflict tracking
    agent_harmony: float = 0.0  # Agreement with other agents
    divergence_flag: bool = False  # True if conflicting with majority
    # NEW: Self-improvement tracking
    reflection: str = ""  # Agent's self-reflection
    confidence_adjustment: float = 1.0  # Applied multiplier
    bias_acknowledged: str = ""  # Detected bias


@dataclass
class MetaDecisionV2:
    """Enhanced meta decision."""

    action: str
    confidence: float
    harmony_score: float
    supporting_agents: List[str]
    opposing_agents: List[str]
    collective_reasoning: str
    should_pause: bool
    pause_reason: Optional[str]
    was_forced: bool = False
    force_reason: str = ""
    # NEW: Conflict analysis
    divergence_detected: bool = False
    strongest_conflict: Optional[Tuple[str, str]] = (
        None  # (agent1, agent2) with biggest disagreement
    )


class MetaOrchestratorV2:
    """
    Enhanced MetaOrchestrator with learning capabilities.
    """

    def __init__(self):
        self.agents: List[BaseAgent] = []
        self.global_chitta = get_global_chitta()
        self.logger = logging.getLogger(__name__)

        # NEW: Multi-level weights
        self.agent_weights: Dict[str, float] = {}  # Base weights
        self.symbol_weights: Dict[str, Dict[str, float]] = defaultdict(dict)  # Per symbol
        self.regime_weights: Dict[str, Dict[str, float]] = defaultdict(dict)  # Per regime

        # NEW: Performance tracking per agent-symbol-regime
        self.performance_db: Dict[str, pd.DataFrame] = {}  # agent -> performance df

        # NEW: Signal log with outcome tracking
        self.signal_log: List[AgentSignalV2] = []
        self.pending_outcomes: Dict[str, AgentSignalV2] = {}  # symbol -> last signal

        # NEW: Trade outcomes log
        self.trade_outcomes: List[Dict] = []

        # Logging
        self.log_dir = Path("backend/data/agent_logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Bias correction
        self.action_history: List[str] = []
        self.bias_threshold = 0.60

        # Load historical performance if exists
        self._load_performance_db()

        logger.info("MetaOrchestratorV2 initialized - Enhanced Learning Mode")

    def _load_performance_db(self):
        """Load historical performance data."""
        perf_file = self.log_dir / "agent_performance_v2.csv"
        if perf_file.exists():
            df = pd.read_csv(perf_file)
            for agent in df["agent_name"].unique():
                self.performance_db[agent] = df[df["agent_name"] == agent]
            logger.info(f"Loaded performance data for {len(self.performance_db)} agents")

    def register_agent(self, agent: BaseAgent):
        """Register agent with orchestrator."""
        self.agents.append(agent)
        if agent.agent_name not in self.agent_weights:
            self.agent_weights[agent.agent_name] = 1.0
        logger.info(f"Registered: {agent.agent_name}")

    def update_trade_outcome(
        self, symbol: str, exit_price: float, exit_time: datetime, pnl: float, exit_reason: str
    ):
        """
        Update pending signals with actual trade outcome.
        Called when a trade exits.
        """
        # Find signals for this symbol within last hour
        cutoff_time = exit_time - timedelta(hours=1)

        for signal in self.signal_log:
            signal_time = datetime.fromisoformat(signal.timestamp)
            if signal.symbol == symbol and signal_time > cutoff_time and signal.pnl is None:

                signal.pnl = pnl
                signal.exit_reason = exit_reason
                signal.was_correct = pnl > 0

                # Update performance metrics
                self._update_agent_performance(signal)

                # Update agent wrapper for self-learning
                for agent in self.agents:
                    if agent.agent_name == signal.agent_name and hasattr(
                        agent, "record_trade_outcome"
                    ):
                        agent.record_trade_outcome(pnl, {"symbol": symbol, "regime": signal.regime})

                logger.info(f"Outcome recorded: {signal.agent_name} {symbol} -> PnL: {pnl:.4f}")

    def _update_agent_performance(self, signal: AgentSignalV2):
        """Update performance database."""
        key = f"{signal.agent_name}_{signal.symbol}_{signal.regime or 'unknown'}"

        record = {
            "timestamp": signal.timestamp,
            "agent_name": signal.agent_name,
            "symbol": signal.symbol,
            "regime": signal.regime or "unknown",
            "action": signal.action,
            "confidence": signal.confidence,
            "pnl": signal.pnl,
            "was_correct": signal.was_correct,
        }

        self.trade_outcomes.append(record)

        # Recalculate weights
        self._recalculate_weights(signal.agent_name, signal.symbol)

    def _recalculate_weights(self, agent_name: str, symbol: str):
        """Recalculate weights based on recent performance."""
        # Get recent outcomes for this agent-symbol
        agent_outcomes = [
            o
            for o in self.trade_outcomes
            if o["agent_name"] == agent_name and o["symbol"] == symbol
        ]

        if len(agent_outcomes) < 3:  # Need minimum samples
            return

        recent = agent_outcomes[-20:]  # Last 20 trades
        winrate = sum(1 for o in recent if o["was_correct"]) / len(recent)
        avg_pnl = sum(o["pnl"] for o in recent) / len(recent)

        # Calculate new weight: base + performance bonus
        base_weight = 1.0
        performance_bonus = (winrate - 0.5) * 0.5 + avg_pnl * 10
        new_weight = max(0.1, min(2.5, base_weight + performance_bonus))

        self.symbol_weights[symbol][agent_name] = new_weight

        logger.info(
            f"Weight updated: {agent_name} {symbol} -> {new_weight:.2f} "
            f"(winrate: {winrate:.2f}, avg_pnl: {avg_pnl:.4f})"
        )

    def get_adaptive_weight(self, agent_name: str, symbol: str, regime: str) -> float:
        """Get context-aware weight."""
        # Priority: symbol-specific > regime-specific > base
        if symbol in self.symbol_weights and agent_name in self.symbol_weights[symbol]:
            return self.symbol_weights[symbol][agent_name]

        if regime in self.regime_weights and agent_name in self.regime_weights[regime]:
            return self.regime_weights[regime][agent_name]

        return self.agent_weights.get(agent_name, 1.0)

    async def deliberate(self, market_state: Dict[str, Any]) -> MetaDecisionV2:
        """
        Enhanced deliberation with divergence detection.
        """
        symbol = market_state.get("symbol", "UNKNOWN")
        regime = market_state.get("regime", "unknown")
        timestamp = datetime.now(UTC).isoformat()

        # Collect signals
        signals = await self._collect_signals(market_state, timestamp)

        if not signals:
            return MetaDecisionV2(
                action="HOLD",
                confidence=0.5,
                harmony_score=0.0,
                supporting_agents=[],
                opposing_agents=[],
                collective_reasoning="No signals",
                should_pause=True,
                pause_reason="No agent signals",
            )

        # Calculate harmony/divergence
        harmony, divergence, strongest_conflict = self._analyze_divergence(signals)

        # Check bias
        bias = self._calculate_bias()
        force_action = self._determine_forced_action(bias)

        if force_action:
            self.action_history.append(force_action)
            return MetaDecisionV2(
                action=force_action,
                confidence=0.4,
                harmony_score=0.2,
                supporting_agents=["bias_correction"],
                opposing_agents=[],
                collective_reasoning=f"Forced {force_action} for balance",
                should_pause=False,
                pause_reason=None,
                was_forced=True,
                force_reason="Bias correction",
                divergence_detected=divergence,
                strongest_conflict=strongest_conflict,
            )

        # Weighted voting with adaptive weights
        weighted_vote = self._weighted_voting(signals, symbol, regime)

        self.action_history.append(weighted_vote["action"])

        return MetaDecisionV2(
            action=weighted_vote["action"],
            confidence=weighted_vote["confidence"],
            harmony_score=harmony,
            supporting_agents=weighted_vote["supporting"],
            opposing_agents=weighted_vote["opposing"],
            collective_reasoning=weighted_vote["reasoning"],
            should_pause=False,
            pause_reason=None,
            divergence_detected=divergence,
            strongest_conflict=strongest_conflict,
        )

    async def _collect_signals(self, market_state: Dict, timestamp: str) -> List[AgentSignalV2]:
        """Collect and parse signals from all agents with self-improvement."""
        signals = []
        symbol = market_state.get("symbol", "UNKNOWN")

        for agent in self.agents:
            try:
                # Check if agent has self-improving capabilities
                if isinstance(agent, SelfImprovingAgentWrapper):
                    enhanced_signal = await agent.analyze_with_reflection(
                        market_state=market_state, performance_db=self.performance_db
                    )

                    # Parse reasoning for features
                    rsi, adx, regime = self._parse_reasoning(enhanced_signal.reasoning)

                    signal = AgentSignalV2(
                        timestamp=timestamp,
                        agent_name=agent.agent_name,
                        symbol=symbol,
                        action=enhanced_signal.action,
                        confidence=enhanced_signal.confidence,
                        reasoning=enhanced_signal.reasoning,
                        weight=self.get_adaptive_weight(
                            agent.agent_name, symbol, regime or "unknown"
                        ),
                        rsi=rsi,
                        adx=adx,
                        regime=regime,
                        reflection=enhanced_signal.reflection,
                        confidence_adjustment=enhanced_signal.confidence_adjustment,
                        bias_acknowledged=enhanced_signal.bias_acknowledged,
                    )
                else:
                    # Legacy agent - basic signal
                    result = await agent.analyze(
                        features=market_state, context={"timestamp": timestamp}
                    )

                    reasoning = result.get("reasoning", "")
                    rsi, adx, regime = self._parse_reasoning(reasoning)

                    signal = AgentSignalV2(
                        timestamp=timestamp,
                        agent_name=agent.agent_name,
                        symbol=symbol,
                        action=result.get("action", "HOLD"),
                        confidence=result.get("confidence", 0.0),
                        reasoning=reasoning,
                        weight=self.get_adaptive_weight(
                            agent.agent_name, symbol, regime or "unknown"
                        ),
                        rsi=rsi,
                        adx=adx,
                        regime=regime,
                    )

                signals.append(signal)
                self.signal_log.append(signal)
                self._log_signal(signal)

            except Exception as e:
                logger.error(f"Signal error {agent.agent_name}: {e}")

        # Calculate harmony for each signal
        if len(signals) > 1:
            action_counts = defaultdict(int)
            for s in signals:
                action_counts[s.action] += 1

            majority_action = max(action_counts, key=action_counts.get)

            for signal in signals:
                agrees = signal.action == majority_action
                signal.agent_harmony = 1.0 if agrees else 0.0
                signal.divergence_flag = not agrees

        return signals

    def _parse_reasoning(
        self, reasoning: str
    ) -> Tuple[Optional[float], Optional[float], Optional[str]]:
        """Extract RSI, ADX, regime from reasoning string."""
        rsi = adx = None
        regime = None

        try:
            # Parse RSI: XX
            if "RSI:" in reasoning:
                rsi_part = reasoning.split("RSI:")[1].split(",")[0].strip()
                rsi = float(rsi_part)

            # Parse ADX: XX
            if "ADX:" in reasoning:
                adx_part = reasoning.split("ADX:")[1].split(",")[0].strip()
                adx = float(adx_part)

            # Parse Regime: XXX
            if "Regime:" in reasoning:
                regime_part = reasoning.split("Regime:")[1].strip().lower()
                # Clean up
                regime = regime_part.split(",")[0].split(".")[0].strip()
        except:
            pass

        return rsi, adx, regime

    def _analyze_divergence(
        self, signals: List[AgentSignalV2]
    ) -> Tuple[float, bool, Optional[Tuple]]:
        """
        Analyze harmony and detect strongest divergence.
        Returns: (harmony_score, divergence_detected, strongest_conflict_pair)
        """
        if len(signals) < 2:
            return 1.0, False, None

        # Count actions
        actions = [s.action for s in signals]
        action_counts = pd.Series(actions).value_counts()

        # Harmony = fraction agreeing with majority
        majority_count = action_counts.iloc[0] if len(action_counts) > 0 else 0
        harmony = majority_count / len(signals)

        # Divergence detected if no clear majority
        divergence = harmony < 0.6

        # Find strongest conflict (highest confidence opposing signals)
        strongest_conflict = None
        max_conflict_score = 0

        if divergence:
            buys = [(s.agent_name, s.confidence) for s in signals if s.action == "BUY"]
            sells = [(s.agent_name, s.confidence) for s in signals if s.action == "SELL"]

            for b_agent, b_conf in buys:
                for s_agent, s_conf in sells:
                    conflict_score = b_conf + s_conf
                    if conflict_score > max_conflict_score:
                        max_conflict_score = conflict_score
                        strongest_conflict = (b_agent, s_agent)

        return harmony, divergence, strongest_conflict

    def _weighted_voting(self, signals: List[AgentSignalV2], symbol: str, regime: str) -> Dict:
        """Weighted voting with adaptive weights."""
        if not signals:
            return {
                "action": "HOLD",
                "confidence": 0.5,
                "supporting": [],
                "opposing": [],
                "reasoning": "No signals",
            }

        action_scores = defaultdict(float)
        agent_votes = defaultdict(list)

        for signal in signals:
            # Use adaptive weight
            weight = self.get_adaptive_weight(signal.agent_name, symbol, regime)
            weighted_conf = signal.confidence * weight

            action_scores[signal.action] += weighted_conf
            agent_votes[signal.action].append(signal.agent_name)

        if not action_scores:
            return {
                "action": "HOLD",
                "confidence": 0.5,
                "supporting": [],
                "opposing": [],
                "reasoning": "No votes",
            }

        # Normalize
        total = sum(action_scores.values())
        if total == 0:
            return {
                "action": "HOLD",
                "confidence": 0.5,
                "supporting": [],
                "opposing": [],
                "reasoning": "Zero total weight",
            }

        for action in action_scores:
            action_scores[action] /= total

        winner = max(action_scores, key=action_scores.get)

        return {
            "action": winner,
            "confidence": action_scores[winner],
            "supporting": agent_votes[winner],
            "opposing": [
                a for action, agents in agent_votes.items() if action != winner for a in agents
            ],
            "reasoning": f"Weighted vote: {dict(action_scores)}",
        }

    def _calculate_bias(self) -> Dict:
        """Calculate action bias."""
        if not self.action_history:
            return {"buy": 0.33, "sell": 0.33, "hold": 0.34, "is_biased": False}

        total = len(self.action_history)
        return {
            "buy": sum(1 for a in self.action_history if a == "BUY") / total,
            "sell": sum(1 for a in self.action_history if a == "SELL") / total,
            "hold": sum(1 for a in self.action_history if a == "HOLD") / total,
            "is_biased": max(
                [
                    sum(1 for a in self.action_history if a == act) / total
                    for act in ["BUY", "SELL", "HOLD"]
                ]
            )
            > self.bias_threshold,
        }

    def _determine_forced_action(self, bias: Dict) -> Optional[str]:
        """Determine forced action for bias correction."""
        if not bias["is_biased"]:
            return None

        # Force under-represented action
        actions = [("BUY", bias["buy"]), ("SELL", bias["sell"]), ("HOLD", bias["hold"])]
        return min(actions, key=lambda x: x[1])[0]

    def _log_signal(self, signal: AgentSignalV2):
        """Log signal to CSV with reflection."""
        csv_path = self.log_dir / f"signals_v2_{datetime.now(UTC).date()}.csv"

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
                        "rsi",
                        "adx",
                        "regime",
                        "pnl",
                        "was_correct",
                        "reflection",
                        "confidence_adjustment",
                        "bias_acknowledged",
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
                    signal.rsi,
                    signal.adx,
                    signal.regime,
                    signal.pnl,
                    signal.was_correct,
                    signal.reflection,
                    signal.confidence_adjustment,
                    signal.bias_acknowledged,
                ]
            )

    def export_performance_report(self) -> pd.DataFrame:
        """Export comprehensive performance report."""
        if not self.trade_outcomes:
            return pd.DataFrame()

        df = pd.DataFrame(self.trade_outcomes)

        # Aggregate per agent-symbol-regime
        report = (
            df.groupby(["agent_name", "symbol", "regime"])
            .agg({"pnl": ["count", "mean", "sum"], "was_correct": "mean"})
            .round(4)
        )

        report.columns = ["trades", "avg_pnl", "total_pnl", "winrate"]
        report = report.reset_index()

        # Save
        report_path = (
            self.log_dir / f"performance_report_{datetime.now(UTC).strftime('%Y%m%d_%H%M')}.csv"
        )
        report.to_csv(report_path, index=False)

        logger.info(f"Performance report exported: {report_path}")
        return report
