from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from datetime import datetime, timezone
import logging
import sys

if TYPE_CHECKING:
    from backend.llm.provider_interface import LLMProvider
    from backend.events.event_bus import EventBus

from backend.governance.agent_gatekeeper import AgentRole
from backend.core.security.prompt_guard import PromptGuard

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

class BaseAgent(ABC):
    """
    Abstract base class for all trading agents.
    Implements ReAct (Reasoning + Acting) pattern with chain-of-thought explanations.
    Refactored with dependency injection for LLM and Event Bus.
    """
    
    def __init__(
        self,
        agent_name: str,
        llm_provider: Optional["LLMProvider"] = None,
        event_bus: Optional["EventBus"] = None,
        agent_role: AgentRole = AgentRole.UNTRUSTED
    ):
        self.agent_name = agent_name
        self.llm_provider = llm_provider
        self.event_bus = event_bus
        self.agent_role = agent_role
        
        self.state: Dict[str, Any] = {}
        self.reasoning_history: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(f"{__name__}.{agent_name}")
        self.logger.info(f"{agent_name} initialized")
        
        # Health Monitoring
        import time
        self.last_heartbeat = time.time()
        self.processed_events = 0
        self.failed_events = 0

    @abstractmethod
    async def analyze(self, features: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
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
        self,
        reasoning: str,
        confidence: float,
        data: Dict[str, Any]
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
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            message_id = await self.event_bus.publish("agent_thoughts", event_data)
            return message_id
        except Exception as e:
            self.logger.error(f"Failed to publish thought: {e}")
            return None
        
    def heartbeat(self):
        """Update the agent's heartbeat timestamp."""
        import time
        self.last_heartbeat = time.time()
        
    def record_activity(self, success: bool = True):
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
        import time
        current_time = time.time()
        is_alive = (current_time - self.last_heartbeat) < 60
        
        error_rate = 0.0
        if self.processed_events > 0:
            error_rate = self.failed_events / self.processed_events
            
        return {
            "agent_name": self.agent_name,
            "status": "healthy" if is_alive else "unhealthy",
            "last_heartbeat": self.last_heartbeat,
            "total_actions": self.processed_events,
            "processed_events": self.processed_events,
            "error_count": self.failed_events,
            "failed_events": self.failed_events,
            "error_rate": error_rate
        }
    
    def think(self, observation: str) -> str:
        """
        ReAct THINK step: Internal reasoning about observation.
        """
        thought = f"[THINK] {observation}"
        self.reasoning_history.append({
            'timestamp': datetime.now(timezone.utc),
            'type': 'think',
            'content': observation
        })
        self.logger.debug(thought)
        return thought
    
    def act(self, action: str, rationale: str) -> Dict[str, Any]:
        """
        ReAct ACT step: Take action based on reasoning.
        """
        action_record = {
            'timestamp': datetime.now(timezone.utc),
            'type': 'act',
            'action': action,
            'rationale': rationale
        }
        self.reasoning_history.append(action_record)
        self.logger.info(f"[ACT] {action}: {rationale}")
        return action_record
    
    def get_reasoning_chain(self) -> List[str]:
        """
        Get complete reasoning chain for explainability.
        Returns list of formatted reasoning strings.
        """
        chain = []
        for entry in self.reasoning_history:
            if entry['type'] == 'think':
                chain.append(f"[THINK] {entry['content']}")
            elif entry['type'] == 'act':
                chain.append(f"[ACT] {entry['action']}: {entry['rationale']}")
        return chain
    
    def update_state(self, updates: Dict[str, Any] | str, value: Any = None):
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
        """
        Get current agent state.
        """
        return self.state.copy()