"""
Buddhi Mind - Final Decision Making

Buddhi is the discriminating intelligence that:
1. Weighs all council perspectives
2. Resolves contradictions
3. Applies risk management
4. Makes final trading decisions

"Buddhi is the seat of decision-making; it is the I that decides."
"""

import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class Action(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class BuddhiDecision:
    """Final decision from Buddhi Mind."""

    action: str
    confidence: float
    coherence: float
    rationale: str
    council_views: list[dict]
    risk_assessment: dict
    session_id: str
    timestamp: str

    def is_executable(self) -> bool:
        """Check if decision meets execution thresholds."""
        return self.confidence >= 0.6 and self.coherence >= 0.5 and self.action != Action.HOLD.value


class BuddhiMind:
    """
    Buddhi Mind - The discriminating decision maker.

    Process:
    1. Collect council views
    2. Calculate weighted consensus
    3. Check coherence
    4. Apply risk filters
    5. Make final decision
    """

    def __init__(self):
        # Minimum thresholds for action
        self.min_confidence = 0.60
        self.min_coherence = 0.50
        self.max_position_size = 0.10  # 10% of portfolio max

        # Council weights (can be adjusted based on performance)
        self.council_weights = {
            "guna": 0.35,
            "mind": 0.30,
            "body": 0.25,
            "elemental": 0.10,  # Placeholder
            "graha": 0.00,  # Not implemented yet
        }

    def decide(
        self, council_views: list[dict], market_data: dict, session_id: str, timestamp: str
    ) -> BuddhiDecision:
        """
        Make final trading decision based on council inputs.

        Args:
            council_views: List of council perspectives
            market_data: Current market conditions
            session_id: Trading session ID
            timestamp: Decision timestamp

        Returns:
            BuddhiDecision object
        """
        logger.info(f"Buddhi deciding for session {session_id}")

        # Calculate coherence
        coherence = self._calculate_coherence(council_views)

        # Weighted perspective calculation
        weighted_perspective, confidence = self._weigh_perspectives(council_views)

        # Check for contradictions
        contradictions = self._find_contradictions(council_views)

        # Risk assessment
        risk = self._assess_risk(council_views, market_data, coherence)

        # Make final decision
        if contradictions and coherence < 0.4:
            # High disagreement - hold
            action = Action.HOLD.value
            rationale = f"High council disagreement: {contradictions[0]}"
            confidence *= 0.8  # Reduce confidence

        elif risk["level"] == "high":
            # High risk - hold
            action = Action.HOLD.value
            rationale = f"Risk limit: {risk['primary_concern']}"

        elif confidence < self.min_confidence:
            # Low confidence - hold
            action = Action.HOLD.value
            rationale = f"Confidence {confidence:.2f} below threshold {self.min_confidence}"

        elif coherence < self.min_coherence:
            # Low coherence - hold
            action = Action.HOLD.value
            rationale = f"Coherence {coherence:.2f} below threshold {self.min_coherence}"

        else:
            # All checks passed - take action
            action = weighted_perspective
            rationale = self._build_rationale(council_views, weighted_perspective, coherence)

        # Build decision
        decision = BuddhiDecision(
            action=action,
            confidence=round(confidence, 3),
            coherence=round(coherence, 3),
            rationale=rationale,
            council_views=[
                {
                    "council": v.get("council_type", v.get("council")),
                    "perspective": v.get("perspective"),
                    "confidence": v.get("confidence"),
                }
                for v in council_views
            ],
            risk_assessment=risk,
            session_id=session_id,
            timestamp=timestamp,
        )

        logger.info(f"Buddhi decision: {action} (conf: {confidence:.2f}, coh: {coherence:.2f})")

        return decision

    def _calculate_coherence(self, views: list[dict]) -> float:
        """
        Calculate coherence (agreement) between councils.

        Returns 0-1, where 1 = perfect agreement.
        """
        if len(views) < 2:
            return 1.0

        # Map perspectives to numeric scores
        scores = []
        for view in views:
            p = view.get("perspective", "neutral")
            if p == "bullish":
                scores.append(1.0)
            elif p == "bearish":
                scores.append(0.0)
            else:  # neutral
                scores.append(0.5)

        # Calculate variance
        mean = sum(scores) / len(scores)
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)

        # Convert to coherence (1 - normalized variance)
        # Max variance for 3 values (0, 0.5, 1) is about 0.22
        coherence = 1.0 - (variance * 4.5)

        return max(0.0, min(1.0, coherence))

    def _weigh_perspectives(self, views: list[dict]) -> tuple:
        """
        Calculate weighted perspective from council views.

        Returns: (perspective, confidence)
        """
        if not views:
            return "neutral", 0.0

        # Calculate weighted scores
        bullish_weight = 0.0
        bearish_weight = 0.0
        total_weight = 0.0

        for view in views:
            council_type = view.get("council_type", view.get("council"))
            weight = self.council_weights.get(council_type, 0.2)
            confidence = view.get("confidence", 0.5)

            weighted = weight * confidence
            total_weight += weighted

            perspective = view.get("perspective", "neutral")
            if perspective == "bullish":
                bullish_weight += weighted
            elif perspective == "bearish":
                bearish_weight += weighted

        if total_weight == 0:
            return "neutral", 0.0

        # Determine winner
        bullish_score = bullish_weight / total_weight
        bearish_score = bearish_weight / total_weight
        neutral_score = 1.0 - bullish_score - bearish_score

        # Threshold for action
        if bullish_score > bearish_score and bullish_score > 0.5:
            return "bullish", bullish_score
        elif bearish_score > bullish_score and bearish_score > 0.5:
            return "bearish", bearish_score
        else:
            return "neutral", max(neutral_score, 0.5)

    def _find_contradictions(self, views: list[dict]) -> list[str]:
        """Find contradictions between council views."""
        contradictions = []

        perspectives = [v.get("perspective") for v in views]

        if "bullish" in perspectives and "bearish" in perspectives:
            contradictions.append("Direct conflict: bullish vs bearish")

        # Check for extreme confidence disagreements
        confidences = [v.get("confidence", 0.5) for v in views]
        if len(confidences) >= 2:
            conf_diff = max(confidences) - min(confidences)
            if conf_diff > 0.5:
                contradictions.append(f"Large confidence gap: {conf_diff:.2f}")

        return contradictions

    def _assess_risk(self, views: list[dict], market_data: dict, coherence: float) -> dict:
        """Assess risk level based on market conditions and council inputs."""
        concerns = []
        risk_score = 0.0

        # High volatility = risk
        vol = market_data.get("volatility_1m", 0.02)
        if vol > 0.05:  # > 5% vol
            risk_score += 0.3
            concerns.append("High volatility")

        # Low coherence = risk (councils disagree)
        if coherence < 0.4:
            risk_score += 0.3
            concerns.append("Council disagreement")

        # Body council warning
        body_view = next((v for v in views if v.get("council_type") == "body"), None)
        if body_view and body_view.get("perspective") == "avoid":
            risk_score += 0.4
            concerns.append("Poor execution conditions")

        # Mind council extreme fear/greed
        mind_view = next((v for v in views if v.get("council_type") == "mind"), None)
        if mind_view and mind_view.get("metadata", {}).get("fear_greed_index"):
            fg = mind_view["metadata"]["fear_greed_index"]
            if fg < 20 or fg > 80:
                risk_score += 0.2
                concerns.append("Extreme sentiment")

        # Determine risk level
        if risk_score >= 0.6:
            level = "high"
        elif risk_score >= 0.3:
            level = "medium"
        else:
            level = "low"

        return {
            "level": level,
            "score": round(risk_score, 2),
            "concerns": concerns,
            "primary_concern": concerns[0] if concerns else "None",
        }

    def _build_rationale(self, views: list[dict], perspective: str, coherence: float) -> str:
        """Build human-readable rationale for the decision."""
        parts = []

        # Council consensus
        agreeing = [v for v in views if v.get("perspective") == perspective]
        if agreeing:
            councils = ", ".join([v.get("council_type", v.get("council")) for v in agreeing])
            parts.append(f"{councils} signal {perspective}")

        # Coherence note
        if coherence > 0.7:
            parts.append("Strong council consensus")
        elif coherence > 0.5:
            parts.append("Moderate agreement")

        return "; ".join(parts)


# Singleton
_buddhi_mind = None


def get_buddhi_mind():
    """Get singleton instance."""
    global _buddhi_mind
    if _buddhi_mind is None:
        _buddhi_mind = BuddhiMind()
    return _buddhi_mind


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("BUDDHI MIND - TEST")
    print("=" * 60)

    buddhi = get_buddhi_mind()

    # Test scenarios
    scenarios = [
        (
            "Strong bullish consensus",
            [
                {"council_type": "guna", "perspective": "bullish", "confidence": 0.85},
                {"council_type": "mind", "perspective": "bullish", "confidence": 0.75},
                {"council_type": "body", "perspective": "favorable", "confidence": 0.90},
            ],
            {"volatility_1m": 0.025},
        ),
        (
            "Mixed signals",
            [
                {"council_type": "guna", "perspective": "bullish", "confidence": 0.70},
                {"council_type": "mind", "perspective": "bearish", "confidence": 0.65},
            ],
            {"volatility_1m": 0.04},
        ),
        (
            "High risk",
            [
                {"council_type": "guna", "perspective": "bullish", "confidence": 0.80},
                {"council_type": "body", "perspective": "avoid", "confidence": 0.70},
            ],
            {"volatility_1m": 0.08},
        ),
    ]

    from datetime import datetime

    for name, views, market in scenarios:
        print(f"\n{name}:")
        decision = buddhi.decide(views, market, "test", datetime.utcnow().isoformat())

        print(f"  Action: {decision.action.upper()}")
        print(f"  Confidence: {decision.confidence:.2f}")
        print(f"  Coherence: {decision.coherence:.2f}")
        print(f"  Risk: {decision.risk_assessment['level']}")
        print(f"  Rationale: {decision.rationale}")
        print(f"  Executable: {decision.is_executable()}")
