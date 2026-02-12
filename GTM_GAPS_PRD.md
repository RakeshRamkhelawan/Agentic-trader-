# Product Requirements Document (PRD): Go-to-Market (GTM) Gaps Audit
**Project:** Agentic Trader Platform v1.734  
**Date:** February 5, 2026  
**Status:** DRAFT - Technical Gaps Analysis  

---

## 1. Executive Summary
This PRD outlines the technical and operational gaps required to transition the Agentic Trader Platform from a high-fidelity prototype/development build to a production-ready, market-competitive SaaS platform. 

While the core cognitive engine (Mahabhutas) and the data layer (multi-tenant ClickHouse) are robust, the platform currently lacks the "last-mile" infrastructure, security, and user-facing components required for a commercial launch.

---

## 2. Infrastructure & DevOps: Cloud-Native Readiness

### Gap 2.1: Missing Kubernetes (K8s) & Service Mesh Orchestration
*   **Current State**: Services run via `docker-compose`. `infrastructure/k8s` is empty. No internal service mesh.
*   **Business Impact**: Low availability and inability to scale agents horizontally per tenant. No automated self-healing.
*   **Implementation Plan**:
    1.  **Containerization Upgrade**: Optimize `Dockerfile` for multi-stage builds to reduce image size.
    2.  **Helm Chart Development**: Create templates for `agent-orchestrator`, `clickhouse-cluster`, `kafka-cluster`, and `redis-stack`.
    3.  **Namespace Isolation**: Implement Kubernetes Namespaces per tenant (or group) for hard resource isolation.
    4.  **Ingress Controller**: Deploy NGINX or Traefik with TLS termination via Cert-Manager.

### Gap 2.2: Secrets Management & Security Hardening
*   **Current State**: Credentials in `.env` and local `.pem` files.
*   **Business Impact**: High risk of API key theft. Non-compliant with SOC2/ISO27001.
*   **Implementation Plan**:
    1.  **Vault Integration**: Replace local file reads in `backend/core/config/settings.py` with a HashiCorp Vault or AWS Secrets Manager client.
    2.  **Runtime Injection**: Inject credentials as K8s Secrets (CSI driver) or environment variables at runtime only.
    3.  **Key Rotation**: Automate Ed25519 key rotation for the `ExchangeAdapter`.

---

## 3. Platform Core: Identity, Access & Multitenancy

### Gap 3.1: Identity & Access Management (IAM)
*   **Current State**: Single-user CLI focus. No auth layer in `backend/api/dashboard.py`.
*   **Business Impact**: Cannot prevent Tenant A from accessing Tenant B's metrics/trades via API.
*   **Implementation Plan**:
    1.  **OAuth2/OIDC Flow**: Integrate an identity provider (Auth0, Keycloak, or AWS Cognito).
    2.  **JWT Middleware**: Implement FastAPI/Starlette middleware to validate JWTs in every request.
    3.  **Tenant Context Injection**:
        *   Extract `tenant_id` from JWT `sub` or custom claim.
        *   Use `ContextVar` to store `current_tenant_id` per request/task.
    4.  **RBAC**: Define roles: `Viewer` (dashboard only), `Trader` (manual orders), `Admin` (config/keys).
*   **Technical Deepdive**:
    *   Create `backend/core/auth/` containing `jwt_validator.py` and `tenant_context.py`.
    *   Initialize `FastAPI` with `dependencies=[Depends(verify_token)]`.
    *   Integrate with `backend/storage/clickhouse_client.py` to automatically include `tenant_id` in every `SELECT` and `INSERT`.

### Gap 3.2: Multi-tenant Enforcement in Runtime
*   **Current State**: DB schema has `tenant_id`, but the Python logic in `backend/agents/` does not always respect it.
*   **Implementation Plan**:
    1.  **Global Filter**: Modify `ClickHouseClient` to automatically append `WHERE tenant_id = current_context.tenant_id` to all queries.
    2.  **Storage Isolation**: Ensure ChromaDB (Vector DB) collections are prefixed or isolated by `tenant_id`.
*   **Technical Deepdive**:
    *   Update `CognitiveOrchestrator` to accept a `tenant_id` in its constructor or `handle_message`.
    *   Ensure `MemoryAgent` uses partitioned namespaces in ChromaDB: `collection_name = f"memories_{tenant_id}"`.

---

## 4. Trading & Execution: Professional Grade Features

### Gap 4.1: Broker/Exchange Adapter Expansion
*   **Current State**: Only `Revolut X` (v1.0 API) supported.
*   **Business Impact**: Market limited to crypto/retail. No access to equities or institutional liquidity. High latency on REST polling.
*   **Implementation Plan**:
    1.  **Standardized SDK**: Refine `backend/execution/broker_interface.py` to support WebSocket-based order updates (FIX-like).
    2.  **New Adapters**: Implement `InteractiveBrokersAdapter` (TWS/Gateway) and `BinanceAdapter`.
    3.  **Smart Order Router (SOR)**: Enhance `backend/execution/smart_order_router.py` to route between multiple connected exchanges based on liquidity.
*   **Technical Deepdive**:
    *   Transition from `httpx.AsyncClient` to `websockets` or `ccxt.pro` for sub-100ms market data ingestion.
    *   Implement an `EventLoop` in `ExchangeAdapter` that emits `OrderUpdate` events to the `Orchestrator`.
    *   Add `latency_monitoring` to track execution delay from `DecisionMade` -> `OrderFilled`.

### Gap 4.2: High-Fidelity Backtesting & Simulation
*   **Current State**: Basic `StressTestSuite` exists. No integrated "Paper Trading" mode for the full agent stack.
*   **Business Impact**: Zero confidence in agent performance during black-swan events.
*   **Implementation Plan**:
    1.  **Backtest Engine**: Create a `BacktestExchangeAdapter` that replicates `ExchangeAdapter` but uses historical ClickHouse data.
    2.  **Time-Travel Debugging**: Use the `Phase 15 Hardware Metrics` framework to simulate high-load conditions during backtests.
    3.  **Performance Metrics**: Generate Sharpe Ratio, Sortino Ratio, and Win Rate reports automatically.
*   **Technical Deepdive**:
    *   Implement a `Clock` service that can "tick" historical data intervals (1m, 5m) instead of real-time.
    *   Simulate "Market Impact" where large agent orders move the price in the simulation.
    *   Integrate `stress_tester.py` scenarios into the automated backtest pipeline.

---

## 5. UI/UX: Frontend Dashboard

### Gap 5.1: Functional Dashboard Application
*   **Current State**: API endpoints exist, but no UI to display the Mahabhutas coherence or portfolio status.
*   **Business Impact**: Zero visibility for non-technical users.
*   **Implementation Plan**:
    1.  **Technology Stack**: Next.js, TailwindCSS, and Shadcn/UI for professional design.
    2.  **Real-time Visualization**: Use WebSockets (Phase 16 `subscribe_metrics`) to power a D3.js or Recharts-based coherence "Aura" map.
    3.  **Trading Terminal**: Build a UI for the `ExecutionInterface` to allow manual intervention/stop-loss overrides.

---

## 6. AIOps & Economic Sustainability

### Gap 6.1: Token Tracking & Billing Engine
*   **Current State**: Agents call LLM APIs without tracking usage costs per tenant.
*   **Business Impact**: High risk of "Bill Shock" and negative margins for the platform provider.
*   **Implementation Plan**:
    1.  **LLM Proxy**: Route all `backend/llm/providers/` calls through a monitoring proxy.
    2.  **Usage Logging**: Store `prompt_tokens` and `completion_tokens` per `tenant_id` in ClickHouse.
    3.  **Subscription Tiers**: Integrate Stripe Billing to enforce usage limits based on the tenant's plan.
*   **Technical Deepdive**:
    *   Create `backend/llm/usage_tracker.py` that intercepts the response from `provider.generate()`.
    *   Implement an asynchronous consumer that flushes usage data to ClickHouse in batches (buffer pattern).
    *   Define a `QuotaGuard` that blocks agent execution if a tenant's daily budget is exceeded.

### Gap 6.2: Model Fallback & Latency Optimization
*   **Current State**: Hardcoded model selection. 
*   **Business Impact**: System becomes unusable during upstream API outages or high latency.
*   **Implementation Plan**:
    1.  **Dynamic Selection**: implement logic to switch from `Gemini-1.5-Pro` to `Gemini-1.5-Flash` if latency exceeds 2000ms.
    2.  **Local LLM Fallback**: If cloud APIs fail, switch to local Ollama (Llama 3/Mistral) as defined in `ENTERPRISE_ARCHITECTURE.md`.
*   **Technical Deepdive**:
    *   Enhance `backend/llm/factory.py` with a `CircuitBreaker`.
    *   Implement "Hedging": send requests to two providers simultaneously and take the first successful one (expensive but reliable for `RiskGovernor`).

---

## 7. Governance & Compliance: Institutional Readiness

### Gap 7.1: MiFID II & Regulatory Audit Logging
*   **Current State**: Schema for `audit_trail` exists, but the logic is not fully integrated into the Agent Decision Loop.
*   **Business Impact**: Cannot operate in highly regulated markets (EU/US) without "Explainable AI" logs for every trade.
*   **Implementation Plan**:
    1.  **Immutable Logs**: Use ClickHouse `ReplacingMergeTree` to ensure logs cannot be tampered with.
    2.  **Reasoning Archiving**: Store the full LLM prompt and response (including search results) for every order submitted.
*   **Technical Deepdive**:
    *   Create `backend/core/compliance/audit_logger.py`.
    *   Implement a decorator `@audit_decision` for agent methods to capture input/output automatically.
    *   Export annual compliance reports via the `DashboardAPI`.

---

## 8. Roadmap & Prioritization

| Priority | Gap | Category | Complexity |
| :--- | :--- | :--- | :--- |
| **P0** | **Identity & IAM** | Security | High |
| **P0** | **Kubernetes Setup** | Infrastructure | Medium |
| **P1** | **Frontend (MVP)** | UX | Medium |
| **P1** | **Token Tracking** | Economics | Low |
| **P2** | **Broker Diversity** | Trading | High |
| **P2** | **Backtesting Engine** | Product | High |

---

## 8. Definition of Done (GTM Ready)
1.  Full SOC2-compliant secrets management.
2.  End-to-end multi-tenant isolation (DB + API).
3.  Functional web dashboard for monitoring coherence and portfolio.
4.  Automated usage-based billing per tenant.
5.  99.9% uptime deployment on Kubernetes.
