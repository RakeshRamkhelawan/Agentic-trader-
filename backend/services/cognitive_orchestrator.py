"""
Cognitive Orchestrator Service.

Responsibility:
- Manage Lifecycle of AI Agents (Sentiment, Macro, etc.).
- Facilitate Inter-Agent Communication (IACP).
- Generate 'Signal' events based on collective intelligence.
"""

import asyncio
import logging
import uuid
import json
import time
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from backend.core.agent_registry import AgentRegistry, ToolRegistry, AgentProfile
from backend.core.guna_quantifier import GunaQuantifier
from backend.services.intent_monitor import IntentMonitor
from backend.schemas.guna import GunaVector
from backend.schemas.agent_messages import AgentMessage
from backend.core.memory_agent import MemoryAgent
from backend.core.regime_detector import RegimeDetector
from backend.core.telemetry.tracing import setup_tracing, get_tracer
from backend.core.telemetry.metrics import PrometheusMetrics # NIEUW
from backend.llm.usage_tracker import UsageTracker
from backend.core.exceptions import QuotaExceededError
from backend.core.exceptions import QuotaExceededError
from backend.core.auth.context import get_current_tenant_optional, tenant_context

# Importeer alle agents die de Orchestrator moet kennen
from backend.services.research_agent import ResearchAgent
from backend.services.macro_agent import MacroAgent
from backend.services.valuation_agent import ValuationAgent
from backend.risk.validators import RiskValidator

# Initialiseer de tracer en metrics voor deze service
tracer = get_tracer("cognitive.orchestrator")
metrics = PrometheusMetrics("cognitive_orchestrator")

# Re-export for convenience
__all__ = [
    'CognitiveOrchestrator',
    'AgentMessage',
    'RegimeDetector',
    'MarketRegime',
] # NIEUW

class CognitiveOrchestrator:
    def __init__(
        self, 
        agent_profiles_path: str = "backend/config/agent_profiles.yaml",
        agent_registry: Optional[AgentRegistry] = None, # Dependency Injection
        guna_quantifier: Optional[GunaQuantifier] = None,
        intent_monitor: Optional[IntentMonitor] = None,
        memory_agent_factory: Callable[[], MemoryAgent] = MemoryAgent, # Factory om MemoryAgent aan te maken
        signal_bridge = None,  # Optional SignalBridge for frontend communication
        usage_tracker: Optional[UsageTracker] = None, # Optional UsageTracker
        audit_logger = None # Optional AuditLogger
    ):
        self.agent_registry = agent_registry or AgentRegistry(config_path=agent_profiles_path)
        self.guna_quantifier = guna_quantifier or GunaQuantifier()
        self.intent_monitor = intent_monitor or IntentMonitor(ideal_balance=GunaVector(sattva=0.4, rajas=0.3, tamas=0.3))
        self.memory_agent_factory = memory_agent_factory
        self.signal_bridge = signal_bridge  # Bridge to WebSocket frontend
        self.usage_tracker = usage_tracker
        self.audit_logger = audit_logger
        
        self.agents: Dict[str, Any] = {}
        self.message_handlers: Dict[str, List[Callable[[AgentMessage], Any]]] = {}
        self.current_guna_balance = GunaVector(sattva=1/3, rajas=1/3, tamas=1/3)
        self.global_guna_history: List[GunaVector] = []
        
        self.logger = logging.getLogger("Orchestrator")
        self._initialize_agents()

    def _initialize_agents(self):
        with tracer.start_as_current_span("initialize_agents"):
            for agent_id, profile in self.agent_registry.profiles.items():
                self.logger.info(f"Initializing agent: {profile.name} ({profile.id}) [{profile.element}]")
                
                metrics.requests_in_progress.inc() # NIEUW: Track initialisatie
                
                memory = self.memory_agent_factory()
                
                if agent_id == "orchestrator_v1":
                    self.agents[agent_id] = self 
                elif agent_id == "research_v1":
                    self.agents[agent_id] = ResearchAgent(memory_agent=memory, message_bus=self.handle_message)
                elif agent_id == "macro_v1":
                    self.agents[agent_id] = MacroAgent(memory_agent=memory, message_bus=self.handle_message)
                elif agent_id == "valuation_v1":
                    self.agents[agent_id] = ValuationAgent(memory_agent=memory, message_bus=self.handle_message)
                elif agent_id == "risk_guardian_v1":
                    from backend.services.risk_guardian_agent import RiskGuardianAgent 
                    # Use Factory if possible, or direct init
                    self.agents[agent_id] = RiskGuardianAgent(message_bus=self.handle_message)
                else:
                    self.logger.warning(f"Unknown agent ID in registry: {agent_id}. Skipping instantiation.")
                    metrics.errors_total.inc()
                    continue
                metrics.requests_in_progress.dec()
            
            self.logger.info("All agents initialized.")

    async def _check_quota(self, tenant_id: str):
        """Check if tenant has exceeded daily quota."""
        if not self.usage_tracker:
            return

        try:
            usage_today = await self.usage_tracker.get_daily_usage(tenant_id)
            # Fetch quota (hardcoded for now, plan to fetch from DB/config)
            quota = 10.0 # Default $10/day
            
            if usage_today >= quota:
                self.logger.warning(f"Tenant {tenant_id} exceeded quota: {usage_today:.2f}/{quota:.2f} USD")
                raise QuotaExceededError(
                    f"Daily LLM budget exceeded. Used ${usage_today:.2f} of ${quota:.2f}",
                    details={"usage": usage_today, "quota": quota}
                )
        except QuotaExceededError:
            raise
        except Exception as e:
            self.logger.error(f"Error checking quota: {e}")
            # Fail open if check fails (don't block user on infra error)

    async def handle_message(self, message: AgentMessage):
        with tracer.start_as_current_span("handle_message", attributes={"message.type": message.type, "message.source": message.source}):
            metrics.requests_in_progress.inc()
            start_time = time.time()
            
            self.logger.info(f"Orchestrator received: {message.type} from {message.source} to {message.target}")
            
            # Determine effective tenant: Message ID > Current Context
            effective_tenant = message.tenant_id or get_current_tenant_optional()
            
            # Create a context manager wrapper
            # If no tenant, we use a null context or just proceed (but tenant_context needs a value)
            # We'll use a helper or simple conditional
            
            try:
                if effective_tenant:
                    token = None
                    # We can't use 'with tenant_context' easily if we want to conditionally apply it 
                    # without indenting the whole block.
                    # But for cleaner code, let's use the context manager and indent.
                    with tenant_context(effective_tenant):
                        await self._process_message_logic(message, effective_tenant)
                else:
                    await self._process_message_logic(message, None)
                    
            except Exception as e:
                metrics.errors_total.inc()
                self.logger.error(f"Error handling message: {e}")
                raise
            finally:
                metrics.requests_total.inc()
                metrics.requests_in_progress.dec()
                metrics.request_latency_seconds.observe(time.time() - start_time)

    async def _process_message_logic(self, message: AgentMessage, tenant_id: Optional[str]):
        """Internal logic for processing message, assumed to be in correct context."""
        if tenant_id:
             await self._check_quota(tenant_id)

        if self.audit_logger and tenant_id:
             await self.audit_logger.log_event(
                tenant_id=tenant_id,
                action="PROCESS_MESSAGE",
                resource_type="agent_message",
                resource_id=message.id,
                details={"type": message.type, "source": message.source, "target": message.target}
             )

        # HITL INTERCEPTION LOGIC
        if self._is_execution_signal(message.type):
            self.logger.info(f"🛑 Intercepting Execution Signal: {message.type}")
            # Route to Risk Guardian for validation
            if message.source != "risk_guardian_v1":
                self.logger.info("Routing to Risk Guardian for Validation...")
                validation_request = AgentMessage(
                    source=message.source,
                    target="risk_guardian_v1",
                    type="VALIDATE_ORDER",
                    payload={
                        "order": message.payload,
                        "preferences": {} # Orchestrator needs to fetch this or Risk agent does
                    },
                    tenant_id=tenant_id # Propagate tenant
                )
                if "risk_guardian_v1" in self.agents:
                    await self.agents["risk_guardian_v1"].handle_message(validation_request)
                return

        event_guna = self._quantify_message_guna(message)
        message.payload["guna_vibration"] = event_guna.to_dict()

        self.global_guna_history.append(event_guna)
        if len(self.global_guna_history) > 10:
            self.global_guna_history.pop(0)

        aggregated_sattva = sum(g.sattva for g in self.global_guna_history) / len(self.global_guna_history)
        aggregated_rajas = sum(g.rajas for g in self.global_guna_history) / len(self.global_guna_history)
        aggregated_tamas = sum(g.tamas for g in self.global_guna_history) / len(self.global_guna_history)
        self.current_guna_balance = GunaVector(sattva=aggregated_sattva, rajas=aggregated_rajas, tamas=aggregated_tamas)
        
        self.intent_monitor.monitor_balance(self.current_guna_balance)
        
        metrics.global_guna_sattva.set(self.current_guna_balance.sattva)
        metrics.global_guna_rajas.set(self.current_guna_balance.rajas)
        metrics.global_guna_tamas.set(self.current_guna_balance.tamas)
        metrics.guna_deviation_score.set(self.intent_monitor.measure_deviation(self.current_guna_balance))

        target_profiles_to_notify: List[AgentProfile] = []

        if message.target == "all" or message.target == self.agent_registry.get_profile("orchestrator_v1").id:
            target_profiles_to_notify = [p for p in self.agent_registry.profiles.values() if message.type in p.subscriptions]
        else:
            profile = self.agent_registry.get_profile(message.target)
            if profile and message.type in profile.subscriptions:
                target_profiles_to_notify.append(profile)

        for profile in target_profiles_to_notify:
            self.logger.debug(f"Routing {message.type} to {profile.name} (ID: {profile.id}) based on subscription.")
            if hasattr(self.agents.get(profile.id), 'handle_message'):
                await self.agents[profile.id].handle_message(message)
            else:
                self.logger.warning(f"Agent {profile.id} has no handle_message method for {message.type}")
        
        # Emit signal to frontend via SignalBridge
        if self.signal_bridge and self._is_actionable_signal(message.type):
            await self.signal_bridge.emit_from_agent_message(
                agent_id=message.source,
                agent_name=self._get_agent_name(message.source),
                message_type=message.type,
                payload=message.payload
            )
        
    def _quantify_message_guna(self, message: AgentMessage) -> GunaVector:
        with tracer.start_as_current_span("quantify_message_guna"):
            """Helper to quantify Gunas from message payload."""
            metrics.requests_in_progress.inc()
            start_time = time.time()
            try:
                if message.payload:
                    if "text" in message.payload:
                        return self.guna_quantifier.quantify_text(message.payload["text"])
                    elif "summary" in message.payload:
                        return self.guna_quantifier.quantify_text(message.payload["summary"])
                    elif "price" in message.payload or "volatility" in message.payload:
                        return self.guna_quantifier.quantify_numerical_data(message.payload)
                return GunaVector(sattva=1/3, rajas=1/3, tamas=1/3) # Neutraal
            finally:
                metrics.requests_in_progress.dec()
                metrics.request_latency_seconds.observe(time.time() - start_time)

    def _is_actionable_signal(self, message_type: str) -> bool:
        """Check if message type should be sent to frontend as a signal."""
        actionable_types = {
            "BUY_SIGNAL", "SELL_SIGNAL", "HOLD_SIGNAL",
            "LONG_SIGNAL", "SHORT_SIGNAL", "NEUTRAL",
            "ALERT", "WARNING", "RISK_ALERT",
            "SENTIMENT_UPDATE", "MACRO_INSIGHT", "VALUATION_UPDATE",
            "RESEARCH_COMPLETE", "ANALYSIS_RESULT",
            "ORDER_VALIDATION_RESULT" # Added for Risk Feedback
        }
        return message_type in actionable_types

    def _is_execution_signal(self, message_type: str) -> bool:
        """Check if message intends to execute an order."""
        return message_type in {"BUY_SIGNAL", "SELL_SIGNAL", "EXECUTE_ORDER"}
    
    def _get_agent_name(self, agent_id: str) -> str:
        """Get human-readable agent name from ID."""
        profile = self.agent_registry.get_profile(agent_id)
        if profile:
            return profile.name
        return agent_id.replace("_", " ").title()

    async def process_generic_message(self, message: AgentMessage):
        self.logger.info(f"Generic handler processed message: {message.id} from {message.source}")


async def main():
    logging.basicConfig(level=logging.INFO)
    setup_tracing("cognitive-orchestrator-service")
    logging.info("Starting Cognitive Orchestrator Service...")
    
    orchestrator = CognitiveOrchestrator()
    
    if "research_v1" in orchestrator.agents:
        research_agent = orchestrator.agents["research_v1"]
        await orchestrator.handle_message(AgentMessage(source="orchestrator", target="research_v1", type="TIMER_TICK_1MIN", payload={}))
    
    while True:
        await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
