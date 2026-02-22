"""
Dasha Strategy Map - Vedic Astrology-Based Strategy Selection (Sprint 3).

Maps planetary periods (Dashas) and transits to trading strategies.
Each Graha (planet) has specific characteristics that map to market behavior.

Budha (Mercury) - The Analyzer:
- Signifies: Intellect, communication, commerce, calculation
- Trading Style: Arbitrage, scalping, statistical analysis
- Markets: Volatile, news-driven, high-frequency
- Strategy: Cross-exchange arbitrage, latency optimization

Integration with Arbitrage Strategy:
Budha Graha activates analytical, high-speed strategies.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class Graha(Enum):
    """The nine grahas (planets) in Vedic astrology."""

    SURYA = "Surya"  # Sun - Authority, trend following
    CHANDRA = "Chandra"  # Moon - Sentiment, mean reversion
    MANGALA = "Mangala"  # Mars - Aggression, momentum breakout
    BUDHA = "Budha"  # Mercury - Analysis, arbitrage, scalping
    GURU = "Guru"  # Jupiter - Expansion, long-term growth
    SHUKRA = "Shukra"  # Venus - Value, dividends, stability
    SHANI = "Shani"  # Saturn - Discipline, risk management
    RAHU = "Rahu"  # North Node - Disruption, contrarian
    KETU = "Ketu"  # South Node - Detachment, exit signals


@dataclass
class StrategyProfile:
    """Trading strategy profile for a Graha."""

    graha: Graha
    strategy_type: str
    time_horizon: str  # "scalping", "day", "swing", "long_term"
    risk_profile: str  # "conservative", "moderate", "aggressive"
    indicators: List[str]
    description: str


# Strategy profiles for each Graha
GRAHA_STRATEGIES: Dict[Graha, StrategyProfile] = {
    Graha.SURYA: StrategyProfile(
        graha=Graha.SURYA,
        strategy_type="trend_following",
        time_horizon="swing",
        risk_profile="moderate",
        indicators=["SMA_50", "SMA_200", "ADX"],
        description="Follow the dominant trend with moving average confirmation",
    ),
    Graha.CHANDRA: StrategyProfile(
        graha=Graha.CHANDRA,
        strategy_type="mean_reversion",
        time_horizon="day",
        risk_profile="moderate",
        indicators=["RSI", "Bollinger_Bands", "Sentiment"],
        description="Counter-trend trading based on sentiment extremes",
    ),
    Graha.MANGALA: StrategyProfile(
        graha=Graha.MANGALA,
        strategy_type="momentum_breakout",
        time_horizon="scalping",
        risk_profile="aggressive",
        indicators=["Volume_Spike", "ATR", "Breakout_Levels"],
        description="Aggressive breakout trading on volume spikes",
    ),
    Graha.BUDHA: StrategyProfile(
        graha=Graha.BUDHA,
        strategy_type="arbitrage",
        time_horizon="scalping",
        risk_profile="moderate",
        indicators=["Price_Delta", "Latency", "Orderbook_Imbalance"],
        description="Statistical arbitrage and cross-exchange price exploitation",
    ),
    Graha.GURU: StrategyProfile(
        graha=Graha.GURU,
        strategy_type="growth",
        time_horizon="long_term",
        risk_profile="conservative",
        indicators=[["Fundamentals", "PEG_Ratio", "Revenue_Growth"]],
        description="Long-term growth investing based on fundamentals",
    ),
    Graha.SHUKRA: StrategyProfile(
        graha=Graha.SHUKRA,
        strategy_type="value",
        time_horizon="swing",
        risk_profile="conservative",
        indicators=["P/E", "P/B", "Dividend_Yield"],
        description="Value investing with quality focus",
    ),
    Graha.SHANI: StrategyProfile(
        graha=Graha.SHANI,
        strategy_type="risk_managed",
        time_horizon="swing",
        risk_profile="conservative",
        indicators=[["VaR", "Position_Size", "Stop_Loss"]],
        description="Disciplined trading with strict risk controls",
    ),
    Graha.RAHU: StrategyProfile(
        graha=Graha.RAHU,
        strategy_type="contrarian",
        time_horizon="day",
        risk_profile="aggressive",
        indicators=[["Extreme_Sentiment", "Reversal_Patterns"]],
        description="Contrarian plays against extreme positioning",
    ),
    Graha.KETU: StrategyProfile(
        graha=Graha.KETU,
        strategy_type="exit",
        time_horizon="scalping",
        risk_profile="conservative",
        indicators=[["Momentum_Divergence", "Volume_Decline"]],
        description="Exit signals and profit taking",
    ),
}


class DashaStrategySelector:
    """
    Selects trading strategies based on Dasha (planetary period) system.

    In Vedic astrology, Dashas are planetary periods that influence
    life events and tendencies. We map these to trading strategies.
    """

    def __init__(self):
        """Initialize Dasha strategy selector."""
        self.active_graha: Optional[Graha] = None
        self.dasha_weights: Dict[Graha, float] = {g: 0.0 for g in Graha}

    def update_dasha(
        self,
        maha_dasha: Graha,  # Major period
        antar_dasha: Graha,  # Sub-period
        pratyantar_dasha: Graha,  # Sub-sub-period
    ) -> None:
        """
        Update current Dasha periods.

        Args:
            maha_dasha: Major planetary period (years)
            antar_dasha: Sub-period (months)
            pratyantar_dasha: Sub-sub-period (days)
        """
        # Weight by period level
        self.dasha_weights = {g: 0.0 for g in Graha}

        self.dasha_weights[maha_dasha] += 0.6
        self.dasha_weights[antar_dasha] += 0.3
        self.dasha_weights[pratyantar_dasha] += 0.1

        # Determine dominant Graha
        self.active_graha = max(self.dasha_weights, key=self.dasha_weights.get)

        logger.info(
            f"Dasha updated: Maha={maha_dasha.value}, "
            f"Antar={antar_dasha.value}, "
            f"Active={self.active_graha.value}"
        )

    def get_active_strategy(self) -> StrategyProfile:
        """Get strategy profile for active Graha."""
        if self.active_graha is None:
            # Default to Budha (Mercury) for analytical trading
            return GRAHA_STRATEGIES[Graha.BUDHA]

        return GRAHA_STRATEGIES[self.active_graha]

    def get_strategy_blend(self) -> Dict[str, float]:
        """
        Get weighted blend of strategies based on Dasha weights.

        Returns:
            Dictionary mapping strategy types to weights
        """
        blend = {}

        for graha, weight in self.dasha_weights.items():
            if weight > 0:
                strategy_type = GRAHA_STRATEGIES[graha].strategy_type
                blend[strategy_type] = blend.get(strategy_type, 0.0) + weight

        # Normalize
        total = sum(blend.values())
        if total > 0:
            blend = {k: v / total for k, v in blend.items()}

        return blend

    def is_budha_active(self) -> bool:
        """Check if Budha (Mercury) is active - for arbitrage strategies."""
        return self.active_graha == Graha.BUDHA or self.dasha_weights[Graha.BUDHA] > 0.3

    def get_arbitrage_confidence(self) -> float:
        """
        Get confidence level for arbitrage strategies.

        Returns:
            Confidence based on Budha's influence
        """
        budha_weight = self.dasha_weights.get(Graha.BUDHA, 0.0)

        # Scale to 0.5 - 0.95 range
        confidence = 0.5 + (budha_weight * 0.45)

        return min(confidence, 0.95)


class TransitAnalyzer:
    """
    Analyzes planetary transits for trading timing.

    Transits are current planetary positions relative to birth chart.
    They indicate short-term influences on trading performance.
    """

    def __init__(self):
        """Initialize transit analyzer."""
        self.transit_aspects: List[Dict] = []

    def analyze_transit(
        self,
        planet: Graha,
        position: float,  # Degrees
        natal_positions: Dict[Graha, float],
    ) -> Dict:
        """
        Analyze transit of a planet.

        Args:
            planet: Transiting planet
            position: Current position in degrees
            natal_positions: Natal chart positions

        Returns:
            Transit analysis
        """
        aspects = []

        for natal_planet, natal_pos in natal_positions.items():
            angle = abs(position - natal_pos)

            # Check major aspects
            if angle < 10 or angle > 350:
                aspects.append(
                    {"planet": natal_planet, "aspect": "conjunction", "angle": angle}
                )
            elif 170 < angle < 190:
                aspects.append(
                    {"planet": natal_planet, "aspect": "opposition", "angle": angle}
                )
            elif 110 < angle < 130:
                aspects.append(
                    {"planet": natal_planet, "aspect": "trine", "angle": angle}
                )

        return {
            "transiting_planet": planet,
            "aspects": aspects,
            "trading_implication": self._get_implication(planet, aspects),
        }

    def _get_implication(self, planet: Graha, aspects: List[Dict]) -> str:
        """Get trading implication of transit."""
        if not aspects:
            return "neutral"

        # Budha aspects favor analysis/arbitrage
        if planet == Graha.BUDHA:
            return "favorable_for_analysis"

        # Mangala aspects favor action/breakouts
        if planet == Graha.MANGALA:
            return "favorable_for_breakouts"

        # Shani aspects favor caution/risk_management
        if planet == Graha.SHANI:
            return "favorable_for_risk_management"

        return "neutral"


def get_budha_arbitrage_config() -> Dict:
    """
    Get arbitrage configuration optimized for Budha Graha.

    Returns:
        Configuration dict for arbitrage strategy
    """
    return {
        "enabled": True,
        "min_profit_pct": 0.05,  # Lower threshold for analytical precision
        "max_positions": 5,
        "time_horizon": "scalping",
        "risk_per_trade": 0.01,
        "indicators": ["price_delta", "latency", "orderbook_imbalance"],
        "description": "Budha-inspired analytical arbitrage",
    }


# Convenience function for strategy factory
def create_strategy_for_graha(graha: Graha) -> StrategyProfile:
    """Create strategy profile for a specific Graha."""
    return GRAHA_STRATEGIES.get(graha, GRAHA_STRATEGIES[Graha.BUDHA])
