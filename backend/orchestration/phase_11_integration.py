"""
Phase 11: Real Agent Integration Implementation

Provides mock implementations of cognitive agents for testing the full pipeline:
- SentimentAgent: Analyzes market sentiment
- MarketRegimeAgent: Detects market regime
- RiskGovernor: Manages risk constraints
- Phase11 Coordinator: Orchestrates the pipeline

All agents follow the standard interface:
- name property
- analyze() method returning {action, confidence, reasoning}
"""

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict

logger = logging.getLogger(__name__)


# ============================================================================
# ABSTRACT AGENT INTERFACE
# ============================================================================


class Agent(ABC):
    """Base class for all trading agents."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Agent name for identification."""
        pass

    @abstractmethod
    def analyze(self) -> Dict[str, Any]:
        """
        Analyze market and return decision.

        Returns:
            dict with keys:
                - action: int (0=hold, 1=long, 2=short)
                - confidence: float [0, 1]
                - reasoning: str (human-readable explanation)
        """
        pass


# ============================================================================
# MOCK SENTIMENT AGENT
# ============================================================================


class MockSentimentAgent(Agent):
    """
    Mock SentimentAgent for Phase 11 testing.

    Simulates sentiment analysis from news, social media, and market signals.
    """

    def __init__(self, default_confidence: float = 0.85):
        """
        Initialize mock sentiment agent.

        Args:
            default_confidence: Default confidence level for decisions
        """
        self._name = "SentimentAgent"
        self._default_confidence = default_confidence
        self._call_count = 0
        self._analysis_history = []

    @property
    def name(self) -> str:
        """Agent name."""
        return self._name

    def analyze(self) -> Dict[str, Any]:
        """
        Analyze sentiment and return decision.

        For mock, returns configurable bullish decision with varying confidence.
        """
        self._call_count += 1

        decision = {
            "action": 1,  # Bullish
            "confidence": self._default_confidence,
            "reasoning": f"Positive sentiment detected (call #{self._call_count})",
        }

        self._analysis_history.append({"timestamp": time.time(), "decision": decision})

        return decision

    @property
    def call_count(self) -> int:
        """Number of times analyze() was called."""
        return self._call_count

    @property
    def analysis_history(self) -> list:
        """History of all analyses."""
        return self._analysis_history


# ============================================================================
# MOCK MARKET REGIME AGENT
# ============================================================================


class MockMarketRegimeAgent(Agent):
    """
    Mock MarketRegimeAgent for Phase 11 testing.

    Simulates market regime detection (trend, mean reversion, etc.).
    """

    def __init__(self, default_action: int = 1, default_confidence: float = 0.72):
        """
        Initialize mock market regime agent.

        Args:
            default_action: Default action (0=hold, 1=long, 2=short)
            default_confidence: Default confidence level
        """
        self._name = "MarketRegimeAgent"
        self._default_action = default_action
        self._default_confidence = default_confidence
        self._call_count = 0
        self._analysis_history = []

    @property
    def name(self) -> str:
        """Agent name."""
        return self._name

    def analyze(self) -> Dict[str, Any]:
        """
        Analyze market regime and return decision.

        For mock, returns configurable action with varying confidence.
        """
        self._call_count += 1

        action_names = {0: "Hold", 1: "Uptrend", 2: "Downtrend"}

        decision = {
            "action": self._default_action,
            "confidence": self._default_confidence,
            "reasoning": f"{action_names[self._default_action]} detected (call #{self._call_count})",
        }

        self._analysis_history.append({"timestamp": time.time(), "decision": decision})

        return decision

    @property
    def call_count(self) -> int:
        """Number of times analyze() was called."""
        return self._call_count

    @property
    def analysis_history(self) -> list:
        """History of all analyses."""
        return self._analysis_history

    def set_default_action(self, action: int, confidence: float = None):
        """Update default action and optionally confidence."""
        self._default_action = action
        if confidence is not None:
            self._default_confidence = confidence


# ============================================================================
# MOCK RISK GOVERNOR
# ============================================================================


class MockRiskGovernor(Agent):
    """
    Mock RiskGovernor for Phase 11 testing.

    Simulates risk management constraints on trading decisions.
    """

    def __init__(self, allow_trading: bool = True, confidence: float = 0.9):
        """
        Initialize mock risk governor.

        Args:
            allow_trading: Whether trading is allowed
            confidence: Confidence in risk assessment
        """
        self._name = "RiskGovernor"
        self._allow_trading = allow_trading
        self._confidence = confidence
        self._call_count = 0
        self._analysis_history = []

    @property
    def name(self) -> str:
        """Agent name."""
        return self._name

    def analyze(self) -> Dict[str, Any]:
        """
        Analyze risk and return decision.

        Returns hold (0) if trading not allowed, otherwise approves decisions.
        """
        self._call_count += 1

        if self._allow_trading:
            action = 1  # Approve (or delegate to other agents)
            reasoning = f"Risk within acceptable bounds (call #{self._call_count})"
        else:
            action = 0  # Hold - deny trading
            reasoning = f"Risk constraints violated (call #{self._call_count})"

        decision = {
            "action": action,
            "confidence": self._confidence,
            "reasoning": reasoning,
        }

        self._analysis_history.append({"timestamp": time.time(), "decision": decision})

        return decision

    @property
    def call_count(self) -> int:
        """Number of times analyze() was called."""
        return self._call_count

    @property
    def analysis_history(self) -> list:
        """History of all analyses."""
        return self._analysis_history

    def set_allow_trading(self, allow: bool, confidence: float = None):
        """Update trading permission and optionally confidence."""
        self._allow_trading = allow
        if confidence is not None:
            self._confidence = confidence


# ============================================================================
# PHASE 11 INTEGRATION TEST COORDINATOR
# ============================================================================


@dataclass
class Phase11IntegrationConfig:
    """Configuration for Phase 11 integration testing."""

    config_path: str
    sentiment_weight: float = 1.0
    market_regime_weight: float = 0.8
    risk_governor_weight: float = 1.5
    update_interval: int = 5
    use_real_agents: bool = False


class Phase11IntegrationCoordinator:
    """
    Orchestrator for Phase 11 integration testing.

    Manages mock agents, coordinates decisions, and validates pipeline.
    """

    def __init__(self, config: Phase11IntegrationConfig):
        """
        Initialize integration coordinator.

        Args:
            config: Phase11IntegrationConfig with paths and weights
        """
        self.config = config
        self.agents: Dict[str, Agent] = {}
        self.agent_weights: Dict[str, float] = {}
        self._call_count = 0
        self._decision_history = []

        logger.info("Phase 11 Integration Coordinator initialized")

    def add_sentiment_agent(self, agent: MockSentimentAgent = None):
        """Add sentiment agent (or create mock)."""
        if agent is None:
            agent = MockSentimentAgent(default_confidence=0.85)
        self.agents["SentimentAgent"] = agent
        self.agent_weights["SentimentAgent"] = self.config.sentiment_weight
        logger.info(f"Added SentimentAgent with weight {self.config.sentiment_weight}")

    def add_market_regime_agent(self, agent: MockMarketRegimeAgent = None):
        """Add market regime agent (or create mock)."""
        if agent is None:
            agent = MockMarketRegimeAgent(default_action=1, default_confidence=0.72)
        self.agents["MarketRegimeAgent"] = agent
        self.agent_weights["MarketRegimeAgent"] = self.config.market_regime_weight
        logger.info(
            f"Added MarketRegimeAgent with weight {self.config.market_regime_weight}"
        )

    def add_risk_governor(self, agent: MockRiskGovernor = None):
        """Add risk governor (or create mock)."""
        if agent is None:
            agent = MockRiskGovernor(allow_trading=True, confidence=0.9)
        self.agents["RiskGovernor"] = agent
        self.agent_weights["RiskGovernor"] = self.config.risk_governor_weight
        logger.info(
            f"Added RiskGovernor with weight {self.config.risk_governor_weight}"
        )

    def execute_agents(self) -> Dict[str, Dict[str, Any]]:
        """
        Execute all agents and return their decisions.

        Returns:
            dict mapping agent names to their decisions
        """
        decisions = {}
        for name, agent in self.agents.items():
            try:
                decision = agent.analyze()
                decisions[name] = decision
                logger.debug(
                    f"{name} decision: action={decision['action']}, confidence={decision['confidence']}"
                )
            except Exception as e:
                logger.error(f"{name} failed to analyze: {e}")
                decisions[name] = None

        return decisions

    def aggregate_decisions(
        self, decisions: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Aggregate agent decisions using weighted averaging.

        Args:
            decisions: dict mapping agent names to their decisions

        Returns:
            aggregated decision: {action, confidence, reasoning, source}
        """
        valid_decisions = {
            name: dec for name, dec in decisions.items() if dec is not None
        }

        if not valid_decisions:
            # Fallback: all agents failed
            return {
                "action": 0,
                "confidence": 0.5,
                "reasoning": "All agents failed - fallback decision",
                "source": "Fallback",
            }

        # Aggregate confidence scores using weights
        total_weight = sum(self.agent_weights[name] for name in valid_decisions.keys())

        weighted_confidence = (
            sum(
                valid_decisions[name]["confidence"] * self.agent_weights[name]
                for name in valid_decisions.keys()
            )
            / total_weight
        )

        # Majority vote for action (weighted)
        action_scores = {0: 0.0, 1: 0.0, 2: 0.0}
        for name, decision in valid_decisions.items():
            weight = self.agent_weights[name]
            action = decision["action"]
            action_scores[action] += weight * decision["confidence"]

        final_action = max(action_scores.items(), key=lambda x: x[1])[0]

        # Combine reasoning from all agents
        sources = list(valid_decisions.keys())
        reasoning = f"Aggregated from {len(sources)} agents"

        return {
            "action": final_action,
            "confidence": min(1.0, weighted_confidence),
            "reasoning": reasoning,
            "source": ", ".join(sources),
        }

    def make_decision(self) -> Dict[str, Any]:
        """
        Execute full pipeline: execute agents, aggregate decisions.

        Returns:
            final aggregated decision
        """
        self._call_count += 1

        # Execute all agents
        decisions = self.execute_agents()

        # Aggregate decisions
        final_decision = self.aggregate_decisions(decisions)
        final_decision["timestamp"] = time.time()

        self._decision_history.append(final_decision)

        logger.info(
            f"Decision #{self._call_count}: action={final_decision['action']}, "
            f"confidence={final_decision['confidence']:.2f}, "
            f"source={final_decision['source']}"
        )

        return final_decision

    def get_metrics(self) -> Dict[str, Any]:
        """Get coordination metrics."""
        if not self._decision_history:
            return {"decisions_made": 0, "avg_confidence": 0, "action_distribution": {}}

        confidences = [d["confidence"] for d in self._decision_history]
        actions = [d["action"] for d in self._decision_history]

        action_dist = {0: 0, 1: 0, 2: 0}
        for action in actions:
            action_dist[action] += 1

        return {
            "decisions_made": len(self._decision_history),
            "avg_confidence": sum(confidences) / len(confidences),
            "action_distribution": action_dist,
            "last_decision": (
                self._decision_history[-1] if self._decision_history else None
            ),
        }

    def get_agent_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for each agent."""
        stats = {}
        for name, agent in self.agents.items():
            stats[name] = {
                "call_count": agent.call_count if hasattr(agent, "call_count") else 0,
                "weight": self.agent_weights.get(name, 0),
            }
        return stats


# ============================================================================
# HELPER FUNCTIONS FOR TESTING
# ============================================================================


def create_test_coordinator(config_path: str) -> Phase11IntegrationCoordinator:
    """Create a fully initialized test coordinator with all mock agents."""
    config = Phase11IntegrationConfig(config_path=config_path)
    coordinator = Phase11IntegrationCoordinator(config)
    coordinator.add_sentiment_agent()
    coordinator.add_market_regime_agent()
    coordinator.add_risk_governor()
    return coordinator


def create_coordinator_with_custom_agents(
    config_path: str,
    sentiment_agent: MockSentimentAgent = None,
    market_regime_agent: MockMarketRegimeAgent = None,
    risk_governor: MockRiskGovernor = None,
) -> Phase11IntegrationCoordinator:
    """Create test coordinator with custom mock agents."""
    config = Phase11IntegrationConfig(config_path=config_path)
    coordinator = Phase11IntegrationCoordinator(config)
    if sentiment_agent:
        coordinator.agents["SentimentAgent"] = sentiment_agent
        coordinator.agent_weights["SentimentAgent"] = config.sentiment_weight
    if market_regime_agent:
        coordinator.agents["MarketRegimeAgent"] = market_regime_agent
        coordinator.agent_weights["MarketRegimeAgent"] = config.market_regime_weight
    if risk_governor:
        coordinator.agents["RiskGovernor"] = risk_governor
        coordinator.agent_weights["RiskGovernor"] = config.risk_governor_weight
    return coordinator


# ============================================================================
# INITIALIZATION
# ============================================================================

if __name__ == "__main__":
    # Example usage
    import tempfile

    # Create temporary config file
    fd, config_path = tempfile.mkstemp(suffix=".bin")
    import os

    os.close(fd)

    try:
        # Create coordinator with mock agents
        coordinator = create_test_coordinator(config_path)

        # Make a decision
        decision = coordinator.make_decision()
        print(f"Decision: {decision}")

        # Get metrics
        metrics = coordinator.get_metrics()
        print(f"Metrics: {metrics}")

        # Get agent stats
        stats = coordinator.get_agent_statistics()
        print(f"Agent stats: {stats}")
    finally:
        if os.path.exists(config_path):
            os.unlink(config_path)
