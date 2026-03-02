"""
Elemental Consensus Agent - 4-element voting system.

This agent implements the Pancha Mahabhuta (5 great elements) consensus
system where Fire, Earth, Water, and Air elements vote on trading decisions.
Ether provides the final consensus.
"""

import logging
from typing import Any

from backend.agents.agent_with_tools import AgentWithTools
from backend.governance.agent_gatekeeper import AgentRole

logger = logging.getLogger(__name__)


class ElementalConsensusAgent(AgentWithTools):
    """
    Agent that uses 4-element voting for trading decisions.

    Elements:
    - Fire (Agni): Momentum, position sizing
    - Earth (Prithvi): Entry/exit timing, stability
    - Water (Apas): Trend following, adaptability
    - Air (Vayu): Market regime, volatility
    - Ether (Akasha): Final consensus and coordination
    """

    def __init__(
        self,
        agent_name: str = "elemental_consensus",
        tool_broker_url: str | None = None,
        consensus_threshold: float = 0.6,
        **kwargs,
    ):
        super().__init__(
            agent_name=agent_name,
            agent_role=AgentRole.STRATEGIST,
            tool_broker_url=tool_broker_url,
            **kwargs,
        )
        self.consensus_threshold = consensus_threshold
        logger.info(f"{agent_name} initialized with threshold={consensus_threshold}")

    async def analyze(self, features: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze features using 4-element voting system.

        Args:
            features: Must contain 'symbol', 'price', and optionally:
                     - 'fire_vote': Fire element score (-1 to 1)
                     - 'earth_vote': Earth element score (-1 to 1)
                     - 'water_vote': Water element score (-1 to 1)
                     - 'air_vote': Air element score (-1 to 1)
            context: Additional context for decision making

        Returns:
            Trading decision based on elemental consensus
        """
        symbol = features.get("symbol", "BTC")
        price = features.get("price", 0.0)

        # Get element votes from features or use defaults
        fire_vote = features.get("fire_vote", 0.0)
        earth_vote = features.get("earth_vote", 0.0)
        water_vote = features.get("water_vote", 0.0)
        air_vote = features.get("air_vote", 0.0)

        # Validate votes are in range [-1, 1]
        votes = {
            "fire": max(-1.0, min(1.0, fire_vote)),
            "earth": max(-1.0, min(1.0, earth_vote)),
            "water": max(-1.0, min(1.0, water_vote)),
            "air": max(-1.0, min(1.0, air_vote)),
        }

        try:
            # Get elemental consensus via MCP
            consensus_result = await self.get_elemental_consensus(
                votes["fire"], votes["earth"], votes["water"], votes["air"]
            )

            if not consensus_result.get("success", False):
                error = consensus_result.get("error", "Unknown error")
                logger.error(f"Elemental consensus failed: {error}")
                return {
                    "action": "hold",
                    "confidence": 0.0,
                    "reason": f"Consensus error: {error}",
                    "element_votes": votes,
                }

            consensus_data = consensus_result.get("result", {})
            consensus_score = consensus_data.get("consensus_score", 0.0)
            consensus_signal = consensus_data.get("consensus_signal", "hold")

            # Map consensus signal to action
            action_map = {
                "strong_buy": "buy",
                "buy": "buy",
                "hold": "hold",
                "sell": "sell",
                "strong_sell": "sell",
            }
            action = action_map.get(consensus_signal, "hold")

            # Check consensus threshold
            if abs(consensus_score) < self.consensus_threshold:
                logger.info(
                    f"Consensus score {consensus_score} below threshold {self.consensus_threshold}"
                )
                return {
                    "action": "hold",
                    "confidence": abs(consensus_score),
                    "reason": f"Weak consensus ({consensus_score:.2f}) - holding",
                    "element_votes": votes,
                    "consensus_data": consensus_data,
                }

            # Build detailed reasoning
            vote_descriptions = []
            for element, vote in votes.items():
                if vote > 0.3:
                    vote_descriptions.append(f"{element.title()}: bullish ({vote:+.2f})")
                elif vote < -0.3:
                    vote_descriptions.append(f"{element.title()}: bearish ({vote:+.2f})")
                else:
                    vote_descriptions.append(f"{element.title()}: neutral ({vote:+.2f})")

            reason = f"Elemental consensus: {consensus_signal} (score: {consensus_score:+.2f}). "
            reason += "Votes: " + ", ".join(vote_descriptions)

            logger.info(
                f"{self.agent_name}: {action} {symbol} @ {price} (consensus: {consensus_score:.2f})"
            )

            return {
                "action": action,
                "confidence": abs(consensus_score),
                "reason": reason,
                "element_votes": votes,
                "consensus_data": consensus_data,
                "dominant_element": consensus_data.get("dominant_element"),
                "suppressed_element": consensus_data.get("suppressed_element"),
            }

        except Exception as e:
            logger.exception(f"Error in elemental analysis: {e}")
            return {
                "action": "hold",
                "confidence": 0.0,
                "reason": f"Analysis error: {str(e)}",
                "element_votes": votes,
            }

    async def analyze_with_indicators(
        self, symbol: str, price: float, indicators: dict[str, float]
    ) -> dict[str, Any]:
        """
        Analyze using technical indicators to generate element votes.

        Args:
            symbol: Asset symbol
            price: Current price
            indicators: Dict with keys like 'rsi', 'macd', 'volatility', 'trend'

            Mapping:
            - Fire: RSI (momentum)
            - Earth: Trend strength (stability)
            - Water: MACD (trend following)
            - Air: Volatility (market regime)

        Returns:
            Trading decision with element breakdown
        """
        # Convert indicators to element votes
        rsi = indicators.get("rsi", 50.0)
        macd = indicators.get("macd", 0.0)
        volatility = indicators.get("volatility", 0.5)
        trend = indicators.get("trend", 0.0)

        # Fire (RSI): 0-100 -> -1 to 1 (oversold to overbought)
        fire_vote = (rsi - 50) / 50

        # Earth (Trend): -1 to 1 (downtrend to uptrend)
        earth_vote = max(-1.0, min(1.0, trend))

        # Water (MACD): Normalize to -1 to 1
        water_vote = max(-1.0, min(1.0, macd / 2))

        # Air (Volatility): 0-1 -> -1 to 1 (low vol to high vol)
        air_vote = (volatility - 0.5) * 2

        features = {
            "symbol": symbol,
            "price": price,
            "fire_vote": fire_vote,
            "earth_vote": earth_vote,
            "water_vote": water_vote,
            "air_vote": air_vote,
        }

        return await self.analyze(features, {})

    def explain_element(self, element: str) -> str:
        """
        Get explanation for an element's meaning.

        Args:
            element: One of 'fire', 'earth', 'water', 'air', 'ether'

        Returns:
            Description of the element's trading significance
        """
        explanations = {
            "fire": "Agni - Momentum and position sizing. High fire = strong momentum, aggressive sizing.",
            "earth": "Prithvi - Entry/exit timing and stability. High earth = good timing, stable conditions.",
            "water": "Apas - Trend following and adaptability. High water = strong trend, adaptive strategy.",
            "air": "Vayu - Market regime and volatility. High air = volatile regime, cautious approach.",
            "ether": "Akasha - Final consensus and coordination. Balances all elements.",
        }
        return explanations.get(element.lower(), "Unknown element")
