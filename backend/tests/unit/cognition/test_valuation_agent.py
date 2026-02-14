from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.services.valuation_agent import ValuationAgent


@pytest.fixture
def mock_memory():
    return MagicMock()

@pytest.fixture
def mock_bus():
    return AsyncMock()

@pytest.mark.asyncio
async def test_valuation_undervalued(mock_memory, mock_bus):
    """Happy Path: Prijs ver onder SMA = Undervalued."""
    agent = ValuationAgent(memory_agent=mock_memory, message_bus=mock_bus)
    
    agent.fetch_market_data = AsyncMock(return_value={
        "price": 40000.0,
        "sma_200": 50000.0,
        "nvt_ratio": 30.0
    })
    
    await agent.run_cycle()
    
    msg = mock_bus.call_args[0][0]
    assert msg.payload["valuation"] == "UNDERVALUED"

@pytest.mark.asyncio
async def test_valuation_overvalued(mock_memory, mock_bus):
    """Happy Path: Prijs ver boven SMA = Overvalued."""
    agent = ValuationAgent(memory_agent=mock_memory, message_bus=mock_bus)
    
    agent.fetch_market_data = AsyncMock(return_value={
        "price": 100000.0, # 100k/40k = 2.5 (> 2.4)
        "sma_200": 40000.0,
        "nvt_ratio": 90.0
    })
    
    await agent.run_cycle()
    
    msg = mock_bus.call_args[0][0]
    assert msg.payload["valuation"] == "OVERVALUED"
