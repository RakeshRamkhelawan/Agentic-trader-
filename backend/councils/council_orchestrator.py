"""
Council Orchestrator

Coördineert alle councils, berekent coherence, en publiceert events.
Integratie punt tussen councils en de event bus.
"""

import asyncio
import logging
from dataclasses import dataclass

from backend.councils.dynamic_guna_council import get_guna_council
from backend.councils.mind_council import get_mind_council
from backend.events.triad_event_bus import publish_decision, publish_deliberation

logger = logging.getLogger(__name__)


@dataclass
class CouncilView:
    """View van een council."""
    council_type: str
    perspective: str  # bullish, bearish, neutral
    confidence: float
    key_insights: list[str]
    metadata: dict  # Extra data (guna_vector, fear_greed, etc.)


class CouncilOrchestrator:
    """
    Orchestrates alle councils en berekent coherence.

    Usage:
        orchestrator = CouncilOrchestrator()
        result = await orchestrator.deliberate(market_data)
        # Publishes events automatically
    """

    def __init__(self):
        self.guna_council = get_guna_council()
        self.mind_council = get_mind_council()

        # Council weights (kan dynamisch worden aangepast)
        self.weights = {
            "guna": 0.35,
            "mind": 0.30,
            "elemental": 0.15,  # Placeholder
            "body": 0.10,       # Placeholder
            "graha": 0.10       # Placeholder
        }

    async def deliberate(self, market_data: dict, session_id: str = "default") -> dict:
        """
        Run deliberatie over alle councils.

        Args:
            market_data: Market microstructure data
            session_id: Trading session ID

        Returns:
            Dict met council_views, coherence, final_perspective
        """
        logger.info(f"Starting council deliberation for session {session_id}")

        # Collect views from all councils
        council_views = []

        # Guna Council
        try:
            guna_result = self.guna_council.analyze(market_data)
            guna_view = CouncilView(
                council_type="guna",
                perspective=guna_result["perspective"],
                confidence=guna_result["confidence"],
                key_insights=guna_result["key_insights"],
                metadata={"guna_vector": guna_result.get("guna_vector", {})}
            )
            council_views.append(guna_view)

            # Publish event
            await publish_deliberation(
                council_type="guna",
                perspective=guna_result["perspective"],
                confidence=guna_result["confidence"],
                reasoning="; ".join(guna_result["key_insights"]),
                metadata=guna_result.get("guna_vector", {})
            )

        except Exception as e:
            logger.error(f"Guna Council error: {e}")

        # Mind Council
        try:
            mind_result = self.mind_council.analyze(market_data)
            mind_view = CouncilView(
                council_type="mind",
                perspective=mind_result["perspective"],
                confidence=mind_result["confidence"],
                key_insights=mind_result["key_insights"],
                metadata={
                    "fear_greed_index": mind_result.get("fear_greed_index"),
                    "components": mind_result.get("components", {})
                }
            )
            council_views.append(mind_view)

            # Publish event
            await publish_deliberation(
                council_type="mind",
                perspective=mind_result["perspective"],
                confidence=mind_result["confidence"],
                reasoning=f"Fear/Greed: {mind_result.get('fear_greed_index', 50)}",
                metadata=mind_result.get("components", {})
            )

        except Exception as e:
            logger.error(f"Mind Council error: {e}")

        # Bereken coherence
        coherence = self._calculate_coherence(council_views)

        # Bepaal final perspective (weighted majority)
        final_perspective, final_confidence = self._weigh_perspectives(council_views)

        # Log decision
        logger.info(f"Deliberation complete: {final_perspective} (coherence: {coherence:.2f})")

        result = {
            "session_id": session_id,
            "council_views": [
                {
                    "council": v.council_type,
                    "perspective": v.perspective,
                    "confidence": v.confidence,
                    "insights": v.key_insights[:2]  # Top 2 insights
                }
                for v in council_views
            ],
            "coherence": coherence,
            "final_perspective": final_perspective,
            "final_confidence": final_confidence,
            "timestamp": asyncio.get_event_loop().time()
        }

        # Publish final decision event
        await publish_decision(
            action=final_perspective if final_perspective != "neutral" else "hold",
            confidence=final_confidence,
            coherence=coherence,
            rationale=f"Weighted consensus: {final_perspective}",
            council_views=result["council_views"],
            session_id=session_id
        )

        return result

    def _calculate_coherence(self, views: list[CouncilView]) -> float:
        """
        Bereken mate van overeenstemming tussen councils.

        Returns 0.0 - 1.0, waar 1.0 = perfecte consensus.
        """
        if len(views) < 2:
            return 1.0  # Single council = perfect coherence

        # Map perspectives to scores
        perspective_scores = {
            "bullish": 1.0,
            "neutral": 0.5,
            "bearish": 0.0
        }

        scores = [perspective_scores.get(v.perspective, 0.5) for v in views]

        # Bereken variance (lower = higher coherence)
        mean_score = sum(scores) / len(scores)
        variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)

        # Convert to coherence (0-1)
        # Max variance = 0.25 (when we have 0 and 1)
        coherence = 1.0 - (variance * 4)  # Scale to 0-1

        return max(0.0, min(1.0, coherence))

    def _weigh_perspectives(self, views: list[CouncilView]) -> tuple:
        """
        Weeg perspectieven op basis van council weights en confidence.

        Returns: (perspective, confidence)
        """
        if not views:
            return "neutral", 0.0

        # Calculate weighted scores
        bullish_score = 0.0
        bearish_score = 0.0
        total_weight = 0.0

        for view in views:
            weight = self.weights.get(view.council_type, 0.2) * view.confidence
            total_weight += weight

            if view.perspective == "bullish":
                bullish_score += weight
            elif view.perspective == "bearish":
                bearish_score += weight
            # Neutral doesn't add to either

        if total_weight == 0:
            return "neutral", 0.0

        # Normalize
        bullish_norm = bullish_score / total_weight
        bearish_norm = bearish_score / total_weight
        neutral_norm = 1.0 - bullish_norm - bearish_norm

        # Determine winner
        if bullish_norm > bearish_norm and bullish_norm > neutral_norm:
            return "bullish", bullish_norm
        elif bearish_norm > bullish_norm and bearish_norm > neutral_norm:
            return "bearish", bearish_norm
        else:
            return "neutral", neutral_norm

    def update_council_weight(self, council_type: str, new_weight: float):
        """
        Update weight voor een council (bijv. na performance evaluatie).
        """
        if council_type in self.weights:
            self.weights[council_type] = max(0.0, min(1.0, new_weight))
            logger.info(f"Updated {council_type} weight to {new_weight}")


# Singleton
_orchestrator = None


def get_orchestrator():
    """Get singleton instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = CouncilOrchestrator()
    return _orchestrator


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("COUNCIL ORCHESTRATOR - TEST")
    print("=" * 60)

    async def test():
        orchestrator = get_orchestrator()

        # Test scenarios
        scenarios = [
            ("Strong uptrend", {
                "volatility_1m": 0.035, "momentum_1d": 0.04,
                "volume_ratio": 1.8, "bid_ask_spread": 0.001,
                "trend": 1, "imbalance": 0.4
            }),
            ("Crash", {
                "volatility_1m": 0.07, "momentum_1d": -0.06,
                "volume_ratio": 2.8, "bid_ask_spread": 0.004,
                "trend": -1, "imbalance": -0.5
            }),
        ]

        for name, data in scenarios:
            print(f"\n{name}:")
            result = await orchestrator.deliberate(data, f"test_{name.lower().replace(' ', '_')}")

            print(f"  Final: {result['final_perspective']} (conf: {result['final_confidence']:.2f})")
            print(f"  Coherence: {result['coherence']:.2f}")
            print("  Councils:")
            for view in result['council_views']:
                print(f"    {view['council']}: {view['perspective']} (conf: {view['confidence']:.2f})")

    asyncio.run(test())
