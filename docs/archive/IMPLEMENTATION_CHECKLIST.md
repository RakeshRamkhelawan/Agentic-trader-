# 📅 Prioritized Implementation Checklist

1.  **Setup Backend Framework [Kanban: To Do]**
    - [ ] Initialize `backend/assets/` module if missing.
    - [ ] Define `AssetStatus` Enum (DISCOVERED, ACTIVE, POOLED, WATCHED, INACTIVE).
2.  **Model Implementation (TDD Phase 1) [Kanban: To Do]**
    - [ ] Create `backend/tests/unit/test_asset_models.py`.
    - [ ] Implement `Asset` SQLAlchemy model.
3.  **State Transition Logic [Kanban: In Progress]**
    - [ ] Implement `AssetManager.update_status()` with validation.
    - [ ] Add unit tests for all allowed/disallowed transitions.
4.  **Kanban Backend Connector [Kanban: Backlog]**
    - [ ] Create API endpoints for Kanban state management.
    - [ ] Add validation hook: `on_transition_to_testing` -> run test suite + coverage.
5.  **Infrastructure Integration [Kanban: Backlog]**
    - [ ] Connect Redis caching for Tier 1 assets.
    - [ ] Implement ClickHouse persistence for decision logging.
6.  **Verification [Kanban: Testing]**
    - [ ] Run full suite, verify 90% LCOV and <1s latency.
