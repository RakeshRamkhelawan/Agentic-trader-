"""
Tests for TriadService - Migrated with OODA Integration.

Week 2 of Exchange Integration Refactor.
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from backend.execution.triad_service import TriadService, get_triad_service
from backend.core.schemas.ooda_types import (
    TradeProposal,
    RiskDecision,
    ExecutionPlan,
    ExecutionOutcome,
    MarketRegime,
    RiskAssessment
)


class MockBuddhiDecision:
    """Mock BuddhiDecision for testing."""
    def __init__(self, action="bullish", confidence=0.8, rationale="Test decision"):
        self.action = action
        self.confidence = confidence
        self.rationale = rationale


class TestTriadServiceInitialization:
    """Test TriadService initialization and configuration."""

    def test_init_paper_mode(self):
        """Test initialization in paper trading mode."""
        service = TriadService(trading_mode="paper")
        assert service.trading_mode == "paper"
        assert service.agent_name == "TriadService"
        assert service.agent_role == "executor"
        assert service.order_executor is None
        assert service.risk_manager is None

    def test_init_live_mode(self):
        """Test initialization in live trading mode."""
        service = TriadService(trading_mode="live")
        assert service.trading_mode == "live"

    def test_init_backtest_mode(self):
        """Test initialization in backtest mode."""
        service = TriadService(trading_mode="backtest")
        assert service.trading_mode == "backtest"

    def test_stats_initialization(self):
        """Test that stats are initialized correctly."""
        service = TriadService()
        assert service.stats["trades_executed"] == 0
        assert service.stats["trades_rejected"] == 0
        assert service.stats["risk_rejections"] == 0
        assert service.stats["auth_failures"] == 0


class TestTriadServiceInitializationAsync:
    """Test async initialization of TriadService."""

    @pytest.mark.asyncio
    async def test_initialize_without_exchange(self):
        """Test initialization without exchange adapter."""
        service = TriadService(trading_mode="paper")

        with patch.object(service, '_create_default_adapter', return_value=None):
            result = await service.initialize()

        assert result is True
        assert service.portfolio_manager is not None
        assert service.risk_manager is not None
        assert service.order_executor is None  # No adapter

    @pytest.mark.asyncio
    async def test_initialize_with_mock_exchange(self):
        """Test initialization with mock exchange adapter."""
        service = TriadService(trading_mode="paper")

        mock_adapter = Mock()
        mock_event_bus = Mock()

        result = await service.initialize(
            event_bus=mock_event_bus,
            exchange_adapter=mock_adapter
        )

        assert result is True
        assert service.order_executor is not None
        assert service.event_bus == mock_event_bus

    @pytest.mark.asyncio
    async def test_initialize_with_enhanced_risk(self):
        """Test initialization with enhanced risk validator."""
        service = TriadService(trading_mode="paper")

        result = await service.initialize(use_enhanced_risk=True)

        assert result is True
        assert service.risk_manager is not None
        assert service.risk_manager.use_enhanced_validator is True


class TestTriadServiceExecuteTrade:
    """Test trade execution flow."""

    @pytest.fixture
    def service(self):
        """Create initialized service with mocks."""
        service = TriadService(trading_mode="paper")

        # Mock dependencies
        service.gatekeeper = Mock()
        service.gatekeeper.check_permission = Mock(return_value=True)

        service.audit_logger = Mock()
        service.audit_logger.log_execution_attempt = AsyncMock()
        service.audit_logger.log_rejected_trade = AsyncMock()
        service.audit_logger.log_security_event = AsyncMock()

        service.event_bus = Mock()
        service.event_bus.publish = AsyncMock()

        # Mock risk manager
        service.risk_manager = Mock()
        service.risk_manager.assess_risk = AsyncMock(return_value=RiskAssessment(
            trade_id="test-trade-123",
            decision=RiskDecision.APPROVE,
            rationale="Risk checks passed",
            risk_score=0.3,
            win_probability=0.7
        ))
        service.risk_manager.risk_validator = Mock()
        service.risk_manager.risk_validator.record_trade = Mock()

        # Mock order executor
        service.order_executor = Mock()
        service.order_executor.execute_trade = AsyncMock(return_value=ExecutionOutcome(
            success=True,
            order_id="order-123",
            filled_qty=0.1,
            avg_price=45000.0,
            fee=0.5
        ))

        return service

    @pytest.mark.asyncio
    async def test_execute_trade_success(self, service):
        """Test successful trade execution."""
        decision = MockBuddhiDecision(action="bullish", confidence=0.8)

        result = await service.execute_trade(
            decision=decision,
            symbol="BTC/EUR",
            quantity=Decimal("0.1")
        )

        assert result["status"] == "filled"
        assert result["order_id"] == "order-123"
        assert result["filled_qty"] == 0.1
        assert result["avg_price"] == 45000.0

        # Verify risk assessment was called
        service.risk_manager.assess_risk.assert_called_once()

        # Verify execution was called
        service.order_executor.execute_trade.assert_called_once()

        # Verify stats updated
        assert service.stats["trades_executed"] == 1

    @pytest.mark.asyncio
    async def test_execute_trade_risk_rejection(self, service):
        """Test trade rejected by risk manager."""
        service.risk_manager.assess_risk = AsyncMock(return_value=RiskAssessment(
            trade_id="test-trade-123",
            decision=RiskDecision.REJECT,
            rationale="Position limit exceeded",
            risk_score=0.9,
            win_probability=0.1
        ))

        decision = MockBuddhiDecision(action="bullish", confidence=0.8)

        result = await service.execute_trade(
            decision=decision,
            symbol="BTC/EUR",
            quantity=Decimal("0.1")
        )

        assert result["status"] == "rejected"
        assert "Position limit" in result["reason"] or "risk" in result["reason"].lower()
        assert service.stats["risk_rejections"] == 1

        # Execution should not be called
        service.order_executor.execute_trade.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_trade_auth_failure(self, service):
        """Test trade rejected due to authorization failure."""
        service.gatekeeper.authorize = Mock(return_value=False)

        decision = MockBuddhiDecision(action="bullish", confidence=0.8)

        result = await service.execute_trade(
            decision=decision,
            symbol="BTC/EUR",
            quantity=Decimal("0.1")
        )

        assert result["status"] == "rejected"
        assert "Not authorized" in result["reason"]
        assert service.stats["auth_failures"] == 1

        # Risk assessment should not be called
        service.risk_manager.assess_risk.assert_not_called()

    @pytest.mark.asyncio
    async def test_execute_trade_size_reduction(self, service):
        """Test trade with size reduction from risk manager."""
        service.risk_manager.assess_risk = AsyncMock(return_value=RiskAssessment(
            trade_id="test-trade-123",
            decision=RiskDecision.REDUCE_SIZE,
            rationale="Reducing size due to volatility",
            risk_score=0.6,
            win_probability=0.5,
            modified_size=0.05
        ))

        decision = MockBuddhiDecision(action="bullish", confidence=0.8)

        result = await service.execute_trade(
            decision=decision,
            symbol="BTC/EUR",
            quantity=Decimal("0.1")
        )

        # Should still execute (with modified size)
        assert result["status"] == "filled"
        service.order_executor.execute_trade.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_trade_execution_failure(self, service):
        """Test handling of execution failure."""
        service.order_executor.execute_trade = AsyncMock(return_value=ExecutionOutcome(
            success=False,
            order_id="",
            filled_qty=0,
            avg_price=0,
            error="Insufficient balance"
        ))

        decision = MockBuddhiDecision(action="bullish", confidence=0.8)

        result = await service.execute_trade(
            decision=decision,
            symbol="BTC/EUR",
            quantity=Decimal("0.1")
        )

        assert result["status"] == "failed"
        assert result["error"] == "Insufficient balance"
        assert service.stats["trades_rejected"] == 1

    @pytest.mark.asyncio
    async def test_execute_trade_bearish_action(self, service):
        """Test sell trade execution."""
        decision = MockBuddhiDecision(action="bearish", confidence=0.8)

        result = await service.execute_trade(
            decision=decision,
            symbol="BTC/EUR",
            quantity=Decimal("0.1")
        )

        assert result["status"] == "filled"

        # Verify sell side was used
        call_args = service.risk_manager.assess_risk.call_args
        proposal = call_args[1]["proposal"]
        assert proposal.side == "sell"

    @pytest.mark.asyncio
    async def test_execute_trade_auto_quantity(self, service):
        """Test auto-calculated quantity from confidence."""
        decision = MockBuddhiDecision(action="bullish", confidence=0.5)

        result = await service.execute_trade(
            decision=decision,
            symbol="BTC/EUR"
            # No quantity specified
        )

        assert result["status"] == "filled"

        # Quantity should be derived from confidence (0.5 * 0.1 = 0.05)
        call_args = service.risk_manager.assess_risk.call_args
        proposal = call_args[1]["proposal"]
        assert proposal.size == 0.05  # 0.5 confidence * 0.1 factor


class TestTriadServiceCancelTrade:
    """Test trade cancellation."""

    @pytest.fixture
    def service(self):
        """Create service with mocked executor."""
        service = TriadService(trading_mode="paper")

        service.gatekeeper = Mock()
        service.gatekeeper.check_permission = Mock(return_value=True)

        service.event_bus = Mock()
        service.event_bus.publish = AsyncMock()

        service.order_executor = Mock()
        service.order_executor.cancel_order = AsyncMock(return_value=True)

        return service

    @pytest.mark.asyncio
    async def test_cancel_trade_success(self, service):
        """Test successful trade cancellation."""
        result = await service.cancel_trade("order-123")

        assert result is True
        service.order_executor.cancel_order.assert_called_once_with("order-123")

        # Event should be published
        service.event_bus.publish.assert_called_once()

    @pytest.mark.asyncio
    async def test_cancel_trade_auth_failure(self, service):
        """Test cancellation without permission."""
        service.gatekeeper.authorize = Mock(return_value=False)

        result = await service.cancel_trade("order-123")

        assert result is False
        service.order_executor.cancel_order.assert_not_called()

    @pytest.mark.asyncio
    async def test_cancel_trade_no_executor(self, service):
        """Test cancellation when executor not initialized."""
        service.order_executor = None

        result = await service.cancel_trade("order-123")

        assert result is False


class TestTriadServicePortfolio:
    """Test portfolio integration."""

    @pytest.mark.asyncio
    async def test_get_portfolio_with_manager(self):
        """Test getting portfolio when manager is available."""
        service = TriadService(trading_mode="paper")

        mock_portfolio = Mock()
        mock_portfolio.total_equity = 100000.0
        mock_portfolio.available_capital = 50000.0

        service.portfolio_manager = Mock()
        service.portfolio_manager.get_portfolio_state = AsyncMock(return_value=mock_portfolio)

        result = await service.get_portfolio()

        assert result == mock_portfolio
        assert result.total_equity == 100000.0

    @pytest.mark.asyncio
    async def test_get_portfolio_no_manager(self):
        """Test getting portfolio when manager not initialized."""
        service = TriadService(trading_mode="paper")
        service.portfolio_manager = None

        result = await service.get_portfolio()

        assert result is None


class TestTriadServiceStatistics:
    """Test statistics tracking."""

    def test_get_statistics(self):
        """Test getting service statistics."""
        service = TriadService(trading_mode="paper")
        service.stats["trades_executed"] = 5
        service.stats["trades_rejected"] = 2

        stats = service.get_statistics()

        assert stats["trades_executed"] == 5
        assert stats["trades_rejected"] == 2
        assert stats["trading_mode"] == "paper"

    def test_get_statistics_with_risk_manager(self):
        """Test stats when risk manager has stats."""
        service = TriadService(trading_mode="paper")

        service.risk_manager = Mock()
        service.risk_manager.get_stats = Mock(return_value={
            "assessments_made": 10,
            "trades_approved": 8
        })

        stats = service.get_statistics()

        assert "risk_manager" in stats
        assert stats["risk_manager"]["assessments_made"] == 10


class TestTriadServiceFactory:
    """Test factory function."""

    def test_get_triad_service_singleton(self):
        """Test that factory returns singleton."""
        # Clear any existing singleton
        import backend.execution.triad_service as triad_module
        triad_module._triad_service = None

        service1 = get_triad_service("paper")
        service2 = get_triad_service("paper")

        assert service1 is service2

    def test_get_triad_service_different_modes(self):
        """Test factory with different trading modes."""
        import backend.execution.triad_service as triad_module
        triad_module._triad_service = None

        service = get_triad_service("live")

        assert service.trading_mode == "live"


class TestTriadServiceClose:
    """Test service cleanup."""

    @pytest.mark.asyncio
    async def test_close_service(self):
        """Test closing service."""
        service = TriadService(trading_mode="paper")

        # Should not raise
        await service.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
