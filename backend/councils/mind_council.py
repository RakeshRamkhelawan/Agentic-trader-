"""
Mind Council - Market Psychology Analysis

Analyseert marktpsychologie (Fear/Greed) gebruikmakend van:
- Price momentum (extreme moves = emotion)
- Volume patterns (spikes = fear or greed)
- Volatility expansion (uncertainty/fear)
- Bid-ask spread (liquidity stress)

Output: Fear/Greed Index (0-100) + trading perspective
"""

import logging

logger = logging.getLogger(__name__)


class MindCouncil:
    """
    Mind Council analyseert marktpsychologie.

    Fear/Greed Index:
    0-20   : Extreme Fear (contrarian bullish)
    20-40  : Fear (caution)
    40-60  : Neutral
    60-80  : Greed (caution)
    80-100 : Extreme Greed (contrarian bearish)
    """

    def __init__(self):
        # Weights for fear/greed calculation
        self.weights = {
            "momentum": 0.25,
            "volatility": 0.25,
            "volume": 0.20,
            "spread": 0.15,
            "imbalance": 0.15,
        }

    def analyze(self, market_data: dict) -> dict:
        """
        Analyseer marktpsychologie.

        Args:
            market_data: Dict met market metrics

        Returns:
            Dict met fear_greed_index, perspective, confidence, insights
        """
        # Calculate components
        momentum_score = self._calc_momentum_component(market_data)
        volatility_score = self._calc_volatility_component(market_data)
        volume_score = self._calc_volume_component(market_data)
        spread_score = self._calc_spread_component(market_data)
        imbalance_score = self._calc_imbalance_component(market_data)

        # Weighted average (0-100)
        fear_greed = (
            momentum_score * self.weights["momentum"]
            + volatility_score * self.weights["volatility"]
            + volume_score * self.weights["volume"]
            + spread_score * self.weights["spread"]
            + imbalance_score * self.weights["imbalance"]
        )

        # Clamp to 0-100
        fear_greed = max(0, min(100, fear_greed))

        # Determine perspective (contrarian strategy)
        perspective, confidence, insight = self._get_perspective(fear_greed, market_data)

        return {
            "council_type": "mind",
            "fear_greed_index": round(fear_greed, 1),
            "perspective": perspective,
            "confidence": round(confidence, 3),
            "key_insights": self._generate_insights(
                fear_greed, momentum_score, volatility_score, volume_score, imbalance_score, insight
            ),
            "components": {
                "momentum": round(momentum_score, 1),
                "volatility": round(volatility_score, 1),
                "volume": round(volume_score, 1),
                "spread": round(spread_score, 1),
                "imbalance": round(imbalance_score, 1),
            },
        }

    def _calc_momentum_component(self, data: dict) -> float:
        """
        Extreme price moves indicate greed (up) or fear (down).
        Returns 0-100 score.
        """
        momentum_1d = data.get("momentum_1d", 0)
        momentum_3d = data.get("momentum_3d", 0)

        # Use max absolute momentum
        max_momentum = max(abs(momentum_1d), abs(momentum_3d) / 3)

        # Score: 0% move = 50 (neutral), 10% move = 100 (extreme)
        if max_momentum > 0.10:  # > 10% move
            return 100.0 if momentum_1d > 0 else 0.0
        elif max_momentum > 0.05:  # > 5% move
            return 80.0 if momentum_1d > 0 else 20.0
        elif max_momentum > 0.02:  # > 2% move
            return 65.0 if momentum_1d > 0 else 35.0
        else:
            return 50.0

    def _calc_volatility_component(self, data: dict) -> float:
        """
        High volatility typically indicates fear.
        Returns 0-100 (high vol = low score = fear).
        """
        vol = data.get("volatility_1m", 0.02)

        # Higher vol = more fear (lower score)
        if vol > 0.06:  # Extreme vol
            return 10.0
        elif vol > 0.04:  # High vol
            return 25.0
        elif vol > 0.025:  # Elevated vol
            return 40.0
        elif vol < 0.015:  # Very low vol (complacency = slight greed)
            return 60.0
        else:
            return 50.0

    def _calc_volume_component(self, data: dict) -> float:
        """
        Volume spikes indicate emotion.
        Returns 0-100.
        """
        vol_ratio = data.get("volume_ratio", 1.0)

        if vol_ratio > 3.0:  # Extreme volume
            return 90.0
        elif vol_ratio > 2.0:  # Very high volume
            return 75.0
        elif vol_ratio > 1.5:  # High volume
            return 65.0
        elif vol_ratio < 0.5:  # Very low volume (disinterest)
            return 45.0
        else:
            return 50.0

    def _calc_spread_component(self, data: dict) -> float:
        """
        Wide spreads indicate fear/uncertainty (low liquidity).
        Returns 0-100 (wide spread = low score).
        """
        spread = data.get("bid_ask_spread", 0.001)

        if spread > 0.005:  # Extreme spread
            return 10.0
        elif spread > 0.002:  # Wide spread
            return 30.0
        elif spread > 0.001:  # Elevated spread
            return 45.0
        else:  # Tight spread (confidence)
            return 60.0

    def _calc_imbalance_component(self, data: dict) -> float:
        """
        Order flow imbalance indicates buying (greed) or selling (fear) pressure.
        Returns 0-100.
        """
        imbalance = data.get("imbalance", 0)  # -1 to 1

        # Map -1..1 to 0..100
        # -1 (all selling) = 0 (extreme fear)
        # +1 (all buying) = 100 (extreme greed)
        return (imbalance + 1) * 50

    def _get_perspective(self, fear_greed: float, data: dict) -> tuple[str, float, str]:
        """
        Contrarian strategy: extreme readings = reversal signals.
        """
        momentum = data.get("momentum_1d", 0)

        if fear_greed < 15:  # Extreme fear
            if momentum < -0.05:  # Capitulation
                return "bullish", 0.75, "Extreme fear with capitulation - potential bottom"
            else:
                return "neutral", 0.6, "Extreme fear - wait for exhaustion"

        elif fear_greed < 30:  # Fear
            return "neutral", 0.55, "Fear present - cautious"

        elif fear_greed > 85:  # Extreme greed
            if momentum > 0.05:  # Euphoria
                return "bearish", 0.70, "Extreme greed with euphoria - risk of reversal"
            else:
                return "neutral", 0.6, "Extreme greed - distribution possible"

        elif fear_greed > 70:  # Greed
            return "neutral", 0.55, "Greed present - take profits"

        else:  # Neutral zone
            return "neutral", 0.5, "Balanced sentiment - wait for setup"

    def _generate_insights(
        self,
        fear_greed: float,
        momentum_c: float,
        volatility_c: float,
        volume_c: float,
        imbalance_c: float,
        primary_insight: str,
    ) -> list[str]:
        """Generate detailed insights."""
        insights = [primary_insight]

        # Add component insights
        if volatility_c < 30:
            insights.append(f"High volatility ({volatility_c:.0f}) suggests fear")

        if volume_c > 70:
            insights.append(f"Volume spike ({volume_c:.0f}) indicates emotional trading")

        if abs(imbalance_c - 50) > 20:
            side = "buying" if imbalance_c > 50 else "selling"
            insights.append(f"Strong {side} pressure detected")

        # Interpretation
        if fear_greed < 20:
            insights.append("Consider contrarian long positions")
        elif fear_greed > 80:
            insights.append("Consider taking profits or hedging")

        return insights

    def get_sentiment_label(self, fear_greed: float) -> str:
        """Get human-readable sentiment label."""
        if fear_greed < 20:
            return "Extreme Fear"
        elif fear_greed < 40:
            return "Fear"
        elif fear_greed < 60:
            return "Neutral"
        elif fear_greed < 80:
            return "Greed"
        else:
            return "Extreme Greed"


# Singleton
mind_council = None


def get_mind_council():
    """Get singleton instance."""
    global mind_council
    if mind_council is None:
        mind_council = MindCouncil()
    return mind_council


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("MIND COUNCIL - TEST")
    print("=" * 60)

    council = get_mind_council()

    scenarios = [
        (
            "Capitulation",
            {
                "momentum_1d": -0.08,
                "momentum_3d": -0.15,
                "volatility_1m": 0.07,
                "volume_ratio": 3.0,
                "bid_ask_spread": 0.004,
                "imbalance": -0.6,
            },
        ),
        (
            "Euphoria",
            {
                "momentum_1d": 0.12,
                "momentum_3d": 0.25,
                "volatility_1m": 0.05,
                "volume_ratio": 2.5,
                "bid_ask_spread": 0.001,
                "imbalance": 0.7,
            },
        ),
        (
            "Calm",
            {
                "momentum_1d": 0.005,
                "momentum_3d": 0.01,
                "volatility_1m": 0.018,
                "volume_ratio": 0.9,
                "bid_ask_spread": 0.0005,
                "imbalance": 0.05,
            },
        ),
    ]

    for name, data in scenarios:
        print(f"\n{name}:")
        result = council.analyze(data)
        label = council.get_sentiment_label(result["fear_greed_index"])
        print(f"  Fear/Greed: {result['fear_greed_index']:.0f} ({label})")
        print(f"  Perspective: {result['perspective']} (conf: {result['confidence']:.2f})")
        print(
            f"  Components: M={result['components']['momentum']:.0f}, "
            f"V={result['components']['volatility']:.0f}, "
            f"Vol={result['components']['volume']:.0f}"
        )
