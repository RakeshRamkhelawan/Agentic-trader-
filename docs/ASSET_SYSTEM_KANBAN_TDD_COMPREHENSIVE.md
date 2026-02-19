# 📋 Asset System: Kanban & TDD Implementation Guide (COMPREHENSIVE)

**Status:** FINAL / UNIFIED | **Methodology:** Kanban + Test-Driven Development (TDD)
**Objective:** Scale the agentic trader platform to support 448+ assets with enterprise-grade reliability, multi-tenant isolation, and tiered real-time synchronization.

## 🚦 1. PROCESS DEFINITION: KANBAN & TDD RULES

### Kanban Workflow & Column Definitions
To maintain flow and transparency, every work item must progress through these columns:

1.  **Backlog:** Approved feature ideas and future tasks.
2.  **To Do:** Tasks prioritized for the current sprint. *Transition Rule: Movement to "In Progress" requires a documented Test Specification.*
3.  **In Progress:** Active implementation phase.
4.  **Peer Review:** Code complete. Peer verification of logic and style.
5.  **Testing (QA):** Final verification. *Condition: Coverage >= 90% LCOV.*
6.  **Done:** Feature is integrated, verified, and documented.

### Definition of Done (DoD)
- ✅ 100% Pass rate on all unit and integration tests.
- ✅ Code coverage meets or exceeds **90% LCOV**.
- ✅ Performance benchmarks met (<1s state transitions, <10ms context buildup).

## 🔄 2. ASSET LIFECYCLE STATE MACHINE

Assets are managed through a tiered state machine:

| State | Description | Sync Frequency | Storage Policy |
| :--- | :--- | :--- | :--- |
| **DISCOVERED** | New symbol found | None | Metadata Registry |
| **ACTIVE** | Enabled for use | 300s (Tier 3) | 1h OHLCV |
| **POOLED** | Trending/High Volume | 30s (Tier 2) | 1m OHLCV |
| **WATCHED** | Hot Asset / Active | 1s (Tier 1) | Raw Ticks |
| **INACTIVE** | Delisted / Disabled | None | Archived |

### State Transition Validation Rules
- `DISCOVERED` -> `ACTIVE`: Only if symbol is verified via exchange API.
- `ACTIVE` <-> `POOLED` <-> `WATCHED`: Based on volume/trending metrics.
- `*` -> `INACTIVE`: Manual disable or delisting event.

## 🛠️ 3. INFRASTRUCTURE & DEPENDENCIES

### Environment Configuration (.env)
```bash
POSTGRES_ASYNC_URL="postgresql+asyncpg://user:pass@localhost:5432/db"
REDIS_URL="redis://localhost:6379/0"
CLICKHOUSE_HOST="localhost"
KAFKA_BOOTSTRAP_SERVERS="localhost:9092"
```

## 🧪 4. TEST COVERAGE REQUIREMENTS (TDD PATHS)

### 4.1 Unit Testing Specs
- **Asset CRUD:** Verify state persistence.
- **Validation:** Unique (symbol, exchange).
- **Transitions:** Valid/Invalid state changes test matrix.

### 4.2 Integration Specs
- Seeding -> Discovery -> Transition to Active.

## 📈 5. PRIORITY CHECKLIST (REVISED)

1.  **Asset Model (`backend/assets/models.py`)** [To Do]
2.  **Asset Manager (`backend/assets/manager.py`)** [In Progress]
3.  **Unit Tests (`backend/tests/unit/test_assets.py`)** [To Do]
4.  **Seeding Logic (`backend/assets/seeding.py`)** [Backlog]

## ⚖️ 6. PERFORMANCE BENCHMARKS

| Metric | Target |
| :--- | :--- |
| **State Change Latency** | < 1s |
| **Context Readiness** | < 10ms |
| **Coverage (LCOV)** | >= 90% |
