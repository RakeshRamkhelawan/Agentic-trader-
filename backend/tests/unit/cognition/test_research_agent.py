import pytest
import respx
from httpx import Response
from unittest.mock import MagicMock, AsyncMock
from backend.services.research_agent import ResearchAgent

@pytest.fixture
def mock_memory():
    return MagicMock()

@pytest.mark.asyncio
async def test_scrape_and_analyze(mock_memory):
    """Happy Path: Haal nieuws op, analyseer en sla op."""
    agent = ResearchAgent(memory_agent=mock_memory)
    
    # Mock de website
    with respx.mock(base_url="https://cointelegraph.com") as respx_mock:
        long_text = "Bitcoin ETF approved! This is a massive signal for the entire crypto market. Bull run confirmed."
        respx_mock.get("").mock(return_value=Response(200, text=f"<html><body><p>{long_text}</p></body></html>"))
        
        # Override sources voor test snelheid
        agent.sources = ["https://cointelegraph.com"]
        
        await agent.run_cycle()
        
        # 1. Check of Memory is aangeroepen
        mock_memory.store_thought.assert_called_once()
        args = mock_memory.store_thought.call_args[1]
        
        # 2. Check de analyse (Bullish)
        assert args["metadata"]["sentiment"] > 0
        assert "Bitcoin ETF approved" in args["text"]

@pytest.mark.asyncio
async def test_skip_failed_scrape(mock_memory):
    """Unhappy Path: 404 error mag niet crashen."""
    agent = ResearchAgent(memory_agent=mock_memory)
    
    with respx.mock(base_url="https://cointelegraph.com") as respx_mock:
        respx_mock.get("").mock(return_value=Response(404))
        agent.sources = ["https://cointelegraph.com"]
        
        await agent.run_cycle()
        
        mock_memory.store_thought.assert_not_called()
