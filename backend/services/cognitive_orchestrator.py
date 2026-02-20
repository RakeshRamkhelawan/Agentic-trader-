"""
Cognitive Orchestrator Service.

Responsibility:
- Manage Lifecycle of AI Agents (Sentiment, Macro, etc.).
- Facilitate Inter-Agent Communication (IACP).
- Generate 'Signal' events based on collective intelligence.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from backend.core.agent_registry import AgentProfile, AgentRegistry
from backend.core.auth.context import (get_current_tenant_optional,
                                       tenant_context)
from backend.core.exceptions import QuotaExceededError
from backend.core.guna_quantifier import GunaQuantifier
from backend.core.memory_agent import MemoryAgent
from backend.core.regime_detector import RegimeDetector
from backend.core.telemetry.metrics import PrometheusMetrics  # NIEUW
from backend.core.telemetry.tracing import get_tracer, setup_tracing
from backend.llm.usage_tracker import UsageTracker
from backend.schemas.agent_messages import AgentMessage
from backend.schemas.guna import GunaVector
from backend.agents.news_agent import NewsAgent
from backend.agents.sentiment_agent import SentimentAgent
from backend.agents.sentiment_agent_v2 import SentimentAgentV2
from backend.services.execution_gateway import ExecutionGateway
from backend.services.federated_triad import FederatedTriadSystem
from backend.services.intent_monitor import IntentMonitor
from backend.services.macro_agent import MacroAgent
# Importeer alle agents die de Orchestrator moet kennen
from backend.services.research_agent import ResearchAgent
from backend.services.valuation_agent import ValuationAgent

# Initialiseer de tracer en metrics voor deze service
tracer = get_tracer("cognitive.orchestrator")
metrics = PrometheusMetrics("cognitive_orchestrator")

# Re-export for convenience
__all__ = [
    "CognitiveOrchestrator",
    "AgentMessage",
    "RegimeDetector",
]  # NIEUW


class CognitiveOrchestrator:
    def __init__(
        self,
        agent_profiles_path: str = "backend/config/agent_profiles.yaml",
        agent_registry: Optional[AgentRegistry] = None,  # Dependency Injection
        guna_quantifier: Optional[GunaQuantifier] = None,
        intent_monitor: Optional[IntentMonitor] = None,
        memory_agent_factory: Callable[
            [], MemoryAgent
        ] = MemoryAgent,  # Factory om MemoryAgent aan te maken
        signal_bridge=None,  # Optional SignalBridge for frontend communication
        usage_tracker: Optional[UsageTracker] = None,  # Optional UsageTracker
        audit_logger=None,  # Optional AuditLogger
        clickhouse_client=None,  # NIEUW: Optional ClickHouseClient
        market_writer=None,  # NIEUW: Optional ClickHouseWriter
        message_writer=None,  # NIEUW: Optional ClickHouseWriter for AgentMessage
        execution_gateway: Optional[ExecutionGateway] = None,  # Phase 9: Real Execution
    ):
        self.agent_registry = agent_registry or AgentRegistry(
            config_path=agent_profiles_path
        )
        self.guna_quantifier = guna_quantifier or GunaQuantifier()
        self.intent_monitor = intent_monitor or IntentMonitor(
            ideal_balance=GunaVector(sattva=0.4, rajas=0.3, tamas=0.3)
        )
        self.memory_agent_factory = memory_agent_factory
        self.signal_bridge = signal_bridge  # Bridge to WebSocket frontend
        self.usage_tracker = usage_tracker
        self.audit_logger = audit_logger
        self.clickhouse_client = clickhouse_client
        self.market_writer = market_writer
        self.message_writer = message_writer
        self.execution_gateway = execution_gateway

        self.agents: Dict[str, Any] = {}
        self.message_handlers: Dict[str, List[Callable[[AgentMessage], Any]]] = {}
        self.current_guna_balance = GunaVector(sattva=1 / 3, rajas=1 / 3, tamas=1 / 3)
        self.global_guna_history: List[GunaVector] = []

        self.logger = logging.getLogger("Orchestrator")
        
        # Federated Triad System - 5 Council deliberation
        self.federated_triad: Optional[FederatedTriadSystem] = None
        self.last_federated_decision: Optional[Dict[str, Any]] = None
        
        self._initialize_agents()

    def _initialize_agents(self):
        with tracer.start_as_current_span("initialize_agents"):
            for agent_id, profile in self.agent_registry.profiles.items():
                self.logger.info(
                    f"Initializing agent: {profile.name} ({profile.id}) [{profile.element}]"
                )

                metrics.requests_in_progress.inc()  # NIEUW: Track initialisatie

                memory = self.memory_agent_factory()

                if agent_id == "orchestrator_v1":
                    self.agents[agent_id] = self
                elif agent_id == "research_v1":
                    self.agents[agent_id] = ResearchAgent(
                        memory_agent=memory, message_bus=self.handle_message
                    )
                elif agent_id == "macro_v1":
                    self.agents[agent_id] = MacroAgent(
                        memory_agent=memory, message_bus=self.handle_message
                    )
                elif agent_id == "valuation_v1":
                    self.agents[agent_id] = ValuationAgent(
                        memory_agent=memory, message_bus=self.handle_message
                    )
                elif agent_id == "risk_guardian_v1":
                    from backend.services.risk_guardian_agent import \
                        RiskGuardianAgent

                    # Use Factory if possible, or direct init
                    self.agents[agent_id] = RiskGuardianAgent(
                        message_bus=self.handle_message
                    )
                elif agent_id == "asset_discovery_v1":
                    from backend.agents.asset_discovery_agent import \
                        AssetDiscoveryAgent

                    self.agents[agent_id] = AssetDiscoveryAgent(
                        llm_provider=None,  # Geen LLM nodig voor discovery
                        event_bus=None,  # TODO: Connect event bus als beschikbaar
                        discovery_interval=86400,  # 1x per dag
                        metadata_sync_interval=3600,  # elk uur
                    )
                elif agent_id == "news_v1":
                    self.agents[agent_id] = NewsAgent(
                        memory_agent=memory,
                        message_bus=self.handle_message,
                        cryptopanic_api_key=None,  # Free tier
                        finnhub_api_key=None,  # Optional: add key for higher limits
                    )
                elif agent_id == "sentiment_v1":
                    # Use V2 with LLM Gateway for optimized GPU routing
                    self.agents[agent_id] = SentimentAgentV2(
                        memory_agent=memory,
                        message_bus=self.handle_message,
                        llm_gateway=None,  # Will be initialized on start
                        enable_cache=True,
                    )
                else:
                    self.logger.warning(
                        f"Unknown agent ID in registry: {agent_id}. Skipping instantiation."
                    )
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
            quota = 10.0  # Default $10/day

            if usage_today >= quota:
                self.logger.warning(
                    f"Tenant {tenant_id} exceeded quota: {usage_today:.2f}/{quota:.2f} USD"
                )
                raise QuotaExceededError(
                    f"Daily LLM budget exceeded. Used ${usage_today:.2f} of ${quota:.2f}",
                    details={"usage": usage_today, "quota": quota},
                )
        except QuotaExceededError:
            raise
        except Exception as e:
            self.logger.error(f"Error checking quota: {e}")
            # Fail open if check fails (don't block user on infra error)

    async def handle_message(self, message: AgentMessage):
        with tracer.start_as_current_span(
            "handle_message",
            attributes={"message.type": message.type, "message.source": message.source},
        ):
            metrics.requests_in_progress.inc()
            start_time = time.time()

            self.logger.info(
                f"Orchestrator received: {message.type} from {message.source} to {message.target}"
            )

            # Determine effective tenant: Message ID > Current Context
            effective_tenant = message.tenant_id or get_current_tenant_optional()

            # 0. PERSIST Message (Async)
            if self.message_writer:
                try:
                    # Format for ClickHouse agent_events table
                    # Schema: id, ts, type, source, target, tenant_id, conversation_id, symbol, price, payload
                    row = {
                        "id": message.id,
                        "ts": datetime.fromtimestamp(message.timestamp),
                        "type": message.type,
                        "source": message.source,
                        "target": message.target,
                        "tenant_id": effective_tenant,
                        "conversation_id": message.payload.get("conversation_id")
                        if isinstance(message.payload, dict)
                        else None,
                        "symbol": message.payload.get("symbol")
                        if isinstance(message.payload, dict)
                        else None,
                        "price": (
                            float(message.payload["price"])
                            if isinstance(message.payload, dict)
                            and "price" in message.payload
                            and message.payload["price"]
                            else None
                        ),
                        "payload": json.dumps(message.payload),  # Store raw JSON
                    }
                    # We might need to handle validation/conversion error inside loop,
                    # but here just enqueue.
                    await self.message_writer.enqueue(row)
                except Exception as e:
                    self.logger.warning(f"Failed to persist message {message.id}: {e}")

            # Create a context manager wrapper
            # If no tenant, we use a null context or just proceed (but tenant_context needs a value)
            # We'll use a helper or simple conditional

            try:
                if effective_tenant:
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

    async def _process_message_logic(
        self, message: AgentMessage, tenant_id: Optional[str]
    ):
        """Internal logic for processing message, assumed to be in correct context."""
        if tenant_id:
            await self._check_quota(tenant_id)

        if self.audit_logger and tenant_id:
            await self.audit_logger.log_event(
                tenant_id=tenant_id,
                action="PROCESS_MESSAGE",
                resource_type="agent_message",
                resource_id=message.id,
                details={
                    "type": message.type,
                    "source": message.source,
                    "target": message.target,
                },
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
                        "preferences": {},  # Orchestrator needs to fetch this or Risk agent does
                    },
                    tenant_id=tenant_id,  # Propagate tenant
                )
                if "risk_guardian_v1" in self.agents:
                    await self.agents["risk_guardian_v1"].handle_message(
                        validation_request
                    )
                return

        event_guna = self._quantify_message_guna(message)
        message.payload["guna_vibration"] = event_guna.model_dump()

        self.global_guna_history.append(event_guna)
        if len(self.global_guna_history) > 10:
            self.global_guna_history.pop(0)

        aggregated_sattva = sum(g.sattva for g in self.global_guna_history) / len(
            self.global_guna_history
        )
        aggregated_rajas = sum(g.rajas for g in self.global_guna_history) / len(
            self.global_guna_history
        )
        aggregated_tamas = sum(g.tamas for g in self.global_guna_history) / len(
            self.global_guna_history
        )
        self.current_guna_balance = GunaVector(
            sattva=aggregated_sattva, rajas=aggregated_rajas, tamas=aggregated_tamas
        )

        self.intent_monitor.monitor_balance(self.current_guna_balance)

        metrics.global_guna_sattva.set(self.current_guna_balance.sattva)
        metrics.global_guna_rajas.set(self.current_guna_balance.rajas)
        metrics.global_guna_tamas.set(self.current_guna_balance.tamas)
        metrics.guna_deviation_score.set(
            self.intent_monitor.measure_deviation(self.current_guna_balance)
        )

        target_profiles_to_notify: List[AgentProfile] = []

        if (
            message.target == "all"
            or message.target == self.agent_registry.get_profile("orchestrator_v1").id
        ):
            target_profiles_to_notify = [
                p
                for p in self.agent_registry.profiles.values()
                if message.type in p.subscriptions
            ]
        else:
            profile = self.agent_registry.get_profile(message.target)
            if profile and message.type in profile.subscriptions:
                target_profiles_to_notify.append(profile)

        for profile in target_profiles_to_notify:
            agent_instance = self.agents.get(profile.id)
            if not agent_instance:
                continue

            self.logger.debug(
                f"Routing {message.type} to {profile.name} (ID: {profile.id}) based on subscription."
            )

            if agent_instance == self:
                await self.process_generic_message(message)
            elif hasattr(agent_instance, "handle_message"):
                await agent_instance.handle_message(message)
            else:
                self.logger.warning(
                    f"Agent {profile.id} has no handle_message method for {message.type}"
                )

        # Emit signal to frontend via SignalBridge
        if self.signal_bridge and self._is_actionable_signal(message.type):
            await self.signal_bridge.emit_from_agent_message(
                agent_id=message.source,
                agent_name=self._get_agent_name(message.source),
                message_type=message.type,
                payload=message.payload,
            )

    def _quantify_message_guna(self, message: AgentMessage) -> GunaVector:
        with tracer.start_as_current_span("quantify_message_guna"):
            """Helper to quantify Gunas from message payload."""
            metrics.requests_in_progress.inc()
            start_time = time.time()
            try:
                if message.payload:
                    if "text" in message.payload:
                        return self.guna_quantifier.quantify_text(
                            message.payload["text"]
                        )
                    elif "summary" in message.payload:
                        return self.guna_quantifier.quantify_text(
                            message.payload["summary"]
                        )
                    elif "price" in message.payload or "volatility" in message.payload:
                        return self.guna_quantifier.quantify_numerical_data(
                            message.payload
                        )
                return GunaVector(sattva=1 / 3, rajas=1 / 3, tamas=1 / 3)  # Neutraal
            finally:
                metrics.requests_in_progress.dec()
                metrics.request_latency_seconds.observe(time.time() - start_time)

    def _is_actionable_signal(self, message_type: str) -> bool:
        """Check if message type should be sent to frontend as a signal."""
        actionable_types = {
            "BUY_SIGNAL",
            "SELL_SIGNAL",
            "HOLD_SIGNAL",
            "LONG_SIGNAL",
            "SHORT_SIGNAL",
            "NEUTRAL",
            "ALERT",
            "WARNING",
            "RISK_ALERT",
            "SENTIMENT_UPDATE",
            "MACRO_INSIGHT",
            "VALUATION_UPDATE",
            "RESEARCH_COMPLETE",
            "ANALYSIS_RESULT",
            "RESEARCH_COMPLETE",
            "ANALYSIS_RESULT",
            "ORDER_VALIDATION_RESULT",  # Added for Risk Feedback
            "SIGNAL",  # Added for generic signals
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
        self.logger.info(
            f"Generic handler processed message: {message.id} from {message.source}"
        )

        # 1. Handle SIGNALS from Research Agent (BULLISH/BEARISH)
        if message.type == "SIGNAL" and message.source == "research_v1":
            payload = message.payload
            direction = payload.get("signal")  # BULLISH_MOMENTUM / BEARISH_MOMENTUM
            symbol = payload.get("symbol")
            price = payload.get("price")
            exchange_id = payload.get("exchange_id")  # NEW: Multi-Broker Routing

            if direction and symbol and price:
                self.logger.info(
                    f"Converting SIGNAL {direction} for {symbol} (Ex: {exchange_id}) to ORDER INTENT"
                )

                # Construct Order Intent
                side = "buy" if "BULLISH" in direction else "sell"
                order_payload = {
                    "symbol": symbol,
                    "side": side,
                    "type": "market",
                    "quantity": 1.0,  # Default for MVP
                    "price": price,
                    "exchange_id": exchange_id,  # Persist preference
                    "timestamp": time.time(),
                }

                # Route to Risk Guardian for Validation
                validation_msg = AgentMessage(
                    source="orchestrator_v1",  # Generated by Orchestrator
                    target="risk_guardian_v1",
                    type="VALIDATE_ORDER",
                    payload={
                        "order": order_payload,
                        "preferences": {
                            "autonomy_status": "semi_auto",  # Default to semi-auto for safety
                            "risk_settings": {
                                "max_order_size": 100000.0,
                                "allowed_assets": ["BTC/E2E", "ETH/USD"],
                                "kill_switch_enabled": False,
                            },
                        },
                    },
                    tenant_id=message.tenant_id,
                )

                if "risk_guardian_v1" in self.agents:
                    await self.agents["risk_guardian_v1"].handle_message(validation_msg)
                else:
                    self.logger.warning(
                        "RiskGuardian not found! Cannot validate order."
                    )

        # 2. Handle ORDER_VALIDATION_RESULT from Risk Guardian
        elif message.type == "ORDER_VALIDATION_RESULT":
            result = message.payload.get("result", {})
            original_msg_id = message.payload.get("original_msg_id")

            if result.get("allowed"):
                self.logger.info(
                    f"✅ ORDER APPROVED by RiskGuardian: {result.get('reason')}"
                )
                # EXECUTE ORDER (REAL)
                if self.execution_gateway:
                    self.logger.info(f"🚀 SENDING ORDER TO GATEWAY: {original_msg_id}")
                    # Extract details from payload
                    try:
                        order_details = message.payload.get("order", {})
                        exec_result = await self.execution_gateway.execute_order(
                            symbol=order_details.get("symbol"),
                            side=order_details.get("side"),
                            amount=order_details.get(
                                "quantity", 0
                            ),  # Ensure quantity is passed
                            order_type=order_details.get("order_type", "market"),
                            price=order_details.get("price"),
                            target_exchange=order_details.get(
                                "exchange_id"
                            ),  # Route to specific exchange
                        )
                        self.logger.info(f"Execution Result: {exec_result}")
                    except Exception as e:
                        self.logger.error(f"Execution Failed: {e}")
                else:
                    self.logger.warning(
                        "Execution Gateway not attached! Order DROPPED."
                    )

            else:
                self.logger.warning(
                    f"❌ ORDER BLOCKED by RiskGuardian: {result.get('reason')}"
                )
                if result.get("requires_approval"):
                    self.logger.info("requesting HITL approval... (not implemented)")

    async def start_market_consumer(self):
        """Start consuming market data from Redis."""
        import msgpack
        import redis.asyncio as redis

        from backend.core.config.settings import settings

        self.logger.info("Starting Market Data Consumer...")
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=False)
        last_id = "$"
        stream_key = "market_events"

        while True:
            try:
                streams = await redis_client.xread(
                    {stream_key: last_id}, count=100, block=1000
                )
                if not streams:
                    continue

                for stream_name, messages in streams:
                    for message_id, data in messages:
                        last_id = message_id
                        payload = data.get(b"data") or data.get("data")
                        if payload:
                            try:
                                event = msgpack.unpackb(payload, raw=False)
                                await self.handle_market_tick(event)
                            except Exception as e:
                                self.logger.error(f"Failed to decode event: {e}")

            except Exception as e:
                self.logger.error(f"Market Consumer error: {e}")
                await asyncio.sleep(5)

    async def handle_market_tick(self, event: Dict[str, Any]):
        """Process incoming market tick with full validation and dispatch."""
        import time as _time

        from backend.core.market_data.models import (EventType,
                                                     UnifiedMarketEvent)

        try:
            # 1. DESERIALIZE & VALIDATE
            raw_event_type = event.get("event_type", "ticker")
            try:
                event_type_enum = EventType(raw_event_type.upper())
            except (ValueError, AttributeError):
                event_type_enum = EventType.TICKER

            # Convert timestamp to datetime as required by UnifiedMarketEvent schema
            ts_val = event.get("timestamp") or _time.time()
            try:
                ts_dt = datetime.fromtimestamp(float(ts_val))
            except (ValueError, TypeError):
                ts_dt = datetime.now()

            unified = UnifiedMarketEvent(
                event_type=event_type_enum,
                exchange=str(event.get("exchange", "unknown")),
                symbol=str(event.get("symbol", "UNKNOWN")),
                timestamp=ts_dt,
                price=float(event.get("price") or event.get("last") or 0.0),
            )

            self.logger.info(f"Validated tick: {unified.symbol} @ {unified.price}")

            # 1b. PERSIST to ClickHouse (Async)
            if self.market_writer:
                # Map UnifiedMarketEvent to market_events table schema
                # Schema: event_type, venue, symbol, ts_exchange, ts_received, price, size, side, bid, ask, bids_price, bids_size, asks_price, asks_size
                now = datetime.now()
                row = {
                    "event_type": unified.event_type.value
                    if hasattr(unified.event_type, "value")
                    else str(unified.event_type),
                    "venue": unified.exchange,
                    "symbol": unified.symbol,
                    "ts_exchange": unified.timestamp,
                    "ts_received": now,
                    "price": unified.price if unified.price > 0 else None,
                    "size": unified.volume if unified.volume > 0 else None,
                    "side": None,  # Not available in UnifiedMarketEvent
                    "bid": None,  # Not available in UnifiedMarketEvent
                    "ask": None,  # Not available in UnifiedMarketEvent
                    "bids_price": [],  # Empty arrays for now
                    "bids_size": [],
                    "asks_price": [],
                    "asks_size": [],
                }
                await self.market_writer.enqueue(row)

            # 2. DISPATCH via AgentMessage pipeline
            msg = AgentMessage(
                source="market_data_consumer",
                target="all",
                type="TICK_DATA",
                payload=unified.model_dump(),
            )
            await self.handle_message(msg)

        except ValueError as e:
            self.logger.warning(f"Invalid tick data rejected: {e}")
        except Exception as e:
            self.logger.error(f"Tick processing error: {e}")


    # =========================================================================
    # FEDERATED TRIAD INTEGRATION
    # =========================================================================

    async def initialize_federated_triad(self):
        """Initialize the Federated Triad system."""
        if self.federated_triad is None:
            self.federated_triad = FederatedTriadSystem(
                enable_caching=True,
                deliberation_iterations=3,
                chitta_max_nodes=10000,
            )
            await self.federated_triad.initialize()
            self.logger.info("Federated Triad System initialized")

    async def run_federated_cycle(self, market_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run a full Federated Triad deliberation cycle.
        
        This coordinates all 5 councils through deliberation and
        produces a synthesized decision.
        """
        if self.federated_triad is None:
            await self.initialize_federated_triad()

        # Build market data from agents if not provided
        if market_data is None:
            market_data = await self._gather_market_context()

        # Run the federated cycle
        result = await self.federated_triad.process_cycle(market_data)
        
        if result.get("success"):
            self.last_federated_decision = result
            
            # Broadcast decision via signal bridge if available
            if self.signal_bridge and result.get("decision"):
                await self.signal_bridge.emit_federated_decision(
                    decision=result["decision"],
                    coherence=result.get("chitta_stats", {}),
                )

        return result

    async def _gather_market_context(self) -> Dict[str, Any]:
        """Gather market context from all agents."""
        context = {
            "timestamp": time.time(),
            "agent_signals": {},
            "trend": "neutral",
        }

        # Gather signals from each agent
        for agent_id, agent in self.agents.items():
            if agent_id == "orchestrator_v1":
                continue
                
            signal = "neutral"
            confidence = 0.5
            
            # Try to get agent's perspective
            if hasattr(agent, 'get_signal'):
                try:
                    signal_data = await agent.get_signal()
                    signal = signal_data.get("signal", "neutral")
                    confidence = signal_data.get("confidence", 0.5)
                except Exception:
                    pass
            elif hasattr(agent, 'prana'):
                # Derive signal from prana
                prana = agent.prana if isinstance(agent.prana, (int, float)) else 50
                if prana > 70:
                    signal = "bullish"
                elif prana < 40:
                    signal = "bearish"
                confidence = prana / 100

            context["agent_signals"][agent_id] = {
                "signal": signal,
                "confidence": confidence,
            }

        # Determine overall trend
        bullish = sum(1 for s in context["agent_signals"].values() if s["signal"] == "bullish")
        bearish = sum(1 for s in context["agent_signals"].values() if s["signal"] == "bearish")
        
        if bullish > bearish + 1:
            context["trend"] = "bullish"
        elif bearish > bullish + 1:
            context["trend"] = "bearish"

        return context

    def get_federated_state(self) -> Dict[str, Any]:
        """Get current Federated Triad state."""
        if self.federated_triad is None:
            return {
                "initialized": False,
                "cycle_count": 0,
                "chitta": {"total_nodes": 0, "verified_nodes": 0},
            }
        return self.federated_triad.get_state()

    # =========================================================================
    # FEDERATED TRIAD INTEGRATION
    # =========================================================================

    async def initialize_federated_triad(self):
        """Initialize the Federated Triad system."""
        if self.federated_triad is None:
            self.federated_triad = FederatedTriadSystem(
                enable_caching=True,
                deliberation_iterations=3,
                chitta_max_nodes=10000,
            )
            await self.federated_triad.initialize()
            self.logger.info("Federated Triad System initialized")

    async def run_federated_cycle(self, market_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run a full Federated Triad deliberation cycle.
        
        This coordinates all 5 councils through deliberation and
        produces a synthesized decision.
        """
        if self.federated_triad is None:
            await self.initialize_federated_triad()

        # Build market data from agents if not provided
        if market_data is None:
            market_data = await self._gather_market_context()

        # Run the federated cycle
        result = await self.federated_triad.process_cycle(market_data)
        
        if result.get("success"):
            self.last_federated_decision = result
            
            # Broadcast decision via signal bridge if available
            if self.signal_bridge and result.get("decision"):
                await self.signal_bridge.emit_federated_decision(
                    decision=result["decision"],
                    coherence=result.get("chitta_stats", {}),
                )

        return result

    async def _gather_market_context(self) -> Dict[str, Any]:
        """Gather market context from all agents."""
        context = {
            "timestamp": time.time(),
            "agent_signals": {},
            "trend": "neutral",
        }

        # Gather signals from each agent
        for agent_id, agent in self.agents.items():
            if agent_id == "orchestrator_v1":
                continue
                
            signal = "neutral"
            confidence = 0.5
            
            # Try to get agent's perspective
            if hasattr(agent, 'get_signal'):
                try:
                    signal_data = await agent.get_signal()
                    signal = signal_data.get("signal", "neutral")
                    confidence = signal_data.get("confidence", 0.5)
                except Exception:
                    pass
            elif hasattr(agent, 'prana'):
                # Derive signal from prana
                prana = agent.prana if isinstance(agent.prana, (int, float)) else 50
                if prana > 70:
                    signal = "bullish"
                elif prana < 40:
                    signal = "bearish"
                confidence = prana / 100

            context["agent_signals"][agent_id] = {
                "signal": signal,
                "confidence": confidence,
            }

        # Determine overall trend
        bullish = sum(1 for s in context["agent_signals"].values() if s["signal"] == "bullish")
        bearish = sum(1 for s in context["agent_signals"].values() if s["signal"] == "bearish")
        
        if bullish > bearish + 1:
            context["trend"] = "bullish"
        elif bearish > bullish + 1:
            context["trend"] = "bearish"

        return context

    def get_federated_state(self) -> Dict[str, Any]:
        """Get current Federated Triad state."""
        if self.federated_triad is None:
            return {
                "initialized": False,
                "cycle_count": 0,
                "chitta": {"total_nodes": 0, "verified_nodes": 0},
            }
        return self.federated_triad.get_state()


if __name__ == "__main__":
    asyncio.run(main())
