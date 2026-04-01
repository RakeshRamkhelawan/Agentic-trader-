import asyncio
import json
import logging
import time
from typing import Any

import numpy as np
import redis.asyncio as redis

from backend.core.config.settings import Settings
from backend.core.karma.episode_memory import EpisodeMemory
from backend.core.risk.guna_sizing import GunaType
from backend.core.risk.mifid_checks import ClientClassification, ClientProfile
from backend.core.risk.portfolio_risk import PortfolioRiskCalculator, RiskState
from backend.core.risk.risk_manager import RiskManager
from backend.core.sensory_processor import SensoryProcessor
from backend.core.strategy.selector import StrategySelector
from backend.core.zero_copy_bridge import TradingIntent, ZeroCopyBridge
from backend.councils.buddhi_mind import Action, get_buddhi_mind
from backend.orchestration.phase_12_real_agents import create_real_agent_coordinator

logger = logging.getLogger(__name__)


class CognitiveMindService:
    """
    Layer 2: Cognitive Mind (The "Interpreting Mind")
    - Operates at mid-frequency (50-200ms).
    - Reads 'Soul Context' from Redis (published by Eternal Soul).
    - Makes decisions (Buddhi) based on market data and Soul Context.
    - Writes 'TradingIntent' to detailed Shared Memory for Reflex Body.
    """

    def __init__(self, shm_name: str = "trading_intents_v2"):
        self.settings = Settings()
        self.shm_name = shm_name
        self.redis_client: redis.Redis | None = None
        self.bridge: ZeroCopyBridge | None = None
        self.running = False
        self._task: asyncio.Task | None = None

        # Buddhi Mind (The Seat of Decision)
        self.buddhi = get_buddhi_mind()

        # Risk Management (Kanchukas/Constraints)
        self.risk_manager = RiskManager()

        # Portfolio Risk Intelligence (Phase 6)
        self.portfolio_risk_calculator = PortfolioRiskCalculator()

        # Karma Episode Memory (Phase 6)
        self.episode_memory = EpisodeMemory()

        # Strategy Selector (Adaptability)
        self.strategy_selector = StrategySelector()
        self.current_strategy = None  # Track the active strategy

        # Integrated Real Agents (Phase 12)
        self.coordinator = create_real_agent_coordinator()

        # Manas: Sensory Processor
        self.sensory_processor = SensoryProcessor()

        # Default Profile for the System (Internal Prop Trading)
        self.profile = ClientProfile(
            classification=ClientClassification.PROFESSIONAL,
            experience_years=5,
            knowledge_score=10,
            max_loss_tolerance_pct=0.02,
            current_drawdown_pct=0.0,
        )

        # Metrics
        try:
            from backend.core.telemetry.metrics import PrometheusMetrics

            self.metrics = PrometheusMetrics("cognitive_mind")
        except:
            self.metrics = None

    async def start(self):
        """Initialize resources and start the mind loop."""
        logger.info("Starting Cognitive Mind Service...")

        # Connect to Redis
        self.redis_client = redis.from_url(self.settings.REDIS_URL, decode_responses=True)
        await self.redis_client.ping()

        # Initialize Zero-Copy Bridge (Writer Mode)
        self.bridge = ZeroCopyBridge(create=True, shm_name=self.shm_name)

        self.running = True
        self._task = asyncio.create_task(self._mind_cycle_loop())
        logger.info("Cognitive Mind Service started.")

    async def stop(self):
        """Stop the service and cleanup."""
        logger.info("Stopping Cognitive Mind Service...")
        self.running = False
        if self._task:
            await self._task

        if self.redis_client:
            await self.redis_client.close()

        if self.bridge:
            self.bridge.close()

        logger.info("Cognitive Mind Service stopped.")

    def _hold_intent(self) -> TradingIntent:
        """Create a HOLD (no-trade) intent."""
        return TradingIntent(
            action=0,
            size=0.0,
            confidence=0.0,
            stop_loss=0.0,
            take_profit=0.0,
            max_hold_ms=0,
            entry_price=0.0,
            timestamp_ns=0,
        )

    async def process_cycle(self, soul_context: dict[str, Any] | None = None) -> dict[str, Any]:
        """Single cognitive cycle."""
        # Logs voor backtest/debug
        result_metadata = {
            "intent": None,
            "agent_decision": None,
            "perception": None,
            "buddhi_views": [],
            "strategy_used": "N/A",
            "reason": "",
        }

        # 1. Fetch Soul Context
        if soul_context is None:
            if not self.redis_client:
                return result_metadata
            soul_context_json = await self.redis_client.get("soul:context")
            soul_context = json.loads(soul_context_json) if soul_context_json else {}

        # 2. Check Constraints (Kanchukas)
        rahu_active = soul_context.get("rahu_kala_active", False)
        if rahu_active:
            intent = self._hold_intent()
            if self.bridge:
                self.bridge.write_intent("BTC/USD", intent)
            result_metadata["intent"] = intent
            result_metadata["reason"] = "RAHU KALA ACTIVE"
            return result_metadata

        # 3. Formulate Intent (Buddhi)
        guna_str = soul_context.get("guna_dominance", "sattva").lower()
        try:
            current_guna = GunaType(guna_str)
        except ValueError:
            current_guna = GunaType.SATTVA

        # --- PORTFOLIO RISK PRE-VALIDATION ---
        try:
            risk_state = RiskState(
                exposure=soul_context.get("portfolio_exposure", 0.0),
                margin=soul_context.get("portfolio_margin", 10000.0),
                var_95=soul_context.get("var_95", 0.0),
                beta=soul_context.get("beta", 1.0),
                max_drawdown=soul_context.get("max_drawdown", 0.0),
                correlation=soul_context.get("correlation", 0.0),
                liquidity=soul_context.get("liquidity", 1.0),
                volatility_percentile=soul_context.get("volatility_percentile", 0.5),
            )
            risk_eval = self.portfolio_risk_calculator.evaluate(risk_state, guna=current_guna)

            if risk_eval.action == "hold":
                intent = self._hold_intent()
                if self.bridge:
                    self.bridge.write_intent("BTC/USD", intent)
                result_metadata["intent"] = intent
                result_metadata["reason"] = f"Portfolio Risk: {risk_eval.reason}"
                return result_metadata
        except Exception as e:
            logger.error(f"Risk eval error: {e}")

        # --- STRATEGY SELECTION & MANAS ---
        regime = soul_context.get("market_regime", "SIDEWAYS")
        strategy = self.strategy_selector.get_strategy(regime, guna_str)
        self.current_strategy = strategy
        result_metadata["strategy_used"] = type(strategy).__name__

        market_data = {
            "price": soul_context.get("market_metrics", {}).get("price", 0.0),
            "order_book": {},
        }

        # Perception (Manas)
        perception = self.sensory_processor.process_input(
            price_stream=np.array([market_data["price"]]),
            volume_stream=np.array([1.0]),
            orderbook_imbalance=0.0,
            funding_rate=0.0,
            social_sentiment=0.0,
            navagraha_state=None,
        )
        result_metadata["perception"] = perception

        # Analyze with Strategy
        candidate_intent = await strategy.analyze(market_data, soul_context)

        # --- REAL AGENT COLLECTIVE (Layer 2) ---
        agent_features = {
            "price": market_data["price"],
            "headlines": soul_context.get("news", []),
            "coin": "BTC",
        }
        agent_decision = self.coordinator.make_decision(agent_features)
        result_metadata["agent_decision"] = agent_decision

        # --- BUDDHI DECISION ---
        council_views = [
            {
                "council_type": "mind",
                "perspective": (
                    "bullish"
                    if candidate_intent.action == 1
                    else "bearish" if candidate_intent.action == 2 else "neutral"
                ),
                "confidence": candidate_intent.confidence,
            },
            {
                "council_type": "guna",
                "perspective": guna_str,
                "confidence": 0.8,
            },
            {
                "council_type": "agent_collective",
                "perspective": (
                    "bullish"
                    if agent_decision.action == 1
                    else "bearish" if agent_decision.action == 2 else "neutral"
                ),
                "confidence": agent_decision.confidence,
                "reasoning": agent_decision.reasoning,
            },
        ]

        # Individual agent views
        for agent_name, dec in agent_decision.agent_inputs.items():
            council_views.append(
                {
                    "council_type": f"agent_{agent_name.lower()}",
                    "perspective": (
                        "bullish"
                        if dec.get("action") == 1
                        else "bearish" if dec.get("action") == 2 else "neutral"
                    ),
                    "confidence": dec.get("confidence", 0.5),
                    "reasoning": dec.get("reasoning", ""),
                }
            )
        result_metadata["buddhi_views"] = council_views

        market_context = {
            "volatility_1m": soul_context.get("market_metrics", {}).get("volatility", 0.02),
            "regime": regime,
            "market_guna": soul_context.get("market_guna", {}),
        }

        decision = self.buddhi.decide(
            council_views=council_views,
            market_data=market_context,
            session_id="live_session",
            timestamp=soul_context.get("timestamp", ""),
        )

        if not decision.is_executable():
            intent = self._hold_intent()
            intent_reason = f"Buddhi REJECT: {decision.rationale}"
        else:
            # Sizing logic (Phase 6)
            kelly_size = self.portfolio_risk_calculator.calculate_kelly_size(0.55, 1.5, 1.0)
            _, guna_mult = self.portfolio_risk_calculator.get_guna_risk_params(current_guna)
            modulated_size = self.portfolio_risk_calculator.modulated_size(
                kelly_size,
                guna_mult,
                risk_eval.capacity if "risk_eval" in locals() else 0.1,
            )

            final_size = min(candidate_intent.size, modulated_size)
            candidate_intent.size = final_size
            intent = candidate_intent
            intent_reason = f"Buddhi OK: {decision.rationale}"

        if self.bridge:
            self.bridge.write_intent("BTC/USD", intent)

        if self.metrics:
            self.metrics.generated_shm_updates_total.labels(shm_name="intent_shm").inc()

        result_metadata["intent"] = intent
        result_metadata["reason"] = intent_reason

        logger.info(f"Mind: Written Intent (Action={intent.action}, Reason={intent_reason})")
        return result_metadata

    async def _mind_cycle_loop(self):
        while self.running:
            try:
                start_time = time.time()
                await self.process_cycle()
                elapsed = time.time() - start_time
                await asyncio.sleep(max(0.05, 0.1 - elapsed))
            except Exception as e:
                logger.error(f"Cycle error: {e}")
                await asyncio.sleep(1)
