"""
MetaOrchestrator V3 - Strategy Evolution + Prompt Evolution

Met multi-LLM support:
- DeepSeek (primary)
- OpenAI (fallback)
- Google GenAI (fallback)
- Ollama (local)

En dual evolution:
- Strategy Evolution: Langetermijn strategie aanpassingen
- Prompt Evolution: LLM past eigen prompts aan
"""

import asyncio
import csv
import json
import logging
import os
import random
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.agents.multi_llm_provider import get_multi_llm
from backend.agents.prompt_evolution import PromptEvolutionEngine, get_prompt_evolution
from backend.agents.strategy_evolution import (
    StrategyEvolutionEngine,
    StrategyProfile,
    get_strategy_evolution,
)

logger = logging.getLogger(__name__)


@dataclass
class AgentSignalV3:
    """Enhanced agent signal met evolution metadata."""

    timestamp: datetime
    agent_name: str
    symbol: str
    action: str
    confidence: float
    reasoning: str
    weight: float

    # Technical indicators
    rsi: Optional[float] = None
    adx: Optional[float] = None
    regime: Optional[str] = None

    # Performance
    pnl: Optional[float] = None
    was_correct: bool = False

    # Evolution metadata
    reflection: str = ""
    confidence_adjustment: float = 1.0
    bias_acknowledged: bool = False
    strategy_version: int = 1
    prompt_version: int = 1


@dataclass
class MetaDecisionV3:
    """Meta decision met evolution tracking."""

    timestamp: datetime
    symbol: str
    final_action: str
    confidence: float
    votes: Dict[str, int]
    agent_signals: List[AgentSignalV3]
    reasoning_summary: str

    # Evolution tracking
    strategy_used: str = "default"
    prompt_used: str = "default"
    evolution_applied: bool = False


class MetaOrchestratorV3:
    """
    V3 MetaOrchestrator met Strategy + Prompt Evolution.
    """

    def __init__(self, enable_evolution: bool = True):
        self.multi_llm = get_multi_llm()
        self.strategy_evolution = get_strategy_evolution()
        self.prompt_evolution = get_prompt_evolution()

        self.agents: Dict[str, Any] = {}
        self.adaptive_weights = defaultdict(lambda: defaultdict(lambda: 1.0))
        self.agent_signals_history: List[AgentSignalV3] = []
        self.trade_outcomes: Dict[str, Dict] = {}

        self.enable_evolution = enable_evolution
        self.evolution_counter = 0

        # Register strategies for evolution
        self._init_strategies()
        self._init_prompts()

    def _init_strategies(self):
        """Initialize strategieen voor evolution."""
        default_strategy = StrategyProfile(
            strategy_name="consensus_weighted",
            entry_threshold=0.6,
            exit_threshold=0.4,
            position_sizing="kelly",
            max_positions=5,
            hold_time_preference="medium",
        )
        self.strategy_evolution.register_strategy("consensus_weighted", default_strategy)

        aggressive_strategy = StrategyProfile(
            strategy_name="aggressive_momentum",
            entry_threshold=0.5,
            exit_threshold=0.3,
            position_sizing="fixed",
            max_positions=10,
            hold_time_preference="short",
        )
        self.strategy_evolution.register_strategy("aggressive_momentum", aggressive_strategy)

    def _init_prompts(self):
        """Initialize prompts voor evolution."""
        reflection_prompt = """# Agent Reflection

Analyseer deze trade performance:
Agent: {agent_name}
Trades: {trades}
Bias: {bias}

Geef reflectie in JSON format."""

        self.prompt_evolution.register_prompt(
            name="agent_reflection",
            template=reflection_prompt,
            system_prompt="Je bent een trading performance analyst.",
        )

        consensus_prompt = """# Consensus Decision

Symbol: {symbol}
Regime: {regime}
Signals: {signals}

Maak een consensus beslissing."""

        self.prompt_evolution.register_prompt(
            name="consensus_decision",
            template=consensus_prompt,
            system_prompt="Je bent een trading consensus builder.",
        )

    def register_agent(self, name: str, agent: Any, weight: float = 1.0) -> None:
        """Registreer een agent."""
        self.agents[name] = {
            "instance": agent,
            "base_weight": weight,
            "current_weight": weight,
        }
        logger.info(f"Agent registered: {name} (weight: {weight})")

    async def deliberate(self, market_state: Dict[str, Any]) -> MetaDecisionV3:
        """Main deliberation met evolution."""
        symbol = market_state.get("symbol", "UNKNOWN")
        regime = market_state.get("regime", "unknown")

        # Collect signals
        signals = await self._collect_signals(market_state)

        # Check bias
        bias_check = self._calculate_bias(signals)
        if bias_check["is_biased"]:
            signals = self._apply_bias_correction(signals)

        # Get current strategy
        strategy = self.strategy_evolution.strategies.get("consensus_weighted")
        if strategy:
            # Apply strategy parameters
            signals = self._apply_strategy_filters(signals, strategy)

        # Weighted voting
        votes = self._weighted_voting(signals, symbol, regime)

        # Determine final action
        final_action = self._determine_final_action(votes, strategy)
        confidence = self._calculate_consensus_confidence(votes)

        # Create decision
        decision = MetaDecisionV3(
            timestamp=datetime.now(),
            symbol=symbol,
            final_action=final_action,
            confidence=confidence,
            votes=votes,
            agent_signals=signals,
            reasoning_summary=self._generate_reasoning_summary(signals, votes),
            strategy_used=strategy.strategy_name if strategy else "default",
            prompt_used="consensus_decision",
            evolution_applied=self.enable_evolution,
        )

        # Log signals
        self._log_signals_csv(signals, symbol, final_action)

        # Trigger evolution periodically
        if self.enable_evolution:
            self.evolution_counter += 1
            if self.evolution_counter % 10 == 0:
                await self._trigger_evolution()

        return decision

    async def _collect_signals(self, market_state: Dict) -> List[AgentSignalV3]:
        """Collect signals van alle agents."""
        signals = []
        symbol = market_state.get("symbol", "UNKNOWN")
        regime = market_state.get("regime", "unknown")

        for name, agent_data in self.agents.items():
            try:
                agent = agent_data["instance"]

                # Get signal (probeer verschillende methoden)
                if hasattr(agent, "analyze_with_reflection"):
                    result = await agent.analyze_with_reflection(market_state, {})
                elif hasattr(agent, "analyze"):
                    result = await agent.analyze(market_state)
                elif hasattr(agent, "orient"):
                    result = await agent.orient(market_state)
                else:
                    continue

                # Parse result
                action, confidence, reasoning = self._parse_signal_result(result)

                # Extract technicals
                rsi, adx = self._parse_reasoning(reasoning)

                # Get reflection if available
                reflection = ""
                confidence_adj = 1.0
                bias_ack = False

                if hasattr(result, "reflection"):
                    reflection = result.reflection
                if hasattr(result, "confidence_adjustment"):
                    confidence_adj = result.confidence_adjustment
                if hasattr(result, "bias_acknowledged"):
                    bias_ack = result.bias_acknowledged

                signal = AgentSignalV3(
                    timestamp=datetime.now(),
                    agent_name=name,
                    symbol=symbol,
                    action=action,
                    confidence=confidence * confidence_adj,
                    reasoning=reasoning,
                    weight=agent_data["current_weight"],
                    rsi=rsi,
                    adx=adx,
                    regime=regime,
                    reflection=reflection,
                    confidence_adjustment=confidence_adj,
                    bias_acknowledged=bias_ack,
                )

                signals.append(signal)
                self.agent_signals_history.append(signal)

                # Record prompt usage
                self.prompt_evolution.record_usage(
                    prompt_name="consensus_decision",
                    input_data=str(market_state),
                    output_data=action,
                    success=True,
                    quality_score=confidence * 10,
                )

            except Exception as e:
                logger.warning(f"Agent {name} failed: {e}")
                continue

        return signals

    def _parse_signal_result(self, result) -> tuple:
        """Parse verschillende return types."""
        if isinstance(result, tuple):
            return result[0], result[1], result[2] if len(result) > 2 else ""
        elif hasattr(result, "action"):
            return (
                result.action,
                getattr(result, "confidence", 0.5),
                getattr(result, "reasoning", ""),
            )
        elif isinstance(result, dict):
            return (
                result.get("action", "HOLD"),
                result.get("confidence", 0.5),
                result.get("reasoning", ""),
            )
        else:
            return str(result), 0.5, ""

    def _parse_reasoning(self, reasoning: str) -> tuple:
        """Parse RSI/ADX uit reasoning."""
        import re

        rsi = adx = None

        rsi_match = re.search(r"RSI[=:]?\s*(\d+\.?\d*)", reasoning, re.I)
        if rsi_match:
            rsi = float(rsi_match.group(1))

        adx_match = re.search(r"ADX[=:]?\s*(\d+\.?\d*)", reasoning, re.I)
        if adx_match:
            adx = float(adx_match.group(1))

        return rsi, adx

    def _calculate_bias(self, signals: List[AgentSignalV3]) -> Dict:
        """Check voor actie bias."""
        if not signals:
            return {"is_biased": False}

        counts = {"BUY": 0, "SELL": 0, "HOLD": 0}
        for s in signals:
            counts[s.action] = counts.get(s.action, 0) + 1

        total = len(signals)
        for action, count in counts.items():
            if count / total > 0.6:
                return {
                    "is_biased": True,
                    "biased_action": action,
                    "percentage": count / total * 100,
                }

        return {"is_biased": False}

    def _apply_bias_correction(self, signals: List[AgentSignalV3]) -> List[AgentSignalV3]:
        """Forceer balans via bias correctie."""
        counts = {"BUY": 0, "SELL": 0, "HOLD": 0}
        for s in signals:
            counts[s.action] = counts.get(s.action, 0) + 1

        total = len(signals)
        majority_action = max(counts, key=counts.get)

        if counts[majority_action] / total > 0.6:
            # Reduce confidence of majority
            for s in signals:
                if s.action == majority_action:
                    s.confidence *= 0.7
                    s.bias_acknowledged = True
                    s.reasoning += " [BIAS_CORRECTION_APPLIED]"

        return signals

    def _apply_strategy_filters(
        self, signals: List[AgentSignalV3], strategy: StrategyProfile
    ) -> List[AgentSignalV3]:
        """Pas strategie filters toe."""
        filtered = []

        for s in signals:
            # Entry threshold
            if s.action in ["BUY", "SELL"] and s.confidence < strategy.entry_threshold:
                s.action = "HOLD"
                s.reasoning += f" [BELOW_ENTRY_THRESHOLD:{strategy.entry_threshold}]"

            filtered.append(s)

        return filtered

    def _weighted_voting(
        self, signals: List[AgentSignalV3], symbol: str, regime: str
    ) -> Dict[str, int]:
        """Gewogen stemmen."""
        votes = {"BUY": 0, "SELL": 0, "HOLD": 0}

        for s in signals:
            # Get adaptive weight
            weight_key = f"{s.agent_name}_{symbol}_{regime}"
            adaptive_weight = self.adaptive_weights[weight_key].get("current", 1.0)

            # Calculate vote power
            vote_power = s.weight * s.confidence * adaptive_weight
            votes[s.action] = votes.get(s.action, 0) + vote_power

        return votes

    def _determine_final_action(
        self, votes: Dict[str, float], strategy: Optional[StrategyProfile]
    ) -> str:
        """Bepaal finale actie."""
        if not votes:
            return "HOLD"

        # Normalize
        total = sum(votes.values())
        if total == 0:
            return "HOLD"

        # Check consensus threshold from strategy
        threshold = strategy.entry_threshold if strategy else 0.5

        for action, vote_power in votes.items():
            if vote_power / total > threshold:
                return action

        return "HOLD"

    def _calculate_consensus_confidence(self, votes: Dict[str, float]) -> float:
        """Bereken consensus confidence."""
        if not votes:
            return 0.0

        total = sum(votes.values())
        max_vote = max(votes.values())

        return max_vote / total if total > 0 else 0.0

    def _generate_reasoning_summary(
        self, signals: List[AgentSignalV3], votes: Dict[str, float]
    ) -> str:
        """Genereer reasoning summary."""
        total = sum(votes.values())

        summary = f"Consensus: {max(votes, key=votes.get)} | "
        summary += f"Votes: BUY={votes.get('BUY',0)/total:.1%}, "
        summary += f"SELL={votes.get('SELL',0)/total:.1%}, "
        summary += f"HOLD={votes.get('HOLD',0)/total:.1%} | "
        summary += f"Agents: {len(signals)}"

        return summary

    def update_trade_outcome(self, symbol: str, exit_price: float, pnl: float, reason: str) -> None:
        """Update trade outcome en trigger learning."""
        # Record outcome
        self.trade_outcomes[symbol] = {
            "exit_price": exit_price,
            "pnl": pnl,
            "reason": reason,
            "timestamp": datetime.now(),
        }

        # Update agent weights
        self._update_adaptive_weights(symbol, pnl)

        # Record for strategy evolution
        self.strategy_evolution.record_trade(
            strategy_name="consensus_weighted",
            symbol=symbol,
            regime="unknown",
            pnl=pnl,
            duration_days=1,
        )

    def _update_adaptive_weights(self, symbol: str, pnl: float) -> None:
        """Pas adaptive weights aan gebaseerd op PnL."""
        # Find signals for this symbol
        recent_signals = [s for s in self.agent_signals_history if s.symbol == symbol][-10:]

        for signal in recent_signals:
            weight_key = f"{signal.agent_name}_{symbol}_{signal.regime}"

            # Update weight
            if pnl > 0:
                # Increase weight for winners
                self.adaptive_weights[weight_key]["current"] *= 1 + pnl * 0.5
            else:
                # Decrease weight for losers
                self.adaptive_weights[weight_key]["current"] *= 1 - abs(pnl) * 0.3

            # Cap weight
            self.adaptive_weights[weight_key]["current"] = min(
                2.0, max(0.5, self.adaptive_weights[weight_key]["current"])
            )

    async def _trigger_evolution(self):
        """Trigger strategy en prompt evolution."""
        logger.info("Triggering evolution cycle...")

        # Strategy evolution
        if self.strategy_evolution.should_evolve("consensus_weighted"):
            logger.info("Evolving strategy...")
            self.strategy_evolution.evolve_strategy("consensus_weighted")

        # Prompt evolution
        if self.prompt_evolution.should_evolve("agent_reflection"):
            logger.info("Evolving reflection prompt...")
            self.prompt_evolution.evolve_prompt("agent_reflection")

        if self.prompt_evolution.should_evolve("consensus_decision"):
            logger.info("Evolving consensus prompt...")
            self.prompt_evolution.evolve_prompt("consensus_decision")

    def _log_signals_csv(
        self, signals: List[AgentSignalV3], symbol: str, final_action: str
    ) -> None:
        """Log signals naar CSV."""
        log_dir = ".tmp"
        os.makedirs(log_dir, exist_ok=True)

        date_str = datetime.now().strftime("%Y-%m-%d")
        csv_path = os.path.join(log_dir, f"signals_v3_{date_str}.csv")

        file_exists = os.path.exists(csv_path)

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
                        "strategy_version",
                        "prompt_version",
                        "final_decision",
                    ]
                )

            for s in signals:
                writer.writerow(
                    [
                        s.timestamp.isoformat(),
                        s.agent_name,
                        s.symbol,
                        s.action,
                        f"{s.confidence:.4f}",
                        s.reasoning[:200],
                        f"{s.weight:.2f}",
                        f"{s.rsi:.2f}" if s.rsi else "",
                        f"{s.adx:.2f}" if s.adx else "",
                        s.regime or "",
                        f"{s.pnl:.4f}" if s.pnl else "",
                        str(s.was_correct),
                        s.reflection[:100] if s.reflection else "",
                        f"{s.confidence_adjustment:.2f}",
                        str(s.bias_acknowledged),
                        s.strategy_version,
                        s.prompt_version,
                        final_action,
                    ]
                )

    def get_evolution_report(self) -> Dict[str, Any]:
        """Genereer complete evolution report."""
        return {
            "timestamp": datetime.now().isoformat(),
            "strategies": {
                name: self.strategy_evolution.get_evolution_report(name)
                for name in self.strategy_evolution.strategies.keys()
            },
            "prompts": {
                name: self.prompt_evolution.get_evolution_report(name)
                for name in self.prompt_evolution.prompts.keys()
            },
            "performance_summary": {
                "total_signals_logged": len(self.agent_signals_history),
                "total_trades": len(self.trade_outcomes),
                "adaptive_weight_updates": len(self.adaptive_weights),
            },
        }
