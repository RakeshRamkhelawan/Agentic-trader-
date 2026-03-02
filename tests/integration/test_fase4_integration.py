"""
Phase 4 Integration Tests

Tests Body Council, Buddhi Mind, and Triad Service integration.
"""

import sys
import asyncio
from datetime import datetime

sys.path.insert(0, '.')

from backend.councils.body_council import get_body_council
from backend.councils.buddhi_mind import get_buddhi_mind
from backend.services.triad_service import get_triad_service


async def test_body_council():
    """Test Body Council execution analysis."""
    print("\n1. Testing Body Council...")
    
    council = get_body_council()
    
    # Test liquid market
    liquid_data = {
        "bid_ask_spread": 0.0005,
        "orderbook_depth": 500000,
        "volume_24h": 50000000,
        "trade_size_usd": 10000
    }
    
    result = council.analyze_execution_environment(liquid_data)
    
    assert result["perspective"] == "favorable"
    assert result["execution_quality"] == "excellent"
    print(f"   Liquid market: {result['execution_quality']} (conf: {result['confidence']:.2f})")
    
    # Test illiquid market
    illiquid_data = {
        "bid_ask_spread": 0.005,
        "orderbook_depth": 5000,
        "volume_24h": 100000,
        "trade_size_usd": 10000
    }
    
    result = council.analyze_execution_environment(illiquid_data)
    
    assert result["perspective"] == "avoid"
    assert result["execution_quality"] == "poor"
    print(f"   Illiquid market: {result['execution_quality']} (conf: {result['confidence']:.2f})")
    
    print("   Status: PASS")
    return True


async def test_buddhi_mind():
    """Test Buddhi Mind decision making."""
    print("\n2. Testing Buddhi Mind...")
    
    buddhi = get_buddhi_mind()
    
    # Test bullish consensus
    bullish_views = [
        {"council_type": "guna", "perspective": "bullish", "confidence": 0.85},
        {"council_type": "mind", "perspective": "bullish", "confidence": 0.75},
        {"council_type": "body", "perspective": "favorable", "confidence": 0.90}
    ]
    
    market = {"volatility_1m": 0.025}
    
    decision = buddhi.decide(bullish_views, market, "test", datetime.utcnow().isoformat())
    
    assert decision.action == "bullish"
    assert decision.confidence > 0.6
    assert decision.coherence > 0.5
    assert decision.is_executable()
    
    print(f"   Bullish consensus: {decision.action} (conf: {decision.confidence:.2f}, coh: {decision.coherence:.2f})")
    
    # Test conflicting views
    mixed_views = [
        {"council_type": "guna", "perspective": "bullish", "confidence": 0.70},
        {"council_type": "mind", "perspective": "bearish", "confidence": 0.65}
    ]
    
    decision = buddhi.decide(mixed_views, market, "test2", datetime.utcnow().isoformat())
    
    assert decision.action == "hold"  # Should hold due to disagreement
    
    print(f"   Mixed signals: {decision.action} (risk: {decision.risk_assessment['level']})")
    print("   Status: PASS")
    return True


async def test_triad_service():
    """Test complete Triad Service pipeline."""
    print("\n3. Testing Triad Service...")
    
    service = get_triad_service()
    
    market_data = {
        "volatility_1m": 0.03,
        "momentum_1d": 0.025,
        "momentum_3d": 0.05,
        "volume_ratio": 1.4,
        "bid_ask_spread": 0.001,
        "trend": 1,
        "imbalance": 0.25,
        "orderbook_depth": 200000,
        "volume_24h": 10000000
    }
    
    # Process through Triad
    decision = await service.process_market_data(market_data, "integration_test")
    
    assert decision is not None
    assert decision.action in ["bullish", "bearish", "neutral"]
    assert 0 <= decision.confidence <= 1
    assert 0 <= decision.coherence <= 1
    
    print(f"   Decision: {decision.action}")
    print(f"   Confidence: {decision.confidence:.2f}")
    print(f"   Coherence: {decision.coherence:.2f}")
    print(f"   Risk: {decision.risk_assessment['level']}")
    
    # Test paper trade execution
    if decision.is_executable():
        result = await service.execute_paper_trade(decision, "BTC")
        assert result["status"] == "filled"
        print(f"   Paper trade: {result['status']}")
    
    # Check stats
    stats = service.get_stats()
    assert stats["total_deliberations"] >= 1
    
    print("   Status: PASS")
    return True


async def main():
    """Run all Phase 4 integration tests."""
    print("=" * 60)
    print("PHASE 4 INTEGRATION TESTS")
    print("=" * 60)
    
    results = []
    
    try:
        results.append(("Body Council", await test_body_council()))
    except Exception as e:
        print(f"   Status: FAIL - {e}")
        results.append(("Body Council", False))
    
    try:
        results.append(("Buddhi Mind", await test_buddhi_mind()))
    except Exception as e:
        print(f"   Status: FAIL - {e}")
        results.append(("Buddhi Mind", False))
    
    try:
        results.append(("Triad Service", await test_triad_service()))
    except Exception as e:
        print(f"   Status: FAIL - {e}")
        results.append(("Triad Service", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {name}: {status}")
    
    print(f"\nTotal: {passed}/{total} passed")
    
    if passed == total:
        print("\n🎉 All Phase 4 integration tests passed!")
        return 0
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
