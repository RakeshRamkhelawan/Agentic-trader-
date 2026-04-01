"""
VedAstro Signal Agent - Vedic astrology based trading signals.

This agent uses VedAstro (Vedic astrology) to generate trading signals
based on planetary positions and astrological analysis.
"""

import logging
from typing import Any

from backend.agents.agent_with_tools import AgentWithTools
from backend.governance.agent_gatekeeper import AgentRole

logger = logging.getLogger(__name__)


class VedAstroSignalAgent(AgentWithTools):
    """
    Agent that generates trading signals using Vedic astrology.

    Uses planetary positions, dasha periods, and transit analysis
    to determine optimal entry and exit points.
    """

    def __init__(
        self,
        agent_name: str = "vedastro_oracle",
        tool_broker_url: str | None = None,
        min_confidence: float = 0.6,
        max_risk_level: str = "medium",
        **kwargs,
    ):
        super().__init__(
            agent_name=agent_name,
            agent_role=AgentRole.STRATEGIST,
            tool_broker_url=tool_broker_url,
            **kwargs,
        )
        self.min_confidence = min_confidence
        self.max_risk_level = max_risk_level
        logger.info(f"{agent_name} initialized with min_confidence={min_confidence}")

    async def analyze(self, features: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze features using VedAstro and return trading decision.

        Args:
            features: Must contain 'symbol' and 'price'
            context: Additional context for decision making

        Returns:
            Trading decision with action, confidence, and reasoning
        """
        symbol = features.get("symbol", "BTC")
        price = features.get("price", 0.0)

        if price <= 0:
            logger.warning(f"Invalid price for {symbol}: {price}")
            return {"action": "hold", "confidence": 0.0, "reason": "Invalid price data"}

        try:
            # Get VedAstro signal via MCP
            signal_result = await self.get_vedastro_signal(symbol, price)

            if not signal_result.get("success", False):
                error = signal_result.get("error", "Unknown error")
                logger.error(f"VedAstro signal failed: {error}")
                return {
                    "action": "hold",
                    "confidence": 0.0,
                    "reason": f"VedAstro error: {error}",
                }

            signal_data = signal_result.get("result", {})
            signal = signal_data.get("signal", "hold")
            confidence = signal_data.get("confidence", 0.0)
            risk_level = signal_data.get("risk_level", "high")
            primary_factors = signal_data.get("primary_factors", [])

            # Check minimum confidence
            if confidence < self.min_confidence:
                logger.info(f"Confidence {confidence} below threshold {self.min_confidence}")
                return {
                    "action": "hold",
                    "confidence": confidence,
                    "reason": f"Confidence {confidence:.2f} below threshold {self.min_confidence}",
                    "vedastro_signal": signal,
                    "risk_level": risk_level,
                }

            # Check risk level
            risk_levels = {"low": 0, "medium": 1, "high": 2}
            max_risk = risk_levels.get(self.max_risk_level, 1)
            current_risk = risk_levels.get(risk_level, 2)

            if current_risk > max_risk:
                logger.info(f"Risk level {risk_level} exceeds max {self.max_risk_level}")
                return {
                    "action": "hold",
                    "confidence": confidence,
                    "reason": f"Risk level {risk_level} too high (max: {self.max_risk_level})",
                    "vedastro_signal": signal,
                    "risk_level": risk_level,
                }

            # Build reasoning
            reason_parts = [f"VedAstro signal: {signal} with {confidence:.0%} confidence"]
            if primary_factors:
                reason_parts.append(f"Primary factors: {', '.join(primary_factors[:3])}")
            reason_parts.append(f"Risk level: {risk_level}")

            logger.info(f"{self.agent_name}: {signal} {symbol} @ {price} (conf: {confidence:.2f})")

            return {
                "action": signal,  # buy, sell, or hold
                "confidence": confidence,
                "reason": "; ".join(reason_parts),
                "vedastro_data": {
                    "signal": signal,
                    "confidence": confidence,
                    "risk_level": risk_level,
                    "strength_score": signal_data.get("strength_score", 0),
                    "primary_factors": primary_factors,
                    "supporting_factors": signal_data.get("supporting_factors", []),
                    "warning_factors": signal_data.get("warning_factors", []),
                },
            }

        except Exception as e:
            logger.exception(f"Error in VedAstro analysis: {e}")
            return {
                "action": "hold",
                "confidence": 0.0,
                "reason": f"Analysis error: {str(e)}",
            }

    async def get_detailed_analysis(self, symbol: str, price: float) -> dict[str, Any]:
        """
        Get detailed VedAstro analysis including dasha and transits.

        Args:
            symbol: Asset symbol
            price: Current price

        Returns:
            Comprehensive analysis with signal, dasha, and transits
        """
        result = {
            "symbol": symbol,
            "price": price,
            "signal": None,
            "dasha": None,
            "transits": None,
        }

        try:
            # Get main signal
            signal_result = await self.get_vedastro_signal(symbol, price)
            if signal_result.get("success"):
                result["signal"] = signal_result.get("result")

            # Get dasha info
            dasha_result = await self.call_tool("vedastro__get_dasha", {"symbol": symbol})
            if dasha_result.get("success"):
                result["dasha"] = dasha_result.get("result")

            # Get transit info
            transit_result = await self.call_tool("vedastro__get_transits", {"symbol": symbol})
            if transit_result.get("success"):
                result["transits"] = transit_result.get("result")

            return result

        except Exception as e:
            logger.exception(f"Error getting detailed analysis: {e}")
            result["error"] = str(e)
            return result
