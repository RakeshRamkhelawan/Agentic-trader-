"""
Base Agent Module - Abstract Base Class for All Trading Agents (v11 Conscious).

Implements ReAct (Reasoning + Acting) pattern with chain-of-thought explanations.
Refactored with dependency injection for LLM and Event Bus.
Memory-safe implementation using deque with maxlen to prevent OOM.

v11: Added Chitta Memory - ALL agents now have persistent learning.
"""

import json
import logging
import sys
import time
import uuid
from abc import ABC, abstractmethod
from collections import deque
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from backend.events.event_bus import EventBus
    from backend.llm.provider_interface import LLMProvider

# v11: Conscious imports - ALL agents get Chitta
from backend.core.conscious.chitta_memory import ChittaMemory, TradeExperience
from backend.core.llm.llm_provider import create_llm_provider
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
        clickhouse_client: Optional[Any] = None,
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
        self.clickhouse_client = clickhouse_client

        # Session tracking
        self.session_id = uuid.uuid4()
        self.state: dict[str, Any] = {}

        # MEMORY-SAFE: Use deque with maxlen to prevent unbounded growth
        # This prevents OOM crashes during long trading sessions
        self._max_reasoning_history = max_reasoning_history
        self.reasoning_history: deque[dict[str, Any]] = deque(maxlen=max_reasoning_history)

        # Event buffer for async processing (also bounded)
        self._max_event_buffer = max_event_buffer
        self._event_buffer: deque[dict[str, Any]] = deque(maxlen=max_event_buffer)

        # Logger
        self.logger = logging.getLogger(f"{__name__}.{agent_name}")
        self.logger.info(f"{agent_name} initialized (max_history={max_reasoning_history})")

        # Health Monitoring
        self.last_heartbeat = time.time()
        self.processed_events = 0
        self.failed_events = 0

        # Memory tracking
        self._peak_reasoning_size = 0

        # v11: CHITTA MEMORY - ALL agents get persistent memory
        self._init_chitta_memory()

    def _init_chitta_memory(self):
        """Initialize Chitta Memory for this agent."""
        try:
            memory_path = f"backend/data/conscious_memory/{self.agent_name.lower()}_chitta"
            self.chitta = ChittaMemory(storage_path=memory_path)

            # Initialize LLM if not provided
            if not self.llm_provider:
                self.llm_provider = create_llm_provider(backend="ollama", model="llama3.2")

            llm_backend = "mock"
            if hasattr(self.llm_provider, "config"):
                llm_backend = getattr(self.llm_provider.config, "backend", "mock")
            self.logger.info(
                f"{self.agent_name} consciousness activated | "
                f"Chitta: {len(self.chitta.trades)} trades | "
                f"LLM: {llm_backend}"
            )
        except Exception as e:
            self.logger.warning(f"Chitta initialization failed for {self.agent_name}: {e}")
            self.chitta = None

    @abstractmethod
    async def analyze(self, features: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze market features and context to generate a decision.
        Must implement ReAct reasoning pattern.
        """
        pass

    async def ask_llm(self, prompt: str, system_prompt: str | None = None) -> str:
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
        self, reasoning: str, confidence: float, data: dict[str, Any]
    ) -> str | None:
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
                "timestamp": datetime.now(UTC).isoformat(),
            }
            message_id = await self.event_bus.publish("agent_thoughts", event_data)
            return message_id
        except Exception as e:
            self.logger.error(f"Failed to publish thought: {e}")
            return None

    async def persist_decision(
        self,
        action: str,
        symbol: str,
        confidence: float,
        perspective: str,
        rationale: str,
        data: Dict[str, Any] | None = None,
        metadata: Dict[str, Any] | None = None,
    ) -> bool:
        """
        Persist agent decision/analysis to ClickHouse database.
        """
        if not self.clickhouse_client:
            self.logger.debug(
                f"ClickHouse client not available for {self.agent_name}, skipping persistence"
            )
            return False

        try:
            record = {
                "agent_id": self.agent_name,
                "session_id": str(self.session_id),
                "timestamp": datetime.now(UTC),
                "symbol": symbol or "N/A",
                "action": action,
                "confidence": float(confidence),
                "perspective": perspective,
                "rationale": rationale,
                "data": json.dumps(data) if data else "{}",
                "metadata": json.dumps(metadata) if metadata else "{}",
            }

            await self.clickhouse_client.insert("agent_decisions", [record])
            self.logger.debug(f"Decision persisted for {self.agent_name}: {action} on {symbol}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to persist decision for {self.agent_name}: {e}")
            return False

    def heartbeat(self) -> None:
        """Update the agent's heartbeat timestamp."""
        self.last_heartbeat = time.time()

    def record_activity(self, success: bool = True) -> None:
        """Record event processing activity for metrics."""
        self.processed_events += 1
        if not success:
            self.failed_events += 1
        self.heartbeat()

    def health_check(self) -> dict[str, Any]:
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
        self.reasoning_history.append(
            {
                "timestamp": datetime.now(UTC),
                "type": "think",
                "content": observation,
            }
        )

        # Log if approaching capacity
        if len(self.reasoning_history) >= self._max_reasoning_history * 0.9:
            self.logger.warning(
                f"Reasoning history at {len(self.reasoning_history)}/{self._max_reasoning_history} "
                f"capacity - old entries being dropped"
            )

        self.logger.debug(thought)
        return thought

    def act(self, action: str, rationale: str) -> dict[str, Any]:
        """
        ReAct ACT step: Take action based on reasoning.

        Stores action in bounded reasoning_history (deque with maxlen).
        """
        action_record = {
            "timestamp": datetime.now(UTC),
            "type": "act",
            "action": action,
            "rationale": rationale,
        }

        # Add to bounded deque - oldest entry auto-removed at maxlen
        self.reasoning_history.append(action_record)

        self.logger.info(f"[ACT] {action}: {rationale}")

        # Async persistence (fire and forget pattern with safety)
        import asyncio

        asyncio.create_task(
            self.persist_decision(
                action="act",
                symbol=self.state.get("current_symbol", "N/A"),
                confidence=self.state.get("confidence", 0.5),
                perspective=action,
                rationale=rationale,
                data={"action_details": action},
            )
        )

        return action_record

    def get_reasoning_chain(self, limit: int | None = None) -> list[str]:
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

    def update_state(self, updates: dict[str, Any] | str, value: Any = None) -> None:
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

    def get_state(self) -> dict[str, Any]:
        """Get current agent state."""
        return self.state.copy()

    def buffer_event(self, event: dict[str, Any]) -> bool:
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

    def get_buffered_events(self, clear: bool = True) -> list[dict[str, Any]]:
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

    # ========== v11: CHITTA MEMORY METHODS (ALL agents) ==========

    def retrieve_similar_experiences(self, market_state: Any, top_k: int = 5) -> list:
        """
        Retrieve similar historical setups from Chitta Memory.
        RAG: Retrieval-Augmented Generation for trading.
        """
        if not self.chitta or len(self.chitta.trades) < 5:
            return []
        return self.chitta.retrieve_similar_setups(market_state, top_k=top_k)

    def reflect_recent_performance(self, n_trades: int = 10) -> dict[str, Any]:
        """
        Reflect on recent trading performance.
        Returns insights for course correction.
        """
        if not self.chitta:
            return {"insight": "No memory", "action": "continue"}
        return self.chitta.reflect_recent(n_trades=n_trades)

    def store_trade_experience(self, trade: TradeExperience):
        """Store completed trade in Chitta Memory for learning."""
        if self.chitta:
            self.chitta.store_trade(trade)
            self.logger.info(f"{self.agent_name} stored trade {trade.trade_id} in Chitta")

    def should_pause_trading(self, drawdown_limit: float = 0.08) -> tuple[bool, str]:
        """
        Check if agent should pause trading based on Chitta state.
        Returns: (should_pause, reason)
        """
        if not self.chitta:
            return False, ""
        return self.chitta.should_pause_trading(drawdown_limit=drawdown_limit)

    def generate_llm_analysis(self, market_state: dict, temperature: float = 0.3) -> dict[str, Any]:
        """
        Generate analysis using LLM with Master Prompt and Chitta context.

        Uses 5-step CoT:
        1. RETRIEVE: Similar experiences from Chitta
        2. ANALYZE: Technical indicators
        3. REASON: Vedic interpretation
        4. DECIDE: Action with confidence
        5. REFLECT: Self-improvement
        """
        if not self.llm_provider:
            return {"action": "HOLD", "confidence": 0.3, "reasoning": "LLM not available"}

        try:
            # Import master prompts
            from backend.agents.prompts.master_prompts import (
                AGENT_SPECIFIC_PROMPTS,
                format_prompt_with_data,
                get_master_prompt,
            )
            from backend.core.llm.llm_provider import LLMProvider

            # Get base master prompt
            guna_balance = getattr(self, "guna_balance", (0.5, 0.3, 0.2))
            base_prompt = get_master_prompt(
                agent_name=self.agent_name,
                agent_role=AGENT_SPECIFIC_PROMPTS.get(self.agent_name, {}).get(
                    "role", "Trading Agent"
                ),
                guna_balance=guna_balance,
            )

            # Get Chitta statistics
            chitta_stats = {}
            if self.chitta:
                recent_trades = (
                    list(self.chitta.trades)[-20:]
                    if len(self.chitta.trades) >= 20
                    else list(self.chitta.trades)
                )
                if recent_trades:
                    wins = sum(1 for t in recent_trades if t.pnl > 0)
                    chitta_stats["recent_winrate"] = wins / len(recent_trades)
                    chitta_stats["recent_pnl"] = sum(t.pnl for t in recent_trades) / len(
                        recent_trades
                    )
                    chitta_stats["harmony"] = self.chitta.get_summary().get("harmony_score", 0)
                    chitta_stats["overall_winrate"] = self.chitta.get_summary().get("winrate", 0.5)

            # Format prompt with runtime data
            formatted_prompt = format_prompt_with_data(
                base_prompt=base_prompt,
                agent=self,
                market_state=market_state,
                chitta_stats=chitta_stats,
            )

            # Call LLM
            if isinstance(self.llm_provider, LLMProvider):
                # Extract system prompt (first part before INPUT)
                system_prompt = formatted_prompt.split("INPUT:")[0].strip()
                user_prompt = f"Market state: {market_state}\nChitta stats: {chitta_stats}"

                result = self.llm_provider.generate(
                    user_prompt, system_prompt=system_prompt, temperature=temperature
                )

                # Parse JSON output
                try:
                    import json

                    if isinstance(result, dict) and "text" in result:
                        # Try to parse JSON from text
                        text = result["text"]
                        # Find JSON block
                        start = text.find("{")
                        end = text.rfind("}")
                        if start >= 0 and end > start:
                            parsed = json.loads(text[start : end + 1])
                            return {
                                "action": parsed.get("step4_decision", {}).get("action", "HOLD"),
                                "confidence": parsed.get("step4_decision", {}).get(
                                    "confidence", 0.5
                                ),
                                "reasoning": parsed.get("step3_reason", {}),
                                "reflection": parsed.get("step5_reflect", {}),
                                "raw_response": text,
                            }
                except Exception as e:
                    self.logger.warning(f"Failed to parse LLM JSON: {e}")

                return result

            # Fallback
            return {"action": "HOLD", "confidence": 0.3, "reasoning": "Legacy LLM"}

        except Exception as e:
            self.logger.error(f"LLM analysis failed: {e}")
            return {"action": "HOLD", "confidence": 0.3, "reasoning": f"Error: {e}"}

    def get_conscious_stats(self) -> dict[str, Any]:
        """Get conscious agent statistics including Chitta and LLM."""
        return {
            "agent_name": self.agent_name,
            "chitta_stats": self.chitta.get_summary() if self.chitta else None,
            "trades_in_memory": len(self.chitta.trades) if self.chitta else 0,
            "has_llm": self.llm_provider is not None,
        }

    # ========== END v11 CHITTA METHODS ==========

    def get_memory_stats(self) -> dict[str, Any]:
        """
        Get detailed memory usage statistics.

        Returns:
            Dictionary with memory statistics
        """
        stats = {
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

        # v11: Add Chitta stats
        if self.chitta:
            stats["chitta_memory"] = self.chitta.get_summary()

        return stats
