"""
Tests for enhanced RiskManagerAgent with OrderRiskValidator.

Week 2 of Exchange Integration Refactor.
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch

from backend.agents.risk_manager_agent import RiskManagerAgent
from backend.core.schemas.ooda_types import TradeProposal, RiskDecision, MarketRegime


class TestRiskManagerEnhanced:
    """Test RiskManagerAgent with OrderRiskValidator."""
    
    @pytest.fixture
    def agent(self):
        """Create RiskManagerAgent with enhanced validator."""
        return RiskManagerAgent(use_enhanced_validator=True)
    
    @pytest.fixture
    def basic_proposal(self):
        """Create basic trade proposal with small size."""
        return TradeProposal(
            symbol="BTC/EUR",
            side="buy",
            size=0.01,  # Small size: 0.01 BTC @ $45000 = $450 (4.5% of $10k portfolio)
            entry_price=45000,
            stop_loss=40000,
            take_profit=50000,
            rationale="Test trade with proper sizing for validation",
            strategy_id="test",
            confidence=0.8
        )
    
    @pytest.mark.asyncio
    async def test_enhanced_validator_enabled(self, agent):
        """Test that enhanced validator is initialized."""
        assert agent.use_enhanced_validator is True
        assert agent.risk_validator is not None
    
    @pytest.mark.asyncio
    async def test_assess_risk_approves_valid_trade(self, agent, basic_proposal):
        """Test that valid trade is approved."""
        assessment = await agent.assess_risk(
            proposal=basic_proposal,
            current_regime=MarketRegime.BULL,
            current_position_size=0.0
        )
        
        # Should be approved or reduced (not rejected due to size)
        assert assessment.decision in [RiskDecision.APPROVE, RiskDecision.REDUCE_SIZE]
        assert assessment.risk_score < 1.0
    
    @pytest.mark.asyncio
    async def test_position_limit_enforcement(self, agent):
        """Test that position limits are enforced."""
        # Create proposal that exceeds position limit
        large_proposal = TradeProposal(
            symbol="BTC/EUR",
            side="buy",
            size=10.0,  # Way too large: 10 BTC @ $45000 = $450k
            entry_price=45000,
            stop_loss=40000,
            take_profit=50000,
            rationale="Large position test exceeding limits",
            strategy_id="test",
            confidence=0.8
        )
        
        assessment = await agent.assess_risk(
            proposal=large_proposal,
            current_regime=MarketRegime.BULL,
            current_position_size=0.0
        )
        
        # Should reject or reduce
        assert assessment.decision in [RiskDecision.REJECT, RiskDecision.REDUCE_SIZE]
    
    @pytest.mark.asyncio
    async def test_daily_trade_limit(self, agent, basic_proposal):
        """Test daily trade count limit."""
        # Simulate max trades reached by mocking the validator's daily trade count
        if agent.risk_validator:
            # Set daily trades to max
            agent.risk_validator._daily_trades = 50
            agent.risk_validator._daily_volume = Decimal("0")
            agent.risk_validator._daily_loss = Decimal("0")
        
        assessment = await agent.assess_risk(
            proposal=basic_proposal,
            current_regime=MarketRegime.BULL,
            current_position_size=0.0
        )
        
        # Should reject due to daily limit
        assert assessment.decision == RiskDecision.REJECT
    
    @pytest.mark.asyncio
    async def test_low_confidence_rejected(self, agent):
        """Test that low confidence trades are rejected or have higher risk."""
        low_confidence_proposal = TradeProposal(
            symbol="BTC/EUR",
            side="buy",
            size=0.01,
            entry_price=45000,
            stop_loss=40000,
            take_profit=50000,
            rationale="Low confidence trade test case",
            strategy_id="test",
            confidence=0.3  # Very low
        )
        
        assessment = await agent.assess_risk(
            proposal=low_confidence_proposal,
            current_regime=MarketRegime.BULL,
            current_position_size=0.0
        )
        
        # Low confidence should result in higher risk score
        # The exact threshold depends on the implementation
        assert assessment.risk_score > 0.15  # Should have elevated risk
    
    @pytest.mark.asyncio
    async def test_volatile_regime_increases_risk(self, agent, basic_proposal):
        """Test that volatile regime increases risk score."""
        # Test in volatile regime
        volatile_assessment = await agent.assess_risk(
            proposal=basic_proposal,
            current_regime=MarketRegime.VOLATILE,
            current_position_size=0.0
        )
        
        # Test in normal regime
        normal_assessment = await agent.assess_risk(
            proposal=basic_proposal,
            current_regime=MarketRegime.BULL,
            current_position_size=0.0
        )
        
        # Volatile should have higher or equal risk
        assert volatile_assessment.risk_score >= normal_assessment.risk_score
    
    @pytest.mark.asyncio
    async def test_legacy_mode(self, basic_proposal):
        """Test that legacy mode works without OrderRiskValidator."""
        legacy_agent = RiskManagerAgent(use_enhanced_validator=False)
        
        assessment = await legacy_agent.assess_risk(
            proposal=basic_proposal,
            current_regime=MarketRegime.BULL,
            current_position_size=0.0
        )
        
        # Should work without validator
        assert assessment.decision in [RiskDecision.APPROVE, RiskDecision.REJECT, RiskDecision.REDUCE_SIZE]
    
    @pytest.mark.asyncio
    async def test_convert_proposal(self, agent, basic_proposal):
        """Test conversion from TradeProposal to UnifiedOrderRequest."""
        order_request = agent._convert_proposal(basic_proposal)
        
        assert order_request.symbol == "BTC/EUR"
        assert order_request.side.value == "buy"
        assert order_request.quantity == Decimal("0.01")
        assert order_request.price == Decimal("45000")
        assert order_request.strategy_id == "test"
    
    def test_enable_enhanced_validator(self):
        """Test enabling enhanced validator after creation."""
        agent = RiskManagerAgent(use_enhanced_validator=False)
        assert agent.risk_validator is None
        
        agent.enable_enhanced_validator()
        
        assert agent.use_enhanced_validator is True
        assert agent.risk_validator is not None
    
    @pytest.mark.asyncio
    async def test_stats_tracking(self, agent, basic_proposal):
        """Test that stats are tracked correctly."""
        initial_stats = agent.get_stats()
        initial_assessments = initial_stats["assessments_made"]
        
        await agent.assess_risk(
            proposal=basic_proposal,
            current_regime=MarketRegime.BULL,
            current_position_size=0.0
        )
        
        updated_stats = agent.get_stats()
        assert updated_stats["assessments_made"] == initial_assessments + 1
    
    @pytest.mark.asyncio
    async def test_analyze_method(self, agent):
        """Test the abstract analyze method implementation."""
        features = {
            "symbol": "BTC/EUR",
            "side": "buy",
            "size": 0.01,
            "entry_price": 45000,
            "confidence": 0.8,
            "rationale": "Test analyze method"
        }
        context = {
            "market_regime": MarketRegime.BULL,
            "current_position_size": 0.0
        }
        
        result = await agent.analyze(features, context)
        
        assert "risk_score" in result
        assert "decision" in result
        assert "rationale" in result


class TestRiskManagerWithPortfolio:
    """Test RiskManagerAgent with PortfolioManager integration."""
    
    @pytest.mark.asyncio
    async def test_portfolio_integration(self):
        """Test risk assessment with portfolio info."""
        # Mock portfolio manager
        mock_pm = Mock()
        mock_pm.get_portfolio_state = AsyncMock(return_value=Mock(
            total_equity=100000.0,
            available_capital=50000.0,
            total_exposure_pct=0.3,
            num_open_positions=2
        ))
        
        agent = RiskManagerAgent(
            use_enhanced_validator=True,
            portfolio_manager=mock_pm
        )
        
        proposal = TradeProposal(
            symbol="BTC/EUR",
            side="buy",
            size=0.01,  # Small size
            entry_price=45000,
            stop_loss=40000,
            take_profit=50000,
            rationale="Portfolio integration test with mock data",
            strategy_id="test",
            confidence=0.8
        )
        
        assessment = await agent.assess_risk(
            proposal=proposal,
            current_regime=MarketRegime.BULL,
            current_position_size=0.0
        )
        
        # Portfolio manager should have been called
        mock_pm.get_portfolio_state.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
