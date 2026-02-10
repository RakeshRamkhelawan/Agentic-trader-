"""
Trader Agent - Decide Phase van OODA Loop.

Genereert trade proposals uit orientation analysis.
"""

import logging
from typing import Dict, Any, Optional

from backend.agents.base_agent import BaseAgent
from backend.core.schemas.ooda_types import (
    Orientation,
    TradeProposal,
    MarketRegime
)
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
        llm_provider: Optional[Any] = None,
        event_bus: Optional[Any] = None,
        default_risk_reward: float = 2.0,
        base_position_size: float = 0.1
    ):
        """
        Initialiseer Trader.
        
        Args:
            llm_provider: LLM voor strategy rationale generation
            event_bus: Event bus
            default_risk_reward: Risk/reward ratio (take_profit / stop_loss)
            base_position_size: Base position size als fractie van capital
        """
        super().__init__(
            agent_name="Trader",
            llm_provider=llm_provider,
            event_bus=event_bus,
            agent_role=AgentRole.STRATEGIST
        )
        
        self.default_risk_reward = default_risk_reward
        self.base_position_size = base_position_size
        
        self.proposals_generated = 0
    
    async def propose_trade(
        self,
        orientation: Orientation,
        current_price: float,
        strategy_id: str = "momentum_v1"
    ) -> Optional[TradeProposal]:
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
            # Determine trade direction van regime + indicators
            side = self._determine_side(orientation)
            
            if side is None:
                logger.info(
                    f"No trade signal for {orientation.symbol}, "
                    f"regime={orientation.regime.value}"
                )
                return None
            
            # Calculate position size (confidence-weighted)
            size = self._calculate_position_size(
                orientation.confidence,
                orientation.regime
            )
            
            # Calculate stop loss & take profit
            stop_loss, take_profit = self._calculate_levels(
                current_price,
                side,
                orientation.regime
            )
            
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
                confidence=orientation.confidence
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
                exploration_rate = config.get('exploration_rate', 0.1)
                
                # Apply exploration rate to confidence (simulated epsilon-greedy or noise)
                # In this simplified implementation, we use it to dampen or boost confidence check
                # or just log it for now as part of the decision context
                
                # Dynamic adjustment: higher exploration -> lower confidence threshold
                if exploration_rate > 0.5:
                    logger.info(f"High exploration rate {exploration_rate} detected - adjusting strategy")
                    
            except Exception as e:
                logger.warning(f"FastConfig read failed: {e}")
                exploration_rate = 0.0

            return proposal
            
        except Exception as e:
            logger.error(f"Failed to generate proposal: {e}")
            self.record_activity(success=False)
            raise
    
    def _determine_side(self, orientation: Orientation) -> Optional[str]:
        """
        Bepaal trade richting (buy/sell) van orientation.
        
        Simplified strategy logic:
        - TRENDING_UP + high confidence → buy
        - TRENDING_DOWN + high confidence → sell
        - RANGING/VOLATILE → no trade
        
        Returns:
            "buy", "sell", or None
        """
        regime = orientation.regime
        confidence = orientation.confidence
        
        # Minimum confidence threshold
        if confidence < 0.6:
            return None
        
        # Regime-based decisions
        if regime == MarketRegime.TRENDING_UP:
            return "buy"
        elif regime == MarketRegime.TRENDING_DOWN:
            return "sell"
        else:
            # RANGING, VOLATILE, UNKNOWN → geen trade
            return None
    
    def _calculate_position_size(
        self,
        confidence: float,
        regime: MarketRegime
    ) -> float:
        """
        Bereken position size op basis van confidence en regime.
        
        Formula: base_size * confidence * regime_multiplier
        
        Returns:
            Position size als fractie van capital
        """
        # Regime risk multipliers
        regime_multipliers = {
            MarketRegime.TRENDING_UP: 1.2,
            MarketRegime.TRENDING_DOWN: 1.2,
            MarketRegime.RANGING: 0.8,
            MarketRegime.VOLATILE: 0.5,
            MarketRegime.UNKNOWN: 0.5
        }
        
        multiplier = regime_multipliers.get(regime, 1.0)
        size = self.base_position_size * confidence * multiplier
        
        # Cap at max
        return min(size, 1.0)
    
    def _calculate_levels(
        self,
        entry_price: float,
        side: str,
        regime: MarketRegime
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
    
    def _determine_leverage(self, regime: MarketRegime) -> Optional[float]:
        """
        Bepaal leverage op basis van regime.
        
        Conservative approach:
        - TRENDING: 2x leverage
        - RANGING: 1x (spot)
        - VOLATILE: None (spot only)
        
        Returns:
            Leverage multiplier of None voor spot
        """
        if regime in [MarketRegime.TRENDING_UP, MarketRegime.TRENDING_DOWN]:
            return 2.0
        elif regime == MarketRegime.RANGING:
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
        rsi = indicators.get('rsi', 50)
        
        rationale = (
            f"{side.upper()} signal in {regime} market. "
            f"Confidence: {confidence_pct}%. "
            f"RSI: {rsi:.1f}. "
        )
        
        # Add RAG context if available
        if orientation.rag_context:
            rationale += f"Historical pattern: {orientation.rag_context[0][:50]}..."
        
        return rationale
    
    async def analyze(self, features: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """BaseAgent abstract - gebruik propose_trade()."""
        logger.warning("analyze() called on Trader - use propose_trade() instead")
        return {
            "recommendation": "Use propose_trade() for TraderAgent",
            "confidence": 0.0
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Krijg Trader statistieken."""
        health = self.health_check()
        return {
            **health,
            "proposals_generated": self.proposals_generated,
            "exploration_rate": FastConfig.read().get('exploration_rate', 0.0)
        }
