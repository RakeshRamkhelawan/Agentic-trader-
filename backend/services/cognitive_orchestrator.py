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

# Importeer alle agents die de Orchestrator moet kennen
from backend.services.research_agent import ResearchAgent
from backend.services.macro_agent import MacroAgent
from backend.services.valuation_agent import ValuationAgent
from backend.risk.validators import RiskValidator

# Initialiseer de tracer en metrics voor deze service
tracer = get_tracer("cognitive.orchestrator")
metrics = PrometheusMetrics("cognitive_orchestrator") # NIEUW

class CognitiveOrchestrator:
    def __init__(
        self, 
        agent_profiles_path: str = "backend/config/agent_profiles.yaml",
        agent_registry: Optional[AgentRegistry] = None, # Dependency Injection
        guna_quantifier: Optional[GunaQuantifier] = None,
        intent_monitor: Optional[IntentMonitor] = None,
        memory_agent_factory: Callable[[], MemoryAgent] = MemoryAgent # Factory om MemoryAgent aan te maken
    ):
        self.agent_registry = agent_registry or AgentRegistry(config_path=agent_profiles_path)
        self.guna_quantifier = guna_quantifier or GunaQuantifier()
        self.intent_monitor = intent_monitor or IntentMonitor(ideal_balance=GunaVector(sattva=0.4, rajas=0.3, tamas=0.3))
        self.memory_agent_factory = memory_agent_factory
        
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
                    from backend.core.config.settings import settings as app_settings
                    self.agents[agent_id] = RiskValidator(
                        max_order_size=app_settings.MAX_ORDER_SIZE_EUR,
                        max_daily_loss=app_settings.MAX_DAILY_LOSS_EUR
                    )
                else:
                    self.logger.warning(f"Unknown agent ID in registry: {agent_id}. Skipping instantiation.")
                    metrics.errors_total.inc() # NIEUW: Tel fouten
                    continue
                metrics.requests_in_progress.dec() # NIEUW: Initialisatie klaar
            
            self.logger.info("All agents initialized.")

    async def handle_message(self, message: AgentMessage):
        with tracer.start_as_current_span("handle_message", attributes={"message.type": message.type, "message.source": message.source}):
            metrics.requests_in_progress.inc() # NIEUW: Berichten in verwerking
            start_time = time.time() # NIEUW: Latency meting
            
            self.logger.info(f"Orchestrator received: {message.type} from {message.source} to {message.target}")
            
            try:
                event_guna = self._quantify_message_guna(message)
                message.payload["guna_vibration"] = event_guna.to_dict()

                self.global_guna_history.append(event_guna)
                if len(self.global_guna_history) > 10:
                    self.global_guna_history.pop(0)

                aggregated_sattva = sum(g.sattva for g in self.global_guna_history) / len(self.global_guna_history)
                aggregated_rajas = sum(g.rajas for g in self.global_guna_history) / len(self.global_guna_history)
                aggregated_tamas = sum(g.tamas for g in self.global_guna_history) / len(self.global_guna_history)
                self.current_guna_balance = GunaVector(sattva=aggregated_sattva, rajas=aggregated_rajas, tamas=aggregated_tamas)
                
                await self.intent_monitor.monitor_balance(self.current_guna_balance)
                
                metrics.global_guna_sattva.set(self.current_guna_balance.sattva) # NIEUW: Guna metrics
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
            except Exception as e:
                metrics.errors_total.inc() # NIEUW: Tel errors
                self.logger.error(f"Error handling message: {e}")
                raise
            finally:
                metrics.requests_total.inc() # NIEUW: Tel verwerkte requests
                metrics.requests_in_progress.dec() # NIEUW: Decrease in progress
                metrics.request_latency_seconds.observe(time.time() - start_time) # NIEUW: Registreer latency
        
    def _quantify_message_guna(self, message: AgentMessage) -> GunaVector:
        with tracer.start_as_current_span("quantify_message_guna"):
            """Helper to quantify Gunas from message payload."""
            metrics.requests_in_progress.inc() # NIEUW
            start_time = time.time() # NIEUW
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
                metrics.requests_in_progress.dec() # NIEUW
                metrics.request_latency_seconds.observe(time.time() - start_time) # NIEUW


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
