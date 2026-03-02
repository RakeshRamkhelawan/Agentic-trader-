"""
Phase 4 Integration Tests: Regime-Aware Strategy Selection

Validates that StrategySelector correctly maps market regime + guna
to the right strategy, and that the chosen strategy's output flows
through the Mind into a TradingIntent.
"""

import uuid

import pytest

from backend.core.cognitive_mind_service import CognitiveMindService
from backend.core.risk.guna_sizing import GunaType
from backend.core.schemas.ooda_types import MarketRegime
from backend.core.strategy.implementations import (
    DefensiveStrategy,
    MeanReversionStrategy,
    TrendFollowingStrategy,
)
from backend.core.strategy.selector import StrategySelector
from backend.core.zero_copy_bridge import ZeroCopyBridge

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def selector():
    return StrategySelector()


@pytest.fixture
def shm_bridge():
    name = f"t_{uuid.uuid4().hex[:12]}"
    bridge = ZeroCopyBridge(create=True, shm_name=name, dtype_name="intent")
    yield bridge
    bridge.close()


# ---------------------------------------------------------------------------
# Strategy Selection Tests
# ---------------------------------------------------------------------------


def test_bull_regime_selects_trend_following(selector):
    """BULL regime should select TrendFollowingStrategy."""
    strategy = selector.get_strategy(MarketRegime.BULL.value, GunaType.RAJAS.value)
    assert isinstance(strategy, TrendFollowingStrategy)


def test_bear_regime_selects_trend_following(selector):
    """BEAR regime should also select TrendFollowingStrategy."""
    strategy = selector.get_strategy(MarketRegime.BEAR.value, GunaType.RAJAS.value)
    assert isinstance(strategy, TrendFollowingStrategy)


def test_sideways_regime_selects_mean_reversion(selector):
    """SIDEWAYS regime should select MeanReversionStrategy."""
    strategy = selector.get_strategy(MarketRegime.SIDEWAYS.value, GunaType.RAJAS.value)
    assert isinstance(strategy, MeanReversionStrategy)


def test_volatile_regime_selects_defensive(selector):
    """VOLATILE regime should select DefensiveStrategy."""
    strategy = selector.get_strategy(MarketRegime.VOLATILE.value, GunaType.RAJAS.value)
    assert isinstance(strategy, DefensiveStrategy)


def test_tamas_guna_overrides_to_defensive(selector):
    """Tamas guna should override regime and select DefensiveStrategy."""
    strategy = selector.get_strategy(MarketRegime.BULL.value, GunaType.TAMAS.value)
    assert isinstance(strategy, DefensiveStrategy)


@pytest.mark.asyncio
async def test_strategy_output_flows_to_intent(shm_bridge):
    """Strategy analyze -> Mind writes valid intent to SHM."""
    mind = CognitiveMindService(shm_name=shm_bridge.shm_name)
    mind.bridge = shm_bridge

    bull_context = {
        "timestamp": "2026-01-01T00:00:00+00:00",
        "rahu_kala_active": False,
        "consciousness_level": 0.8,
        "guna_dominance": "rajas",
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

    await mind.process_cycle(soul_context=bull_context)

    intent = shm_bridge.read_intent("BTC/USD")
    assert intent is not None
    # Mind should have produced some intent (action can be 0, 1, or -1)
    assert intent.timestamp_ns > 0
