from unittest.mock import AsyncMock

import pytest

from backend.agents.researcher_agents import BearResearcher, BullResearcher
from backend.core.schemas.ooda_types import MarketRegime, Observation, Orientation


@pytest.fixture
def mock_llm():
    return AsyncMock()


@pytest.fixture
def bull_agent(mock_llm):
    agent = BullResearcher(llm_provider=mock_llm)
    agent.ask_llm = AsyncMock()  # Mock the base method directly
    return agent


@pytest.fixture
def bear_agent(mock_llm):
    agent = BearResearcher(llm_provider=mock_llm)
    agent.ask_llm = AsyncMock()
    return agent


@pytest.fixture
def sample_observation():
    return Observation(symbol="BTC/USDT", price=50000.0, volume=100.0, timestamp=1000.0)


@pytest.fixture
def sample_orientation():
    return Orientation(
        symbol="BTC/USDT",
        regime=MarketRegime.TRENDING_DOWN,  # Bear market
        confidence=0.8,
        core_sentiment=0.4,  # Bearish sentiment
        rag_context=["Historical crash 2020"],
    )


@pytest.mark.asyncio
async def test_bull_researcher_contrarian_logic(bull_agent, sample_observation, sample_orientation):
    """
    Test BullResearcher generating bullish hypothesis in a Bear market.
    Should be highly contrarian.
    """
    # Mock LLM response
    bull_agent.ask_llm.return_value = """
    CONFIDENCE: 0.75
    ARGUMENTS:
    1. RSI divergence on 4h
    2. Support at 49k
    3. whale accumulation
    """

    hypothesis = await bull_agent.generate_hypothesis(
        "BTC/USDT", sample_observation, sample_orientation
    )

    assert hypothesis.stance == "bullish"
    assert hypothesis.confidence == 0.75
    assert len(hypothesis.arguments) == 3
    assert "RSI divergence" in hypothesis.arguments[0]

    # Contrarian Score: Bullish in Bear Market (Trending Down) -> Should be high (0.9)
    assert hypothesis.contrarian_score == 0.9


@pytest.mark.asyncio
async def test_bear_researcher_contrarian_logic(bear_agent, sample_observation):
    """
    Test BearResearcher in a Bull market.
    """
    bull_orientation = Orientation(
        symbol="BTC/USDT",
        regime=MarketRegime.TRENDING_UP,
        confidence=0.9,
        core_sentiment=0.8,
        rag_context=[],
    )

    bear_agent.ask_llm.return_value = """
    CONFIDENCE: 0.8
    ARGUMENTS:
    - Overbought RSI
    - MACD crossover
    """

    hypothesis = await bear_agent.generate_hypothesis(
        "BTC/USDT", sample_observation, bull_orientation
    )

    assert hypothesis.stance == "bearish"
    assert len(hypothesis.arguments) == 2

    # Contrarian Score: Bearish in Bull Market -> High (0.9)
    assert hypothesis.contrarian_score == 0.9


@pytest.mark.asyncio
async def test_parsing_fallback(bull_agent, sample_observation, sample_orientation):
    """Test resilience against malformed LLM output."""
    bull_agent.ask_llm.return_value = "Just some text without confidence or numbered list."

    hypothesis = await bull_agent.generate_hypothesis(
        "BTC/USDT", sample_observation, sample_orientation
    )

    assert hypothesis.confidence == 0.5  # Default
    assert len(hypothesis.arguments) == 1
    assert "parsing failed" in hypothesis.arguments[0]


@pytest.mark.asyncio
async def test_contrarian_scores_bull(bull_agent):
    """Verify scoring logic for Bull Agent."""
    # Bear market -> High contrarian
    assert bull_agent._calculate_contrarian_score(MarketRegime.TRENDING_DOWN) == 0.9
    # Bull market -> Low contrarian (Consensus)
    assert bull_agent._calculate_contrarian_score(MarketRegime.TRENDING_UP) == 0.2
    # Ranging -> Neutral
    assert bull_agent._calculate_contrarian_score(MarketRegime.RANGING) == 0.5


@pytest.mark.asyncio
async def test_contrarian_scores_bear(bear_agent):
    """Verify scoring logic for Bear Agent."""
    # Bull market -> High contrarian
    assert bear_agent._calculate_contrarian_score(MarketRegime.TRENDING_UP) == 0.9
    # Bear market -> Low contrarian (Consensus)
    assert bear_agent._calculate_contrarian_score(MarketRegime.TRENDING_DOWN) == 0.2
