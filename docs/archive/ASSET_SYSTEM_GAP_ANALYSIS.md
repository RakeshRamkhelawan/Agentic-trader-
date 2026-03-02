# Gap Analysis Report: Asset System TDD & Kanban Workflow

**Project:** Agentic Trader Platform - Asset System Scale-up (448+ Assets)
**Date:** 2026-02-18
**Status:** COMPLETE

## 1. Executive Summary
The current documentation provides a strong conceptual framework for scaling the platform's asset system. However, significant gaps exist in formalizing the TDD lifecycle, defining state transitions for assets, and establishing concrete Kanban process rules. This report identifies these gaps and provides recommendations to ensure a "perfect execution" of the implementation plan.

---

## 2. Key Review Areas Audit

### 2.1 Test Coverage Analysis
*   **Missing Unit Tests:**
    *   Validation of CoinGecko rate limiting headers specifically for Bitvavo's weight system.
    *   Testing the `Heatmap Engine` promotion/demotion logic in isolation (mocking volume spikes).
    *   Validation of multi-tenant isolation at the service layer (attempting to watch an asset for tenant A with tenant B's context).
*   **Missing Integration Tests:**
    *   E2E flow: Bitvavo Mock -> Tiered Sync -> Redis -> Agent Context Builder.
    *   ClickHouse "Decision-Triggered" storage: Verification that only the specified T-30min window is saved upon terminal decision.
*   **Missing Edge Cases:**
    *   Network partitions between the Sync Service and Redis/Kafka.
    *   Corruption in the `bitvavo_assets.csv` file (null values, extra columns).
    *   API keys expiration or revocation handling.

### 2.2 Kanban Workflow Definition
*   **Gap:** The word "Kanban" is used in the title, but no column definitions or transition rules exist.
*   **Missing Elements:**
    *   **Columns:** Backlog, To Do, In Progress, Peer Review, Testing, Done.
    *   **WIP Limits:** Not specified.
    *   **Definition of Done (DoD):** Needs to be defined globally and per-task.
    *   **Transition Rules:** Requirements to move from "To Do" to "In Progress" (e.g., "Must have a defined Test Case design").

### 2.3 Asset System Architecture
*   **Gap:** Asset Lifecycle is only hinted at via "Promotion/Demotion".
*   **Missing Elements:**
    *   **State Machine:** Defined states: `DISCOVERED`, `ACTIVE`, `TIER_1`, `TIER_2`, `TIER_3`, `INACTIVE` (Delisted), `ARCHIVED`.
    *   **Storage Tiers:** Explicit mapping between Asset Tiers and Storage Resolution (e.g., Tier 1 = Ticks, Tier 3 = 1h OHLCV).

### 2.4 Dependencies and Resources
*   **Missing Specification:**
    *   **Environment Variables:** No consolidated list of required secrets (BITVAVO_API_KEY, COINGECKO_KEY, etc.).
    *   **Infrastructure Versions:** Specific versions for Redpanda (Kafka 3.x compatible?) and ClickHouse.

### 2.5 Implementation Gaps
*   **Agent Context:** The context format is broad. It needs specific schema definitions (e.g., correlation matrix size, lookback periods for metrics).
*   **Error Handling:** No plan for "Sync Lag" recovery (e.g., what happens if Tier 1 misses 5 seconds of data).

### 2.6 Quality Criteria
*   **Missing Targets:**
    *   **Coverage:** Minimum 90% LCOV.
    *   **Performance:** <10ms context assembly (specified), <100ms API response time (missing), <1s end-to-end event latency.

---

## 3. Prioritized Recommendations
1.  **Define the Asset State Machine:** Create a formal diagram/table of how assets transition between tiers and statuses.
2.  **Codify Kanban Rules:** Add a section to the TDD doc defining "Definition of Ready" and "Definition of Done".
3.  **Expand TDD Lifecycle:** Ensure every task in the Kanban starts with a specific test file path.
4.  **Consolidate Infrastructure:** List all Docker-compose requirements and .env keys.
