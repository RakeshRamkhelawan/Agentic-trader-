"""
ColdPathCoordinator - LLM-based decision orchestration system.

Characteristics:
- Orchestrates multiple cognitive agents
- Makes trading decisions based on agent outputs
- Updates FastConfig every 5-60 seconds
- Thread-safe event-driven architecture
- Graceful agent failure handling
- Deterministic decision aggregation

Architecture:
Cold Path (100ms-1000ms)
├── SentimentAgent → sentiment score
├── MarketRegimeAgent → regime classification
├── Other cognitive agents → various signals
└── ColdPathCoordinator
    ├── Aggregates agent outputs
    ├── Makes weighted decision
    ├── Updates FastConfig (throttled)
    └── Publishes events

Integration:
ColdPath → FastConfig → HotPath (reads config, <1ms execution)
"""

import time
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable
from threading import Lock, RLock
from pathlib import Path
import logging

from backend.execution.fast_config import FastConfigManager, FALLBACK_CONFIG


logger = logging.getLogger(__name__)


@dataclass
class CoordinatorDecision:
    """Decision made by coordinator."""
    action: int  # 0=hold, 1=long, 2=short
    confidence: float  # [0, 1]
    reasoning: str  # Why this decision
    source: str  # Which agents contributed (comma-separated)
    timestamp: float  # When decision was made
    
    def to_config(self) -> Dict[str, Any]:
        """Convert to FastConfig format."""
        return {
            'action': self.action,
            'confidence': self.confidence,
            'exploration_rate': 0.1  # Default exploration
        }


@dataclass
class AgentMetrics:
    """Metrics for a single agent."""
    name: str
    calls: int = 0
    failures: int = 0
    total_latency: float = 0.0  # Sum of all latencies
    total_confidence: float = 0.0  # Sum of confidences
    last_failure: Optional[float] = None
    
    @property
    def avg_latency(self) -> float:
        """Average latency per call."""
        if self.calls == 0:
            return 0.0
        return self.total_latency / self.calls
    
    @property
    def avg_confidence(self) -> float:
        """Average confidence per call."""
        if self.calls == 0:
            return 0.0
        return self.total_confidence / self.calls
    
    @property
    def failure_rate(self) -> float:
        """Fraction of calls that failed."""
        if self.calls == 0:
            return 0.0
        return self.failures / self.calls


@dataclass
class CoordinatorMetrics:
    """Metrics for coordinator."""
    decisions_made: int = 0
    config_writes: int = 0
    config_skips: int = 0
    total_decision_latency: float = 0.0
    agent_metrics: Dict[str, AgentMetrics] = field(default_factory=dict)
    action_distribution: Dict[int, int] = field(default_factory=lambda: {0: 0, 1: 0, 2: 0})
    
    @property
    def avg_decision_latency(self) -> float:
        """Average decision latency."""
        if self.decisions_made == 0:
            return 0.0
        return self.total_decision_latency / self.decisions_made


@dataclass
class CoordinatorHealth:
    """Health status of coordinator."""
    operational_agents: int
    failed_agents: int
    total_agents: int
    last_update: float
    config_version: int
    is_operational: bool
    failed_agent_names: List[str] = field(default_factory=list)


class ColdPathCoordinator:
    """
    Orchestrates multiple cognitive agents for trading decisions.
    
    Responsibilities:
    - Register and manage agents
    - Call agents and aggregate their outputs
    - Make unified trading decisions
    - Update FastConfig with decisions (throttled)
    - Handle agent failures gracefully
    - Publish events
    - Track metrics and health
    """
    
    DEFAULT_UPDATE_INTERVAL = 30.0  # seconds
    MIN_UPDATE_INTERVAL = 5.0
    MAX_UPDATE_INTERVAL = 60.0
    AGENT_RETRY_INTERVAL = 60.0  # Retry failed agents after 60s
    
    def __init__(
        self,
        config_path: str,
        event_bus: Optional[Any] = None,
        update_interval: float = DEFAULT_UPDATE_INTERVAL
    ):
        """
        Initialize ColdPathCoordinator.
        
        Args:
            config_path: Path to FastConfig file
            event_bus: Optional event bus for publishing events
            update_interval: FastConfig update interval in seconds
        """
        self.config_path = Path(config_path)
        self.config_manager = FastConfigManager(str(config_path))
        self.event_bus = event_bus
        
        # Validate and set update interval
        self.update_interval = max(
            self.MIN_UPDATE_INTERVAL,
            min(update_interval, self.MAX_UPDATE_INTERVAL)
        )
        
        # Agent management
        self.agents: List[Any] = []
        self.agent_weights: Dict[str, float] = {}  # Reliability weights
        self.failed_agents: Dict[str, float] = {}  # name -> failure_time
        
        # Config write throttling
        self.last_config_write = 0.0
        self.last_best_decision: Optional[CoordinatorDecision] = None
        
        # Metrics and monitoring
        self.metrics = CoordinatorMetrics()
        self.decision_history: List[CoordinatorDecision] = []
        self.max_history_size = 100
        
        # Thread safety
        self.write_lock = RLock()
        self.agent_lock = RLock()
        
        # State
        self.is_operational = True
        self._initialize_from_config()
    
    def _initialize_from_config(self) -> None:
        """Initialize coordinator from FastConfig."""
        try:
            config = self.config_manager.read_fast()
            logger.info(f"Initialized from config: action={config.get('action')}")
        except Exception as e:
            logger.warning(f"Could not read initial config: {e}")
    
    def register_agent(self, agent: Any, weight: float = 1.0) -> None:
        """
        Register a cognitive agent.
        
        Args:
            agent: Agent with analyze() method and name attribute
            weight: Reliability weight (default 1.0)
            
        Raises:
            ValueError: Agent missing required attributes/methods
        """
        # Validate agent interface
        if not hasattr(agent, 'analyze'):
            raise ValueError(f"Agent must have analyze() method")
        if not hasattr(agent, 'name'):
            raise ValueError(f"Agent must have name attribute")
        
        with self.agent_lock:
            self.agents.append(agent)
            self.agent_weights[agent.name] = weight
            self.metrics.agent_metrics[agent.name] = AgentMetrics(agent.name)
            
            logger.info(f"Registered agent: {agent.name} (weight={weight})")
    
    def make_decision(self) -> CoordinatorDecision:
        """
        Make a trading decision by aggregating agent outputs.
        
        Returns:
            CoordinatorDecision with action and confidence
        """
        start_time = time.perf_counter()
        
        try:
            # Execute all agents
            agent_results = self._execute_agents()
            
            if not agent_results:
                # Fallback: all agents failed
                decision = self._make_fallback_decision()
            else:
                # Aggregate results
                decision = self._aggregate_decisions(agent_results)
            
            # Record decision
            with self.write_lock:
                self.metrics.decisions_made += 1
                self.metrics.action_distribution[decision.action] += 1
                
                elapsed = time.perf_counter() - start_time
                self.metrics.total_decision_latency += elapsed
                
                # Keep history and track best decision
                self.decision_history.append(decision)
                if len(self.decision_history) > self.max_history_size:
                    self.decision_history.pop(0)
                
                # Update last best decision
                if self.last_best_decision is None or decision.confidence > self.last_best_decision.confidence:
                    self.last_best_decision = decision
            
            return decision
        
        except Exception as e:
            logger.error(f"Error making decision: {e}", exc_info=True)
            return self._make_fallback_decision()
    
    def _execute_agents(self) -> Dict[str, Any]:
        """
        Execute all registered agents.
        
        Returns:
            Dict of agent_name -> agent_output
        """
        results = {}
        current_time = time.time()
        
        with self.agent_lock:
            for agent in self.agents:
                agent_name = agent.name
                
                # Skip if agent recently failed (will retry after interval)
                if agent_name in self.failed_agents:
                    failure_time = self.failed_agents[agent_name]
                    if current_time - failure_time < self.AGENT_RETRY_INTERVAL:
                        logger.debug(f"Skipping failed agent: {agent_name}")
                        continue
                    else:
                        # Time to retry
                        del self.failed_agents[agent_name]
                        logger.info(f"Retrying failed agent: {agent_name}")
                
                try:
                    # Call agent
                    start = time.perf_counter()
                    output = agent.analyze()
                    elapsed = time.perf_counter() - start
                    
                    # Validate output format
                    self._validate_agent_output(output)
                    
                    results[agent_name] = output
                    
                    # Update metrics
                    metrics = self.metrics.agent_metrics[agent_name]
                    metrics.calls += 1
                    metrics.total_latency += elapsed
                    metrics.total_confidence += output.get('confidence', 0.5)
                    
                    logger.debug(f"Agent {agent_name}: action={output.get('action')}, "
                               f"confidence={output.get('confidence'):.2f}, latency={elapsed*1000:.1f}ms")
                
                except Exception as e:
                    logger.warning(f"Agent {agent_name} failed: {e}")
                    
                    # Mark as failed
                    self.failed_agents[agent_name] = current_time
                    
                    # Update metrics
                    metrics = self.metrics.agent_metrics[agent_name]
                    metrics.calls += 1
                    metrics.failures += 1
                    metrics.last_failure = current_time
        
        return results
    
    def _aggregate_decisions(self, results: Dict[str, Any]) -> CoordinatorDecision:
        """
        Aggregate agent outputs into a single decision.
        
        Args:
            results: Dict of agent_name -> output
            
        Returns:
            CoordinatorDecision
        """
        if not results:
            return self._make_fallback_decision()
        
        # Group by action
        action_groups: Dict[int, List[float]] = {0: [], 1: [], 2: []}
        
        for agent_name, output in results.items():
            action = output.get('action', 0)
            confidence = output.get('confidence', 0.5)
            weight = self.agent_weights.get(agent_name, 1.0)
            
            # Weighted confidence
            weighted_confidence = confidence * weight
            action_groups[action].append(weighted_confidence)
        
        # Find action with highest average confidence
        action_scores = {
            action: sum(scores) / len(scores)
            for action, scores in action_groups.items()
            if scores
        }
        
        if not action_scores:
            return self._make_fallback_decision()
        
        # Choose action with highest score
        best_action = max(action_scores, key=action_scores.get)
        best_confidence = action_scores[best_action]
        
        # Normalize confidence to [0, 1]
        best_confidence = min(1.0, max(0.0, best_confidence))
        
        # Create decision
        decision = CoordinatorDecision(
            action=best_action,
            confidence=best_confidence,
            reasoning=self._generate_reasoning(results, best_action, best_confidence),
            source=','.join(sorted(results.keys())),
            timestamp=time.time()
        )
        
        return decision
    
    def _make_fallback_decision(self) -> CoordinatorDecision:
        """
        Make fallback decision when agents unavailable.
        
        Returns:
            Safe default decision (hold)
        """
        return CoordinatorDecision(
            action=0,  # Hold
            confidence=0.5,  # Neutral
            reasoning='Fallback decision (agents unavailable)',
            source='',
            timestamp=time.time()
        )
    
    def _validate_agent_output(self, output: Dict[str, Any]) -> None:
        """
        Validate agent output format.
        
        Args:
            output: Agent output dict
            
        Raises:
            ValueError: Invalid format
        """
        if not isinstance(output, dict):
            raise ValueError(f"Agent output must be dict, got {type(output)}")
        
        if 'action' not in output:
            raise ValueError("Agent output missing 'action'")
        if 'confidence' not in output:
            raise ValueError("Agent output missing 'confidence'")
        
        action = output['action']
        confidence = output['confidence']
        
        if not isinstance(action, int) or action not in [0, 1, 2]:
            raise ValueError(f"action must be 0-2, got {action}")
        if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
            raise ValueError(f"confidence must be 0-1, got {confidence}")
    
    def _generate_reasoning(
        self,
        results: Dict[str, Any],
        best_action: int,
        confidence: float
    ) -> str:
        """
        Generate human-readable decision reasoning.
        
        Args:
            results: Agent outputs
            best_action: Chosen action
            confidence: Decision confidence
            
        Returns:
            Reasoning string
        """
        agents = ', '.join(sorted(results.keys()))
        action_name = {0: 'HOLD', 1: 'LONG', 2: 'SHORT'}[best_action]
        return f"{action_name} (confidence={confidence:.2f}) from {agents}"
    
    def write_config(self, decision: Optional[CoordinatorDecision] = None) -> None:
        """
        Write decision to FastConfig if enough time has passed.
        
        Uses throttling to avoid writing config too frequently.
        
        Args:
            decision: Decision to write (uses last decision if None)
        """
        current_time = time.time()
        
        # Check if enough time has passed since last write
        if current_time - self.last_config_write < self.update_interval:
            with self.write_lock:
                self.metrics.config_skips += 1
            return
        
        # Use provided decision or last decision
        if decision is None:
            if self.last_best_decision is None:
                return  # No decision to write yet
            decision = self.last_best_decision
        
        try:
            with self.write_lock:
                # Write config
                config = decision.to_config()
                self.config_manager.write_atomic(config)
                
                # Update tracking
                self.last_config_write = current_time
                self.last_best_decision = decision
                self.metrics.config_writes += 1
                
                logger.info(f"Wrote config: action={decision.action}, "
                           f"confidence={decision.confidence:.2f}")
        
        except Exception as e:
            logger.error(f"Error writing config: {e}", exc_info=True)
    
    def set_update_interval(self, interval: float) -> None:
        """
        Set FastConfig update interval.
        
        Args:
            interval: Seconds between updates (5-60)
        """
        self.update_interval = max(
            self.MIN_UPDATE_INTERVAL,
            min(interval, self.MAX_UPDATE_INTERVAL)
        )
        logger.info(f"Set update interval to {self.update_interval}s")
    
    def get_current_config(self) -> Dict[str, Any]:
        """
        Get current config from FastConfig.
        
        Returns:
            Current configuration
        """
        return self.config_manager.read_fast()
    
    def get_health(self) -> CoordinatorHealth:
        """
        Get health status.
        
        Returns:
            CoordinatorHealth object
        """
        with self.agent_lock:
            operational = len(self.agents) - len(self.failed_agents)
            failed = len(self.failed_agents)
            total = len(self.agents)
        
        return CoordinatorHealth(
            operational_agents=operational,
            failed_agents=failed,
            total_agents=total,
            last_update=self.last_config_write,
            config_version=self.config_manager.get_version(),
            is_operational=self.is_operational and operational > 0,
            failed_agent_names=list(self.failed_agents.keys())
        )
    
    def get_metrics(self) -> CoordinatorMetrics:
        """
        Get coordinator metrics.
        
        Returns:
            CoordinatorMetrics object
        """
        with self.write_lock:
            return CoordinatorMetrics(
                decisions_made=self.metrics.decisions_made,
                config_writes=self.metrics.config_writes,
                config_skips=self.metrics.config_skips,
                total_decision_latency=self.metrics.total_decision_latency,
                agent_metrics=dict(self.metrics.agent_metrics),
                action_distribution=dict(self.metrics.action_distribution)
            )
    
    def get_decision_history(self, num_decisions: int = 10) -> List[CoordinatorDecision]:
        """
        Get recent decision history.
        
        Args:
            num_decisions: Number of recent decisions to return
            
        Returns:
            List of CoordinatorDecision objects
        """
        with self.write_lock:
            return list(self.decision_history[-num_decisions:])
    
    def get_agent_metrics(self, agent_name: str) -> Optional[AgentMetrics]:
        """
        Get metrics for specific agent.
        
        Args:
            agent_name: Name of agent
            
        Returns:
            AgentMetrics or None if agent not found
        """
        return self.metrics.agent_metrics.get(agent_name)
