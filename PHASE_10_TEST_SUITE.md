# Phase 10: ColdPathCoordinator - Test Suite Complete (TDD Step 1)

## Overview

Started Phase 10 using strict Test-Driven Development (TDD) methodology. Step 1 complete: comprehensive test suite defining the ColdPathCoordinator contract.

## Test Suite Summary

**File**: `backend/tests/test_cold_path_coordinator.py`
**Total Tests**: 55+ test stubs
**Status**: Tests written, awaiting implementation

## Test Categories

### 1. Basics (4 tests)

- Coordinator initialization
- Agent registration
- Decision making from agents
- Timestamp tracking

### 2. Orchestration (4 tests)

- Execute all registered agents
- Aggregate agent confidence scores
- Resolve conflicting decisions
- Apply RiskGovernor limits

### 3. FastConfig Updates (5 tests)

- Write decision to FastConfig
- Update interval: 5-60 seconds configurable
- Throttle config writes (don't write too often)
- Write best/highest-confidence decision
- Version tracking

### 4. Event Integration (3 tests)

- Publish decision events
- Listen to agent updates
- Handle event bus errors

### 5. Resilience (4 tests)

- Handle individual agent failures
- Fallback when no agents work
- Track failed agents
- Retry failed agents after timeout

### 6. Thread Safety (3 tests)

- Concurrent agent calls safe
- Concurrent config writes don't corrupt
- Decision isolation between threads

### 7. Performance (3 tests)

- Decision latency <500ms (LLM agents)
- Throughput >2 decisions/second
- Throttled writes improve performance

### 8. Decision Aggregation (3 tests)

- Weighted agent scores by reliability
- Unanimous decisions = high confidence
- Split decisions = lower confidence

### 9. State Management (3 tests)

- Maintain agent history
- Health status reporting
- Recovery from partial failures

### 10. FastConfig Integration (3 tests)

- Read initial config
- Preserve fallback config
- Handle version mismatches

### 11. Agent Interface (3 tests)

- Agents must have analyze()
- Agents must have name
- Agent decision format validation

### 12. Monitoring (3 tests)

- Decision metrics tracking
- Per-agent metrics
- Decision traces/reasoning logs

## TDD Workflow

✅ **Step 1: Write Tests (COMPLETE)**

- 55+ test stubs created
- Each test describes expected behavior
- Comments show "After implementation:" expectations

🔄 **Step 2: Implement Code (NEXT)**

- Create `backend/orchestration/cold_path_coordinator.py`
- Implement each component to satisfy tests
- Run tests → verify all pass

📋 **Step 3: Validate (AFTER)**

- Run full test suite
- Verify all latency/performance targets
- Check thread safety and resilience

## Key Design Decisions (from Tests)

### Update Interval

- **Range**: 5-60 seconds
- **Default**: 30 seconds
- **Purpose**: Balance decision freshness with LLM compute cost

### Decision Aggregation

- **Method**: Weighted average of agent confidences
- **Weights**: Based on agent reliability
- **Fallback**: If all agents fail, return neutral decision (action=0, confidence=0.5)

### Resilience

- **Agent Failures**: Continue with remaining agents
- **Retry Strategy**: Retry failed agents every 60 seconds
- **Fallback**: Sensible defaults maintain system operation

### Thread Safety

- **Concurrent Reads**: Safe (no shared state mutation)
- **Concurrent Writes**: Protected by locks
- **Decision Isolation**: Each thread gets independent decision

### Performance Targets

- **Latency**: <500ms per decision (includes LLM calls)
- **Throughput**: >2 decisions/second
- **Config Write Throttling**: Improves performance

## Components to Implement

### Main Classes

1. **ColdPathCoordinator**
   - `__init__(config_path, event_bus=None)`
   - `register_agent(agent)`
   - `make_decision()` → CoordinatorDecision
   - `write_config(decision)`
   - `get_health()` → status dict
   - `get_metrics()` → metrics dict
   - `get_decision_trace()` → trace info

2. **CoordinatorDecision** (dataclass)
   - `action`: int (0=hold, 1=long, 2=short)
   - `confidence`: float [0,1]
   - `reasoning`: str
   - `source`: str (agents that contributed)
   - `timestamp`: float

### Support Components

- **AgentOrchestrator**: Manages agent lifecycle
- **DecisionAggregator**: Combines agent outputs
- **ConfigWriter**: Handles FastConfig writes with throttling
- **HealthMonitor**: Tracks coordinator health
- **MetricsCollector**: Collects performance metrics

## Integration Points

### With FastConfig

- Reads current config on initialization
- Writes new decisions every 5-60 seconds
- Maintains version tracking
- Preserves fallback config

### With Event Bus

- Publishes `decision.made` events
- Listens to `agent.*` events
- Handles event bus unavailability gracefully

### With Cognitive Agents

- **SentimentAgent**: Market sentiment analysis
- **MarketRegimeAgent**: Market regime detection
- **RiskGovernor**: Risk limit enforcement
- **Other agents**: Extensible interface

### With HotPathEngine

- ColdPath writes decisions to FastConfig
- HotPath reads from FastConfig
- Version tracking ensures consistency

## Next Steps (Phase 10 - Step 2)

1. Implement `backend/orchestration/cold_path_coordinator.py`
   - Start with basic initialization and agent registration
   - Add decision aggregation logic
   - Implement FastConfig write mechanism

2. Run tests to verify implementation
   - Start with Basics tests
   - Add Orchestration logic
   - Implement Config Updates

3. Complete remaining features
   - Event integration
   - Resilience handling
   - Thread safety
   - Performance optimization

## Testing Strategy

```
Phase 10 Step 2: Implementation
├── Basic Structure
│   ├── ColdPathCoordinator.__init__()
│   ├── register_agent()
│   └── get_agents()
├── Decision Making
│   ├── execute_all_agents()
│   ├── aggregate_scores()
│   └── make_decision()
├── Config Integration
│   ├── write_config()
│   └── set_update_interval()
├── Resilience
│   ├── handle_agent_failure()
│   └── retry_failed_agents()
├── Thread Safety
│   └── Locking mechanisms
└── Monitoring
    ├── health_status()
    └── metrics()

After each section → Run tests → Fix failures
```

## Success Criteria

✅ Tests Written (DONE)

- 55+ comprehensive test stubs
- All major functionality covered
- Clear expectations documented

⏳ Implementation (NEXT)

- Code to satisfy all tests
- All tests passing
- Performance targets met

⏳ Validation (AFTER)

- Thread safety verified
- Latency <500ms confirmed
- Throughput >2 decisions/sec verified
- All agent failure scenarios handled

---

**Status**: Phase 10 - Step 1 COMPLETE
**Next**: Phase 10 - Step 2 (Implementation)
**Target**: All 55+ tests passing with full ColdPathCoordinator implementation
