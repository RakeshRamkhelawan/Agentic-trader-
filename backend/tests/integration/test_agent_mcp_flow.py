"""
Integration Tests: Agent -> MCP Tool Flow

End-to-end tests verifying agents can successfully call MCP tools
and process the results.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.agents.elemental_consensus_agent import ElementalConsensusAgent
from backend.agents.risk_check_agent import RiskCheckAgent
from backend.agents.vedastro_signal_agent import VedAstroSignalAgent


class TestAgentMCPFlow:
    """Integration tests for Agent -> MCP communication."""

    @pytest.fixture
    def mock_tool_client(self):
        """Create a mock tool broker client."""
        client = MagicMock()
        client.call_tool = AsyncMock()
        return client

    @pytest.fixture
    def vedastro_agent(self, mock_tool_client):
        """Create VedAstroSignalAgent with mock client."""
        agent = VedAstroSignalAgent(
            agent_name="test_vedastro", tool_broker_url="http://localhost:8001"
        )
        agent.tool_broker = mock_tool_client
        return agent

    @pytest.fixture
    def elemental_agent(self, mock_tool_client):
        """Create ElementalConsensusAgent with mock client."""
        agent = ElementalConsensusAgent(
            agent_name="test_elemental", tool_broker_url="http://localhost:8001"
        )
        agent.tool_broker = mock_tool_client
        return agent

    @pytest.fixture
    def risk_agent(self, mock_tool_client):
        """Create RiskCheckAgent with mock client."""
        agent = RiskCheckAgent(agent_name="test_risk", tool_broker_url="http://localhost:8001")
        agent.tool_broker = mock_tool_client
        return agent

    @pytest.mark.asyncio
    async def test_vedastro_agent_success(self, vedastro_agent, mock_tool_client):
        """Test VedAstro agent successfully gets signal and makes decision."""
        # Mock the MCP tool response
        mock_tool_client.call_tool.return_value = {
            "success": True,
            "result": {
                "signal": "buy",
                "confidence": 0.75,
                "risk_level": "low",
                "strength_score": 65,
                "primary_factors": ["strong_jupiter", "positive_transit"],
                "supporting_factors": ["moon_in_favorable_house"],
                "warning_factors": [],
            },
        }

        features = {"symbol": "BTC", "price": 45000.0}

        result = await vedastro_agent.analyze(features, {})

        # Verify MCP tool was called
        mock_tool_client.call_tool.assert_called_once()
        call_args = mock_tool_client.call_tool.call_args[0]
        assert call_args[0] == "vedastro__generate_signal"
        assert call_args[1]["symbol"] == "BTC"
        assert call_args[1]["current_price"] == 45000.0

        # Verify result structure
        assert result["action"] == "buy"
        assert result["confidence"] == 0.75
        assert "VedAstro signal" in result["reason"]
        assert result["vedastro_data"]["risk_level"] == "low"
        assert "strong_jupiter" in result["vedastro_data"]["primary_factors"]

    @pytest.mark.asyncio
    async def test_vedastro_agent_low_confidence(self, vedastro_agent, mock_tool_client):
        """Test VedAstro agent holds when confidence is too low."""
        mock_tool_client.call_tool.return_value = {
            "success": True,
            "result": {
                "signal": "buy",
                "confidence": 0.4,  # Below default threshold of 0.6
                "risk_level": "medium",
                "strength_score": 45,
                "primary_factors": [],
                "supporting_factors": [],
                "warning_factors": [],
            },
        }

        features = {"symbol": "ETH", "price": 3000.0}

        result = await vedastro_agent.analyze(features, {})

        assert result["action"] == "hold"
        assert result["confidence"] == 0.4
        assert "below threshold" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_vedastro_agent_high_risk(self, vedastro_agent, mock_tool_client):
        """Test VedAstro agent holds when risk is too high."""
        mock_tool_client.call_tool.return_value = {
            "success": True,
            "result": {
                "signal": "buy",
                "confidence": 0.8,
                "risk_level": "high",  # High risk
                "strength_score": 70,
                "primary_factors": [],
                "supporting_factors": [],
                "warning_factors": ["mars_retrograde"],
            },
        }

        features = {"symbol": "BTC", "price": 45000.0}

        result = await vedastro_agent.analyze(features, {})

        assert result["action"] == "hold"
        assert "Risk level" in result["reason"]

    @pytest.mark.asyncio
    async def test_vedastro_agent_tool_failure(self, vedastro_agent, mock_tool_client):
        """Test VedAstro agent handles MCP tool failure gracefully."""
        mock_tool_client.call_tool.return_value = {
            "success": False,
            "error": "VedAstro service unavailable",
        }

        features = {"symbol": "BTC", "price": 45000.0}

        result = await vedastro_agent.analyze(features, {})

        assert result["action"] == "hold"
        assert result["confidence"] == 0.0
        assert "VedAstro error" in result["reason"]

    @pytest.mark.asyncio
    async def test_elemental_consensus_success(self, elemental_agent, mock_tool_client):
        """Test Elemental agent generates consensus from votes."""
        mock_tool_client.call_tool.return_value = {
            "success": True,
            "result": {
                "consensus_score": 0.75,
                "consensus_signal": "strong_buy",
                "dominant_element": "fire",
                "suppressed_element": "air",
                "element_weights": {
                    "fire": 0.8,
                    "earth": 0.6,
                    "water": 0.4,
                    "air": -0.2,
                },
            },
        }

        features = {
            "symbol": "BTC",
            "price": 45000.0,
            "fire_vote": 0.8,
            "earth_vote": 0.6,
            "water_vote": 0.4,
            "air_vote": -0.2,
        }

        result = await elemental_agent.analyze(features, {})

        # Verify MCP tool was called with correct votes
        mock_tool_client.call_tool.assert_called_once()
        call_args = mock_tool_client.call_tool.call_args[0]
        assert call_args[0] == "elemental__ether_consensus"

        # Verify result
        assert result["action"] == "buy"
        assert result["confidence"] == 0.75
        assert "Elemental consensus" in result["reason"]
        assert result["dominant_element"] == "fire"

    @pytest.mark.asyncio
    async def test_elemental_consensus_weak(self, elemental_agent, mock_tool_client):
        """Test Elemental agent holds when consensus is weak."""
        mock_tool_client.call_tool.return_value = {
            "success": True,
            "result": {
                "consensus_score": 0.3,  # Below threshold
                "consensus_signal": "hold",
                "dominant_element": None,
                "suppressed_element": None,
                "element_weights": {},
            },
        }

        features = {
            "symbol": "ETH",
            "price": 3000.0,
            "fire_vote": 0.2,
            "earth_vote": 0.1,
            "water_vote": -0.1,
            "air_vote": 0.0,
        }

        result = await elemental_agent.analyze(features, {})

        assert result["action"] == "hold"
        assert "Weak consensus" in result["reason"]

    @pytest.mark.asyncio
    async def test_risk_agent_approve(self, risk_agent, mock_tool_client):
        """Test Risk agent approves valid trade."""
        features = {
            "symbol": "BTC",
            "price": 45000.0,
            "side": "buy",
            "proposed_quantity": 0.1,
            "portfolio_value": 100000.0,
        }

        result = await risk_agent.analyze(features, {})

        # Should approve (position is ~4.5% of portfolio, below 10% limit)
        assert result["action"] == "approve"
        assert result["approved_quantity"] == 0.1
        assert result["confidence"] > 0.9

    @pytest.mark.asyncio
    async def test_risk_agent_modify(self, risk_agent, mock_tool_client):
        """Test Risk agent modifies oversized position."""
        features = {
            "symbol": "BTC",
            "price": 45000.0,
            "side": "buy",
            "proposed_quantity": 0.5,  # 22.5k, too large
            "portfolio_value": 100000.0,
        }

        result = await risk_agent.analyze(features, {})

        # Should modify (reduce to ~10% max)
        assert result["action"] == "modify"
        assert result["approved_quantity"] < 0.5
        assert "reduced" in result["reason"].lower() or "capped" in result["reason"].lower()

    @pytest.mark.asyncio
    async def test_risk_agent_reject_invalid_price(self, risk_agent, mock_tool_client):
        """Test Risk agent rejects trade with invalid price."""
        features = {
            "symbol": "BTC",
            "price": 0.0,  # Invalid
            "side": "buy",
            "proposed_quantity": 0.1,
            "portfolio_value": 100000.0,
        }

        result = await risk_agent.analyze(features, {})

        assert result["action"] == "reject"
        assert result["approved_quantity"] == 0.0
        assert "Invalid price" in result["reason"]

    @pytest.mark.asyncio
    async def test_agent_with_indicators(self, elemental_agent, mock_tool_client):
        """Test Elemental agent converts technical indicators to votes."""
        mock_tool_client.call_tool.return_value = {
            "success": True,
            "result": {
                "consensus_score": 0.65,
                "consensus_signal": "buy",
                "dominant_element": "fire",
                "suppressed_element": "air",
                "element_weights": {},
            },
        }

        indicators = {
            "rsi": 65.0,  # Slightly bullish
            "macd": 0.5,  # Bullish
            "volatility": 0.3,  # Low volatility
            "trend": 0.6,  # Uptrend
        }

        result = await elemental_agent.analyze_with_indicators("BTC", 45000.0, indicators)

        assert result["action"] == "buy"
        assert result["confidence"] > 0.5


class TestAgentIntegration:
    """Tests for multi-agent integration scenarios."""

    @pytest.mark.asyncio
    async def test_multi_agent_consensus(self):
        """
        Test scenario where multiple agents vote on a trade.

        Flow:
        1. VedAstroSignalAgent generates astrological signal
        2. ElementalConsensusAgent validates element balance
        3. RiskCheckAgent approves position size
        """
        # This would be a full integration test with real MCP server
        # For now, we verify the structure is correct

        agents = {
            "vedastro": VedAstroSignalAgent,
            "elemental": ElementalConsensusAgent,
            "risk": RiskCheckAgent,
        }

        for name, agent_class in agents.items():
            assert agent_class is not None
            assert hasattr(agent_class, "analyze")

        # Verify all inherit from AgentWithTools
        from backend.agents.agent_with_tools import AgentWithTools

        for agent_class in agents.values():
            assert issubclass(agent_class, AgentWithTools)
