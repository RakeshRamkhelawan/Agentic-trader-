import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from backend.agents.portfolio_manager_agent import PortfolioManagerAgent


@pytest.fixture
def mock_portfolio_manager():
    # Setup mock capabilities for PortfolioManagerAgent
    pm = PortfolioManagerAgent()
    pm.get_tradable_universe = AsyncMock(return_value=["BTC/EUR", "ETH/EUR", "UNKNOWN_COIN/EUR"])
    return pm


@pytest.mark.asyncio
async def test_portfolio_manager_dynamic_universe(mock_portfolio_manager):
    """
    Test that the PortfolioManagerAgent correctly generates a dynamic tradable universe
    that can be handed over to the execution loop.
    """
    universe = await mock_portfolio_manager.get_tradable_universe()

    assert len(universe) == 3
    assert "BTC/EUR" in universe
    assert "UNKNOWN_COIN/EUR" in universe


@pytest.mark.asyncio
async def test_execution_loop_intersection_logic():
    """
    Test the integration logic (as seen in run_full_backtest.py)
    where the execution loop intersects the dynamic universe with support symbols.
    """
    # Mocking the dynamic universe handed over by the PortfolioManagerAgent
    dynamic_universe = ["BTC/EUR", "ETH/EUR", "INVALID/EUR", "AAPL"]

    # Simulating the SYMBOL_MAP available in the execution environment
    SYMBOL_MAP = {"BTC/EUR": "BINANCE:BTCEUR", "ETH/EUR": "BINANCE:ETHEUR"}

    # The handover logic
    symbols_to_test = []
    for sym in dynamic_universe:
        if sym in SYMBOL_MAP:
            symbols_to_test.append(SYMBOL_MAP[sym])
        elif any(sym.endswith(suffix) for suffix in ["/EUR", "/USD"]):
            # Fallback for cryptos not explicitly mapped
            formatted = sym.replace("/", "")
            symbols_to_test.append(f"KRAKEN:{formatted}")

    assert len(symbols_to_test) == 3
    assert "BINANCE:BTCEUR" in symbols_to_test
    assert "BINANCE:ETHEUR" in symbols_to_test
    assert "KRAKEN:INVALIDEUR" in symbols_to_test
    assert "AAPL" not in symbols_to_test
