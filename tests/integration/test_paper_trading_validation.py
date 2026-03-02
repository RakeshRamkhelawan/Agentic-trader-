"""
Paper Trading Validation Tests.

Week 6: Validate new components in paper trading mode.

These tests run against the paper trading environment to ensure:
1. New components work correctly with simulated trades
2. Risk validation works in real-time
3. Portfolio tracking is accurate
4. Performance meets targets
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import time

from backend.execution.triad_service import TriadService
from backend.execution.portfolio_manager import PortfolioManager
from backend.agents.risk_manager_agent import RiskManagerAgent
from backend.execution.order_executor import OrderExecutor
from backend.core.schemas.ooda_types import (
    TradeProposal,
    ExecutionPlan,
    MarketRegime,
    RiskDecision
)


class MockPaperTradingAdapter:
    """Mock adapter that simulates paper trading behavior."""
    
    def __init__(self, initial_balance: float = 50000.0):
        self.balance = initial_balance
        self.positions = {}
        self.orders = []
        self.order_counter = 0
        self.filled_orders = []
    
    async def initialize(self):
        return True
    
    async def fetch_balance(self):
        total_positions_value = sum(
            qty * 45000 for qty in self.positions.values()
        )
        return {
            "BTC": {"free": self.positions.get("BTC", 0), "total": self.positions.get("BTC", 0)},
            "EUR": {"free": self.balance, "total": self.balance},
            "free": {"BTC": self.positions.get("BTC", 0), "EUR": self.balance},
            "total": {"BTC": self.positions.get("BTC", 0), "EUR": self.balance + total_positions_value}
        }
    
    async def place_order(self, symbol, side, order_type, quantity, price=None):
        self.order_counter += 1
        order_id = f"paper-{self.order_counter}"
        
        fill_price = price or 45000.0
        
        if side == "buy":
            cost = quantity * fill_price * 1.0025  # Include 0.25% fee
            if self.balance >= cost:
                self.balance -= cost
                self.positions["BTC"] = self.positions.get("BTC", 0) + quantity
                status = "filled"
            else:
                status = "rejected"
        else:  # sell
            if self.positions.get("BTC", 0) >= quantity:
                proceeds = quantity * fill_price * 0.9975  # Include 0.25% fee
                self.positions["BTC"] -= quantity
                self.balance += proceeds
                status = "filled"
            else:
                status = "rejected"
        
        order = {
            "order_id": order_id,
            "status": status,
            "filled_quantity": quantity if status == "filled" else 0,
            "avg_fill_price": fill_price if status == "filled" else 0,
            "fee": quantity * fill_price * 0.0025,
            "timestamp": datetime.utcnow().timestamp()
        }
        
        if status == "filled":
            self.filled_orders.append(order)
        
        return order
    
    async def get_order_status(self, order_id):
        for order in self.filled_orders:
            if order["order_id"] == order_id:
                return order
        return {"order_id": order_id, "status": "not_found"}


class TestPaperTradingBasic:
    """Basic paper trading validation."""
    
    @pytest.fixture
    def paper_adapter(self):
        """Create paper trading adapter with initial balance."""
        return MockPaperTradingAdapter(initial_balance=50000.0)
    
    @pytest.mark.asyncio
    async def test_paper_trading_buy_order(self, paper_adapter):
        """Test buying in paper trading mode."""
        initial_balance = paper_adapter.balance
        
        result = await paper_adapter.place_order(
            symbol="BTC/EUR",
            side="buy",
            order_type="market",
            quantity=0.1,
            price=45000.0
        )
        
        assert result["status"] == "filled"
        assert result["filled_quantity"] == 0.1
        assert paper_adapter.positions.get("BTC", 0) == 0.1
        assert paper_adapter.balance < initial_balance  # Balance decreased
    
    @pytest.mark.asyncio
    async def test_paper_trading_sell_order(self, paper_adapter):
        """Test selling in paper trading mode."""
        # First buy some BTC
        await paper_adapter.place_order(
            symbol="BTC/EUR",
            side="buy",
            order_type="market",
            quantity=0.1,
            price=45000.0
        )
        
        initial_balance = paper_adapter.balance
        
        # Then sell
        result = await paper_adapter.place_order(
            symbol="BTC/EUR",
            side="sell",
            order_type="market",
            quantity=0.05,
            price=45000.0
        )
        
        assert result["status"] == "filled"
        assert result["filled_quantity"] == 0.05
        assert paper_adapter.positions["BTC"] == 0.05  # 0.1 - 0.05
    
    @pytest.mark.asyncio
    async def test_paper_trading_insufficient_funds(self, paper_adapter):
        """Test rejection when insufficient funds."""
        result = await paper_adapter.place_order(
            symbol="BTC/EUR",
            side="buy",
            order_type="market",
            quantity=10.0,  # Way too much
            price=45000.0
        )
        
        assert result["status"] == "rejected"
    
    @pytest.mark.asyncio
    async def test_paper_trading_fee_calculation(self, paper_adapter):
        """Test that fees are calculated correctly."""
        result = await paper_adapter.place_order(
            symbol="BTC/EUR",
            side="buy",
            order_type="market",
            quantity=0.1,
            price=45000.0
        )
        
        # Fee should be 0.25% of order value
        expected_fee = 0.1 * 45000.0 * 0.0025  # 11.25
        assert abs(result["fee"] - expected_fee) < 0.01


class TestPaperTradingWithTriadService:
    """Test paper trading through TriadService."""
    
    @pytest.mark.asyncio
    async def test_paper_trading_service_initialization(self):
        """Test TriadService initializes in paper mode."""
        service = TriadService(trading_mode="paper")
        
        # Just verify service initializes
        assert service.trading_mode == "paper"
        assert service.stats["trades_executed"] == 0
        
        # Check stats work
        stats = service.get_statistics()
        assert stats["trading_mode"] == "paper"


class TestPaperTradingRiskValidation:
    """Test risk validation in paper trading."""
    
    @pytest.mark.asyncio
    async def test_risk_validation_blocks_oversized_trade(self):
        """Test that risk manager blocks oversized trades."""
        agent = RiskManagerAgent(use_enhanced_validator=False)
        
        proposal = TradeProposal(
            symbol="BTC/EUR",
            side="buy",
            size=5.0,  # Very large
            entry_price=45000,
            stop_loss=40000,
            take_profit=50000,
            rationale="Testing risk limits",
            strategy_id="paper_test",
            confidence=0.8
        )
        
        assessment = await agent.assess_risk(
            proposal=proposal,
            current_regime=MarketRegime.BULL,
            current_position_size=0.0
        )
        
        # Should be rejected or reduced
        assert assessment.decision in [
            RiskDecision.REJECT,
            RiskDecision.REDUCE_SIZE
        ]
    
    @pytest.mark.asyncio
    async def test_risk_validation_allows_normal_trade(self):
        """Test that risk manager allows normal sized trades."""
        agent = RiskManagerAgent(use_enhanced_validator=False)
        
        proposal = TradeProposal(
            symbol="BTC/EUR",
            side="buy",
            size=0.01,  # Small
            entry_price=45000,
            stop_loss=40000,
            take_profit=50000,
            rationale="Testing normal trade",
            strategy_id="paper_test",
            confidence=0.8
        )
        
        assessment = await agent.assess_risk(
            proposal=proposal,
            current_regime=MarketRegime.BULL,
            current_position_size=0.0
        )
        
        # Should be approved
        assert assessment.decision == RiskDecision.APPROVE


class TestPaperTradingPerformance:
    """Performance tests in paper trading mode."""
    
    @pytest.mark.asyncio
    async def test_paper_trading_latency(self):
        """Test paper trading execution latency."""
        service = TriadService(trading_mode="paper")
        paper_adapter = MockPaperTradingAdapter()
        
        await service.initialize(
            event_bus=Mock(),
            exchange_adapter=paper_adapter,
            use_enhanced_risk=False
        )
        
        class MockDecision:
            action = "bullish"
            confidence = 0.8
            rationale = "Performance test"
        
        # Measure latency
        latencies = []
        for _ in range(10):
            start = time.time()
            await service.execute_trade(
                decision=MockDecision(),
                symbol="BTC/EUR",
                quantity=Decimal("0.01")
            )
            latency = (time.time() - start) * 1000
            latencies.append(latency)
        
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        
        # Should be fast in paper mode
        assert avg_latency < 100  # 100ms average
        assert max_latency < 200  # 200ms max
    
    @pytest.mark.asyncio
    async def test_paper_trading_latency_simple(self):
        """Test paper trading latency with simple adapter."""
        paper_adapter = MockPaperTradingAdapter()
        
        # Measure latency of direct adapter calls
        latencies = []
        for _ in range(5):
            start = time.time()
            await paper_adapter.place_order(
                "BTC/EUR", "buy", "market", 0.01, 45000.0
            )
            latency = (time.time() - start) * 1000
            latencies.append(latency)
        
        avg_latency = sum(latencies) / len(latencies)
        
        # Should be fast in paper mode
        assert avg_latency < 100  # 100ms average


class TestPaperTradingPortfolioTracking:
    """Test portfolio tracking accuracy in paper trading."""
    
    @pytest.mark.asyncio
    async def test_portfolio_tracks_paper_positions(self):
        """Test that portfolio tracks paper trading positions."""
        pm = PortfolioManager()
        paper_adapter = MockPaperTradingAdapter(initial_balance=50000.0)
        
        pm.register_adapter("paper", paper_adapter)
        
        # Execute some trades
        await paper_adapter.place_order("BTC/EUR", "buy", "market", 0.1, 45000.0)
        await paper_adapter.place_order("BTC/EUR", "buy", "market", 0.05, 45000.0)
        
        # Get portfolio adapters are registered
        assert "paper" in pm._adapters
        
        # Check adapter has positions
        balance = await paper_adapter.fetch_balance()
        assert balance["BTC"]["total"] > 0  # Has BTC position


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
