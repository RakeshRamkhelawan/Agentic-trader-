"""
StrategicAdapter - Bridges v8 Symbiotic Agents with v9 Strategic Layer

This module provides a non-breaking integration layer that wraps v8 agents
with v9 strategic capabilities (MCTS, ToT, Memory).

Design Principles:
1. Non-destructive: v8 agents remain unchanged
2. Composable: Strategic layer is optional
3. Transparent: v8 sees strategic layer as "advice", not commands
4. Measurable: Track strategic override impact on performance
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class ActionType(Enum):
    """Action types matching v8"""

    HOLD = 0
    BUY = 1
    SELL = 2


@dataclass
class StrategicContext:
    """Context passed from v9 strategic layer to v8 agents"""

    lookahead_days: int = 10
    mcts_confidence: float = 0.5
    strategic_bias: str = "neutral"  # "bullish", "bearish", "neutral"
    time_horizon: str = "swing"  # "scalp", "swing", "position"

    # Sizing modifiers
    position_size_mult: float = 1.0
    stop_loss_mult: float = 1.0
    take_profit_mult: float = 1.0

    # Risk modifiers
    max_risk_override: Optional[float] = None

    # Symbol filtering
    recommended_symbols: List[str] = field(default_factory=list)
    avoided_symbols: List[str] = field(default_factory=list)


@dataclass
class StrategicDecision:
    """Decision augmented with strategic layer guidance"""

    action: ActionType
    confidence: float
    coherence: float
    harmony_score: float
    weighted_strength: float
    participating_agents: List[str]
    dominant_element: str
    suppressed_element: Optional[str]
    guna_state: Dict[str, float]
    rationale: str
    is_maya: bool

    # v9 additions
    strategic_override: bool = False
    strategic_rationale: str = ""
    mcts_confidence: float = 0.0
    expected_sharpe: float = 0.0


class StrategicV8Adapter:
    """
    Adapter that wraps v8 CollectiveConsciousness with v9 strategic layer

    Usage:
        v8_collective = CollectiveConsciousness()
        adapter = StrategicV8Adapter(v8_collective)

        # Get decision with strategic overlay
        decision = adapter.deliberate_with_strategy(market_state, ctx, plan)
    """

    def __init__(self, v8_collective, enable_tot: bool = True):
        self.v8 = v8_collective
        self.enable_tot = enable_tot

        # Statistics
        self.stats = {
            "total_deliberations": 0,
            "strategic_overrides": 0,
            "mcts_agreements": 0,
            "mcta_disagreements": 0,
            "avg_boost": 0.0,
        }

    def deliberate_with_strategy(
        self,
        market_state: Any,
        ctx: StrategicContext,
        strategic_plan: Optional[Dict] = None,
    ) -> StrategicDecision:
        """
        Run v8 deliberation with v9 strategic overlay

        Args:
            market_state: v8 MarketState object
            ctx: Strategic context from v9 layer
            strategic_plan: Optional MCTS plan

        Returns:
            StrategicDecision with v9 annotations
        """
        # Run v8 deliberation (unchanged)
        v8_decision = self.v8.deliberation(market_state)

        self.stats["total_deliberations"] += 1

        # Apply strategic layer
        if strategic_plan:
            # Check MCTS agreement with v8
            mcts_action = strategic_plan.get("recommended_action", "hold")
            v8_action = (
                "buy"
                if v8_decision.action == ActionType.BUY
                else "sell" if v8_decision.action == ActionType.SELL else "hold"
            )

            # Determine strategic override
            override = False
            boost = 0.0
            strategic_rationale = "No override"

            if mcts_action in ["buy", "sell"]:
                if mcts_action == v8_action:
                    # Agreement - boost confidence
                    boost = strategic_plan.get("confidence", 0.5) * 0.3
                    self.stats["mcts_agreements"] += 1
                    strategic_rationale = f"MCTS agrees with v8 ({mcts_action})"
                elif v8_action == "hold":
                    # MCTS wants to trade, v8 says hold - respect v8 (tactical expertise)
                    strategic_rationale = f"MCTS suggests {mcts_action} but v8 holds"
                else:
                    # Disagreement - v8 tactical trumps MCTS strategic
                    override = True
                    self.stats["mcta_disagreements"] += 1
                    strategic_rationale = f"v8 {v8_action} overrides MCTS {mcts_action}"

            # Update stats
            self.stats["strategic_overrides"] += int(override)

            return StrategicDecision(
                action=v8_decision.action,
                confidence=min(1.0, v8_decision.confidence + boost),
                coherence=v8_decision.coherence,
                harmony_score=v8_decision.harmony_score,
                weighted_strength=v8_decision.weighted_strength,
                participating_agents=v8_decision.participating_agents,
                dominant_element=v8_decision.dominant_element.value,
                suppressed_element=(
                    v8_decision.suppressed_element.value if v8_decision.suppressed_element else None
                ),
                guna_state=v8_decision.guna_state.__dict__,
                rationale=v8_decision.rationale,
                is_maya=v8_decision.is_maya,
                strategic_override=override,
                strategic_rationale=strategic_rationale,
                mcts_confidence=strategic_plan.get("confidence", 0.0),
                expected_sharpe=strategic_plan.get("expected_sharpe", 0.0),
            )

        # No strategic plan - return v8 decision as-is
        return StrategicDecision(
            action=v8_decision.action,
            confidence=v8_decision.confidence,
            coherence=v8_decision.coherence,
            harmony_score=v8_decision.harmony_score,
            weighted_strength=v8_decision.weighted_strength,
            participating_agents=v8_decision.participating_agents,
            dominant_element=v8_decision.dominant_element.value,
            suppressed_element=(
                v8_decision.suppressed_element.value if v8_decision.suppressed_element else None
            ),
            guna_state=v8_decision.guna_state.__dict__,
            rationale=v8_decision.rationale,
            is_maya=v8_decision.is_maya,
            strategic_override=False,
            strategic_rationale="No strategic plan available",
            mcts_confidence=0.0,
            expected_sharpe=0.0,
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get adapter statistics"""
        if self.stats["total_deliberations"] > 0:
            agreement_rate = self.stats["mcts_agreements"] / self.stats["total_deliberations"]
        else:
            agreement_rate = 0.0

        return {**self.stats, "mcts_agreement_rate": round(agreement_rate, 3)}


class StrategicPositionSizer:
    """
    Position sizer with strategic overrides from v9 layer
    """

    def __init__(self, base_risk: float = 0.022):
        self.base_risk = base_risk

    def calculate_size(
        self,
        capital: float,
        decision: StrategicDecision,
        atr: float,
        price: float,
        ctx: StrategicContext,
    ) -> float:
        """
        Calculate position size with strategic multipliers

        Args:
            capital: Available capital
            decision: Strategic decision from deliberation
            atr: Average True Range for stop calculation
            price: Current price
            ctx: Strategic context with multipliers

        Returns:
            Position size in USD
        """
        # Base risk amount
        base_risk = capital * self.base_risk

        # Apply multipliers
        adjusted_risk = base_risk * ctx.position_size_mult

        # Boost if MCTS agrees with v8
        if decision.mcts_confidence > 0.6 and not decision.strategic_override:
            adjusted_risk *= 1 + decision.mcts_confidence * 0.2

        # Cap if override
        if decision.strategic_override:
            adjusted_risk *= 0.7

        # Calculate position from stop distance
        stop_distance = atr * 1.6 * ctx.stop_loss_mult
        if stop_distance <= 0:
            stop_distance = price * 0.02

        position_value = (adjusted_risk / stop_distance) * price

        # Max position limit
        max_position = capital * 0.25

        return min(position_value, max_position)


# Factory function for easy instantiation
def create_strategic_v8(v8_collective, enable_tot: bool = True) -> StrategicV8Adapter:
    """Create strategic adapter from v8 collective"""
    return StrategicV8Adapter(v8_collective, enable_tot=enable_tot)
