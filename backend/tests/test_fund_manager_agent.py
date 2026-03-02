from datetime import datetime, timezone

import pytest
import pytest_asyncio

from backend.agents.fund_manager_agent import FundManagerAgent
from backend.core.schemas.ooda_types import (
    AgentRole,
    PortfolioState,
    RiskAssessment,
    RiskDecision,
    TradeProposal,
)


@pytest.fixture
def fund_manager():
    return FundManagerAgent(
        agent_name="TestFundManager",
        max_position_pct=0.10,
        max_total_exposure=0.90,
        kelly_multiplier=0.5,
    )


@pytest.fixture
def sample_proposal():
    return TradeProposal(
        symbol="BTC/USDT",
        side="buy",
        size=1.0,  # Placeholder
        entry_price=50000.0,
        stop_loss=49000.0,  # 2% loss
        take_profit=52000.0,  # 4% win (Reward:Risk 2:1)
        rationale="Test Trade",
        strategy_id="Strat_1",
        confidence=0.8,
    )


@pytest.fixture
def sample_risk(sample_proposal):
    return RiskAssessment(
        trade_id=sample_proposal.trade_id,
        decision=RiskDecision.APPROVE,
        rationale="Safe trade confirmed",
        risk_score=0.2,
        win_probability=0.6,
    )


@pytest.fixture
def sample_portfolio():
    return PortfolioState(
        total_equity=10000.0,
        available_capital=10000.0,
        total_exposure_pct=0.0,
        num_open_positions=0,
    )


@pytest.mark.asyncio
async def test_kelly_calculation_logic(fund_manager):
    """
    Test Kelly Logic manually.
    Win% = 0.6, WinAmt = 0.04 (4%), LossAmt = 0.02 (2%)
    Kelly = (0.6 * 0.04 - 0.4 * 0.02) / 0.04 = (0.024 - 0.008) / 0.04 = 0.016 / 0.04 = 0.40 (40%)
    Safe Kelly = 0.5 * 0.40 = 0.20 (20%)
    Max Limit = 0.10 (10%)
    Final = 10%
    """
    # Use helper directly to test formula
    k = fund_manager._calculate_kelly(0.6, 0.04, 0.02)
    assert k == pytest.approx(0.40)


@pytest.mark.asyncio
async def test_allocation_sizing(fund_manager, sample_proposal, sample_risk, sample_portfolio):
    """
    Test full allocation flow.
    Expect capping at 10% due to max_position_pct.
    """
    alloc = await fund_manager.allocate_capital(sample_proposal, sample_risk, sample_portfolio)

    assert alloc.approved is True
    assert alloc.kelly_fraction == pytest.approx(0.40)
    # 0.40 * 0.5 = 0.20 -> Capped at 0.10
    assert alloc.position_fraction == 0.10
    assert alloc.position_size_usd == 1000.0  # 10% of 10k


@pytest.mark.asyncio
async def test_exposure_limit(fund_manager, sample_proposal, sample_risk):
    """
    Test total exposure limit.
    Portfolio already at 85% exposure. Max is 90%.
    Space left = 5%.
    """
    portfolio = PortfolioState(
        total_equity=10000.0,
        available_capital=1500.0,
        total_exposure_pct=0.85,  # 85% full
        num_open_positions=5,
    )

    alloc = await fund_manager.allocate_capital(sample_proposal, sample_risk, portfolio)

    # Kelly asks for 20% (safe) -> 10% (max pos)
    # Exposure cap space is 90% - 85% = 5%
    # Should be capped at 5%
    assert alloc.position_fraction == pytest.approx(0.05)
    assert alloc.position_size_usd == pytest.approx(500.0)


@pytest.mark.asyncio
async def test_negative_kelly_rejection(fund_manager, sample_proposal, sample_portfolio):
    """
    Test rejection when Kelly is negative (Expected Value negative).
    Win% = 0.3, Win=4%, Loss=2%
    Kelly = (0.3*0.04 - 0.7*0.02) / 0.04 = (0.012 - 0.014) = -0.002 ... Negative
    """
    bad_risk = RiskAssessment(
        trade_id="bad",
        decision=RiskDecision.APPROVE,
        rationale="Risk ok but negative EV",
        risk_score=0.8,
        win_probability=0.3,
    )

    alloc = await fund_manager.allocate_capital(sample_proposal, bad_risk, sample_portfolio)

    assert alloc.approved is False
    assert "Zero/Negative Kelly" in alloc.reasoning


@pytest.mark.asyncio
async def test_liquidity_constraint(fund_manager, sample_proposal, sample_risk):
    """
    Test when available capital is less than calculated size.
    """
    portfolio = PortfolioState(
        total_equity=10000.0,
        available_capital=500.0,  # Only $500 cash left
        total_exposure_pct=0.0,
        num_open_positions=0,
    )

    # Target is $1000 (10%)
    alloc = await fund_manager.allocate_capital(sample_proposal, sample_risk, portfolio)

    assert alloc.position_size_usd == 500.0
    assert alloc.position_fraction == 0.05  # 500/10000


@pytest.mark.asyncio
async def test_risk_rejection(fund_manager, sample_proposal, sample_portfolio):
    """Test standard risk rejection upstream."""
    risk = RiskAssessment(
        trade_id="rej",
        decision=RiskDecision.REJECT,
        rationale="Too risky for this portfolio",
        risk_score=0.9,
        win_probability=0.5,
    )

    alloc = await fund_manager.allocate_capital(sample_proposal, risk, sample_portfolio)
    assert alloc.approved is False
    assert "Risk Rejected" in alloc.reasoning
