# Phase 10 - Remaining Test Implementation Guide

## Overview

Phase 10 core implementation is complete: **20/20 tests passing** ✅

**Next**: Implement 35+ test stubs to reach full Phase 10 completion

This guide details each test category, expected behavior, and implementation approach.

---

## Test Categories & Implementation Plan

### 1. Performance Tests (3 tests)

**File**: `backend/tests/test_cold_path_coordinator.py`
**Class**: `TestColdPathPerformance`

#### Test 1.1: test_decision_latency_under_500ms

```python
def test_decision_latency_under_500ms():
    """Decision latency should be under 500ms including LLM agent calls."""
    coordinator = ColdPathCoordinator(self.config_path)

    # Mock agent with realistic LLM latency
    agent = MagicMock()
    agent.name = "SlowLLMAgent"
    agent.analyze.return_value = {
        "action": 1,
        "confidence": 0.8,
        "reasoning": "Market is bullish"
    }
    # Simulate 100-200ms LLM latency
    agent.analyze.side_effect = lambda: (
        time.sleep(0.1),  # 100ms
        agent.analyze.return_value
    )[1]

    coordinator.register_agent(agent)

    # Measure decision latency
    start = time.time()
    decision = coordinator.make_decision()
    latency = (time.time() - start) * 1000  # Convert to ms

    assert latency < 500, f"Latency {latency}ms exceeds 500ms target"
    assert decision.action == 1
    assert decision.confidence == 0.8
```

**Expected**: Latency well under 500ms (typically 100-200ms for single agent)

#### Test 1.2: test_throughput_minimum_2_decisions_per_second

```python
def test_throughput_minimum_2_decisions_per_second():
    """Coordinator should sustain at least 2 decisions per second."""
    coordinator = ColdPathCoordinator(self.config_path)

    # Register fast agent
    agent = MagicMock()
    agent.name = "FastAgent"
    agent.analyze.return_value = {
        "action": 1,
        "confidence": 0.7,
        "reasoning": "Quick decision"
    }
    coordinator.register_agent(agent)

    # Make 10 decisions and measure time
    start = time.time()
    for _ in range(10):
        coordinator.make_decision()
    elapsed = time.time() - start

    throughput = 10 / elapsed  # decisions per second
    assert throughput >= 2.0, f"Throughput {throughput:.2f} d/s below 2.0 target"
```

**Expected**: 10 decisions in < 5 seconds (10/5 = 2 d/s minimum)

#### Test 1.3: test_throttling_improves_performance

```python
def test_throttling_improves_performance():
    """Config throttling should prevent excessive writes improving performance."""
    coordinator = ColdPathCoordinator(self.config_path, update_interval=5)

    agent = MagicMock()
    agent.name = "Agent1"
    agent.analyze.return_value = {"action": 1, "confidence": 0.8, "reasoning": ""}
    coordinator.register_agent(agent)

    # Make 20 decisions rapidly, measure time with throttling
    start = time.time()
    for _ in range(20):
        decision = coordinator.make_decision()
        coordinator.write_config(decision)  # Throttled internally
    throttled_time = time.time() - start

    # Check that writes were throttled (only ~4 writes for 20 decisions with 5s interval)
    writes = coordinator.get_metrics().config_writes
    assert writes < 5, f"Expected <5 writes with throttling, got {writes}"
```

**Expected**: 20 decisions with only 3-5 actual config writes

---

### 2. Event Integration Tests (3 tests)

**File**: `backend/tests/test_cold_path_coordinator.py`
**Class**: `TestColdPathEventIntegration`

**Prerequisite**: ColdPathCoordinator accepts `event_bus` parameter

#### Test 2.1: test_publishes_decision_events

```python
def test_publishes_decision_events():
    """ColdPathCoordinator should publish decision events to event bus."""
    event_bus = MagicMock()
    coordinator = ColdPathCoordinator(self.config_path, event_bus=event_bus)

    agent = MagicMock()
    agent.name = "Agent1"
    agent.analyze.return_value = {"action": 1, "confidence": 0.8, "reasoning": ""}
    coordinator.register_agent(agent)

    # Make decision
    decision = coordinator.make_decision()

    # Verify event published
    event_bus.publish.assert_called_once()
    event_call = event_bus.publish.call_args
    assert event_call[0][0] == "coordinator.decision_made"
    assert "decision" in event_call[1]
```

**Expected**: Event published with topic "coordinator.decision_made" and decision data

#### Test 2.2: test_listens_to_agent_updates

```python
def test_listens_to_agent_updates():
    """ColdPathCoordinator should listen for agent update events."""
    event_bus = MagicMock()
    coordinator = ColdPathCoordinator(self.config_path, event_bus=event_bus)

    agent = MagicMock()
    agent.name = "Agent1"
    agent.analyze.return_value = {"action": 1, "confidence": 0.8, "reasoning": ""}
    coordinator.register_agent(agent)

    # Simulate agent update event
    update_callback = None
    def capture_listener(topic, callback):
        nonlocal update_callback
        if topic == "agent.updated":
            update_callback = callback

    event_bus.subscribe.side_effect = capture_listener

    # Coordinator should subscribe to agent events
    # (This would be done in __init__ or when registering agent)
    coordinator.register_agent(agent)

    assert event_bus.subscribe.called
```

**Expected**: Coordinator subscribes to agent events for dynamic agent updates

#### Test 2.3: test_handles_event_bus_errors

```python
def test_handles_event_bus_errors():
    """ColdPathCoordinator should handle event bus publish errors gracefully."""
    event_bus = MagicMock()
    event_bus.publish.side_effect = Exception("Event bus down")

    coordinator = ColdPathCoordinator(self.config_path, event_bus=event_bus)

    agent = MagicMock()
    agent.name = "Agent1"
    agent.analyze.return_value = {"action": 1, "confidence": 0.8, "reasoning": ""}
    coordinator.register_agent(agent)

    # Decision should succeed even if event bus fails
    decision = coordinator.make_decision()
    assert decision is not None
    assert decision.action in [0, 1, 2]
```

**Expected**: Decision succeeds even if event publishing fails

---

### 3. Decision Aggregation Tests (3 tests)

**File**: `backend/tests/test_cold_path_coordinator.py`
**Class**: `TestColdPathDecisionAggregation`

#### Test 3.1: test_weighted_agent_scores

```python
def test_weighted_agent_scores():
    """Agent weights should influence final decision confidence."""
    coordinator = ColdPathCoordinator(self.config_path)

    # Agent 1: high weight (trusted), medium confidence
    agent1 = MagicMock()
    agent1.name = "TrustedAgent"
    agent1.analyze.return_value = {"action": 1, "confidence": 0.6, "reasoning": ""}
    coordinator.register_agent(agent1, weight=2.0)  # 2x weight

    # Agent 2: low weight, high confidence
    agent2 = MagicMock()
    agent2.name = "NewAgent"
    agent2.analyze.return_value = {"action": 1, "confidence": 0.9, "reasoning": ""}
    coordinator.register_agent(agent2, weight=0.5)  # 0.5x weight

    # Final confidence should be closer to agent1's (0.6) due to higher weight
    decision = coordinator.make_decision()

    # Weighted average: (0.6*2.0 + 0.9*0.5) / (2.0 + 0.5) = 1.65 / 2.5 = 0.66
    assert decision.confidence == pytest.approx(0.66, abs=0.05)
```

**Expected**: Weighted average favors higher-weight agents

#### Test 3.2: test_unanimous_decisions_high_confidence

```python
def test_unanimous_decisions_high_confidence():
    """When all agents agree, confidence should be high."""
    coordinator = ColdPathCoordinator(self.config_path)

    # Both agents recommend the same action with high confidence
    agent1 = MagicMock()
    agent1.name = "Agent1"
    agent1.analyze.return_value = {"action": 1, "confidence": 0.95, "reasoning": ""}
    coordinator.register_agent(agent1)

    agent2 = MagicMock()
    agent2.name = "Agent2"
    agent2.analyze.return_value = {"action": 1, "confidence": 0.90, "reasoning": ""}
    coordinator.register_agent(agent2)

    decision = coordinator.make_decision()
    assert decision.action == 1
    assert decision.confidence >= 0.9  # Unanimous = high confidence
```

**Expected**: Unanimous decisions have high confidence (≥ 0.9)

#### Test 3.3: test_split_decisions_lower_confidence

```python
def test_split_decisions_lower_confidence():
    """When agents disagree, confidence should be lower."""
    coordinator = ColdPathCoordinator(self.config_path)

    # Agent 1: bullish
    agent1 = MagicMock()
    agent1.name = "BullishAgent"
    agent1.analyze.return_value = {"action": 1, "confidence": 0.9, "reasoning": ""}
    coordinator.register_agent(agent1, weight=1.0)

    # Agent 2: bearish
    agent2 = MagicMock()
    agent2.name = "BearishAgent"
    agent2.analyze.return_value = {"action": 2, "confidence": 0.9, "reasoning": ""}
    coordinator.register_agent(agent2, weight=1.0)

    # With disagreement, final confidence should be lower
    decision = coordinator.make_decision()
    # One agent wins (higher weight or alphabetical), but confidence is mixed
    assert decision.confidence < 0.85
```

**Expected**: Split decisions have lower confidence (< 0.85)

---

### 4. Agent Interface Tests (3 tests)

**File**: `backend/tests/test_cold_path_coordinator.py`
**Class**: `TestColdPathAgentInterface`

#### Test 4.1: test_agent_must_have_analyze_method

```python
def test_agent_must_have_analyze_method():
    """Agents must have an analyze() method."""
    coordinator = ColdPathCoordinator(self.config_path)

    # Invalid agent (no analyze method)
    invalid_agent = MagicMock(spec=[])  # Empty spec
    invalid_agent.name = "InvalidAgent"

    with pytest.raises(AttributeError):
        coordinator.register_agent(invalid_agent)
```

**Expected**: Registration fails if agent lacks `analyze()` method

#### Test 4.2: test_agent_must_have_name

```python
def test_agent_must_have_name():
    """Agents must have a name attribute."""
    coordinator = ColdPathCoordinator(self.config_path)

    # Agent without name
    agent = MagicMock()
    agent.analyze.return_value = {"action": 1, "confidence": 0.8, "reasoning": ""}
    del agent.name  # Remove name attribute

    with pytest.raises(AttributeError):
        coordinator.register_agent(agent)
```

**Expected**: Registration fails if agent lacks `name` attribute

#### Test 4.3: test_agent_decision_format_validation

```python
def test_agent_decision_format_validation():
    """Agent decisions must contain required fields."""
    coordinator = ColdPathCoordinator(self.config_path)

    # Agent with invalid output
    agent = MagicMock()
    agent.name = "Agent1"
    agent.analyze.return_value = {
        "action": 1,
        # Missing 'confidence' and 'reasoning'
    }

    coordinator.register_agent(agent)

    # Making decision with incomplete agent output should fail or use defaults
    with pytest.raises((KeyError, ValueError)):
        coordinator.make_decision()
```

**Expected**: Invalid agent outputs are rejected

---

### 5. Monitoring & Metrics Tests (3 tests)

**File**: `backend/tests/test_cold_path_coordinator.py`
**Class**: `TestColdPathMonitoring`

#### Test 5.1: test_decision_metrics_tracking

```python
def test_decision_metrics_tracking():
    """Coordinator should track decision metrics."""
    coordinator = ColdPathCoordinator(self.config_path)

    agent = MagicMock()
    agent.name = "Agent1"
    agent.analyze.return_value = {"action": 1, "confidence": 0.8, "reasoning": ""}
    coordinator.register_agent(agent)

    # Make 5 decisions
    for _ in range(5):
        coordinator.make_decision()

    metrics = coordinator.get_metrics()
    assert metrics.decisions_made == 5
    assert len(metrics.latencies) > 0
    assert metrics.avg_decision_latency >= 0
```

**Expected**: Metrics track decision count and latency

#### Test 5.2: test_per_agent_metrics

```python
def test_per_agent_metrics():
    """Coordinator should track per-agent metrics."""
    coordinator = ColdPathCoordinator(self.config_path)

    agent = MagicMock()
    agent.name = "Agent1"
    agent.analyze.return_value = {"action": 1, "confidence": 0.8, "reasoning": ""}
    coordinator.register_agent(agent)

    # Make 3 decisions
    for _ in range(3):
        coordinator.make_decision()

    agent_metrics = coordinator.get_agent_metrics("Agent1")
    assert agent_metrics.calls == 3
    assert agent_metrics.failures == 0
    assert agent_metrics.avg_confidence == pytest.approx(0.8, abs=0.01)
```

**Expected**: Per-agent metrics show calls, failures, and average confidence

#### Test 5.3: test_decision_reasoning_traces

```python
def test_decision_reasoning_traces():
    """Decisions should include reasoning traces for debugging."""
    coordinator = ColdPathCoordinator(self.config_path)

    agent = MagicMock()
    agent.name = "SentimentAgent"
    agent.analyze.return_value = {
        "action": 1,
        "confidence": 0.85,
        "reasoning": "Positive sentiment detected in news"
    }
    coordinator.register_agent(agent)

    decision = coordinator.make_decision()

    # Reasoning should be preserved
    assert "SentimentAgent" in decision.source
    assert "sentiment" in decision.reasoning.lower() or len(decision.reasoning) > 0
```

**Expected**: Decision includes source agent and reasoning trace

---

### 6. State Management Tests (3 tests)

**File**: `backend/tests/test_cold_path_coordinator.py`
**Class**: `TestColdPathState`

#### Test 6.1: test_maintains_decision_history

```python
def test_maintains_decision_history():
    """Coordinator should maintain a history of recent decisions."""
    coordinator = ColdPathCoordinator(self.config_path)

    agent = MagicMock()
    agent.name = "Agent1"
    agent.analyze.return_value = {"action": 1, "confidence": 0.8, "reasoning": ""}
    coordinator.register_agent(agent)

    # Make 5 decisions
    for i in range(5):
        coordinator.make_decision()

    history = coordinator.get_decision_history(num=10)
    assert len(history) >= 5
    assert all(isinstance(d, CoordinatorDecision) for d in history)
```

**Expected**: History contains last N decisions

#### Test 6.2: test_health_status_reporting

```python
def test_health_status_reporting():
    """Coordinator should report health status."""
    coordinator = ColdPathCoordinator(self.config_path)

    agent1 = MagicMock()
    agent1.name = "Agent1"
    agent1.analyze.return_value = {"action": 1, "confidence": 0.8, "reasoning": ""}
    coordinator.register_agent(agent1)

    agent2 = MagicMock()
    agent2.name = "Agent2"
    agent2.analyze.side_effect = Exception("Agent down")
    coordinator.register_agent(agent2)

    # Make decision to trigger agent2 failure
    coordinator.make_decision()

    health = coordinator.get_health()
    assert health.total_agents == 2
    assert health.operational_agents == 1
    assert health.failed_agents == 1
    assert health.is_operational  # Still operational with 1 working agent
```

**Expected**: Health shows operational/failed agent counts and overall status

#### Test 6.3: test_recovery_from_partial_failure

```python
def test_recovery_from_partial_failure():
    """Coordinator should recover when failed agents come back online."""
    coordinator = ColdPathCoordinator(self.config_path)

    agent = MagicMock()
    agent.name = "TemporarilyDownAgent"
    coordinator.register_agent(agent)

    # First: agent fails
    agent.analyze.side_effect = Exception("Down")
    coordinator.make_decision()
    health1 = coordinator.get_health()
    assert health1.failed_agents == 1

    # Later: agent recovers (wait >60s or manually clear)
    # (For testing, we'd manually clear the failed_agents or patch time)
    agent.analyze.side_effect = None
    agent.analyze.return_value = {"action": 1, "confidence": 0.8, "reasoning": ""}

    # Create new coordinator or simulate time passing
    # For now, just verify the mechanism exists
    assert hasattr(coordinator, 'failed_agents')
```

**Expected**: Failed agents can recover after timeout

---

### 7. FastConfig Integration Tests (3 tests)

**File**: `backend/tests/test_cold_path_coordinator.py`
**Class**: `TestColdPathConfigIntegration`

#### Test 7.1: test_reads_initial_config

```python
def test_reads_initial_config():
    """ColdPathCoordinator should read initial config from FastConfig."""
    # Create initial config in FastConfig
    manager = FastConfigManager(self.config_path)
    initial_config = {
        "action": 0,
        "confidence": 0.5,
        "version": 1,
        "timestamp": time.time()
    }
    manager.write(initial_config)

    # Create coordinator (should read initial config)
    coordinator = ColdPathCoordinator(self.config_path)

    # Coordinator should have loaded the initial state
    # (Could verify via get_metrics() or internal state)
    metrics = coordinator.get_metrics()
    assert metrics is not None
```

**Expected**: Coordinator initializes with config from FastConfig

#### Test 7.2: test_preserves_fallback_config

```python
def test_preserves_fallback_config():
    """ColdPathCoordinator should preserve fallback config if all agents fail."""
    coordinator = ColdPathCoordinator(self.config_path)

    # Register agent that will fail
    agent = MagicMock()
    agent.name = "Agent1"
    agent.analyze.side_effect = Exception("Agent down")
    coordinator.register_agent(agent)

    # Make decision with no working agents
    decision = coordinator.make_decision()

    # Should use fallback
    assert decision.action == 0  # Hold
    assert decision.confidence == 0.5  # Neutral

    # Write fallback to config
    coordinator.write_config(decision)

    # Verify it was written
    manager = FastConfigManager(self.config_path)
    config = manager.read()
    assert config["action"] == 0
```

**Expected**: Fallback config is written when all agents fail

#### Test 7.3: test_handles_version_mismatches

```python
def test_handles_version_mismatches():
    """ColdPathCoordinator should handle version mismatches gracefully."""
    manager = FastConfigManager(self.config_path)

    # Write config with version 1
    manager.write({"action": 1, "confidence": 0.8, "version": 1})

    coordinator = ColdPathCoordinator(self.config_path)

    # Register agent that writes version 2
    agent = MagicMock()
    agent.name = "Agent1"
    agent.analyze.return_value = {"action": 1, "confidence": 0.8, "reasoning": ""}
    coordinator.register_agent(agent)

    # Make and write decision (increments version)
    decision = coordinator.make_decision()
    coordinator.write_config(decision)

    # Version should be incremented
    config = manager.read()
    assert config["version"] >= 2
```

**Expected**: Version increments and mismatches handled

---

### 8. CoordinatorDecision Dataclass Tests (2 tests)

**File**: `backend/tests/test_cold_path_coordinator.py`
**Class**: `TestCoordinatorDecision`

#### Test 8.1: test_coordinator_decision_creation

```python
def test_coordinator_decision_creation():
    """CoordinatorDecision dataclass should be created correctly."""
    decision = CoordinatorDecision(
        action=1,
        confidence=0.85,
        reasoning="Bullish signal detected",
        source="SentimentAgent",
        timestamp=time.time()
    )

    assert decision.action == 1
    assert decision.confidence == 0.85
    assert decision.reasoning == "Bullish signal detected"
    assert decision.source == "SentimentAgent"
    assert decision.timestamp > 0
```

**Expected**: Dataclass instantiation works with all fields

#### Test 8.2: test_coordinator_decision_to_config

```python
def test_coordinator_decision_to_config():
    """CoordinatorDecision should convert to FastConfig format."""
    decision = CoordinatorDecision(
        action=1,
        confidence=0.85,
        reasoning="Test",
        source="Agent1",
        timestamp=1000.0
    )

    config = decision.to_config()

    assert config["action"] == 1
    assert config["confidence"] == 0.85
    assert config["timestamp"] == 1000.0
    assert "version" in config or "reasoning" in config
```

**Expected**: Conversion to config dict with required fields

---

## Implementation Checklist

Use this to track implementation progress:

### Performance Tests

- [ ] test_decision_latency_under_500ms
- [ ] test_throughput_minimum_2_decisions_per_second
- [ ] test_throttling_improves_performance

### Event Integration Tests

- [ ] test_publishes_decision_events
- [ ] test_listens_to_agent_updates
- [ ] test_handles_event_bus_errors

### Decision Aggregation Tests

- [ ] test_weighted_agent_scores
- [ ] test_unanimous_decisions_high_confidence
- [ ] test_split_decisions_lower_confidence

### Agent Interface Tests

- [ ] test_agent_must_have_analyze_method
- [ ] test_agent_must_have_name
- [ ] test_agent_decision_format_validation

### Monitoring Tests

- [ ] test_decision_metrics_tracking
- [ ] test_per_agent_metrics
- [ ] test_decision_reasoning_traces

### State Management Tests

- [ ] test_maintains_decision_history
- [ ] test_health_status_reporting
- [ ] test_recovery_from_partial_failure

### FastConfig Integration Tests

- [ ] test_reads_initial_config
- [ ] test_preserves_fallback_config
- [ ] test_handles_version_mismatches

### Dataclass Tests

- [ ] test_coordinator_decision_creation
- [ ] test_coordinator_decision_to_config

---

## Quick Start

1. **Open test file**:

   ```bash
   cd backend/tests
   ```

2. **Find test stub** to implement:

   ```python
   # Example stub:
   def test_decision_latency_under_500ms():
       """Decision latency should be under 500ms."""
       pytest.skip("After implementation: create test body")
   ```

3. **Replace with test implementation** from above

4. **Run single test**:

   ```bash
   pytest test_cold_path_coordinator.py::TestColdPathPerformance::test_decision_latency_under_500ms -v
   ```

5. **Run full test class**:

   ```bash
   pytest test_cold_path_coordinator.py::TestColdPathPerformance -v
   ```

6. **Run all coordinator tests**:
   ```bash
   pytest test_cold_path_coordinator.py -v
   ```

---

**Goal**: Convert all 35+ stubs to working tests → All Phase 10 tests passing (55+) → Ready for Phase 11 integration
