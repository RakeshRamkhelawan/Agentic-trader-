# 📋 Prioritized Implementation Checklist: Asset System

**Goal:** Transition from documentation to full 448-asset system implementation using TDD and Kanban.
**Methodology:** Red-Green-Refactor. No logic without a failing test first.

---

## 🟢 PHASE 1: DATABASE & MODELS (Foundation)
*Focus: Establishing the data structures.*

1.  **[TO DO] [TDD] Create `backend/tests/unit/test_asset_models.py`**
    *   *Kanban Column:* To Do
    *   *Check:* Define tests for Asset, Category, and Watchlist CRUD.
2.  **[TO DO] Implement `backend/models/assets.py`**
    *   *Kanban Column:* In Progress
    *   *Check:* Pass model tests. Ensure `tenant_id` isolation.
3.  **[TO DO] Generate & Run Alembic Migrations**
    *   *Kanban Column:* In Progress
    *   *Check:* Database schema matches models exactly.

---

## 🟡 PHASE 2: DATA INGESTION (Seeding)
*Focus: Filling the registry with 448+ symbols.*

4.  **[TO DO] [TDD] Create `backend/tests/unit/test_asset_seeding.py`**
    *   *Kanban Column:* To Do
    *   *Check:* Define mocks for CoinGecko and CSV parsing errors.
5.  **[TO DO] Create `backend/scripts/seed_assets.py`**
    *   *Kanban Column:* In Progress
    *   *Check:* Import symbols from `data/bitvavo_assets.csv` with category enrichment.

---

## 🟠 PHASE 3: REAL-TIME PIPELINE (Sync Engine)
*Focus: High-frequency data flow.*

6.  **[TO DO] [TDD] Create `backend/tests/unit/test_tiered_sync.py`**
    *   *Kanban Column:* To Do
    *   *Check:* Test promotion/demotion logic based on mocked volume data.
7.  **[TO DO] Implement `TieredMarketDataService`**
    *   *Kanban Column:* In Progress
    *   *Check:* Pass sync tests. Verify Redis key structure (`markets:tier1`).
8.  **[TO DO] [TDD] Create `backend/tests/unit/test_kafka_events.py`**
    *   *Kanban Column:* To Do
    *   *Check:* Verify serialization to Kafka topics.
9.  **[TO DO] Integrate Redpanda/Kafka Producer**
    *   *Kanban Column:* In Progress
    *   *Check:* Events flowing to `market.ticks.raw`.

---

## 🔴 PHASE 4: AGENT CONTEXT & STORAGE
*Focus: Connecting to the "Brain".*

10. **[TO DO] [TDD] Create `backend/tests/unit/test_agent_context.py`**
    *   *Kanban Column:* To Do
    *   *Check:* Test context assembly speed (<10ms target).
11. **[TO DO] Implement `AgentContextBuilder`**
    *   *Kanban Column:* In Progress
    *   *Check:* Context contains correct data for watched assets.
12. **[TO DO] [TDD] Create `backend/tests/integration/test_decision_logging.py`**
    *   *Kanban Column:* To Do
    *   *Check:* Trigger Decision event and verify ClickHouse dump.

---

## 🟣 PHASE 5: LOAD TESTING & HARDENING
*Focus: Performance verification.*

13. **[TO DO] Create `backend/tests/load/test_asset_system_load.py`**
    *   *Kanban Column:* To Do
    *   *Check:* Simulate production load (50 agents, 448 assets).
14. **[TO DO] Final E2E Verification**
    *   *Kanban Column:* Testing
    *   *Check:* All 5 phases interoperate without errors.
