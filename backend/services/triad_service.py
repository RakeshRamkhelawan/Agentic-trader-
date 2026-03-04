"""
Triad Service - Unified Integration Layer with Exchange Support

Integrates all components:
- Councils (Guna, Mind, Body)
- Buddhi Mind (decision maker)
- Event Bus (real-time updates)
- Exchange Managers (Bitvavo, Revolut)
- Risk Validation
- Paper Trading & Live Trading

This is the main entry point for the Federated Triad system.
"""

from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any

from backend.core.ab_testing.ab_framework import get_ab_framework
from backend.core.memory.episodic_memory import TradingEpisode, get_episodic_memory
from backend.core.ml.triad_ml_trainer import get_ml_trainer
from backend.councils.body_council import get_body_council
from backend.councils.buddhi_mind import BuddhiDecision, get_buddhi_mind
from backend.councils.dynamic_guna_council import get_guna_council
from backend.councils.mind_council import get_mind_council
from backend.events.triad_event_bus import publish_decision, publish_deliberation

# Exchange imports
from backend.exchange import (
    ExchangeFactory,
    OrderManager,
    OrderRequest,
    OrderRiskValidator,
    OrderSide,
    OrderType,
    PortfolioManager,
    RiskLimits,
    Symbol,
)

logger = logging.getLogger(__name__)


class TriadService:
    """
    Unified Triad Service that orchestrates the complete pipeline:

    Market Data → Councils (Guna, Mind, Body) → Buddhi → Risk Check → Exchange Execution

    Usage:
        # Paper Trading (default)
        service = TriadService()
        decision = await service.process_market_data(market_data)
        if decision.is_executable():
            result = await service.execute_paper_trade(decision)

        # Live Trading
        service = TriadService(trading_mode="live")
        await service.initialize_exchanges()
        result = await service.execute_live_trade(decision, exchange_id="bitvavo")
    """

    def __init__(self, trading_mode: str = "paper"):
        """
        Initialize Triad Service.

        Args:
            trading_mode: "paper" (default), "live", or "backtest"
        """
        self.trading_mode = trading_mode

        # Councils
        self.guna_council = get_guna_council()
        self.mind_council = get_mind_council()
        self.body_council = get_body_council()

        # Decision maker
        self.buddhi = get_buddhi_mind()

        # Episodic memory
        self.memory = get_episodic_memory()

        # ML trainer
        self.ml_trainer = get_ml_trainer()

        # A/B Testing
        self.ab_framework = get_ab_framework()
        self.active_experiments: dict[str, str] = {}

        # Exchange Management
        self.exchange_factory = ExchangeFactory()
        self.order_manager = OrderManager()
        self.portfolio_manager = PortfolioManager()
        self.risk_validator = OrderRiskValidator(RiskLimits())
        self._exchanges: dict[str, Any] = {}

        # Session tracking
        self.current_session: str | None = None
        self.decision_history: list[dict] = []
        self.active_episodes: dict[str, str] = {}

        # Stats
        self.stats = {
            "total_deliberations": 0,
            "decisions_made": 0,
            "trades_executed": 0,
            "live_trades": 0,
            "paper_trades": 0,
            "risk_rejections": 0,
        }

        logger.info(f"[TriadService] Initialized (mode={trading_mode})")

    # =========================================================================
    # Exchange Management
    # =========================================================================

    async def initialize_exchanges(self, exchange_ids: list[str] | None = None) -> dict[str, bool]:
        """
        Initialize and connect to exchanges.

        Args:
            exchange_ids: List of exchanges to initialize, or None for all configured

        Returns:
            Dictionary of exchange_id -> success status
        """
        results = {}

        # Determine which exchanges to initialize
        if exchange_ids is None:
            from backend.core.config.settings import settings

            exchange_ids = []
            if settings.BITVAVO_API_KEY:
                exchange_ids.append("bitvavo")
            if settings.REVOLUT_API_KEY:
                exchange_ids.append("revolut")

        # Initialize each exchange
        for exchange_id in exchange_ids:
            try:
                exchange = await self.exchange_factory.create_exchange(
                    exchange_id, auto_connect=True
                )

                if exchange:
                    self._exchanges[exchange_id] = exchange
                    self.order_manager.register_exchange(exchange_id, exchange)
                    self.portfolio_manager.register_exchange(exchange_id, exchange)
                    results[exchange_id] = True
                    logger.info(f"[TriadService] Initialized {exchange_id}")
                else:
                    results[exchange_id] = False
                    logger.error(f"[TriadService] Failed to initialize {exchange_id}")

            except Exception as e:
                results[exchange_id] = False
                logger.error(f"[TriadService] Error initializing {exchange_id}: {e}")

        # Start order manager background tasks
        await self.order_manager.start()

        return results

    async def close_exchanges(self) -> None:
        """Close all exchange connections."""
        await self.order_manager.stop()
        await self.exchange_factory.close_all()
        self._exchanges = {}
        logger.info("[TriadService] All exchanges closed")

    def get_exchange_status(self) -> dict[str, Any]:
        """Get status of all exchanges."""
        return {
            exchange_id: {
                "connected": exchange.connected if hasattr(exchange, "connected") else False,
                "capabilities": (
                    exchange.get_capabilities().name
                    if hasattr(exchange, "get_capabilities")
                    else "Unknown"
                ),
            }
            for exchange_id, exchange in self._exchanges.items()
        }

    # =========================================================================
    # Core Pipeline
    # =========================================================================

    async def process_market_data(
        self, market_data: dict, session_id: str = None
    ) -> BuddhiDecision | None:
        """
        Process market data through complete Triad pipeline.

        Args:
            market_data: Real-time market metrics
            session_id: Optional trading session ID

        Returns:
            BuddhiDecision or None if processing failed
        """
        session_id = session_id or f"triad_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        self.current_session = session_id

        logger.info(f"[TriadService] Processing market data for session {session_id}")

        try:
            # 1. Collect council views
            council_views = await self._collect_council_views(market_data)

            if not council_views:
                logger.warning("[TriadService] No council views collected")
                return None

            # 2. Retrieve episodic memory
            similar_episodes = self.memory.find_similar_episodes(market_data, limit=5)
            karma_score = self.memory.calculate_karma_score(similar_episodes)

            if similar_episodes:
                logger.info(
                    f"[TriadService] Found {len(similar_episodes)} similar episodes, karma: {karma_score:.2f}"
                )

            # 3. Get ML prediction
            ml_prediction = self.ml_trainer.predict_outcome(market_data, council_views, 0.5, 0.5)
            logger.debug(f"[TriadService] ML predicts success probability: {ml_prediction:.2f}")

            # 4. Buddhi makes decision
            decision = self.buddhi.decide(
                council_views=council_views,
                market_data=market_data,
                session_id=session_id,
                timestamp=datetime.utcnow().isoformat(),
            )

            # Adjust confidence based on ML prediction
            if ml_prediction > 0.7:
                decision.confidence = min(0.95, decision.confidence * 1.1)
            elif ml_prediction < 0.3:
                decision.confidence *= 0.9

            # 5. Store episode in memory
            episode = TradingEpisode(
                id=f"ep_{session_id}",
                session_id=session_id,
                timestamp=datetime.utcnow(),
                market_context=market_data,
                volatility=market_data.get("volatility_1m", 0.02),
                trend=(
                    "up"
                    if market_data.get("trend", 0) > 0
                    else "down" if market_data.get("trend", 0) < 0 else "neutral"
                ),
                volume_profile="high" if market_data.get("volume_ratio", 1.0) > 1.5 else "normal",
                guna_vector=council_views[0].get("guna_vector", {}) if council_views else {},
                fear_greed_index=(
                    council_views[1].get("fear_greed_index", 50) if len(council_views) > 1 else 50
                ),
                execution_quality=(
                    council_views[2].get("execution_quality", "unknown")
                    if len(council_views) > 2
                    else "unknown"
                ),
                action=decision.action,
                confidence=decision.confidence,
                coherence=decision.coherence,
                rationale=decision.rationale,
                karma_score=karma_score,
            )

            self.memory.store_episode(episode)
            self.active_episodes[session_id] = episode.id

            # 6. Publish decision event
            await self._publish_decision(decision)

            # 7. Update stats
            self.stats["total_deliberations"] += 1
            if decision.action != "hold":
                self.stats["decisions_made"] += 1

            # 8. Store in history
            self.decision_history.append(
                {
                    "timestamp": decision.timestamp,
                    "action": decision.action,
                    "confidence": decision.confidence,
                    "coherence": decision.coherence,
                }
            )

            logger.info(
                f"[TriadService] Decision: {decision.action} (conf: {decision.confidence:.2f})"
            )

            return decision

        except Exception as e:
            logger.error(f"[TriadService] Error processing market data: {e}", exc_info=True)
            return None

    async def _collect_council_views(self, market_data: dict) -> list:
        """Collect views from all councils."""
        views = []

        # Guna Council
        try:
            guna_view = self.guna_council.analyze(market_data)
            views.append(guna_view)

            await publish_deliberation(
                council_type="guna",
                perspective=guna_view["perspective"],
                confidence=guna_view["confidence"],
                reasoning="; ".join(guna_view["key_insights"]),
                metadata=guna_view.get("guna_vector", {}),
            )
            logger.debug(f"[TriadService] Guna: {guna_view['perspective']}")

        except Exception as e:
            logger.error(f"[TriadService] Guna Council error: {e}")

        # Mind Council
        try:
            mind_view = self.mind_council.analyze(market_data)
            views.append(mind_view)

            await publish_deliberation(
                council_type="mind",
                perspective=mind_view["perspective"],
                confidence=mind_view["confidence"],
                reasoning=f"Fear/Greed: {mind_view.get('fear_greed_index', 50)}",
                metadata={
                    "fear_greed": mind_view.get("fear_greed_index"),
                    "components": mind_view.get("components", {}),
                },
            )
            logger.debug(f"[TriadService] Mind: {mind_view['perspective']}")

        except Exception as e:
            logger.error(f"[TriadService] Mind Council error: {e}")

        # Body Council
        try:
            body_view = self.body_council.analyze_execution_environment(market_data)
            views.append(body_view)

            await publish_deliberation(
                council_type="body",
                perspective=body_view["perspective"],
                confidence=body_view["confidence"],
                reasoning=f"Execution quality: {body_view['execution_quality']}",
                metadata=body_view.get("metrics", {}),
            )
            logger.debug(f"[TriadService] Body: {body_view['perspective']}")

        except Exception as e:
            logger.error(f"[TriadService] Body Council error: {e}")

        return views

    async def _publish_decision(self, decision: BuddhiDecision):
        """Publish decision to event bus."""
        try:
            await publish_decision(
                action=decision.action,
                confidence=decision.confidence,
                coherence=decision.coherence,
                rationale=decision.rationale,
                council_views=decision.council_views,
                session_id=decision.session_id,
            )
        except Exception as e:
            logger.error(f"[TriadService] Failed to publish decision: {e}")

    # =========================================================================
    # Trade Execution
    # =========================================================================

    async def execute_trade(
        self,
        decision: BuddhiDecision,
        symbol: str = "BTC/EUR",
        quantity: Decimal | None = None,
        exchange_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Execute trade based on Buddhi decision.

        Routes to paper or live trading based on trading_mode.

        Args:
            decision: BuddhiDecision object
            symbol: Trading symbol (e.g., "BTC/EUR")
            quantity: Trade size, or None for auto-calculation
            exchange_id: Specific exchange for live trading, or None for auto-route

        Returns:
            Execution result dictionary
        """
        if not decision.is_executable():
            logger.warning(f"[TriadService] Decision not executable: {decision.action}")
            return {"status": "rejected", "reason": "Decision not executable"}

        # Route to appropriate executor
        if self.trading_mode == "paper":
            return await self.execute_paper_trade(decision, symbol, quantity)
        elif self.trading_mode == "live":
            return await self.execute_live_trade(decision, symbol, quantity, exchange_id)
        else:
            return {"status": "rejected", "reason": f"Unknown trading mode: {self.trading_mode}"}

    async def execute_paper_trade(
        self, decision: BuddhiDecision, symbol: str = "BTC/EUR", quantity: Decimal | None = None
    ) -> dict[str, Any]:
        """
        Execute paper trade based on Buddhi decision.

        Args:
            decision: BuddhiDecision object
            symbol: Trading symbol
            quantity: Trade size

        Returns:
            Execution result
        """
        # Default quantity based on confidence
        if quantity is None:
            quantity = Decimal(str(decision.confidence)) * Decimal("0.1")

        logger.info(f"[TriadService] Executing paper trade: {decision.action} {quantity} {symbol}")

        try:
            execution_result = {
                "status": "filled",
                "mode": "paper",
                "symbol": symbol,
                "action": decision.action,
                "quantity": float(quantity),
                "confidence": decision.confidence,
                "coherence": decision.coherence,
                "session_id": decision.session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "paper": True,
            }

            self.stats["trades_executed"] += 1
            self.stats["paper_trades"] += 1

            logger.info(f"[TriadService] Paper trade executed: {execution_result}")

            return execution_result

        except Exception as e:
            logger.error(f"[TriadService] Paper trade execution failed: {e}")
            return {"status": "error", "reason": str(e)}

    async def execute_live_trade(
        self,
        decision: BuddhiDecision,
        symbol: str = "BTC/EUR",
        quantity: Decimal | None = None,
        exchange_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Execute live trade on exchange.

        Args:
            decision: BuddhiDecision object
            symbol: Trading symbol
            quantity: Trade size
            exchange_id: Specific exchange, or None for auto-route

        Returns:
            Execution result
        """
        if not self._exchanges:
            return {"status": "error", "reason": "No exchanges initialized"}

        # Parse symbol
        try:
            trading_symbol = Symbol.from_string(symbol)
        except ValueError as e:
            return {"status": "error", "reason": f"Invalid symbol: {e}"}

        # Determine order side
        if decision.action == "bullish":
            side = OrderSide.BUY
        elif decision.action == "bearish":
            side = OrderSide.SELL
        else:
            return {"status": "rejected", "reason": f"No trade action for: {decision.action}"}

        # Default quantity
        if quantity is None:
            # Get portfolio value for sizing
            portfolio = await self.portfolio_manager.get_portfolio()
            portfolio_value = portfolio.total_value_usd if portfolio else Decimal("10000")
            # Risk 2% max per trade
            max_value = portfolio_value * Decimal("0.02")
            # Estimate price (would get actual from exchange)
            quantity = max_value / Decimal("45000")  # Approximate BTC price

        # Create order request
        order_request = OrderRequest(
            symbol=trading_symbol,
            side=side,
            order_type=OrderType.MARKET,  # Could use LIMIT for better price
            amount=quantity,
            client_order_id=f"triad_{decision.session_id}",
        )

        # Risk validation
        try:
            # Get portfolio and balance info for validation
            portfolio = await self.portfolio_manager.get_portfolio()
            positions = {}  # Would get actual positions

            balance = None
            if exchange_id and exchange_id in self._exchanges:
                balance = await self._exchanges[exchange_id].get_balance(trading_symbol.quote)

            validation = await self.risk_validator.validate_order(
                order_request,
                portfolio_value=portfolio.total_value_usd if portfolio else Decimal("10000"),
                current_positions=positions,
                exchange=self._exchanges.get(exchange_id) if exchange_id else None,
                balance=balance,
            )

            if not validation.is_valid:
                self.stats["risk_rejections"] += 1
                logger.warning(
                    f"[TriadService] Order rejected by risk validator: {validation.overall_message}"
                )
                return {
                    "status": "rejected",
                    "reason": validation.overall_message,
                    "validation": validation.to_dict(),
                }

            if validation.has_warnings:
                logger.warning(f"[TriadService] Order has warnings: {validation.overall_message}")

        except Exception as e:
            logger.error(f"[TriadService] Risk validation error: {e}")
            return {"status": "error", "reason": f"Risk validation failed: {e}"}

        # Execute order
        try:
            order = await self.order_manager.place_order(order_request, exchange_id=exchange_id)

            if not order:
                return {"status": "error", "reason": "Order placement failed"}

            self.stats["trades_executed"] += 1
            self.stats["live_trades"] += 1

            # Record trade for risk tracking
            order_value = order.amount * (order.average_price or order.price or Decimal("0"))
            self.risk_validator.record_trade(order_value)

            result = {
                "status": order.status.value,
                "mode": "live",
                "order_id": order.order_id,
                "exchange": order.exchange_id,
                "symbol": str(order.symbol),
                "side": order.side.value,
                "amount": float(order.amount),
                "filled": float(order.filled),
                "price": float(order.average_price) if order.average_price else None,
                "session_id": decision.session_id,
                "timestamp": datetime.utcnow().isoformat(),
            }

            logger.info(f"[TriadService] Live trade executed: {result}")
            return result

        except Exception as e:
            logger.error(f"[TriadService] Live trade execution failed: {e}")
            return {"status": "error", "reason": str(e)}

    async def cancel_trade(self, order_id: str) -> bool:
        """Cancel a pending trade."""
        return await self.order_manager.cancel_order(order_id)

    # =========================================================================
    # Portfolio & Balance
    # =========================================================================

    async def get_portfolio(self) -> Any | None:
        """Get aggregated portfolio across all exchanges."""
        return await self.portfolio_manager.get_portfolio()

    async def get_exchange_balance(self, exchange_id: str, asset: str) -> Balance | None:
        """Get balance for specific exchange and asset."""
        exchange = self._exchanges.get(exchange_id)
        if not exchange:
            return None
        return await exchange.get_balance(asset)

    # =========================================================================
    # A/B Testing
    # =========================================================================

    def start_ab_experiment(self, experiment_id: str, baseline: str = "v17") -> dict:
        """Start A/B testing experiment."""
        return self.ab_framework.start_experiment(experiment_id, baseline)

    def run_ab_comparison(self, market_data: dict, experiment_id: str) -> dict:
        """Run both Triad and baseline on same market data."""
        triad_decision = self.process_market_data(market_data, f"{experiment_id}_triad")
        baseline_decision = self.ab_framework.get_baseline_decision(experiment_id, market_data)

        return {"triad": triad_decision, "baseline": baseline_decision}

    def record_ab_outcome(self, experiment_id: str, variant: str, pnl: float):
        """Record outcome for A/B test variant."""
        self.ab_framework.record_outcome(experiment_id, variant, pnl)

    def end_ab_experiment(self, experiment_id: str) -> dict:
        """End A/B experiment and get results."""
        return self.ab_framework.end_experiment(experiment_id)

    # =========================================================================
    # Outcome Management
    # =========================================================================

    def update_trade_outcome(
        self, session_id: str, pnl: float, exit_reason: str = "unknown"
    ) -> bool:
        """Update trade outcome in episodic memory."""
        try:
            episode_id = self.active_episodes.get(session_id)
            if not episode_id:
                logger.warning(f"[TriadService] No episode found for session {session_id}")
                return False

            outcome = "success" if pnl > 0 else "failure" if pnl < 0 else "neutral"

            updated = self.memory.update_outcome(
                episode_id=episode_id, outcome=outcome, pnl=pnl, exit_reason=exit_reason
            )

            if updated:
                logger.info(
                    f"[TriadService] Updated trade outcome for {session_id}: {outcome}, PnL: {pnl:.2f}"
                )
                del self.active_episodes[session_id]

            return updated

        except Exception as e:
            logger.error(f"[TriadService] Failed to update trade outcome: {e}")
            return False

    # =========================================================================
    # Statistics & Reporting
    # =========================================================================

    def get_statistics(self) -> dict[str, Any]:
        """Get service statistics."""
        return {
            **self.stats,
            "exchanges": self.get_exchange_status(),
            "orders": self.order_manager.get_statistics(),
        }

    def get_memory_stats(self) -> dict[str, Any]:
        """Get episodic memory statistics."""
        return {
            "total_episodes": len(self.memory.episodes),
            "episodes_with_outcomes": len([e for e in self.memory.episodes if e.outcome]),
            "karma_score": self.memory.calculate_karma_score(self.memory.episodes),
        }


# =============================================================================
# Singleton Instance
# =============================================================================

_triad_service: TriadService | None = None


def get_triad_service(trading_mode: str = "paper") -> TriadService:
    """Get or create TriadService singleton."""
    global _triad_service
    if _triad_service is None:
        _triad_service = TriadService(trading_mode=trading_mode)
    return _triad_service
