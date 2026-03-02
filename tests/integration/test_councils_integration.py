"""
Integration Tests for Dynamic Councils (Phase 3)

Tests Guna Council, Mind Council, and Orchestrator integration.
"""

import asyncio
import pytest
from datetime import datetime

from backend.councils.dynamic_guna_council import (
    DynamicGunaCouncil, GunaVector, get_guna_council
)
from backend.councils.mind_council import MindCouncil, get_mind_council
from backend.councils.council_orchestrator import (
    CouncilOrchestrator, CouncilView, get_orchestrator
)


@pytest.fixture
def guna_council():
    """Create Guna Council with test calibration."""
    calibration = {
        "normal_vol": 0.02,
        "high_vol": 0.035,
        "high_volume": 1.34
    }
    return DynamicGunaCouncil(calibration)


@pytest.fixture
def mind_council():
    """Create Mind Council."""
    return MindCouncil()


@pytest.fixture
def orchestrator():
    """Create Council Orchestrator."""
    return get_orchestrator()


class TestGunaCouncilIntegration:
    """Test Dynamic Guna Council with real market scenarios."""
    
    def test_calm_market(self, guna_council):
        """Test Guna analysis in calm market conditions."""
        market_data = {
            "volatility_1m": 0.015,
            "momentum_1d": 0.005,
            "volume_ratio": 0.9,
            "bid_ask_spread": 0.0005,
            "trend": 0
        }
        
        result = guna_council.analyze(market_data)
        
        assert result["council_type"] == "guna"
        assert "guna_vector" in result
        
        guna = result["guna_vector"]
        assert guna["sattva"] > 0.5, f"Expected Sattva > 50%, got {guna['sattva']}"
        assert guna["dominant"] == "sattva"
        
        print(f"\nCalm market: Sattva={guna['sattva']:.1%}, Rajas={guna['rajas']:.1%}, Tamas={guna['tamas']:.1%}")
    
    def test_trending_market(self, guna_council):
        """Test Guna analysis in trending market."""
        market_data = {
            "volatility_1m": 0.04,
            "momentum_1d": 0.035,
            "volume_ratio": 1.8,
            "bid_ask_spread": 0.001,
            "trend": 1
        }
        
        result = guna_council.analyze(market_data)
        guna = result["guna_vector"]
        
        assert guna["rajas"] > 0.5, f"Expected Rajas > 50%, got {guna['rajas']}"
        assert guna["dominant"] == "rajas"
        assert result["perspective"] == "bullish"
        
        print(f"\nTrending market: Sattva={guna['sattva']:.1%}, Rajas={guna['rajas']:.1%}, Tamas={guna['tamas']:.1%}")
    
    def test_crash_scenario(self, guna_council):
        """Test Guna analysis in crash scenario."""
        market_data = {
            "volatility_1m": 0.08,
            "momentum_1d": -0.05,
            "volume_ratio": 2.5,
            "bid_ask_spread": 0.003,
            "trend": -1
        }
        
        result = guna_council.analyze(market_data)
        guna = result["guna_vector"]
        
        assert guna["rajas"] > 0.7, f"Expected high Rajas in crash, got {guna['rajas']}"
        assert result["perspective"] == "bearish"
        
        print(f"\nCrash: Sattva={guna['sattva']:.1%}, Rajas={guna['rajas']:.1%}, Tamas={guna['tamas']:.1%}")
    
    def test_illiquid_market(self, guna_council):
        """Test Guna analysis in illiquid market."""
        market_data = {
            "volatility_1m": 0.01,
            "momentum_1d": 0.001,
            "volume_ratio": 0.4,
            "bid_ask_spread": 0.005,
            "trend": 0
        }
        
        result = guna_council.analyze(market_data)
        guna = result["guna_vector"]
        
        assert guna["tamas"] > 0.3, f"Expected elevated Tamas, got {guna['tamas']}"
        
        print(f"\nIlliquid: Sattva={guna['sattva']:.1%}, Rajas={guna['rajas']:.1%}, Tamas={guna['tamas']:.1%}")


class TestMindCouncilIntegration:
    """Test Mind Council fear/greed analysis."""
    
    def test_extreme_fear(self, mind_council):
        """Test fear detection in capitulation."""
        market_data = {
            "momentum_1d": -0.08,
            "momentum_3d": -0.15,
            "volatility_1m": 0.07,
            "volume_ratio": 3.0,
            "bid_ask_spread": 0.004,
            "imbalance": -0.6
        }
        
        result = mind_council.analyze(market_data)
        
        assert result["fear_greed_index"] < 30, f"Expected Fear < 30, got {result['fear_greed_index']}"
        assert result["council_type"] == "mind"
        assert "components" in result
        
        print(f"\nExtreme fear: {result['fear_greed_index']:.0f} - {mind_council.get_sentiment_label(result['fear_greed_index'])}")
    
    def test_extreme_greed(self, mind_council):
        """Test greed detection in euphoria."""
        market_data = {
            "momentum_1d": 0.12,
            "momentum_3d": 0.25,
            "volatility_1m": 0.05,
            "volume_ratio": 2.5,
            "bid_ask_spread": 0.001,
            "imbalance": 0.7
        }
        
        result = mind_council.analyze(market_data)
        
        assert result["fear_greed_index"] > 70, f"Expected Greed > 70, got {result['fear_greed_index']}"
        
        print(f"\nExtreme greed: {result['fear_greed_index']:.0f} - {mind_council.get_sentiment_label(result['fear_greed_index'])}")
    
    def test_neutral_sentiment(self, mind_council):
        """Test neutral market sentiment."""
        market_data = {
            "momentum_1d": 0.005,
            "momentum_3d": 0.01,
            "volatility_1m": 0.018,
            "volume_ratio": 0.9,
            "bid_ask_spread": 0.0005,
            "imbalance": 0.05
        }
        
        result = mind_council.analyze(market_data)
        
        assert 40 <= result["fear_greed_index"] <= 60, f"Expected neutral 40-60, got {result['fear_greed_index']}"
        
        print(f"\nNeutral: {result['fear_greed_index']:.0f} - {mind_council.get_sentiment_label(result['fear_greed_index'])}")


class TestCouncilOrchestratorIntegration:
    """Test Council Orchestrator with multiple councils."""
    
    @pytest.mark.asyncio
    async def test_deliberation_bullish_consensus(self, orchestrator):
        """Test deliberation with bullish consensus."""
        market_data = {
            "volatility_1m": 0.035,
            "momentum_1d": 0.04,
            "momentum_3d": 0.08,
            "volume_ratio": 1.8,
            "bid_ask_spread": 0.001,
            "trend": 1,
            "imbalance": 0.4
        }
        
        result = await orchestrator.deliberate(market_data, "test_bullish")
        
        assert "council_views" in result
        assert "coherence" in result
        assert "final_perspective" in result
        assert "final_confidence" in result
        
        # Should have 2 councils
        assert len(result["council_views"]) == 2
        
        # Coherence should be calculable
        assert 0 <= result["coherence"] <= 1
        
        print(f"\nBullish consensus:")
        print(f"  Final: {result['final_perspective']} (conf: {result['final_confidence']:.2f})")
        print(f"  Coherence: {result['coherence']:.2f}")
        for view in result["council_views"]:
            print(f"  {view['council']}: {view['perspective']} (conf: {view['confidence']:.2f})")
    
    @pytest.mark.asyncio
    async def test_deliberation_mixed_signals(self, orchestrator):
        """Test deliberation with conflicting council views."""
        # Guna: bullish (trend up), Mind: neutral/fear (extreme move)
        market_data = {
            "volatility_1m": 0.06,  # High vol = fear
            "momentum_1d": 0.08,    # But strong up
            "momentum_3d": 0.15,
            "volume_ratio": 2.2,
            "bid_ask_spread": 0.002,
            "trend": 1,
            "imbalance": 0.5
        }
        
        result = await orchestrator.deliberate(market_data, "test_mixed")
        
        # Coherence should be lower with mixed signals
        assert result["coherence"] < 1.0
        
        print(f"\nMixed signals:")
        print(f"  Final: {result['final_perspective']} (conf: {result['final_confidence']:.2f})")
        print(f"  Coherence: {result['coherence']:.2f} (lower = more disagreement)")
    
    def test_coherence_calculation_agreement(self, orchestrator):
        """Test coherence with agreeing councils."""
        views = [
            CouncilView("guna", "bullish", 0.8, [], {}),
            CouncilView("mind", "bullish", 0.7, [], {}),
        ]
        
        coherence = orchestrator._calculate_coherence(views)
        
        assert coherence == 1.0, f"Expected perfect coherence, got {coherence}"
        print(f"\nAgreement coherence: {coherence:.2f}")
    
    def test_coherence_calculation_conflict(self, orchestrator):
        """Test coherence with conflicting councils."""
        views = [
            CouncilView("guna", "bullish", 0.8, [], {}),
            CouncilView("mind", "bearish", 0.7, [], {}),
        ]
        
        coherence = orchestrator._calculate_coherence(views)
        
        assert coherence < 0.5, f"Expected low coherence, got {coherence}"
        print(f"\nConflict coherence: {coherence:.2f}")
    
    def test_weighted_perspective_bullish(self, orchestrator):
        """Test weighted perspective calculation."""
        views = [
            CouncilView("guna", "bullish", 0.8, [], {}),
            CouncilView("mind", "neutral", 0.5, [], {}),
        ]
        
        perspective, confidence = orchestrator._weigh_perspectives(views)
        
        assert perspective == "bullish"
        assert confidence > 0
        
        print(f"\nWeighted perspective: {perspective} (conf: {confidence:.2f})")


class TestEndToEndIntegration:
    """End-to-end integration tests."""
    
    @pytest.mark.asyncio
    async def test_full_pipeline(self):
        """Test complete pipeline: Market Data → Councils → Events."""
        from backend.events.triad_event_bus import get_event_bus
        
        # Setup
        orchestrator = get_orchestrator()
        
        # Realistic market scenario
        market_data = {
            "volatility_1m": 0.03,
            "momentum_1d": 0.025,
            "momentum_3d": 0.05,
            "volume_ratio": 1.5,
            "bid_ask_spread": 0.001,
            "trend": 1,
            "imbalance": 0.3
        }
        
        # Run deliberation (publishes events)
        result = await orchestrator.deliberate(market_data, "e2e_test")
        
        # Verify result structure
        assert result["final_perspective"] in ["bullish", "bearish", "neutral"]
        assert 0 <= result["coherence"] <= 1
        assert len(result["council_views"]) >= 1
        
        print(f"\n✓ Full pipeline completed")
        print(f"  Final decision: {result['final_perspective']}")
        print(f"  Coherence: {result['coherence']:.2f}")
        print(f"  Councils consulted: {len(result['council_views'])}")


class TestPerformanceIntegration:
    """Performance tests."""
    
    @pytest.mark.asyncio
    async def test_deliberation_performance(self, orchestrator):
        """Test that deliberation completes within 100ms."""
        import time
        
        market_data = {
            "volatility_1m": 0.025,
            "momentum_1d": 0.02,
            "volume_ratio": 1.2,
            "bid_ask_spread": 0.001,
            "trend": 1,
            "imbalance": 0.2
        }
        
        # Warm up
        await orchestrator.deliberate(market_data, "perf_warmup")
        
        # Measure
        start = time.time()
        await orchestrator.deliberate(market_data, "perf_test")
        elapsed = (time.time() - start) * 1000
        
        print(f"\nDeliberation time: {elapsed:.1f}ms")
        assert elapsed < 100, f"Deliberation too slow: {elapsed:.1f}ms"
    
    def test_guna_calculation_performance(self, guna_council):
        """Test Guna calculation performance."""
        import time
        
        market_data = {
            "volatility_1m": 0.02,
            "momentum_1d": 0.015,
            "volume_ratio": 1.1,
            "bid_ask_spread": 0.001,
            "trend": 1
        }
        
        # Run 100 calculations
        start = time.time()
        for _ in range(100):
            guna_council.analyze(market_data)
        elapsed = (time.time() - start) * 1000 / 100
        
        print(f"\nGuna calculation: {elapsed:.2f}ms avg")
        assert elapsed < 10, f"Guna calculation too slow: {elapsed:.2f}ms"


if __name__ == "__main__":
    # Manual test runner
    print("=" * 60)
    print("COUNCILS INTEGRATION TESTS")
    print("=" * 60)
    
    guna = DynamicGunaCouncil()
    mind = MindCouncil()
    
    # Test scenarios
    scenarios = [
        ("Bullish trend", {
            "volatility_1m": 0.03, "momentum_1d": 0.03, "volume_ratio": 1.5,
            "bid_ask_spread": 0.001, "trend": 1, "imbalance": 0.3
        }),
        ("Bearish crash", {
            "volatility_1m": 0.07, "momentum_1d": -0.05, "volume_ratio": 2.5,
            "bid_ask_spread": 0.003, "trend": -1, "imbalance": -0.5
        }),
        ("Neutral calm", {
            "volatility_1m": 0.018, "momentum_1d": 0.005, "volume_ratio": 0.9,
            "bid_ask_spread": 0.0005, "trend": 0, "imbalance": 0.05
        }),
    ]
    
    for name, data in scenarios:
        print(f"\n{name}:")
        
        # Guna
        guna_result = guna.analyze(data)
        gv = guna_result["guna_vector"]
        print(f"  Guna: {gv['dominant']} (S:{gv['sattva']:.0%} R:{gv['rajas']:.0%} T:{gv['tamas']:.0%})")
        
        # Mind
        mind_result = mind.analyze(data)
        fg = mind_result["fear_greed_index"]
        print(f"  Mind: {fg:.0f} - {mind.get_sentiment_label(fg)}")
    
    print("\n" + "=" * 60)
    print("Tests complete!")
