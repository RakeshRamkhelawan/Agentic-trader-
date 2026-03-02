"""
Phase 3 Integration Tests: Risk Intelligence in Mind Cycle

Validates that PortfolioRiskCalculator, Kelly sizing, and Guna modulation
are correctly integrated into the CognitiveMindService process_cycle.
"""

import uuid

import pytest

from backend.core.cognitive_mind_service import CognitiveMindService
from backend.core.risk.guna_sizing import GunaType
from backend.core.risk.portfolio_risk import PortfolioRiskCalculator, RiskState
from backend.core.zero_copy_bridge import ZeroCopyBridge

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def risk_calculator():
    return PortfolioRiskCalculator()


@pytest.fixture
def normal_risk_state():
    return RiskState(
        exposure=2000.0,
        margin=10000.0,
        var_95=500.0,
        beta=1.0,
        max_drawdown=0.05,
        correlation=0.3,
        liquidity=0.9,
        volatility_percentile=0.5,
    )


@pytest.fixture
def exhausted_risk_state():
    return RiskState(
        exposure=9500.0,
        margin=10000.0,
        var_95=2000.0,
        beta=1.5,
        max_drawdown=0.15,
        correlation=0.8,
        liquidity=0.3,
        volatility_percentile=0.9,
    )


@pytest.fixture
def shm_bridge():
    name = f"t_{uuid.uuid4().hex[:12]}"
    bridge = ZeroCopyBridge(create=True, shm_name=name, dtype_name="intent")
    yield bridge
    bridge.close()


def _make_bull_context(guna="rajas"):
    return {
        "timestamp": "2026-01-01T00:00:00+00:00",
        "rahu_kala_active": False,
        "consciousness_level": 0.8,
        "guna_dominance": guna,
        "trading_gate_open": True,
        "market_regime": "BULL",
        "causality_threshold": 0.6,
        "market_metrics": {
            "price": 42000.0,
            "sma_50": 41500.0,
            "sma_200": 40000.0,
            "volatility": 0.005,
        },
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_risk_calculator_evaluates_capacity(risk_calculator, normal_risk_state):
    """PortfolioRiskCalculator should evaluate capacity and return accept."""
    result = risk_calculator.evaluate(normal_risk_state, GunaType.RAJAS)
    assert result.action == "accept"
    assert result.capacity == pytest.approx(0.8, abs=0.01)


def test_low_capacity_returns_hold(risk_calculator, exhausted_risk_state):
    """When risk capacity is very low, evaluate should return hold."""
    result = risk_calculator.evaluate(exhausted_risk_state, GunaType.RAJAS)
    assert result.action == "hold"
    assert result.reason == "insufficient_risk_capacity"
    assert result.capacity < 0.1


def test_guna_modulates_position_size(risk_calculator, normal_risk_state):
    """Different Gunas should produce different size multipliers."""
    kelly_size = risk_calculator.calculate_kelly_size(win_rate=0.55, avg_win=1.5, avg_loss=1.0)
    capacity = risk_calculator.get_risk_capacity(normal_risk_state)

    _, sattva_mult = risk_calculator.get_guna_risk_params(GunaType.SATTVA)
    _, rajas_mult = risk_calculator.get_guna_risk_params(GunaType.RAJAS)
    _, tamas_mult = risk_calculator.get_guna_risk_params(GunaType.TAMAS)

    sattva_size = risk_calculator.modulated_size(kelly_size, sattva_mult, capacity)
    rajas_size = risk_calculator.modulated_size(kelly_size, rajas_mult, capacity)
    tamas_size = risk_calculator.modulated_size(kelly_size, tamas_mult, capacity)

    # Sattva < Rajas > Tamas (conservative -> normal -> defensive)
    assert sattva_size < rajas_size
    assert tamas_size < sattva_size


def test_kelly_sizing_integrated_with_risk(risk_calculator, normal_risk_state):
    """Kelly size * guna_mult * risk_capacity = final modulated size."""
    kelly = risk_calculator.calculate_kelly_size(win_rate=0.55, avg_win=1.5, avg_loss=1.0)
    assert kelly > 0

    capacity = risk_calculator.get_risk_capacity(normal_risk_state)
    _, guna_mult = risk_calculator.get_guna_risk_params(GunaType.RAJAS)

    final = risk_calculator.modulated_size(kelly, guna_mult, capacity)
    assert final == pytest.approx(kelly * guna_mult * capacity, abs=0.001)


@pytest.mark.asyncio
async def test_mind_process_cycle_with_risk(shm_bridge):
    """Mind process_cycle should integrate risk evaluation without crashing."""
    mind = CognitiveMindService(shm_name=shm_bridge.shm_name)
    mind.bridge = shm_bridge

    context = _make_bull_context(guna="rajas")
    # Should not raise
    await mind.process_cycle(soul_context=context)

    intent = shm_bridge.read_intent("BTC/USD")
    assert intent is not None
    assert intent.timestamp_ns > 0
