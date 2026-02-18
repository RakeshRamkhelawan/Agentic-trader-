import asyncio
import json
import logging
import time
from typing import Any, Dict, Optional

import redis.asyncio as redis

from backend.core.config.settings import Settings
from backend.core.karma.episode_memory import EpisodeMemory
from backend.core.risk.guna_sizing import GunaType
from backend.core.risk.mifid_checks import (ClientClassification,
                                            ClientProfile, TradeRequest)
from backend.core.risk.portfolio_risk import PortfolioRiskCalculator, RiskState
from backend.core.risk.risk_manager import RiskManager
from backend.core.strategy.selector import StrategySelector
from backend.core.zero_copy_bridge import TradingIntent, ZeroCopyBridge

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
        self.redis_client: Optional[redis.Redis] = None
        self.bridge: Optional[ZeroCopyBridge] = None
        self.running = False
        self._task: Optional[asyncio.Task] = None

        # Risk Management (Kanchukas/Constraints)
        self.risk_manager = RiskManager()

        # Portfolio Risk Intelligence (Phase 6)
        self.portfolio_risk_calculator = PortfolioRiskCalculator()

        # Karma Episode Memory (Phase 6)
        self.episode_memory = EpisodeMemory()

        # Strategy Selector (Adaptability)
        self.strategy_selector = StrategySelector()
        self.current_strategy = None  # Track the active strategy

        # Default Profile for the System (Internal Prop Trading)
        self.profile = ClientProfile(
            classification=ClientClassification.PROFESSIONAL,
            experience_years=5,
            knowledge_score=10,
            max_loss_tolerance_pct=0.02,
            current_drawdown_pct=0.0,
        )

        # Metrics
        from backend.core.telemetry.metrics import PrometheusMetrics

        self.metrics = PrometheusMetrics("cognitive_mind")

    async def start(self):
        """Initialize resources and start the mind loop."""
        logger.info("Starting Cognitive Mind Service...")

        # Connect to Redis
        self.redis_client = redis.from_url(
            self.settings.REDIS_URL, decode_responses=True
        )
        await self.redis_client.ping()

        # Initialize Zero-Copy Bridge (Writer Mode)
        # We likely want to be the creator if it doesn't exist, or just attach
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

    async def process_cycle(self, soul_context: Optional[Dict[str, Any]] = None):
        """Single cognitive cycle for testing."""
        # 1. Fetch Soul Context
        if soul_context is None:
            if not self.redis_client:
                return
            soul_context_json = await self.redis_client.get("soul:context")
            soul_context = json.loads(soul_context_json) if soul_context_json else {}

        # 2. Check Constraints (Kanchukas)
        rahu_active = soul_context.get("rahu_kala_active", False)

        # 3. Formulate Intent (Buddhi)
        if not rahu_active:
            # Map Guna String to Enum
            guna_str = soul_context.get("guna_dominance", "sattva").lower()
            try:
                current_guna = GunaType(guna_str)
            except ValueError:
                current_guna = GunaType.SATTVA

            # --- PORTFOLIO RISK PRE-VALIDATION (Phase 6) ---
            try:
                risk_state = RiskState(
                    exposure=soul_context.get("portfolio_exposure", 0.0),
                    margin=soul_context.get("portfolio_margin", 10000.0),
                    var_95=soul_context.get("var_95", 0.0),
                    beta=soul_context.get("beta", 1.0),
                    max_drawdown=soul_context.get("max_drawdown", 0.0),
                    correlation=soul_context.get("correlation", 0.0),
                    liquidity=soul_context.get("liquidity", 1.0),
                    volatility_percentile=soul_context.get(
                        "volatility_percentile", 0.5
                    ),
                )
                risk_eval = self.portfolio_risk_calculator.evaluate(
                    risk_state, guna=current_guna
                )

                if risk_eval.action == "hold":
                    logger.warning(
                        f"Portfolio risk HOLD: {risk_eval.reason} (capacity={risk_eval.capacity:.2f}, threshold={risk_eval.threshold:.2f})"
                    )
                    intent = self._hold_intent()
                    self.bridge.write_intent("BTC/USD", intent)
                    self.metrics.generated_shm_updates_total.labels(
                        shm_name="intent_shm"
                    ).inc()
                    logger.info(
                        f"Mind: Written Intent to SHM (Action=0, Size=0.0, Reason={risk_eval.reason})"
                    )
                    return
            except Exception as e:
                logger.error(
                    f"Portfolio risk calculator error: {e}, falling back to HOLD"
                )
                intent = self._hold_intent()
                self.bridge.write_intent("BTC/USD", intent)
                return

            # STRATEGY SELECTION & EXECUTION (Adaptability)
            regime = soul_context.get("market_regime", "SIDEWAYS")
            strategy = self.strategy_selector.get_strategy(regime, guna_str)
            self.current_strategy = strategy  # Track active strategy

            # Prepare Market Data for Strategy
            market_data = {
                "price": soul_context.get("market_metrics", {}).get("price", 0.0),
                "order_book": {},
            }

            # Analyze
            candidate_intent = await strategy.analyze(market_data, soul_context)

            # --- RISK MANAGEMENT INTEGRATION (Kanchukas) ---
            trade_req = TradeRequest(
                asset="BTC/USD",
                amount=candidate_intent.size,
                price=candidate_intent.entry_price,
                side="buy" if candidate_intent.action == 1 else "sell",
                notional_value=candidate_intent.size * candidate_intent.entry_price,
            )

            risk_decision = self.risk_manager.evaluate_trade(
                self.profile, trade_req, current_guna
            )
            reason = risk_decision.reason

            if risk_decision.decision == "reject":
                logger.warning(f"Risk Reject: {reason}")
                intent = self._hold_intent()
            else:
                if risk_decision.decision == "warn":
                    logger.warning(f"Risk Warning: {reason}")

                # Apply Kelly-modulated sizing (Phase 6)
                kelly_size = self.portfolio_risk_calculator.calculate_kelly_size(
                    win_rate=0.55,
                    avg_win=1.5,
                    avg_loss=1.0,
                )
                _, guna_mult = self.portfolio_risk_calculator.get_guna_risk_params(
                    current_guna
                )
                modulated_size = self.portfolio_risk_calculator.modulated_size(
                    kelly_size=kelly_size,
                    guna_multiplier=guna_mult,
                    risk_capacity=risk_eval.capacity,
                )

                # Use the smaller of MiFID-adjusted and Kelly-modulated size
                final_size = (
                    min(risk_decision.adjusted_size, modulated_size)
                    if modulated_size > 0
                    else risk_decision.adjusted_size
                )
                candidate_intent.size = final_size
                intent = candidate_intent
                reason = (
                    "OK" if risk_decision.decision == "accept" else risk_decision.reason
                )

            if self.bridge:
                self.bridge.write_intent("BTC/USD", intent)

            # --- Metrics ---
            self.metrics.generated_shm_updates_total.labels(shm_name="intent_shm").inc()

            if intent.action > 0 and self.current_strategy:
                strategy_name = getattr(self.current_strategy, "name", "UNKNOWN")
                self.metrics.strategy_signal_total.labels(
                    strategy=strategy_name, action=str(intent.action)
                ).inc()

            logger.info(
                f"Mind: Written Intent to SHM (Action={intent.action}, Size={intent.size:.4f}, Reason={reason})"
            )
        else:
            # Rahu is active: CLEAR INTENTS or Defensive Mode
            intent = self._hold_intent()
            if self.bridge:
                self.bridge.write_intent("BTC/USD", intent)
            logger.info(
                f"Mind: Written Intent to SHM (Action={intent.action}, Conf={intent.confidence}) [RAHU KALA]"
            )

    async def _mind_cycle_loop(self):
        """
        The main cognitive cycle.
        Runs frequently (e.g., every 100ms) to update intentions.
        """
        while self.running:
            try:
                start_time = time.time()
                await self.process_cycle()

                # 4. Pace the loop (100ms frequency)
                elapsed = time.time() - start_time
                sleep_time = max(0.05, 0.1 - elapsed)  # Aim for 100ms cycle
                await asyncio.sleep(sleep_time)

            except Exception as e:
                logger.error(f"Error in cognitive cycle: {e}")
                await asyncio.sleep(1)  # Backoff on error
