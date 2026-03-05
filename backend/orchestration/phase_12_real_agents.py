"""
Phase 12: Real Agent Integration Coordinator

Integrates real cognitive agents (SentimentAgent, MarketRegimeAgent, RiskGovernor)
from backend/agents/ into a unified orchestration system for end-to-end testing.

Key Differences from Phase 11:
- Uses real agent implementations instead of mocks
- Agents have actual cognitive capabilities and state
- May have variable latency due to model execution
- Agents may have initialization overhead
- Agents may fail and require error handling

Architecture:
    Real Agents (from backend/agents/)
        ↓
    Phase12RealAgentCoordinator
        ↓
    Agent Orchestration (parallel execution)
        ↓
    Decision Aggregation (weighted average)
        ↓
    Complete Decision Output

Performance Targets:
- Single agent latency: <200ms
- Three agents latency: <400ms
- Throughput: >1 decisions/second
- Agent startup: <1 second per agent
"""

import logging
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

# Setup logging
logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================


class DecisionAction(Enum):
    """Market decision actions."""

    HOLD = 0
    LONG = 1
    SHORT = 2


# ============================================================================
# DATA CLASSES
# ============================================================================


@dataclass
class Phase12Decision:
    """Complete decision from real agent coordinator."""

    action: int  # 0=hold, 1=long, 2=short
    confidence: float  # [0, 1]
    reasoning: str  # Human-readable explanation
    source: str = "phase12_real_coordinator"
    timestamp: datetime = field(default_factory=datetime.now)
    agent_inputs: dict[str, dict] = field(default_factory=dict)  # Each agent's decision
    aggregation_weights: dict[str, float] = field(default_factory=dict)  # Agent weights


@dataclass
class AgentMetrics:
    """Metrics for a single agent."""

    call_count: int = 0
    total_latency: float = 0.0
    average_latency: float = 0.0
    failure_count: int = 0
    last_decision: dict | None = None
    last_execution_time: float = 0.0


@dataclass
class Phase12RealAgentConfig:
    """Configuration for Phase12RealAgentCoordinator."""

    agent_timeout: float = 5.0  # Timeout per agent in seconds
    fallback_action: int = 0  # Action if all agents fail
    fallback_confidence: float = 0.5  # Confidence for fallback
    enable_parallel_execution: bool = True
    max_decision_history: int = 100
    sentiment_weight: float = 0.25
    market_regime_weight: float = 0.25
    risk_governor_weight: float = 0.25
    vedastro_weight: float = 0.25  # Toegevoegd voor v7


# ============================================================================
# ABSTRACT AGENT INTERFACE
# ============================================================================


class Agent(ABC):
    """Abstract base class for agents."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return agent name."""
        pass

    @abstractmethod
    def analyze(self, features: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        Analyze market and return decision.
        """
        pass


# ============================================================================
# AGENT ADAPTERS
# ============================================================================


class SentimentAdapter(Agent):
    def __init__(self, agent: Any):
        self._agent = agent

    @property
    def name(self) -> str:
        return "SentimentAgent"

    def analyze(self, features: dict[str, Any] | None = None) -> dict[str, Any]:
        # Synchronous wrapper for async analyze_news
        import asyncio

        loop = asyncio.get_event_loop()
        headlines = features.get("headlines", []) if features else []
        coin = features.get("coin", "BTC") if features else "BTC"
        if loop.is_running():
            # In an async loop, we need to be careful. Coordinator uses threads.
            # For simplicity in this L2 context, we mock the async call if needed or use run_coroutine_threadsafe
            return {"action": 0, "confidence": 0.5, "reasoning": "Async sentiment pending"}
        res = asyncio.run(self._agent.analyze_news(headlines, coin))
        return {
            "action": 1 if res.trend == "bullish" else 2 if res.trend == "bearish" else 0,
            "confidence": res.confidence,
            "reasoning": res.rationale,
        }


class VedAstroAdapter(Agent):
    def __init__(self, agent: Any):
        self._agent = agent

    @property
    def name(self) -> str:
        return "VedAstroOracle"

    def analyze(self, features: dict[str, Any] | None = None) -> dict[str, Any]:
        import asyncio

        try:
            res = asyncio.run(self._agent.analyze(features or {}, {}))
            action_map = {"buy": 1, "sell": 2, "hold": 0}
            return {
                "action": action_map.get(res.get("action", "hold"), 0),
                "confidence": res.get("confidence", 0.0),
                "reasoning": res.get("reason", "No reason"),
            }
        except:
            return {"action": 0, "confidence": 0.0, "reasoning": "VedAstro failed"}


class RegimeAdapter(Agent):
    def __init__(self, detector: Any):
        self._detector = detector

    @property
    def name(self) -> str:
        return "MarketRegimeAgent"

    def analyze(self, features: dict[str, Any] | None = None) -> dict[str, Any]:
        if not features:
            return {"action": 0, "confidence": 0.5, "reasoning": "No features"}
        price = features.get("price", 0.0)
        history = features.get("price_history", [price])
        sma50, sma200, vol = self._detector.calculate_indicators(history)
        regime = self._detector.detect(price, sma50, sma200, vol)
        return {
            "action": 0,  # Regime detector doesn't decide buy/sell directly
            "confidence": 1.0,
            "reasoning": f"Regime: {regime.value}",
        }


# ============================================================================
# REAL AGENT DISCOVERY AND LOADING
# ============================================================================


class RealAgentLoader:
    """Loader for real agent implementations."""

    @staticmethod
    def load_sentiment_agent(config_path: str | None = None) -> Agent | None:
        try:
            from backend.agents.sentiment_agent_v2 import SentimentAgentV2

            agent = SentimentAgentV2()
            return SentimentAdapter(agent)
        except Exception as e:
            logger.error(f"Failed to load SentimentAgent: {e}")
            return None

    @staticmethod
    def load_market_regime_agent(config_path: str | None = None) -> Agent | None:
        try:
            from backend.core.regime_detector import RegimeDetector

            detector = RegimeDetector()
            return RegimeAdapter(detector)
        except Exception as e:
            logger.error(f"Failed to load MarketRegimeAgent: {e}")
            return None

    @staticmethod
    def load_vedastro_agent(config_path: str | None = None) -> Agent | None:
        try:
            from backend.agents.vedastro_signal_agent import VedAstroSignalAgent

            agent = VedAstroSignalAgent()
            return VedAstroAdapter(agent)
        except Exception as e:
            logger.error(f"Failed to load VedAstroAgent: {e}")
            return None


# ============================================================================
# PHASE 12 REAL AGENT COORDINATOR
# ============================================================================


class Phase12RealAgentCoordinator:
    """
    Coordinates real cognitive agents for unified decision making.

    Orchestrates SentimentAgent, MarketRegimeAgent, and RiskGovernor
    with proper error handling, state management, and performance tracking.
    """

    def __init__(self, config: Phase12RealAgentConfig):
        """
        Initialize Phase12RealAgentCoordinator.

        Args:
            config: Phase12RealAgentConfig instance
        """
        self.config = config
        self.agents: dict[str, Agent] = {}
        self.agent_weights: dict[str, float] = {}
        self.agent_metrics: dict[str, AgentMetrics] = {}
        self.decision_history: list[Phase12Decision] = []
        self.lock = threading.RLock()

        logger.info("Phase12RealAgentCoordinator initialized")

    def register_agent(self, agent: Agent, weight: float = 1.0) -> None:
        """
        Register a real agent with the coordinator.

        Args:
            agent: Agent instance to register
            weight: Weight for decision aggregation (default 1.0)
        """
        with self.lock:
            self.agents[agent.name] = agent
            self.agent_weights[agent.name] = weight
            self.agent_metrics[agent.name] = AgentMetrics()
            logger.info(f"Registered agent: {agent.name} (weight={weight})")

    def register_all_real_agents(self, config_path: str | None = None) -> int:
        """
        Discover and register all real agents.

        Args:
            config_path: Optional configuration path for agents

        Returns:
            Number of agents successfully registered
        """
        registered_count = 0

        # Load SentimentAgent
        sentiment = RealAgentLoader.load_sentiment_agent(config_path)
        if sentiment:
            self.register_agent(sentiment, self.config.sentiment_weight)
            registered_count += 1

        # Load MarketRegimeAgent
        market_regime = RealAgentLoader.load_market_regime_agent(config_path)
        if market_regime:
            self.register_agent(market_regime, self.config.market_regime_weight)
            registered_count += 1

        # Load VedAstroAgent
        vedastro = RealAgentLoader.load_vedastro_agent(config_path)
        if vedastro:
            self.register_agent(vedastro, self.config.vedastro_weight)
            registered_count += 1

        logger.info(f"Registered {registered_count} real agents")
        return registered_count

    def execute_agent(
        self, agent_name: str, agent: Agent, features: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Execute a single real agent with timeout and error handling.

        Args:
            agent_name: Name of agent being executed
            agent: Agent instance to execute
            features: Context features for analysis

        Returns:
            Agent decision dict or fallback dict
        """
        start_time = time.time()

        try:
            # Call agent's analyze method
            decision = agent.analyze(features)

            # Validate decision format
            if not isinstance(decision, dict):
                logger.error(f"Agent {agent_name} returned invalid type: {type(decision)}")
                return self._create_fallback_decision()

            if not all(key in decision for key in ["action", "confidence", "reasoning"]):
                logger.error(f"Agent {agent_name} missing required fields in decision")
                return self._create_fallback_decision()

            latency = time.time() - start_time

            # Update metrics
            with self.lock:
                metrics = self.agent_metrics[agent_name]
                metrics.call_count += 1
                metrics.total_latency += latency
                metrics.average_latency = metrics.total_latency / metrics.call_count
                metrics.last_decision = decision
                metrics.last_execution_time = latency

            logger.debug(f"Agent {agent_name} executed in {latency:.3f}s")
            return decision

        except Exception as e:
            logger.error(f"Agent {agent_name} failed: {e}")

            with self.lock:
                metrics = self.agent_metrics[agent_name]
                metrics.failure_count += 1

            return self._create_fallback_decision()

    def execute_agents_parallel(
        self, features: dict[str, Any] | None = None
    ) -> dict[str, dict[str, Any]]:
        """
        Execute all registered agents in parallel.

        Returns:
            Dict mapping agent names to their decisions
        """
        results = {}
        threads = []
        results_lock = threading.Lock()

        def worker(agent_name: str, agent: Agent):
            decision = self.execute_agent(agent_name, agent, features)
            with results_lock:
                results[agent_name] = decision

        # Launch all agent threads
        for agent_name, agent in self.agents.items():
            thread = threading.Thread(target=worker, args=(agent_name, agent), daemon=False)
            thread.start()
            threads.append(thread)

        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=self.config.agent_timeout)

        # Ensure all agents are in results (use fallback if timeout)
        for agent_name in self.agents:
            if agent_name not in results:
                logger.warning(f"Agent {agent_name} timed out, using fallback")
                results[agent_name] = self._create_fallback_decision()

        return results

    def aggregate_decisions(
        self, agent_decisions: dict[str, dict[str, Any]]
    ) -> tuple[int, float, str]:
        """
        Aggregate decisions from all agents using weighted averaging.

        Args:
            agent_decisions: Dict mapping agent names to decisions

        Returns:
            (aggregated_action, aggregated_confidence, combined_reasoning)
        """
        if not agent_decisions:
            logger.warning("No agent decisions to aggregate")
            return 0, 0.5, "No agents available"

        # Extract decisions and weights
        actions = []
        confidences = []
        reasoning_parts = []

        for agent_name, decision in agent_decisions.items():
            action = decision.get("action", 0)
            confidence = decision.get("confidence", 0.5)
            reasoning = decision.get("reasoning", "")
            weight = self.agent_weights.get(agent_name, 1.0)

            actions.append(action)
            confidences.append(confidence * weight)

            if reasoning:
                reasoning_parts.append(f"{agent_name}: {reasoning}")

        # Calculate weighted average confidence
        total_weight = sum(self.agent_weights.values())
        avg_confidence = sum(confidences) / total_weight if total_weight > 0 else 0.5
        avg_confidence = min(1.0, max(0.0, avg_confidence))  # Clamp to [0, 1]

        # Determine action from weighted sum
        weighted_actions = []
        for agent_name, decision in agent_decisions.items():
            action = decision.get("action", 0)
            weight = self.agent_weights.get(agent_name, 1.0)
            weighted_actions.append(action * weight)

        avg_action_value = sum(weighted_actions) / total_weight if total_weight > 0 else 0

        # Convert to action (round to nearest valid action)
        if avg_action_value < 0.5:
            final_action = 0  # HOLD
        elif avg_action_value < 1.5:
            final_action = 1  # LONG
        else:
            final_action = 2  # SHORT

        # Combine reasoning
        combined_reasoning = (
            " | ".join(reasoning_parts) if reasoning_parts else "No reasoning available"
        )

        return final_action, avg_confidence, combined_reasoning

    def make_decision(self, features: dict[str, Any] | None = None) -> Phase12Decision:
        """
        Execute all agents and make unified decision.

        Returns:
            Phase12Decision with complete decision information
        """
        start_time = time.time()

        # Execute all agents in parallel
        agent_decisions = self.execute_agents_parallel(features)

        # Aggregate decisions
        action, confidence, reasoning = self.aggregate_decisions(agent_decisions)

        # Create decision object
        decision = Phase12Decision(
            action=action,
            confidence=confidence,
            reasoning=reasoning,
            agent_inputs=agent_decisions,
            aggregation_weights=dict(self.agent_weights),
        )

        # Store in history
        with self.lock:
            self.decision_history.append(decision)

            # Trim history if needed
            if len(self.decision_history) > self.config.max_decision_history:
                self.decision_history = self.decision_history[-self.config.max_decision_history :]

        latency = time.time() - start_time
        logger.info(
            f"Decision made in {latency:.3f}s: action={action}, confidence={confidence:.2f}"
        )

        return decision

    def get_metrics(self) -> dict[str, Any]:
        """
        Get system-wide metrics.

        Returns:
            Dict with aggregate metrics
        """
        with self.lock:
            total_decisions = len(self.decision_history)

            confidences = [d.confidence for d in self.decision_history]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            action_counts = {0: 0, 1: 0, 2: 0}
            for decision in self.decision_history:
                action_counts[decision.action] += 1

            return {
                "decisions_made": total_decisions,
                "average_confidence": avg_confidence,
                "action_distribution": action_counts,
                "last_decision": (self.decision_history[-1] if self.decision_history else None),
                "agents_registered": len(self.agents),
                "agents_available": list(self.agents.keys()),
            }

    def get_agent_statistics(self, agent_name: str | None = None) -> dict[str, Any]:
        """
        Get statistics for specific agent or all agents.

        Args:
            agent_name: Specific agent name or None for all agents

        Returns:
            Dict with agent statistics
        """
        with self.lock:
            if agent_name:
                if agent_name not in self.agent_metrics:
                    return {"error": f"Agent {agent_name} not found"}

                metrics = self.agent_metrics[agent_name]
                return {
                    "name": agent_name,
                    "call_count": metrics.call_count,
                    "average_latency": metrics.average_latency,
                    "failure_count": metrics.failure_count,
                    "last_execution_time": metrics.last_execution_time,
                    "weight": self.agent_weights.get(agent_name, 1.0),
                }
            else:
                result = {}
                for name, metrics in self.agent_metrics.items():
                    result[name] = {
                        "call_count": metrics.call_count,
                        "average_latency": metrics.average_latency,
                        "failure_count": metrics.failure_count,
                        "weight": self.agent_weights.get(name, 1.0),
                    }
                return result

    def get_decision_history(self, limit: int | None = None) -> list[Phase12Decision]:
        """
        Get decision history.

        Args:
            limit: Maximum number of decisions to return

        Returns:
            List of Phase12Decision objects
        """
        with self.lock:
            if limit:
                return self.decision_history[-limit:]
            return list(self.decision_history)

    def reset_metrics(self) -> None:
        """Reset all metrics and history."""
        with self.lock:
            self.decision_history.clear()
            for metrics in self.agent_metrics.values():
                metrics.call_count = 0
                metrics.total_latency = 0.0
                metrics.average_latency = 0.0
                metrics.failure_count = 0

        logger.info("Metrics reset")

    def _create_fallback_decision(self) -> dict[str, Any]:
        """
        Create a fallback decision when agent fails.

        Returns:
            Fallback decision dict
        """
        return {
            "action": self.config.fallback_action,
            "confidence": self.config.fallback_confidence,
            "reasoning": "Fallback decision - agent failed to respond",
        }


# ============================================================================
# HELPER FUNCTIONS FOR TESTING
# ============================================================================


def create_real_agent_coordinator(
    config_path: str | None = None, config: Phase12RealAgentConfig | None = None
) -> Phase12RealAgentCoordinator:
    """
    Create a Phase12RealAgentCoordinator with all real agents.

    Args:
        config_path: Optional configuration path for agents
        config: Optional Phase12RealAgentConfig (uses defaults if None)

    Returns:
        Configured Phase12RealAgentCoordinator
    """
    if config is None:
        config = Phase12RealAgentConfig()

    coordinator = Phase12RealAgentCoordinator(config)
    coordinator.register_all_real_agents(config_path)

    return coordinator


def create_coordinator_with_agents(
    agents: list[Agent], config: Phase12RealAgentConfig | None = None
) -> Phase12RealAgentCoordinator:
    """
    Create coordinator with specific agents.

    Args:
        agents: List of Agent instances to register
        config: Optional Phase12RealAgentConfig

    Returns:
        Configured Phase12RealAgentCoordinator
    """
    if config is None:
        config = Phase12RealAgentConfig()

    coordinator = Phase12RealAgentCoordinator(config)

    for agent in agents:
        coordinator.register_agent(agent)

    return coordinator
