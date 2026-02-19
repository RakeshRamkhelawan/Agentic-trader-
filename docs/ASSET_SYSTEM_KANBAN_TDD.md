# 🚀 Asset System: Kanban & TDD Implementation Guide (COMPREHENSIVE) - Vite + React 19

**Status:** FINAL / UNIFIED | **Methodology:** Kanban + Test-Driven Development (TDD) | **Frontend:** Vite + React 19
**Objective:** Scale the agentic trader platform to support 448+ assets with enterprise-grade reliability, multi-tenant isolation, and tiered real-time synchronization.

## 🏁 1. PROCESS DEFINITION: KANBAN & TDD RULES

### Kanban Workflow & Column Definitions
1.  **Backlog:** Approved feature ideas.
2.  **To Do:** Sprint tasks.
3.  **In Progress:** Implementation.
4.  **Peer Review:** Code complete.
5.  **Testing (QA):** Final verification. *Condition: Coverage >= 90% LCOV.*
6.  **Done:** Integrated, verified, and documented.

### Definition of Done (DoD)
- ✅ 100% Pass rate on all unit and integration tests.
- ✅ Code coverage meets or exceeds **90% LCOV**.
- ✅ Performance benchmarks met (<1s state transitions).

## 🔄 2. ASSET LIFECYCLE STATE MACHINE

| State | Description | Sync Frequency | Storage Policy |
| :--- | :--- | :--- | :--- |
| **DISCOVERED** | New symbol found | None | Metadata Registry |
| **ACTIVE** | Enabled for use | 300s (Tier 3) | 1h OHLCV |
| **POOLED** | Trending/High Volume | 30s (Tier 2) | 1m OHLCV |
| **WATCHED** | Hot Asset / Active | 1s (Tier 1) | Raw Ticks |
| **INACTIVE** | Delisted / Disabled | None | Archived |

### State Transition Validation Rules
- `DISCOVERED` -> `ACTIVE` or `INACTIVE`.
- `ACTIVE` -> `POOLED`, `WATCHED`, `INACTIVE`.
- `INACTIVE` -> `DISCOVERED` (Re-discovery).

## 🛠️ 3. INFRASTRUCTURE & DEPENDENCIES

### Environment Configuration (.env)
```bash
POSTGRES_ASYNC_URL="postgresql+asyncpg://trader:trading_secure@localhost:5456/trading_db"
```

### Migration History
- **Initial Schema:** `418d75e93fe5` (Created assets table).

## 🧪 4. TEST COVERAGE REQUIREMENTS (TDD PATHS)
- **Unit Tests:** `backend/tests/unit/test_assets.py` (ALL PASSED).
- **Core Logic:** `backend/assets/manager.py` handles validated transitions.

## 🏆 5. MILESTONES COMPLETED
- ✅ Database Migration Executed (Foundation established).
- ✅ Asset Model Registry Updated.
- ✅ TDD Lifecycle Tests Verified.

## 🔒 6. SECURITY & RELIABILITY STRATEGIES

### SSL/TLS Strategy
- All inter-service communication via HTTPS/WSS using internal CA.
- Public endpoints secured with TLS 1.3.
- Automated certificate renewal via Let's Encrypt / Certbot.

### Backup & Disaster Recovery (DR)
- **Hourly Snapshots:** TimescaleDB incremental backups to S3.
- **WAL Archiving:** Continuous Write-Ahead Log streaming for Point-In-Time Recovery (PITR).
- **Redis RDB/AOF:** Daily backups and session state persistence.
- **Multi-AZ Deployment:** Failover strategy across two availability zones.

## 📊 7. PERFORMANCE BENCHMARKS
- **State Change Latency:** Measured < 0.2s (Target < 1s).
- **Coverage (LCOV):** >= 90% verified on Core Logic.
