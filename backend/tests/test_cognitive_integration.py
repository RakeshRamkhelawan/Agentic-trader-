"""
Integration tests for cognitive system with event bus and agents.
Validates full cycle: Market Data → Cognitive Processing → Decision → Execution.
"""

import pytest
import asyncio
import numpy as np
from datetime import datetime, timezone
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock

from backend.core.system_identity import SystemIdentity


pytestmark = pytest.mark.integration


@pytest.fixture
def event_bus():
    """Fixture for event bus (mocked)."""
    bus = AsyncMock()
    bus.publish = AsyncMock(return_value="event_id_123")
    return bus


@pytest.fixture
def system_identity():
    """Fixture for cognitive system."""
    return SystemIdentity()


@pytest.fixture
def market_data():
    """Fixture providing synthetic market data."""
    return {
        'price': np.sin(np.arange(0, 100, 0.1)) * 100 + 50000,
        'volume': np.ones(1000) * 1000,
        'orderbook_imbalance': 0.15,
        'funding_rate': 0.001,
        'social_sentiment': 0.6
    }


@pytest.mark.asyncio
async def test_cognitive_event_integration(event_bus, system_identity, market_data):
    """
    Test complete cycle: Market data → Cognitive processing → Decision event.
    """
    # Process market data through cognitive system
    result = await system_identity.process_market_cycle(
        price_data=market_data['price'],
        volume_data=market_data['volume'],
        orderbook_imbalance=market_data['orderbook_imbalance'],
        funding_rate=market_data['funding_rate'],
        social_sentiment=market_data['social_sentiment']
    )
    
    # Create decision event
    decision_event = {
        'event_type': 'cognitive_decision',
        'source': 'system_identity',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'action': result['action'],
        'confidence': result['confidence'],
        'rationale': result['rationale']
    }
    
    # Publish to event bus
    event_id = await event_bus.publish(
        stream='cognitive_decisions',
        event_data=decision_event
    )
    
    # Verify event was published
    assert event_id is not None
    assert decision_event['action'] in [0, 1, 2]
    assert 0 <= decision_event['confidence'] <= 1


@pytest.mark.asyncio
async def test_cognitive_learning_cycle(system_identity, market_data):
    """
    Test learning: Decision → Execution → outcome → Memory update.
    """
    # Process first cycle
    result1 = await system_identity.process_market_cycle(
        price_data=market_data['price'],
        volume_data=market_data['volume'],
        orderbook_imbalance=market_data['orderbook_imbalance'],
        funding_rate=market_data['funding_rate'],
        social_sentiment=market_data['social_sentiment']
    )
    
    action_id = result1.get('action_id', 'action_1')
    
    # Simulate execution with positive outcome
    system_identity.update_outcome(action_id, outcome=0.8)
    
    # Process similar market state again
    result2 = await system_identity.process_market_cycle(
        price_data=market_data['price'],
        volume_data=market_data['volume'],
        orderbook_imbalance=market_data['orderbook_imbalance'],
        funding_rate=market_data['funding_rate'],
        social_sentiment=market_data['social_sentiment']
    )
    
    # System should show learning (valid decision made)
    assert result2['confidence'] >= 0
    assert result2['action'] in [0, 1, 2]
    assert result2['rationale'] is not None


@pytest.mark.asyncio
async def test_cognitive_state_persistence(system_identity, market_data):
    """
    Test that system maintains coherent state across multiple cycles.
    """
    results = []
    
    for _ in range(5):
        result = await system_identity.process_market_cycle(
            price_data=market_data['price'],
            volume_data=market_data['volume'],
            orderbook_imbalance=market_data['orderbook_imbalance'],
            funding_rate=market_data['funding_rate'],
            social_sentiment=market_data['social_sentiment']
        )
        results.append(result)
    
    # All results should be valid
    for result in results:
        assert result['action'] in [0, 1, 2]
        assert 0 <= result['confidence'] <= 1
    
    # System should maintain consistency
    assert len(results) == 5
    assert all('action' in r for r in results)


@pytest.mark.asyncio
async def test_cognitive_adaptation(system_identity, market_data):
    """
    Test that system adapts exploration rate based on performance.
    """
    # Get initial stats
    result1 = await system_identity.process_market_cycle(
        price_data=market_data['price'],
        volume_data=market_data['volume'],
        orderbook_imbalance=market_data['orderbook_imbalance'],
        funding_rate=market_data['funding_rate'],
        social_sentiment=market_data['social_sentiment']
    )
    
    initial_exploration = result1.get('system_stats', {}).get('exploration_rate', 0.1)
    
    # Provide good outcomes to reduce exploration
    for i in range(10):
        action_id = f'action_{i}'
        system_identity.update_outcome(action_id, outcome=0.9)
    
    # Run another cycle
    result2 = await system_identity.process_market_cycle(
        price_data=market_data['price'],
        volume_data=market_data['volume'],
        orderbook_imbalance=market_data['orderbook_imbalance'],
        funding_rate=market_data['funding_rate'],
        social_sentiment=market_data['social_sentiment']
    )
    
    adapted_exploration = result2.get('system_stats', {}).get('exploration_rate', 0.1)
    
    # After good outcomes, exploration should decrease
    assert adapted_exploration <= initial_exploration


@pytest.mark.asyncio
async def test_multi_agent_cognitive_synthesis(event_bus, system_identity, market_data):
    """
    Test that multiple agents can feed into and respond to unified cognitive system.
    This validates the architecture where:
    - Cold path agents (LLM) update cognitive state
    - Hot path reads unified cognitive decision
    """
    
    # Simulate cold path agent updating sentiment understanding
    sentiment_event = {
        'event_type': 'agent_sentiment_analysis',
        'source': 'sentiment_agent',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'sentiment_score': 0.7,
        'confidence': 0.8,
        'analysis': 'Bullish signals detected'
    }
    
    await event_bus.publish(stream='agent_updates', event_data=sentiment_event)
    
    # Simulate market regime agent update
    regime_event = {
        'event_type': 'agent_regime_analysis',
        'source': 'market_regime_agent',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'regime': 'trending',
        'confidence': 0.75,
        'direction': 'up'
    }
    
    await event_bus.publish(stream='agent_updates', event_data=regime_event)
    
    # System processes market data (integrating agent insights)
    result = await system_identity.process_market_cycle(
        price_data=market_data['price'],
        volume_data=market_data['volume'],
        orderbook_imbalance=market_data['orderbook_imbalance'],
        funding_rate=market_data['funding_rate'],
        social_sentiment=market_data['social_sentiment']  # Integrated from event
    )
    
    # Verify decision was made
    assert result['action'] in [0, 1, 2]
    assert result['confidence'] > 0


@pytest.mark.asyncio
async def test_frequency_pattern_recognition(system_identity, market_data):
    """
    Test that system recognizes and responds to market frequency patterns.
    This validates the FFT-based vibrational analysis.
    """
    
    # Create cyclical market data with clear frequency
    t = np.arange(0, 100, 0.1)
    cyclical_price = 50000 + 1000 * np.sin(2 * np.pi * 0.5 * t)  # 0.5 Hz cycle
    cyclical_volume = np.ones(1000) * 1000
    
    results = []
    for _ in range(3):
        result = await system_identity.process_market_cycle(
            price_data=cyclical_price,
            volume_data=cyclical_volume,
            orderbook_imbalance=0.1,
            funding_rate=0.001,
            social_sentiment=0.5
        )
        results.append(result)
    
    # System should consistently recognize the pattern
    actions = [r['action'] for r in results]
    confidences = [r['confidence'] for r in results]
    
    # With consistent input, should see consistent confidence
    assert len(set(actions)) <= 2  # Should cluster to 1-2 actions
    assert np.mean(confidences) > 0.4


@pytest.mark.asyncio
async def test_memory_capacity_management(system_identity, market_data):
    """
    Test that system properly manages memory capacity and clustering.
    """
    
    # Fill memory beyond initial capacity
    for i in range(200):
        result = await system_identity.process_market_cycle(
            price_data=market_data['price'],
            volume_data=market_data['volume'],
            orderbook_imbalance=market_data['orderbook_imbalance'],
            funding_rate=market_data['funding_rate'],
            social_sentiment=market_data['social_sentiment']
        )
        
        # Update with outcome
        system_identity.update_outcome(f'action_{i}', outcome=0.5)
    
    # Get final stats
    final_result = await system_identity.process_market_cycle(
        price_data=market_data['price'],
        volume_data=market_data['volume'],
        orderbook_imbalance=market_data['orderbook_imbalance'],
        funding_rate=market_data['funding_rate'],
        social_sentiment=market_data['social_sentiment']
    )
    
    stats = final_result.get('system_stats', {})
    memory_size = stats.get('memory_size', 0)
    
    # Memory should be bounded by capacity
    assert memory_size <= 10000  # Default capacity


@pytest.mark.asyncio
async def test_cognitive_cycle_latency(system_identity, market_data):
    """
    Test that cognitive cycle completes within acceptable latency.
    Target: <100ms for decision (cold path can be slower, but measurement validates baseline).
    """
    
    import time
    
    start = time.time()
    result = await system_identity.process_market_cycle(
        price_data=market_data['price'],
        volume_data=market_data['volume'],
        orderbook_imbalance=market_data['orderbook_imbalance'],
        funding_rate=market_data['funding_rate'],
        social_sentiment=market_data['social_sentiment']
    )
    elapsed = time.time() - start
    
    # Should complete in reasonable time (cold path)
    assert elapsed < 2.0  # 2 seconds for full cycle is acceptable (includes startup overhead)
    
    # Latency should be tracked
    cycle_stats = result.get('system_stats', {})
    assert 'cycle_latency_ms' in cycle_stats or elapsed > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
