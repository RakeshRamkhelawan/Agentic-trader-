"""
Elemental Base Agent - Samkhya/Vedic Layer with Consciousness (v11).

This module defines the abstract base class for all Elemental Agents (Ether, Air, Fire, Water, Earth).
It adds Samkhya philosophy properties AND conscious capabilities:
- Guna Balance (Sattva, Rajas, Tamas)
- Prana Energy (Lifecycle and Depletion)
- Tattva Layer Registration (SystemIdentity)
- Chitta Memory (Persistent learning per agent)
- LLM Integration (DeepSeek/Ollama)
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from backend.agents.base_agent import BaseAgent
from backend.core.conscious.chitta_memory import ChittaMemory, TradeExperience
from backend.core.llm.llm_provider import LLMProvider, create_llm_provider
from backend.governance.agent_gatekeeper import AgentRole

logger = logging.getLogger(__name__)


class ElementalBase(BaseAgent, ABC):
    """
    Abstract base class for Elemental Agents.

    Adds Vedic/Samkhya properties:
    - element: The classical element (Ether, Air, Fire, Water, Earth)
    - guna_balance: Composition of Sattva (light), Rajas (action), Tamas (stability)
    - prana: Energy level (0-100) that determines operational capacity
    - tattva_layer: The associated layer in the 36-Tattva system
    """

    def __init__(
        self,
        agent_name: str,
        element: str,
        tattva_layer: int,
        guna_balance: dict[str, float],
        llm_provider: Any | None = None,
        event_bus: Any | None = None,
        system_identity: Any | None = None,
        agent_role: AgentRole = AgentRole.STRATEGIST,
        max_prana: float = 100.0,
        prana_decay_rate: float = 0.5,  # Prana loss per action
    ):
        """
        Initialize Elemental Agent.

        Args:
            agent_name: Unique name
            element: 'ether', 'air', 'fire', 'water', or 'earth'
            tattva_layer: Layer number (32-36)
            guna_balance: Dict with 'sattva', 'rajas', 'tamas' (must sum to 1.0)
            llm_provider: LLM service
            event_bus: Event system
            system_identity: Central consciousness coordination
            agent_role: RBAC role
            max_prana: Max energy level
            prana_decay_rate: Energy cost per action
        """
        super().__init__(
            agent_name=agent_name,
            llm_provider=llm_provider,
            event_bus=event_bus,
            agent_role=agent_role,
        )

        self.element = element.lower()
        self.tattva_layer = tattva_layer
        self.max_prana = max_prana
        self.prana = max_prana
        self.prana_decay_rate = prana_decay_rate
        self.system_identity = system_identity

        # Validate Guna Balance
        self._validate_gunas(guna_balance)
        self.guna_balance = guna_balance

        # Initialize Chitta Memory (v11 - Consciousness)
        memory_path = f"backend/data/conscious_memory/{self.agent_name.lower()}_chitta"
        self.chitta = ChittaMemory(storage_path=memory_path)

        # Initialize LLM if not provided (v11 - Intelligence)
        if llm_provider is None:
            self.llm = create_llm_provider(backend="ollama", model="llama3.2")
        else:
            self.llm = llm_provider

        # Register with SystemIdentity if available
        if self.system_identity and hasattr(self.system_identity, "register_elemental_agent"):
            # Logic to register would go here - keeping it non-blocking for init
            self._register_with_identity()

        logger.info(
            f"Initialized {self.agent_name} ({self.element}) - Prana: {self.prana} | Chitta: {len(self.chitta.trades)} trades"
        )

    def _validate_gunas(self, balance: dict[str, float]):
        """Ensure Gunas sum to 1.0 within floating point tolerance."""
        total = sum(balance.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Guna balance must sum to 1.0, got {total}")
        required = {"sattva", "rajas", "tamas"}
        if not all(k in balance for k in required):
            raise ValueError(f"Missing Guna keys. Required: {required}")

    def _register_with_identity(self):
        """Register agent with SystemIdentity."""
        try:
            self.system_identity.register_elemental_agent(
                tattva_id=self.tattva_layer,
                agent_id=self.agent_name,
                element=self.element,
            )
            logger.info(
                f"Registered {self.agent_name} with SystemIdentity layer {self.tattva_layer}"
            )
        except Exception as e:
            logger.warning(f"Failed to register with SystemIdentity: {e}")

    async def consume_prana(self, amount: float | None = None) -> bool:
        """
        Consume prana for an action.

        Args:
            amount: Amount to consume (defaults to self.prana_decay_rate)

        Returns:
            True if sufficient prana existed, False if depleted (< 10)
        """
        cost = amount if amount is not None else self.prana_decay_rate

        # Check depletion threshold
        if self.prana < 10.0:
            logger.warning(f"{self.agent_name} is Prana Depleted ({self.prana:.1f})")
            return False

        self.prana = max(0.0, self.prana - cost)
        return True

    async def regenerate_prana(self, rest_period_seconds: int) -> float:
        """
        Regenerate prana based on rest period.

        Args:
            rest_period_seconds: Time spent resting

        Returns:
            New prana level
        """
        if rest_period_seconds <= 0:
            return self.prana

        # Recovery rate: ~20 prana per hour (adjustable)
        if rest_period_seconds > 3600:
            recovery_amount = (rest_period_seconds / 3600.0) * 20.0
        else:
            recovery_amount = (
                rest_period_seconds / 3600.0
            ) * 10.0  # Slower recovery for short naps

        # Ether element regenerates faster (source energy)
        if self.element == "ether":
            recovery_amount *= 1.5

        self.prana = min(self.max_prana, self.prana + recovery_amount)
        logger.info(
            f"{self.agent_name} regenerated {recovery_amount:.1f} prana. Level: {self.prana:.1f}"
        )
        return self.prana

    def get_dominant_guna(self) -> str:
        """Return the dominant Guna (sattva/rajas/tamas)."""
        return max(self.guna_balance, key=self.guna_balance.get)

    def elemental_health_check(self) -> dict[str, Any]:
        """Extended health check with Elemental metrics."""
        base_health = self.health_check()
        base_health.update(
            {
                "element": self.element,
                "prana": self.prana,
                "is_depleted": self.prana < 10.0,
                "guna_balance": self.guna_balance,
                "dominant_guna": self.get_dominant_guna(),
                "tattva_layer": self.tattva_layer,
            }
        )
        return base_health

    # ========== CONSCIOUS CAPABILITIES (v11) ==========

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
            logger.info(f"{self.agent_name} stored trade {trade.trade_id} in Chitta")

    def should_pause_trading(self, drawdown_limit: float = 0.08) -> tuple[bool, str]:
        """
        Check if agent should pause trading based on Chitta/Ahamkara state.
        Returns: (should_pause, reason)
        """
        if not self.chitta:
            return False, ""
        return self.chitta.should_pause_trading(drawdown_limit=drawdown_limit)

    def generate_llm_analysis(self, prompt: str, temperature: float = 0.3) -> dict[str, Any]:
        """
        Generate analysis using LLM (DeepSeek/Ollama).
        """
        if not self.llm:
            return {
                "text": "No LLM",
                "confidence": 0.0,
                "reasoning": "LLM not available",
            }

        system_prompt = f"""JIJ = {self.agent_name}, een {self.element.upper()} element trading agent.
JE ROL: Analyseer markt vanuit {self.element} perspectief.
JE GEHEUGEN: {len(self.chitta.trades)} trades opgeslagen.

Wees analytisch, geef confidence score (0-1), en leg uit WAAROM."""

        return self.llm.generate(prompt, system_prompt=system_prompt, temperature=temperature)

    def get_conscious_stats(self) -> dict[str, Any]:
        """Get conscious agent statistics including Chitta and LLM."""
        return {
            "agent_name": self.agent_name,
            "element": self.element,
            "prana": self.prana,
            "guna_balance": self.guna_balance,
            "chitta_stats": self.chitta.get_summary() if self.chitta else None,
            "llm_stats": self.llm.get_stats() if self.llm else None,
        }

    # ========== ABSTRACT METHODS ==========

    @abstractmethod
    async def process_signal(self, signal: dict[str, Any]) -> dict[str, Any]:
        """
        Process an incoming signal according to elemental nature.
        Must be implemented by subclasses.

        Args:
           signal: Input data (market data, alert, request)

        Returns:
           Processing result
        """
        pass

    # Implement BaseAgent abstract method
    async def analyze(self, features: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """
        Bridge method to support BaseAgent interface.
        Redirects to process_signal.
        """
        return await self.process_signal({**features, **context})
