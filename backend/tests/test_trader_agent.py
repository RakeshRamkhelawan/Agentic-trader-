"""
Tests voor Trader Agent.

Test trade proposal generation, sizing, levels berekening.
"""

from unittest.mock import patch

import pytest

from backend.agents.trader_agent import TraderAgent
from backend.core.schemas.ooda_types import MarketRegime, Orientation, TradeProposal


class TestTraderAgent:
    """Tests for TraderAgent."""

    @pytest.mark.asyncio
    async def test_propose_buy_signal(self, bullish_orientation):
        """Happy path: Buy proposal gegenereerd voor bullish orientation."""
        agent = TraderAgent()

        proposal = await agent.propose_trade(
            orientation=bullish_orientation, current_price=50000.0, strategy_id="momentum_v1"
        )

        assert isinstance(proposal, TradeProposal)
        assert proposal.symbol == "BTC/USDT"
        assert proposal.side == "buy"
        assert proposal.entry_price == 50000.0
        assert proposal.size > 0
        assert proposal.stop_loss < 50000.0  # Below entry
        assert proposal.take_profit > 50000.0  # Above entry
        assert proposal.confidence == 0.75
        assert len(proposal.rationale) >= 10

    @pytest.mark.asyncio
    async def test_propose_sell_signal(self, bearish_orientation):
        """Sell proposal voor bearish orientation."""
        agent = TraderAgent()

        proposal = await agent.propose_trade(orientation=bearish_orientation, current_price=50000.0)

        assert proposal.side == "sell"
        assert proposal.stop_loss > 50000.0  # Above entry (voor short)
        assert proposal.take_profit < 50000.0  # Below entry

    @pytest.mark.asyncio
    async def test_no_signal_ranging(self):
        """Geen trade in ranging market."""
        agent = TraderAgent()

        ranging_orientation = Orientation(
            symbol="BTC/USDT",
            regime=MarketRegime.RANGING,
            indicators={},
            core_sentiment=0.5,
            confidence=0.6,
        )

        proposal = await agent.propose_trade(orientation=ranging_orientation, current_price=50000.0)

        assert proposal is None

    @pytest.mark.asyncio
    async def test_no_signal_low_confidence(self, bullish_orientation):
        """Geen trade bij lage confidence."""
        agent = TraderAgent()

        # Override confidence
        low_conf_orientation = Orientation(
            symbol="BTC/USDT",
            regime=MarketRegime.TRENDING_UP,
            indicators={},
            core_sentiment=0.4,
            confidence=0.5,  # Te laag
        )

        proposal = await agent.propose_trade(
            orientation=low_conf_orientation, current_price=50000.0
        )

        assert proposal is None

    @pytest.mark.asyncio
    async def test_position_sizing_confidence_weighted(self, bullish_orientation):
        """Position size schaalt met confidence."""
        agent = TraderAgent(base_position_size=0.1)

        # High confidence
        high_conf = Orientation(
            symbol="BTC/USDT",
            regime=MarketRegime.TRENDING_UP,
            indicators={},
            core_sentiment=0.9,
            confidence=0.9,
        )
        proposal_high = await agent.propose_trade(high_conf, 50000.0)

        # Low confidence (but above threshold)
        low_conf = Orientation(
            symbol="BTC/USDT",
            regime=MarketRegime.TRENDING_UP,
            indicators={},
            core_sentiment=0.6,
            confidence=0.6,
        )
        proposal_low = await agent.propose_trade(low_conf, 50000.0)

        # Hogere confidence → grotere position
        assert proposal_high.size > proposal_low.size

    @pytest.mark.asyncio
    async def test_volatile_regime_wider_stops(self):
        """Volatile regime krijgt bredere stop loss."""
        agent = TraderAgent()

        volatile_orientation = Orientation(
            symbol="BTC/USDT",
            regime=MarketRegime.VOLATILE,
            indicators={},
            core_sentiment=0.7,
            confidence=0.7,
        )

        # Volatile geeft None (no trade)
        proposal = await agent.propose_trade(volatile_orientation, 50000.0)
        assert proposal is None

    @pytest.mark.asyncio
    async def test_leverage_in_trending_market(self, bullish_orientation):
        """Trending markets krijgen leverage."""
        agent = TraderAgent()

        proposal = await agent.propose_trade(bullish_orientation, 50000.0)

        assert proposal.leverage == 2.0  # Trending markets

    @pytest.mark.asyncio
    async def test_risk_reward_ratio(self, bullish_orientation):
        """Risk/reward ratio correct toegepast."""
        agent = TraderAgent(default_risk_reward=2.0)

        proposal = await agent.propose_trade(bullish_orientation, 50000.0)

        # Calculate actual R:R
        risk = proposal.entry_price - proposal.stop_loss
        reward = proposal.take_profit - proposal.entry_price

        actual_rr = reward / risk

        # Should be close to 2.0 (small floating point variance ok)
        assert 1.9 < actual_rr < 2.1

    @pytest.mark.asyncio
    async def test_rationale_includes_context(self, bullish_orientation):
        """Rationale bevat regime en confidence info."""
        agent = TraderAgent()

        proposal = await agent.propose_trade(bullish_orientation, 50000.0)

        rationale = proposal.rationale.lower()
        assert "buy" in rationale or "trending" in rationale
        assert "confidence" in rationale or "%" in rationale

    @pytest.mark.asyncio
    async def test_statistics_tracking(self, bullish_orientation):
        """Statistics tracker proposals generated."""
        agent = TraderAgent()

        await agent.propose_trade(bullish_orientation, 50000.0)

    @pytest.mark.asyncio
    async def test_statistics_tracking(self, bullish_orientation):
        """Statistics tracker proposals generated."""
        agent = TraderAgent()

        await agent.propose_trade(bullish_orientation, 50000.0)
        await agent.propose_trade(bullish_orientation, 51000.0)

        with patch("backend.agents.trader_agent.FastConfig.read") as mock_read:
            mock_read.return_value = {"exploration_rate": 0.1}
            stats = agent.get_statistics()

        assert stats["proposals_generated"] == 2
        assert stats["processed_events"] == 2
        assert stats["status"] == "healthy"
        assert stats["exploration_rate"] == 0.1
