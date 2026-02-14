"""
ResearcherAgents - Bull & Bear Hypothesis Generation

Contrarian perspective generators voor bias detection.
"""

import logging
from typing import List, Optional
from datetime import datetime, UTC

from backend.agents.base_agent import BaseAgent
from backend.core.schemas.ooda_types import (
    Observation,
    Orientation,
    ResearchHypothesis,
    MarketRegime,
)
from backend.governance.agent_gatekeeper import AgentRole
from backend.core.security.prompt_guard import PromptGuard


class BullResearcher(BaseAgent):
    """
    Bullish hypothesis generator (devil's advocate).

    Generates arguments VOOR buying, even in bearish conditions.
    """

    def __init__(
        self,
        llm_provider: Optional["LLMProvider"] = None,
        event_bus: Optional["EventBus"] = None,
    ):
        super().__init__(
            agent_name="BullResearcher",
            llm_provider=llm_provider,
            event_bus=event_bus,
            agent_role=AgentRole.RESEARCHER,
        )
        self.logger = logging.getLogger(self.__class__.__name__)

    async def analyze(self, *args, **kwargs):
        """BaseAgent abstract method - use generate_hypothesis instead."""
        raise NotImplementedError("BullResearcher uses generate_hypothesis()")

    async def _generate_text(self, prompt: str, context: Optional[dict] = None) -> str:
        """Wrapper for ask_llm to match expected interface."""
        # We can optionally use context for logging or specialized prompting
        return await self.ask_llm(prompt)

    async def generate_hypothesis(
        self, symbol: str, observation: Observation, analyst_view: Orientation
    ) -> ResearchHypothesis:
        """
        Generate bullish hypothesis.

        Args:
            symbol: Trading symbol
            observation: Market observation
            analyst_view: Analyst's orientation

        Returns:
            Bullish research hypothesis
        """
        self.logger.info(f"Generating bullish hypothesis for {symbol}")

        # Build contrarian prompt
        prompt = self._build_bullish_prompt(symbol, observation, analyst_view)

        # Generate via LLM
        response = await self._generate_text(
            prompt=prompt,
            context={
                "symbol": symbol,
                "price": observation.price,
                "regime": analyst_view.regime.value,
            },
        )

        # Parse response
        arguments = self._extract_arguments(response)
        confidence = self._extract_confidence(response)
        contrarian_score = self._calculate_contrarian_score(analyst_view.regime)

        return ResearchHypothesis(
            stance="bullish",
            confidence=confidence,
            arguments=arguments,
            contrarian_score=contrarian_score,
        )

    def _build_bullish_prompt(
        self, symbol: str, observation: Observation, analyst_view: Orientation
    ) -> str:
        """Build bullish prompt."""
        market_data = PromptGuard.wrap_data(
            "MARKET_DATA", observation.model_dump_json(indent=2)
        )
        analyst_context = PromptGuard.wrap_data(
            "ANALYST_VIEW", analyst_view.model_dump_json(indent=2)
        )

        return f"""
You are a BULLISH researcher. Your job is to find reasons TO BUY {symbol}.

{analyst_context}
{market_data}

Play devil's advocate. What bullish signals might we be missing?

Consider:
1. Technical oversold conditions (contrarian buy signal)
2. Volume divergence (accumulation)
3. Fundamental catalysts (adoption, partnerships)
4. Macro tailwinds (rate cuts, regulatory clarity)
5. Contrarian opportunity (extreme fear = buy)

Generate 3 SPECIFIC bullish arguments. Be concrete, not generic.

Format your response as:
CONFIDENCE: [0.0-1.0]
ARGUMENTS:
1. [Argument 1]
2. [Argument 2]
3. [Argument 3]
"""

    def _extract_arguments(self, response: str) -> List[str]:
        """Extract arguments from LLM response."""
        arguments = []
        lines = response.split("\n")

        for line in lines:
            line = line.strip()
            # Look for numbered lines
            if line and (line[0].isdigit() or line.startswith("-")):
                # Remove numbering
                arg = line.lstrip("0123456789.-) ").strip()
                if arg:
                    arguments.append(arg)

        # Fallback if parsing failed
        if not arguments:
            arguments = ["Generated hypothesis (parsing failed)"]

        return arguments[:3]  # Max 3

    def _extract_confidence(self, response: str) -> float:
        """Extract confidence from LLM response."""
        lines = response.split("\n")

        for line in lines:
            if "CONFIDENCE:" in line.upper():
                try:
                    # Extract number
                    parts = line.split(":")
                    if len(parts) > 1:
                        conf_str = parts[1].strip()
                        confidence = float(conf_str)
                        return max(0.0, min(confidence, 1.0))
                except ValueError:
                    pass

        # Default medium confidence
        return 0.5

    def _calculate_contrarian_score(self, regime: MarketRegime) -> float:
        """
        Calculate how contrarian this bullish view is.

        High score = very contrarian (bullish in bear market)
        Low score = consensus (bullish in bull market)
        """
        if regime == MarketRegime.TRENDING_DOWN:
            return 0.9  # Very contrarian
        elif regime == MarketRegime.VOLATILE:
            return 0.7  # Moderately contrarian
        elif regime == MarketRegime.RANGING:
            return 0.5  # Neutral
        elif regime == MarketRegime.TRENDING_UP:
            return 0.2  # Consensus view
        else:
            return 0.5


class BearResearcher(BaseAgent):
    """
    Bearish hypothesis generator (devil's advocate).

    Generates arguments VOOR selling/shorting, even in bullish conditions.
    """

    def __init__(
        self,
        llm_provider: Optional["LLMProvider"] = None,
        event_bus: Optional["EventBus"] = None,
    ):
        super().__init__(
            agent_name="BearResearcher",
            llm_provider=llm_provider,
            event_bus=event_bus,
            agent_role=AgentRole.RESEARCHER,
        )
        self.logger = logging.getLogger(self.__class__.__name__)

    async def analyze(self, *args, **kwargs):
        """BaseAgent abstract method - use generate_hypothesis instead."""
        raise NotImplementedError("BearResearcher uses generate_hypothesis()")

    async def _generate_text(self, prompt: str, context: Optional[dict] = None) -> str:
        """Wrapper for ask_llm to match expected interface."""
        return await self.ask_llm(prompt)

    async def generate_hypothesis(
        self, symbol: str, observation: Observation, analyst_view: Orientation
    ) -> ResearchHypothesis:
        """
        Generate bearish hypothesis.

        Args:
            symbol: Trading symbol
            observation: Market observation
            analyst_view: Analyst's orientation

        Returns:
            Bearish research hypothesis
        """
        self.logger.info(f"Generating bearish hypothesis for {symbol}")

        prompt = self._build_bearish_prompt(symbol, observation, analyst_view)

        response = await self._generate_text(
            prompt=prompt,
            context={
                "symbol": symbol,
                "price": observation.price,
                "regime": analyst_view.regime.value,
            },
        )

        arguments = self._extract_arguments(response)
        confidence = self._extract_confidence(response)
        contrarian_score = self._calculate_contrarian_score(analyst_view.regime)

        return ResearchHypothesis(
            stance="bearish",
            confidence=confidence,
            arguments=arguments,
            contrarian_score=contrarian_score,
        )

    def _build_bearish_prompt(
        self, symbol: str, observation: Observation, analyst_view: Orientation
    ) -> str:
        """Build bearish prompt."""
        market_data = PromptGuard.wrap_data(
            "MARKET_DATA", observation.model_dump_json(indent=2)
        )
        analyst_context = PromptGuard.wrap_data(
            "ANALYST_VIEW", analyst_view.model_dump_json(indent=2)
        )

        return f"""
You are a BEARISH researcher. Your job is to find reasons TO SELL/SHORT {symbol}.

{analyst_context}
{market_data}

Play devil's advocate. What bearish risks might we be missing?

Consider:
1. Technical overbought conditions (distribution)
2. Volume divergence (smart money exiting)
3. Fundamental risks (regulation, competition)
4. Macro headwinds (rate hikes, recession fears)
5. Contrarian warning (extreme greed = sell)

Generate 3 SPECIFIC bearish arguments. Be concrete, not generic.

Format your response as:
CONFIDENCE: [0.0-1.0]
ARGUMENTS:
1. [Argument 1]
2. [Argument 2]
3. [Argument 3]
"""

    def _extract_arguments(self, response: str) -> List[str]:
        """Extract arguments from LLM response."""
        arguments = []
        lines = response.split("\n")

        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-")):
                arg = line.lstrip("0123456789.-) ").strip()
                if arg:
                    arguments.append(arg)

        if not arguments:
            arguments = ["Generated hypothesis (parsing failed)"]

        return arguments[:3]

    def _extract_confidence(self, response: str) -> float:
        """Extract confidence from LLM response."""
        lines = response.split("\n")

        for line in lines:
            if "CONFIDENCE:" in line.upper():
                try:
                    parts = line.split(":")
                    if len(parts) > 1:
                        conf_str = parts[1].strip()
                        confidence = float(conf_str)
                        return max(0.0, min(confidence, 1.0))
                except ValueError:
                    pass

        return 0.5

    def _calculate_contrarian_score(self, regime: MarketRegime) -> float:
        """
        Calculate how contrarian this bearish view is.

        High score = very contrarian (bearish in bull market)
        Low score = consensus (bearish in bear market)
        """
        if regime == MarketRegime.TRENDING_UP:
            return 0.9  # Very contrarian
        elif regime == MarketRegime.VOLATILE:
            return 0.7  # Moderately contrarian
        elif regime == MarketRegime.RANGING:
            return 0.5  # Neutral
        elif regime == MarketRegime.TRENDING_DOWN:
            return 0.2  # Consensus view
        else:
            return 0.5
