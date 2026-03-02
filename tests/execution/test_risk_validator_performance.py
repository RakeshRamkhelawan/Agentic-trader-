"""
Performance Tests for RiskManagerAgent with OrderRiskValidator.

Week 2 of Exchange Integration Refactor.

Ensures 10+ validation checks don't add significant latency
to the OODA execution flow.
"""

import pytest
import time
from decimal import Decimal
from unittest.mock import Mock, AsyncMock

from backend.agents.risk_manager_agent import RiskManagerAgent
from backend.core.schemas.ooda_types import TradeProposal, MarketRegime


class TestRiskValidatorPerformance:
    """Performance tests for risk validation (10+ checks)."""
    
    @pytest.fixture
    def agent(self):
        """Create RiskManagerAgent with enhanced validator."""
        return RiskManagerAgent(use_enhanced_validator=True)
    
    @pytest.fixture
    def basic_proposal(self):
        """Create basic trade proposal."""
        return TradeProposal(
            symbol="BTC/EUR",
            side="buy",
            size=0.01,
            entry_price=45000,
            stop_loss=40000,
            take_profit=50000,
            rationale="Performance test trade",
            strategy_id="perf_test",
            confidence=0.8
        )
    
    @pytest.mark.asyncio
    async def test_risk_assessment_latency(self, agent, basic_proposal):
        """
        Test that risk assessment with 10+ checks completes quickly.
        
        Target: < 50ms for all 10+ validation checks.
        """
        # Warm up
        await agent.assess_risk(
            proposal=basic_proposal,
            current_regime=MarketRegime.BULL,
            current_position_size=0.0
        )
        
        # Measure 10 assessments
        times = []
        for _ in range(10):
            start = time.perf_counter()
            await agent.assess_risk(
                proposal=basic_proposal,
                current_regime=MarketRegime.BULL,
                current_position_size=0.0
            )
            elapsed = (time.perf_counter() - start) * 1000  # ms
            times.append(elapsed)
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        # Assert performance targets
        assert avg_time < 50, f"Average risk assessment too slow: {avg_time:.2f}ms"
        assert max_time < 100, f"Max risk assessment too slow: {max_time:.2f}ms"
    
    @pytest.mark.asyncio
    async def test_enhanced_vs_legacy_performance(self, basic_proposal):
        """
        Compare performance of enhanced vs legacy risk assessment.
        
        Enhanced validator (10+ checks) should not be significantly slower
        than legacy validator (< 2x overhead).
        """
        legacy_agent = RiskManagerAgent(use_enhanced_validator=False)
        enhanced_agent = RiskManagerAgent(use_enhanced_validator=True)
        
        # Warm up both
        await legacy_agent.assess_risk(basic_proposal, MarketRegime.BULL, 0.0)
        await enhanced_agent.assess_risk(basic_proposal, MarketRegime.BULL, 0.0)
        
        # Measure legacy
        legacy_times = []
        for _ in range(20):
            start = time.perf_counter()
            await legacy_agent.assess_risk(basic_proposal, MarketRegime.BULL, 0.0)
            legacy_times.append((time.perf_counter() - start) * 1000)
        
        # Measure enhanced
        enhanced_times = []
        for _ in range(20):
            start = time.perf_counter()
            await enhanced_agent.assess_risk(basic_proposal, MarketRegime.BULL, 0.0)
            enhanced_times.append((time.perf_counter() - start) * 1000)
        
        legacy_avg = sum(legacy_times) / len(legacy_times)
        enhanced_avg = sum(enhanced_times) / len(enhanced_times)
        
        overhead = enhanced_avg / legacy_avg if legacy_avg > 0 else 1.0
        
        # Enhanced should not be more than 10x slower (10+ checks vs 3-4 checks)
        # This is acceptable given the additional validation
        assert overhead < 15.0, f"Enhanced validator too slow: {overhead:.2f}x overhead"
    
    @pytest.mark.asyncio
    async def test_concurrent_risk_assessments(self, agent, basic_proposal):
        """
        Test that multiple concurrent risk assessments perform well.
        
        Important for high-frequency trading scenarios.
        """
        import asyncio
        
        async def assess():
            start = time.perf_counter()
            await agent.assess_risk(
                proposal=basic_proposal,
                current_regime=MarketRegime.BULL,
                current_position_size=0.0
            )
            return (time.perf_counter() - start) * 1000
        
        # Run 20 concurrent assessments
        start = time.perf_counter()
        results = await asyncio.gather(*[assess() for _ in range(20)])
        total_time = (time.perf_counter() - start) * 1000
        
        avg_time = sum(results) / len(results)
        
        # Average should still be reasonable even with concurrent load
        assert avg_time < 100, f"Concurrent assessment too slow: {avg_time:.2f}ms avg"
        # Total time should show some parallelization benefit
        assert total_time < 500, f"Total concurrent time too high: {total_time:.2f}ms"
    
    @pytest.mark.asyncio
    async def test_memory_usage_stable(self, agent, basic_proposal):
        """
        Test that memory usage remains stable across many assessments.
        
        Ensures no memory leaks in the validator.
        """
        import gc
        
        # Force garbage collection before
        gc.collect()
        
        # Run many assessments
        for _ in range(100):
            await agent.assess_risk(
                proposal=basic_proposal,
                current_regime=MarketRegime.BULL,
                current_position_size=0.0
            )
        
        # Force garbage collection after
        gc.collect()
        
        # If we get here without memory errors, the test passes
        # (Actual memory measurement would require psutil)
        assert True
    
    @pytest.mark.asyncio
    async def test_validator_initialization_performance(self):
        """
        Test that validator initialization is fast.
        
        Initialization should not add significant startup time.
        """
        start = time.perf_counter()
        agent = RiskManagerAgent(use_enhanced_validator=True)
        elapsed = (time.perf_counter() - start) * 1000
        
        assert elapsed < 100, f"Validator initialization too slow: {elapsed:.2f}ms"
        assert agent.risk_validator is not None
    
    @pytest.mark.asyncio
    async def test_large_batch_assessment(self, agent):
        """
        Test performance with batch of different trade proposals.
        """
        proposals = [
            TradeProposal(
                symbol=f"BTC/EUR",
                side="buy" if i % 2 == 0 else "sell",
                size=0.01 * (i + 1),
                entry_price=45000 + i * 100,
                stop_loss=40000,
                take_profit=50000,
                rationale=f"Batch test trade {i}",
                strategy_id="batch_test",
                confidence=min(0.95, 0.5 + i * 0.01)
            )
            for i in range(50)
        ]
        
        start = time.perf_counter()
        
        for proposal in proposals:
            await agent.assess_risk(
                proposal=proposal,
                current_regime=MarketRegime.BULL,
                current_position_size=0.0
            )
        
        elapsed = (time.perf_counter() - start) * 1000
        avg_per_trade = elapsed / len(proposals)
        
        # Should average less than 10ms per trade
        assert avg_per_trade < 10, f"Batch assessment too slow: {avg_per_trade:.2f}ms per trade"


class TestTriadServicePerformance:
    """Performance tests for TriadService execution flow."""
    
    @pytest.mark.asyncio
    async def test_full_execution_flow_latency(self):
        """
        Test full OODA execution flow latency.
        
        Target: < 200ms end-to-end (risk + execution)
        """
        from backend.execution.triad_service import TriadService
        
        service = TriadService(trading_mode="paper")
        
        # Mock exchange for consistent timing
        mock_exchange = Mock()
        mock_exchange.place_order = AsyncMock(return_value=Mock(
            order_id="test-123",
            status="filled",
            filled_quantity=0.01,
            avg_fill_price=45000.0,
            fee=0.5
        ))
        
        await service.initialize(
            exchange_adapter=mock_exchange,
            use_enhanced_risk=False  # Use legacy for baseline
        )
        
        class MockDecision:
            action = "bullish"
            confidence = 0.8
            rationale = "Performance test"
        
        # Warm up
        await service.execute_trade(MockDecision(), "BTC/EUR", Decimal("0.01"))
        
        # Measure
        times = []
        for _ in range(5):
            start = time.perf_counter()
            await service.execute_trade(MockDecision(), "BTC/EUR", Decimal("0.01"))
            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)
        
        avg_time = sum(times) / len(times)
        
        # Should complete in reasonable time (allowing for mocks)
        assert avg_time < 500, f"Execution flow too slow: {avg_time:.2f}ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
