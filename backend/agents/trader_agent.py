"""
Trader Agent - Decide Phase van OODA Loop.

Genereert trade proposals uit orientation analysis.
Strategy Integration: Accepteert strategy_registry voor Dasha-based strategie selectie.
"""

import logging
from typing import Any

from backend.agents.base_agent import BaseAgent
from backend.core.schemas.ooda_types import MarketRegime, Orientation, TradeProposal
from backend.execution.fast_config import FastConfig
from backend.governance.agent_gatekeeper import AgentRole

logger = logging.getLogger(__name__)


class TraderAgent(BaseAgent):
    """
    Trader Agent - Strategy execution specialist.

    Rol in OODA: **DECIDE** (proposal generation)
    - Analyseert Orientation data
    - Bepaalt entry/exit prijzen
    - Berekent position size
    - Genereert TradeProposal met rationale
    """

    def __init__(
        self,
        llm_provider: Any | None = None,
        event_bus: Any | None = None,
        default_risk_reward: float = 2.0,
        base_position_size: float = 0.1,
        strategy_registry: Any | None = None,  # UnifiedStrategyRegistry
    ):
        """
        Initialiseer Trader.

        Args:
            llm_provider: LLM voor strategy rationale generation
            event_bus: Event bus
            default_risk_reward: Risk/reward ratio (take_profit / stop_loss)
            base_position_size: Base position size als fractie van capital
            strategy_registry: UnifiedStrategyRegistry voor Dasha-based strategy selectie
        """
        super().__init__(
            agent_name="Trader",
            llm_provider=llm_provider,
            event_bus=event_bus,
            agent_role=AgentRole.STRATEGIST,
        )

        self.default_risk_reward = default_risk_reward
        self.base_position_size = base_position_size
        self.strategy_registry = strategy_registry

        self.proposals_generated = 0

    async def propose_trade(
        self,
        orientation: Orientation,
        current_price: float,
        strategy_id: str = "momentum_v1",
    ) -> TradeProposal | None:
        """
        Genereer trade proposal uit orientation.

        Args:
            orientation: Orientation van AnalystAgent
            current_price: Huidige marktprijs
            strategy_id: Strategy identifier voor audit

        Returns:
            TradeProposal of None als geen trade opportunity
        """
        self.heartbeat()

        try:
            # === STRATEGY REGISTRY INTEGRATION (Phase D) ===
            if self.strategy_registry:
                try:
                    # Use Dasha-based strategy analysis
                    market_data = {
                        "price": current_price,
                        "symbol": orientation.symbol,
                        "regime": orientation.regime.value,
                        "indicators": orientation.indicators,
                    }
                    soul_context = {
                        "confidence": orientation.confidence,
                        "core_sentiment": orientation.core_sentiment,
                    }

                    intent = await self.strategy_registry.analyze_with_dasha_strategy(
                        market_data=market_data,
                        soul_context=soul_context,
                    )

                    if intent and intent.action in ["buy", "sell"]:
                        # Convert TradingIntent to TradeProposal
                        side = intent.action
                        size = intent.size if intent.size > 0 else self.base_position_size

                        # Adjust confidence by strategy confidence
                        final_confidence = orientation.confidence * intent.confidence

                        logger.info(
                            f"Strategy registry generated {side.upper()} signal "
                            f"with confidence={final_confidence:.2f}"
                        )
                    else:
                        side = None

                except Exception as e:
                    logger.warning(f"Strategy registry analysis failed: {e}, using fallback")
                    side = None
            else:
                # Fallback: use legacy determination
                side = None

            # Fallback: Determine trade direction van regime + indicators
            if side is None:
                side = self._determine_side(orientation)

            if side is None:
                logger.info(
                    f"No trade signal for {orientation.symbol}, "
                    f"regime={orientation.regime.value}"
                )
                return None

            # Calculate position size (confidence-weighted)
            size = self._calculate_position_size(orientation.confidence, orientation.regime)

            # Calculate stop loss & take profit
            stop_loss, take_profit = self._calculate_levels(current_price, side, orientation.regime)

            # Generate rationale
            rationale = self._generate_rationale(orientation, side)

            # Determine leverage based on regime
            leverage = self._determine_leverage(orientation.regime)

            # Create proposal
            proposal = TradeProposal(
                symbol=orientation.symbol,
                side=side,
                size=size,
                entry_price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                leverage=leverage,
                rationale=rationale,
                strategy_id=strategy_id,
                confidence=orientation.confidence,
            )

            self.proposals_generated += 1
            self.record_activity(success=True)

            logger.info(
                f"Trade proposal generated: {side.upper()} {orientation.symbol} "
                f"@ {current_price}, size={size}, confidence={orientation.confidence:.2f}"
            )

            # Read FastConfig for exploration/dynamic adjustment
            try:
                config = FastConfig.read()
                exploration_rate = config.get("exploration_rate", 0.1)

                # Dynamic adjustment: higher exploration -> lower confidence threshold
                if exploration_rate > 0.5:
                    logger.info(
                        f"High exploration rate {exploration_rate} detected - adjusting strategy"
                    )

            except Exception as e:
                logger.warning(f"FastConfig read failed: {e}")

            return proposal

        except Exception as e:
            logger.error(f"Failed to generate proposal: {e}")
            self.record_activity(success=False)
            raise

    def _determine_side(self, orientation: Orientation) -> str | None:
        """
        Bepaal trade richting (buy/sell) van orientation.

        Simplified strategy logic:
        - BULL + high confidence → buy
        - BEAR + high confidence → sell
        - SIDEWAYS/VOLATILE → no trade

        Returns:
            "buy", "sell", or None
        """
        regime = orientation.regime
        confidence = orientation.confidence

        # Minimum confidence threshold
        if confidence < 0.6:
            return None

        # Regime-based decisions
        if regime == MarketRegime.BULL:
            return "buy"
        elif regime == MarketRegime.BEAR:
            return "sell"
        else:
            # SIDEWAYS, VOLATILE, UNKNOWN → geen trade
            return None

    def _calculate_position_size(self, confidence: float, regime: MarketRegime) -> float:
        """
        Bereken position size op basis van confidence en regime.

        Formula: base_size * confidence * regime_multiplier

        Returns:
            Position size als fractie van capital
        """
        # Regime risk multipliers
        regime_multipliers = {
            MarketRegime.BULL: 1.2,
            MarketRegime.BEAR: 1.2,
            MarketRegime.SIDEWAYS: 0.8,
            MarketRegime.VOLATILE: 0.5,
            MarketRegime.UNKNOWN: 0.5,
        }

        multiplier = regime_multipliers.get(regime, 1.0)
        size = self.base_position_size * confidence * multiplier

        # Cap at max
        return min(size, 1.0)

    def _calculate_levels(
        self, entry_price: float, side: str, regime: MarketRegime
    ) -> tuple[float, float]:
        """
        Bereken stop loss en take profit levels.

        Args:
            entry_price: Entry price
            side: "buy" of "sell"
            regime: Market regime (beïnvloedt volatility buffer)

        Returns:
            (stop_loss, take_profit) tuple
        """
        # Base stop distance als percentage
        # Volatiele regimes krijgen bredere stops
        if regime == MarketRegime.VOLATILE:
            stop_pct = 0.03  # 3%
        else:
            stop_pct = 0.02  # 2%

        # Take profit based on risk/reward ratio
        tp_pct = stop_pct * self.default_risk_reward

        if side == "buy":
            stop_loss = entry_price * (1 - stop_pct)
            take_profit = entry_price * (1 + tp_pct)
        else:  # sell
            stop_loss = entry_price * (1 + stop_pct)
            take_profit = entry_price * (1 - tp_pct)

        return stop_loss, take_profit

    def _determine_leverage(self, regime: MarketRegime) -> float | None:
        """
        Bepaal leverage op basis van regime.

        Conservative approach:
        - TRENDING: 2x leverage
        - RANGING: 1x (spot)
        - VOLATILE: None (spot only)

        Returns:
            Leverage multiplier of None voor spot
        """
        if regime in [MarketRegime.BULL, MarketRegime.BEAR]:
            return 2.0
        elif regime == MarketRegime.SIDEWAYS:
            return 1.0
        else:
            return None  # Spot trading

    def _generate_rationale(self, orientation: Orientation, side: str) -> str:
        """
        Genereer human-readable rationale voor trade.

        Returns:
            Rationale string (min 10 chars voor validation)
        """
        regime = orientation.regime.value.replace("_", " ").title()
        confidence_pct = int(orientation.confidence * 100)

        # Extract key indicators
        indicators = orientation.indicators
        rsi = indicators.get("rsi", 50)

        rationale = (
            f"{side.upper()} signal in {regime} market. "
            f"Confidence: {confidence_pct}%. "
            f"RSI: {rsi:.1f}. "
        )

        # Add RAG context if available
        if orientation.rag_context:
            rationale += f"Historical pattern: {orientation.rag_context[0][:50]}..."

        return rationale

    async def analyze(self, features: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """BaseAgent abstract - gebruik propose_trade()."""
        logger.warning("analyze() called on Trader - use propose_trade() instead")
        return {
            "recommendation": "Use propose_trade() for TraderAgent",
            "confidence": 0.0,
        }

    def get_statistics(self) -> dict[str, Any]:
        """Krijg Trader statistieken."""
        health = self.health_check()
        stats = {
            **health,
            "proposals_generated": self.proposals_generated,
            "exploration_rate": FastConfig.read().get("exploration_rate", 0.0),
            "strategy_registry_enabled": self.strategy_registry is not None,
        }
        return stats
