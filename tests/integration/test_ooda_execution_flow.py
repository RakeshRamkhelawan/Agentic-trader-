"""
Integration Tests for Full OODA Execution Flow.

Week 2 of Exchange Integration Refactor.

Tests the complete OODA loop:
    Observe → Orient → Decide → Act
    
With new components:
    - UnifiedOrderRequest (Decimal precision)
    - PortfolioManagerAgent (portfolio aggregation)
    - RiskManagerAgent (enhanced validation)
    - TriadService (execution coordination)
    - OrderExecutor (secure execution)
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

# OODA components
from backend.core.schemas.ooda_types import (
    TradeProposal,
    RiskDecision,
    ExecutionPlan,
    ExecutionOutcome,
    MarketRegime,
    PortfolioState,
    RiskAssessment
)

# New execution components
from backend.execution.triad_service import TriadService
from backend.execution.portfolio_manager import PortfolioManager
from backend.execution.order_executor import OrderExecutor

# Agents
from backend.agents.risk_manager_agent import RiskManagerAgent
from backend.agents.portfolio_manager_agent import PortfolioManagerAgent

# Unified schema
from backend.schemas.unified_execution import (
    UnifiedOrderRequest,
    OrderSide,
    OrderType,
    TimeInForce
)

# Security
from backend.governance.agent_gatekeeper import AgentGatekeeper, ToolPermission


class MockExchangeAdapter:
    """Mock exchange adapter for integration testing."""
    
    def __init__(self):
        self.orders = {}
        self.order_counter = 0
    
    async def place_order(self, symbol, side, order_type, quantity, price=None):
        self.order_counter += 1
        order_id = f"mock-order-{self.order_counter}"
        
        # Create order as simple object with required attributes
        class MockOrder:
            pass
        
        order = MockOrder()
        order.order_id = order_id
        order.symbol = symbol
        order.side = side
        order.order_type = order_type
        order.quantity = quantity
        order.price = price or 45000.0
        order.status = "filled"
        order.filled_quantity = quantity
        order.remaining_quantity = 0
        order.average_price = price or 45000.0
        order.avg_fill_price = price or 45000.0  # Required by ExecutionOutcome
        order.created_at = datetime.utcnow().timestamp()
        
        self.orders[order_id] = order
        return order
    
    async def get_order_status(self, order_id):
        return self.orders.get(order_id)
    
    async def cancel_order(self, order_id):
        if order_id in self.orders:
            self.orders[order_id].status = "canceled"
            return True
        return False
    
    async def fetch_balance(self):
        # Return in CCXT format
        return {
            "BTC": {"free": 1.0, "used": 0.0, "total": 1.0},
            "EUR": {"free": 50000.0, "used": 0.0, "total": 50000.0},
            "free": {"BTC": 1.0, "EUR": 50000.0},
            "used": {"BTC": 0.0, "EUR": 0.0},
            "total": {"BTC": 1.0, "EUR": 50000.0}
        }


class MockBuddhiDecision:
    """Mock BuddhiDecision from councils."""
    def __init__(self, action="bullish", confidence=0.8, rationale="Test decision"):
        self.action = action
        self.confidence = confidence
        self.rationale = rationale


@pytest.fixture
def mock_event_bus():
    """Create mock event bus."""
    eb = Mock()
    eb.publish = AsyncMock()
    return eb


class TestOODAFullFlow:
    """Test complete OODA loop with new components."""
    
    @pytest.mark.asyncio
    async def test_complete_ooda_flow_bullish(self, mock_event_bus):
        """
        Test complete OODA flow for bullish signal.
        
        Flow:
        1. BuddhiDecision (bullish) → TriadService
        2. Risk assessment → RiskManagerAgent
        3. Portfolio check → PortfolioManagerAgent
        4. Execution → OrderExecutor
        5. Event publication → EventBus
        """
        # Setup
        service = TriadService(trading_mode="paper")
        
        exchange_adapter = MockExchangeAdapter()
        
        # Initialize components
        await service.initialize(
            event_bus=mock_event_bus,
            exchange_adapter=exchange_adapter,
            use_enhanced_risk=False  # Use legacy mode for simpler testing
        )
        
        # Create bullish decision
        decision = MockBuddhiDecision(
            action="bullish",
            confidence=0.85,
            rationale="Strong upward momentum detected"
        )
        
        # Execute
        result = await service.execute_trade(
            decision=decision,
            symbol="BTC/EUR",
            quantity=Decimal("0.01")  # Small test quantity
        )
        
        # Verify
        assert result["status"] == "filled"
        assert result["order_id"].startswith("mock-order")
        assert result["filled_qty"] == 0.01
    
    @pytest.mark.asyncio
    async def test_complete_ooda_flow_bearish(self, mock_event_bus):
        """Test complete OODA flow for bearish signal (sell)."""
        service = TriadService(trading_mode="paper")
        
        exchange_adapter = MockExchangeAdapter()
        
        await service.initialize(
            event_bus=mock_event_bus,
            exchange_adapter=exchange_adapter,
            use_enhanced_risk=False
        )
        
        # Create bearish decision
        decision = MockBuddhiDecision(
            action="bearish",
            confidence=0.75,
            rationale="Resistance level rejection"
        )
        
        result = await service.execute_trade(
            decision=decision,
            symbol="BTC/EUR",
            quantity=Decimal("0.01")
        )
        
        assert result["status"] == "filled"
    
    @pytest.mark.asyncio
    async def test_ooda_flow_risk_rejection(self, mock_event_bus):
        """Test OODA flow when risk manager rejects trade."""
        service = TriadService(trading_mode="paper")
        
        exchange_adapter = MockExchangeAdapter()
        
        await service.initialize(
            event_bus=mock_event_bus,
            exchange_adapter=exchange_adapter,
            use_enhanced_risk=False
        )
        
        # Mock risk manager to reject
        service.risk_manager.assess_risk = AsyncMock(return_value=RiskAssessment(
            trade_id="test-123",
            decision=RiskDecision.REJECT,
            rationale="Position limit would be exceeded",
            risk_score=0.85,
            win_probability=0.2
        ))
        
        decision = MockBuddhiDecision(
            action="bullish",
            confidence=0.9,
            rationale="Large position test"
        )
        
        # Try to execute large order
        result = await service.execute_trade(
            decision=decision,
            symbol="BTC/EUR",
            quantity=Decimal("10.0")  # Very large
        )
        
        assert result["status"] == "rejected"


class TestOODADecimalPrecision:
    """Test Decimal precision throughout OODA flow."""
    
    @pytest.mark.asyncio
    async def test_decimal_precision_maintained(self, mock_event_bus):
        """Test that Decimal precision is maintained through OODA loop."""
        service = TriadService(trading_mode="paper")
        
        exchange_adapter = MockExchangeAdapter()
        
        await service.initialize(
            event_bus=mock_event_bus,
            exchange_adapter=exchange_adapter,
            use_enhanced_risk=False
        )
        
        # Use precise quantity
        precise_qty = Decimal("0.12345678")
        
        decision = MockBuddhiDecision(action="bullish", confidence=0.8)
        
        result = await service.execute_trade(
            decision=decision,
            symbol="BTC/EUR",
            quantity=precise_qty
        )
        
        assert result["status"] == "filled"
    
    def test_decimal_vs_float_precision(self):
        """Demonstrate Decimal vs float precision in OODA flow."""
        # Decimal is exact
        decimal_qty = Decimal("0.1")
        decimal_price = Decimal("45000.33")
        decimal_value = decimal_qty * decimal_price
        
        # Verify Decimal precision
        assert decimal_value == Decimal("4500.033")
        
        # Float has precision issues
        float_qty = 0.1
        float_price = 45000.33
        float_value = float_qty * float_price
        
        # Float string representation shows precision loss
        # (e.g., 4500.032999999999 instead of 4500.033)
        assert "4500.032" in str(float_value) or "4500.033" in str(float_value)


class TestOODASecurityIntegration:
    """Test security integration in OODA flow."""
    
    @pytest.mark.asyncio
    async def test_gatekeeper_blocks_unauthorized(self, mock_event_bus):
        """Test that AgentGatekeeper blocks unauthorized trades."""
        service = TriadService(trading_mode="paper")
        
        exchange_adapter = MockExchangeAdapter()
        
        await service.initialize(
            event_bus=mock_event_bus,
            exchange_adapter=exchange_adapter
        )
        
        # Mock gatekeeper to deny permission
        service.gatekeeper.authorize = Mock(return_value=False)
        
        decision = MockBuddhiDecision(action="bullish", confidence=0.8)
        
        result = await service.execute_trade(
            decision=decision,
            symbol="BTC/EUR",
            quantity=Decimal("0.01")
        )
        
        assert result["status"] == "rejected"
        assert "Not authorized" in result["reason"]


class TestOODAStatistics:
    """Test statistics tracking in OODA flow."""
    
    @pytest.mark.asyncio
    async def test_trade_statistics_accumulated(self, mock_event_bus):
        """Test that trade statistics are accumulated correctly."""
        service = TriadService(trading_mode="paper")
        
        exchange_adapter = MockExchangeAdapter()
        
        await service.initialize(
            event_bus=mock_event_bus,
            exchange_adapter=exchange_adapter,
            use_enhanced_risk=False
        )
        
        # Execute multiple trades
        decision = MockBuddhiDecision(action="bullish", confidence=0.8)
        
        for _ in range(3):
            await service.execute_trade(
                decision=decision,
                symbol="BTC/EUR",
                quantity=Decimal("0.01")
            )
        
        stats = service.get_statistics()
        
        assert stats["trades_executed"] == 3
        assert stats["trading_mode"] == "paper"
    
    @pytest.mark.asyncio
    async def test_rejection_statistics_tracked(self, mock_event_bus):
        """Test that rejections are tracked in statistics."""
        service = TriadService(trading_mode="paper")
        
        exchange_adapter = MockExchangeAdapter()
        
        await service.initialize(
            event_bus=mock_event_bus,
            exchange_adapter=exchange_adapter,
            use_enhanced_risk=False
        )
        
        # Mock risk manager to reject
        service.risk_manager.assess_risk = AsyncMock(return_value=RiskAssessment(
            trade_id="test-123",
            decision=RiskDecision.REJECT,
            rationale="Risk limit",
            risk_score=0.9,
            win_probability=0.1
        ))
        
        decision = MockBuddhiDecision(action="bullish", confidence=0.8)
        
        await service.execute_trade(
            decision=decision,
            symbol="BTC/EUR",
            quantity=Decimal("1.0")
        )
        
        stats = service.get_statistics()
        
        assert stats["risk_rejections"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
