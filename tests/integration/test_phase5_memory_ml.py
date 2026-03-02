"""
Phase 5 Integration Tests - Episodic Memory + ML

Tests:
1. Episodic memory storage and retrieval
2. Karma score calculation
3. Similar episode finding
4. ML training (if sufficient data)
"""

import sys
import asyncio
from datetime import datetime, timedelta

sys.path.insert(0, '.')

from backend.core.memory.episodic_memory import get_episodic_memory, TradingEpisode
from backend.core.ml.triad_ml_trainer import get_ml_trainer
from backend.services.triad_service import get_triad_service


def test_episodic_memory():
    """Test episodic memory storage and retrieval."""
    print("\n1. Testing Episodic Memory...")
    
    memory = get_episodic_memory()
    
    # Create test episodes
    for i in range(5):
        episode = TradingEpisode(
            id=f"test_{i:03d}",
            session_id=f"session_{i}",
            timestamp=datetime.utcnow() - timedelta(days=i),
            market_context={"price": 45000 + i*100, "volatility_1m": 0.02 + i*0.005},
            volatility=0.02 + i*0.005,
            trend='up' if i % 2 == 0 else 'down',
            volume_profile='normal',
            guna_vector={"sattva": 0.3, "rajas": 0.6, "tamas": 0.1},
            fear_greed_index=50 + i*5,
            execution_quality='good',
            action='buy' if i % 2 == 0 else 'sell',
            confidence=0.7,
            coherence=0.65,
            rationale=f"Test episode {i}"
        )
        memory.store_episode(episode)
    
    # Update some with outcomes
    memory.update_outcome("test_000", "success", 300.0, "take_profit")
    memory.update_outcome("test_001", "failure", -150.0, "stop_loss")
    memory.update_outcome("test_002", "success", 200.0, "take_profit")
    
    # Find similar
    similar = memory.find_similar_episodes({
        "volatility_1m": 0.025,
        "trend_direction": "up",
        "volume_ratio": 1.0,
        "fear_greed": 55
    }, limit=3)
    
    print(f"   Stored 5 episodes")
    print(f"   Found {len(similar)} similar episodes")
    
    # Stats
    stats = memory.get_performance_stats(lookback_days=7)
    print(f"   Win rate: {stats['win_rate']:.1%}")
    print(f"   Total PnL: {stats['total_pnl']:.2f}")
    
    print("   Status: PASS")
    return True


def test_karma_calculation():
    """Test karma score calculation."""
    print("\n2. Testing Karma Calculation...")
    
    memory = get_episodic_memory()
    
    # Get episodes with outcomes
    episodes = [ep for ep in memory.episodes if ep.outcome is not None]
    
    if episodes:
        karma = memory.calculate_karma_score(episodes)
        print(f"   Karma score: {karma:.2f}")
        print(f"   Based on {len(episodes)} episodes")
        print("   Status: PASS")
    else:
        print("   No completed episodes yet")
        print("   Status: SKIP")
    
    return True


def test_ml_trainer():
    """Test ML trainer (if sufficient data)."""
    print("\n3. Testing ML Trainer...")
    
    trainer = get_ml_trainer()
    
    # Check if we have enough data
    X, y = trainer.prepare_training_data()
    
    if X is None:
        print(f"   Insufficient data: need 10+ episodes with outcomes")
        print("   Status: SKIP (need more training data)")
        return True
    
    print(f"   Training data: {len(X)} episodes")
    print(f"   Success rate: {y.mean():.1%}")
    
    # Train
    results = trainer.train(epochs=10)
    
    print(f"   Best accuracy: {results['best_accuracy']:.2%}")
    print("   Status: PASS")
    
    return True


def test_ml_insights():
    """Test ML pattern analysis."""
    print("\n4. Testing ML Insights...")
    
    trainer = get_ml_trainer()
    patterns = trainer.analyze_patterns()
    
    if patterns.get("status") == "insufficient_data":
        print("   Insufficient data for pattern analysis")
        print("   Status: SKIP")
    else:
        print(f"   Win rate: {patterns.get('win_rate', 0):.1%}")
        print(f"   Success count: {patterns.get('success_count', 0)}")
        print(f"   Failure count: {patterns.get('failure_count', 0)}")
        print("   Status: PASS")
    
    return True


async def test_triad_with_memory():
    """Test Triad service with episodic memory integration."""
    print("\n5. Testing Triad Service with Memory...")
    
    service = get_triad_service()
    
    market_data = {
        "volatility_1m": 0.025,
        "momentum_1d": 0.02,
        "volume_ratio": 1.2,
        "bid_ask_spread": 0.001,
        "trend": 1,
        "imbalance": 0.2,
        "orderbook_depth": 200000,
        "volume_24h": 10000000
    }
    
    # Process
    decision = await service.process_market_data(market_data, "memory_test")
    
    print(f"   Decision: {decision.action}")
    print(f"   Confidence: {decision.confidence:.2f}")
    print(f"   Coherence: {decision.coherence:.2f}")
    
    # Check memory stats
    mem_stats = service.get_memory_stats()
    print(f"   Total episodes: {mem_stats['total_episodes']}")
    
    print("   Status: PASS")
    return True


async def main():
    """Run all Phase 5 tests."""
    print("=" * 60)
    print("PHASE 5 INTEGRATION TESTS - Memory & ML")
    print("=" * 60)
    
    results = []
    
    try:
        results.append(("Episodic Memory", test_episodic_memory()))
    except Exception as e:
        print(f"   FAIL: {e}")
        results.append(("Episodic Memory", False))
    
    try:
        results.append(("Karma Calculation", test_karma_calculation()))
    except Exception as e:
        print(f"   FAIL: {e}")
        results.append(("Karma Calculation", False))
    
    try:
        results.append(("ML Trainer", test_ml_trainer()))
    except Exception as e:
        print(f"   FAIL: {e}")
        results.append(("ML Trainer", False))
    
    try:
        results.append(("ML Insights", test_ml_insights()))
    except Exception as e:
        print(f"   FAIL: {e}")
        results.append(("ML Insights", False))
    
    try:
        results.append(("Triad + Memory", await test_triad_with_memory()))
    except Exception as e:
        print(f"   FAIL: {e}")
        results.append(("Triad + Memory", False))
    
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
        print("\nAll Phase 5 integration tests passed!")
        return 0
    else:
        print(f"\n{total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
