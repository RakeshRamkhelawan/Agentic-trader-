"""
Base Agent Module - Abstract Base Class for All Trading Agents.

Implements ReAct (Reasoning + Acting) pattern with chain-of-thought explanations.
Refactored with dependency injection for LLM and Event Bus.
Memory-safe implementation using deque with maxlen to prevent OOM.
"""

import logging
import sys
import time
from abc import ABC, abstractmethod
from collections import deque
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from backend.events.event_bus import EventBus
    from backend.llm.provider_interface import LLMProvider

from backend.core.security.prompt_guard import PromptGuard
from backend.governance.agent_gatekeeper import AgentRole

# Module-level logger
logger = logging.getLogger(__name__)

# Default maximum size for bounded collections
DEFAULT_MAX_HISTORY = 1000
DEFAULT_MAX_EVENTS = 10000

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


class BaseAgent(ABC):
    """
    Abstract base class for all trading agents.
    
    Features:
    - ReAct (Reasoning + Acting) pattern implementation
    - Memory-safe bounded collections (prevents OOM)
    - Chain-of-thought explanations
    - Dependency injection for LLM and Event Bus
    - Health monitoring and metrics
    """

    def __init__(
        self,
        agent_name: str,
        llm_provider: Optional["LLMProvider"] = None,
        event_bus: Optional["EventBus"] = None,
        agent_role: AgentRole = AgentRole.UNTRUSTED,
        max_reasoning_history: int = DEFAULT_MAX_HISTORY,
        max_event_buffer: int = DEFAULT_MAX_EVENTS,
    ):
        """
        Initialize base agent.
        
        Args:
            agent_name: Unique name for this agent instance
            llm_provider: Optional LLM provider for reasoning
            event_bus: Optional event bus for publishing thoughts
            agent_role: Security role of this agent
            max_reasoning_history: Maximum reasoning entries (prevents OOM)
            max_event_buffer: Maximum buffered events (prevents OOM)
        """
        self.agent_name = agent_name
        self.llm_provider = llm_provider
        self.event_bus = event_bus
        self.agent_role = agent_role

        # State management
        self.state: Dict[str, Any] = {}
        
        # MEMORY-SAFE: Use deque with maxlen to prevent unbounded growth
        # This prevents OOM crashes during long trading sessions
        self._max_reasoning_history = max_reasoning_history
        self.reasoning_history: deque[Dict[str, Any]] = deque(maxlen=max_reasoning_history)
        
        # Event buffer for async processing (also bounded)
        self._max_event_buffer = max_event_buffer
        self._event_buffer: deque[Dict[str, Any]] = deque(maxlen=max_event_buffer)
        
        # Logger
        self.logger = logging.getLogger(f"{__name__}.{agent_name}")
        self.logger.info(f"{agent_name} initialized (max_history={max_reasoning_history})")

        # Health Monitoring
        self.last_heartbeat = time.time()
        self.processed_events = 0
        self.failed_events = 0
        
        # Memory tracking
        self._peak_reasoning_size = 0

    @abstractmethod
    async def analyze(
        self, features: Dict[str, Any], context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze market features and context to generate a decision.
        Must implement ReAct reasoning pattern.
        """
        pass

    async def ask_llm(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Ask LLM provider for reasoning or explanation.
        Returns fallback message if provider not available.
        """
        if not self.llm_provider:
            return "LLM provider not available."

        try:
            # Sanitize user prompt to prevent instruction injection
            safe_prompt = PromptGuard.sanitize_input(prompt)
            return await self.llm_provider.generate_text(safe_prompt, system_prompt)
        except Exception as e:
            self.logger.error(f"LLM error: {e}")
            return f"LLM error: {str(e)}"

    async def publish_thought(
        self, reasoning: str, confidence: float, data: Dict[str, Any]
    ) -> Optional[str]:
        """
        Publish agent thought to event bus.
        Returns message ID if published, None if bus not available.
        """
        if not self.event_bus:
            self.logger.debug("Event bus not available, skipping thought publication")
            return None

        try:
            event_data = {
                "agent_name": self.agent_name,
                "reasoning": reasoning,
                "confidence": str(confidence),
                "data": str(data),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            message_id = await self.event_bus.publish("agent_thoughts", event_data)
            return message_id
        except Exception as e:
            self.logger.error(f"Failed to publish thought: {e}")
            return None

    def heartbeat(self) -> None:
        """Update the agent's heartbeat timestamp."""
        self.last_heartbeat = time.time()

    def record_activity(self, success: bool = True) -> None:
        """Record event processing activity for metrics."""
        self.processed_events += 1
        if not success:
            self.failed_events += 1
        self.heartbeat()

    def health_check(self) -> Dict[str, Any]:
        """
        Return current health status and metrics.
        Status is 'unhealthy' if no heartbeat for > 60 seconds.
        """
        current_time = time.time()
        is_alive = (current_time - self.last_heartbeat) < 60

        error_rate = 0.0
        if self.processed_events > 0:
            error_rate = self.failed_events / self.processed_events

        # Track peak memory usage
        current_size = len(self.reasoning_history)
        if current_size > self._peak_reasoning_size:
            self._peak_reasoning_size = current_size

        return {
            "agent_name": self.agent_name,
            "status": "healthy" if is_alive else "unhealthy",
            "last_heartbeat": self.last_heartbeat,
            "total_actions": self.processed_events,
            "processed_events": self.processed_events,
            "error_count": self.failed_events,
            "failed_events": self.failed_events,
            "error_rate": error_rate,
            "memory": {
                "reasoning_history_size": current_size,
                "reasoning_history_max": self._max_reasoning_history,
                "peak_size": self._peak_reasoning_size,
                "event_buffer_size": len(self._event_buffer),
            },
        }

    def think(self, observation: str) -> str:
        """
        ReAct THINK step: Internal reasoning about observation.
        
        Stores thought in bounded reasoning_history (deque with maxlen).
        """
        thought = f"[THINK] {observation}"
        
        # Add to bounded deque - oldest entry auto-removed at maxlen
        self.reasoning_history.append({
            "timestamp": datetime.now(timezone.utc),
            "type": "think",
            "content": observation,
        })
        
        # Log if approaching capacity
        if len(self.reasoning_history) >= self._max_reasoning_history * 0.9:
            self.logger.warning(
                f"Reasoning history at {len(self.reasoning_history)}/{self._max_reasoning_history} "
                f"capacity - old entries being dropped"
            )
        
        self.logger.debug(thought)
        return thought

    def act(self, action: str, rationale: str) -> Dict[str, Any]:
        """
        ReAct ACT step: Take action based on reasoning.
        
        Stores action in bounded reasoning_history (deque with maxlen).
        """
        action_record = {
            "timestamp": datetime.now(timezone.utc),
            "type": "act",
            "action": action,
            "rationale": rationale,
        }
        
        # Add to bounded deque - oldest entry auto-removed at maxlen
        self.reasoning_history.append(action_record)
        
        self.logger.info(f"[ACT] {action}: {rationale}")
        return action_record

    def get_reasoning_chain(self, limit: Optional[int] = None) -> List[str]:
        """
        Get complete reasoning chain for explainability.
        
        Args:
            limit: Maximum number of entries to return (None = all)
            
        Returns:
            List of formatted reasoning strings
        """
        chain = []
        
        # Convert deque to list for slicing (respects maxlen)
        history_list = list(self.reasoning_history)
        if limit:
            history_list = history_list[-limit:]
        
        for entry in history_list:
            if entry["type"] == "think":
                chain.append(f"[THINK] {entry['content']}")
            elif entry["type"] == "act":
                chain.append(f"[ACT] {entry['action']}: {entry['rationale']}")
        return chain

    def clear_reasoning_history(self) -> int:
        """
        Clear reasoning history (useful for long-running sessions).
        
        Returns:
            Number of entries cleared
        """
        cleared = len(self.reasoning_history)
        self.reasoning_history.clear()
        self.logger.info(f"Cleared {cleared} reasoning history entries")
        return cleared

    def update_state(self, updates: Dict[str, Any] | str, value: Any = None) -> None:
        """
        Update agent internal state.
        Can accept either dict of updates or key-value pair.
        """
        if isinstance(updates, dict):
            self.state.update(updates)
            self.logger.debug(f"State updated: {list(updates.keys())}")
        else:
            self.state[updates] = value
            self.logger.debug(f"State updated: {updates} = {value}")

    def get_state(self) -> Dict[str, Any]:
        """Get current agent state."""
        return self.state.copy()

    def buffer_event(self, event: Dict[str, Any]) -> bool:
        """
        Buffer an event for async processing.
        
        Args:
            event: Event data to buffer
            
        Returns:
            True if buffered, False if buffer is full
        """
        if len(self._event_buffer) >= self._max_event_buffer:
            self.logger.warning(f"Event buffer full ({self._max_event_buffer}), dropping event")
            return False
        
        self._event_buffer.append(event)
        return True

    def get_buffered_events(self, clear: bool = True) -> List[Dict[str, Any]]:
        """
        Get buffered events for processing.
        
        Args:
            clear: If True, clear buffer after retrieval
            
        Returns:
            List of buffered events
        """
        events = list(self._event_buffer)
        if clear:
            self._event_buffer.clear()
        return events

    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get detailed memory usage statistics.
        
        Returns:
            Dictionary with memory statistics
        """
        return {
            "reasoning_history": {
                "current": len(self.reasoning_history),
                "max": self._max_reasoning_history,
                "peak": self._peak_reasoning_size,
                "utilization": len(self.reasoning_history) / self._max_reasoning_history,
            },
            "event_buffer": {
                "current": len(self._event_buffer),
                "max": self._max_event_buffer,
                "utilization": len(self._event_buffer) / self._max_event_buffer,
            },
            "state": {
                "keys": len(self.state),
            },
        }
