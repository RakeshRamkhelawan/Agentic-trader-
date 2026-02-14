from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.services.macro_agent import MacroAgent


@pytest.fixture
def mock_memory():
    return MagicMock()

@pytest.fixture
def mock_bus():
    return AsyncMock()

@pytest.mark.asyncio
async def test_macro_analysis_risk_off(mock_memory, mock_bus):
    """
    Happy Path: Hoge rente + Fear = Risk Off.
    """
    agent = MacroAgent(memory_agent=mock_memory, message_bus=mock_bus)
    
    # We mocken de interne data-fetch methode
    agent.fetch_macro_data = AsyncMock(return_value={
        "us_10y_yield": 4.5, # Hoog
        "fear_greed_index": 20, # Extreme Fear
        "dxy": 105.0 # Sterke Dollar
    })
    
    await agent.run_cycle()
    
    # Check bericht op de bus
    mock_bus.assert_called_once()
    msg = mock_bus.call_args[0][0]
    
    assert msg.type == "SIGNAL"
    assert msg.payload["regime"] == "RISK_OFF"
    assert msg.payload["score"] < 0.0

@pytest.mark.asyncio
async def test_macro_analysis_risk_on(mock_memory, mock_bus):
    """
    Happy Path: Lage rente + Greed = Risk On.
    """
    agent = MacroAgent(memory_agent=mock_memory, message_bus=mock_bus)
    
    agent.fetch_macro_data = AsyncMock(return_value={
        "us_10y_yield": 2.0, # Laag
        "fear_greed_index": 75, # Greed
        "dxy": 90.0 # Zwakke Dollar
    })
    
    await agent.run_cycle()
    
    msg = mock_bus.call_args[0][0]
    assert msg.payload["regime"] == "RISK_ON"
    assert msg.payload["score"] > 0.0
