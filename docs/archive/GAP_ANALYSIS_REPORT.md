# 📝 Gap Analysis Report: Asset System Kanban & TDD

## 1. Test Coverage Analysis
- **Missing:** Detailed transition matrix for asset lifecycle states. We need tests that verify invalid transitions (e.g., INACTIVE to POOLED without re-discovery).
- **Missing:** Mock fixtures for ClickHouse and Redpanda are referenced but not defined.
- **Requirement:** 90% LCOV on state transition logic specifically.

## 2. Kanban Workflow Definition
- **Missing:** Metadata requirements for "Peer Review" (e.g., link to PR, checklist).
- **Missing:** Transition rules for moving items back to "To Do" from "Testing" on failure.

## 3. Asset System Architecture
- **Incomplete:** Defining the "Pooled" criteria (volume/trend threshold values).
- **Missing:** Logic for "Soft-delete" in INACTIVE state.

## 4. Dependencies and Resources
- **Verified:** PostgreSQL, Redis, ClickHouse, Kafka.
- **Note:** Need to ensure `asyncpg` and `aiokafka` are in requirements.

## 5. Implementation Gap Analysis
- **Rule:** Kanban transition from "In Progress" to "Peer Review" must be blocked if coverage < 90%.
- **Validation:** Unique constraint on `symbol` + `exchange` is mentioned but not the handling of ticker overlaps across exchanges.

## 6. Quality Criteria
- **Performance:** 10ms context builder latency is aggressive; needs optimized SQL/Redis pipelines.
