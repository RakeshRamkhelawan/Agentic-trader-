# Module Overview & Dependency Table

**Quick reference guide for all modules and their relationships**

---

## Backend Modules

### 1. Agent System (`backend/agents/`)

| Module | File | Purpose | Dependencies | Integrates With |
|--------|------|---------|--------------|-----------------|
| Base Agent | `base_agent.py` | Abstract ReAct agent | LLM, Memory | All agents |
| Analyst | `analyst_agent.py` | Market analysis | Data, LLM | Orchestrator |
| Asset Discovery | `asset_discovery_agent.py` | Asset scanning | Exchange APIs | Asset service |
| Data Scout | `data_scout_agent.py` | Data collection | Market data | Memory |
| Fund Manager | `fund_manager_agent.py` | Portfolio mgmt | Risk, Execution | Trading service |
| News | `news_agent.py` | News ingestion | News APIs | Sentiment |
| Orchestrator | `orchestrator_agent.py` | Agent coordination | All agents | Cognitive |
| Researcher | `researcher_agents.py` | Deep research | LLM, RAG | Memory |
| Risk Manager | `risk_manager_agent.py` | Risk assessment | Risk engine | Execution |
| Sentiment | `sentiment_agent.py` | Sentiment analysis | News, LLM | Decision |
| Trader | `trader_agent.py` | Trade decisions | Execution | Orchestrator |
| Elemental Base | `elemental_base.py` | Vedic agents base | Guna system | Elemental |
| Elemental Macro | `elemental_macro.py` | Macro analysis | Elemental base | Researcher |
| Elemental Orchestrator | `elemental_orchestrator.py` | Vedic coordination | Elemental | Main orchestrator |
| Elemental Research | `elemental_research.py` | Vedic research | Elemental base | Researcher |
| Elemental Risk | `elemental_risk_guardian.py` | Vedic risk | Elemental base | Risk |
| Elemental Router | `elemental_router.py` | Vedic routing | Elemental | Execution |
| Elemental Valuation | `elemental_valuation.py` | Vedic valuation | Elemental base | Valuation |

### 2. API Layer (`backend/api/`)

| Module | File | Purpose | Dependencies | Route Prefix |
|--------|------|---------|--------------|--------------|
| Main API | `main.py` | FastAPI app | All APIs | `/` |
| Gateway | `gateway.py` | API aggregation | All routers | `/` |
| Agents API | `agents_api.py` | Agent control | Agents | `/api/v1/agents` |
| Analytics API | `analytics_api.py` | Analytics | Risk, Storage | `/api/v1/analytics` |
| Approval API | `approval_api.py` | Trade approval | Governance | `/api/v1/approvals` |
| Auth API | `auth_api.py` | Authentication | Auth0 | `/api/v1/auth` |
| Backtest API | `backtest_api.py` | Backtesting | Backtesting | `/api/v1/backtest` |
| Dashboard | `dashboard.py` | Dashboard data | All services | `/dashboard` |
| Federated API | `federated_api.py` | Federated triad | Federated | `/api/v1/federated` |
| KYC API | `kyc_api.py` | Identity | Auth | `/api/v1/kyc` |
| Monitoring API | `monitoring_api.py` | Health checks | Telemetry | `/api/v1/monitoring` |
| Navagraha API | `navagraha_api.py` | Vedic astrology | Navagraha | `/api/v1/navagraha` |
| OODA API | `ooda_api.py` | OODA cycle | System identity | `/api/v1/ooda` |
| Paper Trading API | `paper_trading_api.py` | Paper trading | Shadow portfolio | `/api/v1/paper-trading` |
| Prediction API | `prediction_api.py` | Predictions | Prediction market | `/api/v1/prediction` |
| Trading API | `trading_api.py` | Trading ops | Execution | `/api/v1/trading` |
| User Settings API | `user_settings_api.py` | Preferences | User service | `/api/v1/settings` |
| WebSocket Endpoints | `websocket_endpoints.py` | WS handlers | WS Manager | `/ws` |
| WebSocket Manager | `websocket_manager.py` | WS coordination | Redis | Internal |
| Paper Trading WS | `paper_trading_ws*.py` | Paper WS | Paper engine | `/ws/paper-trading` |

### 3. Core System (`backend/core/`)

| Module | File | Purpose | Dependencies | Frequency |
|--------|------|---------|--------------|-----------|
| Cognitive Mind | `cognitive_mind_service.py` | Decision layer | Memory, LLM | 50-200ms |
| Eternal Soul | `eternal_soul_service.py` | Cosmic constraints | Guna, Navagraha | ~1 minute |
| Memory System | `memory_system.py` | Long-term memory | ChromaDB | On-demand |
| Memory Agent | `memory_agent.py` | Memory interface | Memory system | On-demand |
| System Identity | `system_identity.py` | Self-awareness | Karma, OODA | Continuous |
| Guna Quantifier | `guna_quantifier.py` | Behavioral state | Sensors | Real-time |
| Decision Discriminator | `decision_discriminator.py` | Classify decisions | Rules | Per decision |
| Frequency Analysis | `frequency_analysis.py` | Pattern detection | Market data | Periodic |
| Regime Detector | `regime_detector.py` | Market regime | Analytics | Periodic |
| Sensory Processor | `sensory_processor.py` | Input processing | Market data | Real-time |
| Zero Copy Bridge | `zero_copy_bridge.py` | Fast data | SHM | <10ms |
| Cache Layer | `cache_layer.py` | Caching | Redis | On-demand |
| Context | `context.py` | Execution context | Auth | Per request |
| Config | `config/settings.py` | Configuration | Environment | Startup |

### 4. Execution Layer (`backend/execution/`)

| Module | File | Purpose | Dependencies | Latency |
|--------|------|---------|--------------|---------|
| Smart Order Router | `smart_order_router.py` | Route orders | Risk, Exchanges | <10ms |
| Shadow Portfolio | `shadow_portfolio.py` | Paper trading | Portfolio | <10ms |
| Hot Path Engine | `hot_path_engine.py` | Fast execution | SHM | <1ms |
| Fast Config | `fast_config.py` | Quick config | Binary storage | <1ms |
| Reflex Executor | `reflex_executor.py` | Layer 3 execution | SHM | <10ms |
| Order Executor | `order_executor.py` | Order logic | Exchanges | Variable |
| Exchange Adapter | `exchange_adapter.py` | Exchange abstraction | CCXT | Variable |
| Broker Interface | `broker_interface.py` | Broker API | Exchanges | Variable |
| Bitvavo Adapter | `bitvavo_adapter.py` | Bitvavo API | Bitvavo SDK | Network |
| Revolut X Adapter | `revolut_x_adapter.py` | Revolut API | Revolut SDK | Network |
| CCXT Adapter | `ccxt_adapter.py` | Universal adapter | CCXT | Network |

### 5. Services Layer (`backend/services/`)

| Module | File | Purpose | Dependencies | Scale |
|--------|------|---------|--------------|-------|
| Cognitive Orchestrator | `cognitive_orchestrator.py` | Main coordinator | All agents | Singleton |
| Execution Gateway | `execution_gateway.py` | Execution API | Execution | Per request |
| Market Data Processor | `market_data_processor.py` | Data handling | Market APIs | Continuous |
| Market Data Streamer | `market_data_streamer.py` | Data streaming | WebSocket | Continuous |
| Paper Trading Engine | `paper_trading_engine.py` | Paper trading | Shadow portfolio | Session |
| Trading Service | `trading_service.py` | Trading logic | Execution | Per request |
| Research Agent | `research_agent.py` | Research | LLM, RAG | On-demand |
| Macro Agent | `macro_agent.py` | Macro analysis | Data | Periodic |
| Valuation Agent | `valuation_agent.py` | Valuation | Models | On-demand |
| Risk Engine | `risk_engine.py` | Risk computation | Risk | Real-time |
| Risk Guardian | `risk_guardian_agent.py` | Risk monitoring | Risk | Continuous |
| Signal Bridge | `signal_bridge.py` | Signal distribution | WebSocket | Real-time |

### 6. Risk Management (`backend/risk/`)

| Module | File | Purpose | Dependencies | Metric |
|--------|------|---------|--------------|--------|
| VaR Calculator | `var_calculator.py` | Value at Risk | Statistics | 95%, 99% |
| Stress Tester | `stress_tester.py` | Stress tests | Scenarios | 6 scenarios |
| Kelly Criterion | `kelly_criterion.py` | Position sizing | Probability | Kelly % |
| Position Sizer | `position_sizer.py` | Sizing logic | Risk limits | Units |
| Risk Orchestrator | `risk_orchestrator.py` | Risk coordination | All risk | Aggregate |
| Validators | `validators.py` | Validation rules | Limits | Pass/Fail |
| Drawdown Monitor | `drawdown_monitor.py` | DD tracking | Portfolio | DD % |

### 7. LLM Integration (`backend/llm/`)

| Module | File | Purpose | Dependencies | Provider |
|--------|------|---------|--------------|----------|
| Gateway | `gateway.py` | LLM routing | All providers | Router |
| Factory | `factory.py` | Provider factory | Providers | Factory |
| Provider Interface | `provider_interface.py` | Abstract base | - | Interface |
| Service | `service.py` | LLM service | Gateway | Wrapper |
| Prompt Loader | `prompt_loader.py` | Prompt mgmt | Files | Loader |
| Gemini Provider | `providers/gemini.py` | Google Gemini | Google AI | Google |
| DeepSeek Provider | `providers/deepseek.py` | DeepSeek | DeepSeek API | DeepSeek |
| Ollama Provider | `providers/ollama.py` | Local LLM | Ollama | Local |
| Standard Provider | `providers/standard.py` | Standard interface | OpenAI | OpenAI |
| Usage Tracker | `usage_tracker.py` | Token tracking | Analytics | Metrics |

### 8. Event System (`backend/events/`)

| Module | File | Purpose | Dependencies | Transport |
|--------|------|---------|--------------|-----------|
| Event Bus | `event_bus.py` | Redis Streams | Redis | Redis |
| Kafka Broker | `kafka_broker.py` | Kafka impl | Kafka | Kafka |
| Message Broker | `message_broker.py` | Abstract broker | - | Interface |
| Schemas | `schemas.py` | Event models | Pydantic | - |

### 9. Storage Layer (`backend/storage/`)

| Module | File | Purpose | Dependencies | Type |
|--------|------|---------|--------------|------|
| ClickHouse Client | `clickhouse_client.py` | Analytics DB | ClickHouse | Columnar |
| Tenant-Aware CH | `tenant_aware_clickhouse.py` | Multi-tenant | ClickHouse | Columnar |
| Tenant-Aware Chroma | `tenant_aware_chroma.py` | Multi-tenant | ChromaDB | Vector |

### 10. Backtesting (`backend/backtesting/`)

| Module | File | Purpose | Dependencies | Feature |
|--------|------|---------|--------------|---------|
| Engine | `engine.py` | Backtest engine | Data | Main |
| Exchange | `exchange.py` | Sim exchange | Orders | Simulation |
| Data Feed | `data_feed.py` | Data loading | CSV/DB | Historical |
| Metrics | `metrics.py` | Performance | Statistics | Analytics |
| Position Sizing | `position_sizing.py` | Sizing | Risk | Kelly |
| Fill Models | `fill_models.py` | Fill simulation | Orders | Realistic |
| Slippage Models | `slippage_models.py` | Slippage | Statistics | Realistic |

### 11. Strategies (`backend/strategies/`)

| Module | File | Purpose | Dependencies | Type |
|--------|------|---------|--------------|------|
| Base | `base.py` | Strategy base | Backtesting | Abstract |
| Momentum | `momentum.py` | Momentum strategy | Indicators | Trend |
| Mean Reversion | `mean_reversion.py` | MR strategy | Statistics | Reversion |
| Breakout | `breakout.py` | Breakout strategy | Levels | Trend |
| Trend Following | `trend_following.py` | Trend strategy | Indicators | Trend |
| Simple Tremor | `simple_tremor.py` | Tremor strategy | Volatility | Volatility |

---

## Frontend Modules

### 1. Pages (`frontend/src/pages/`)

| Module | File | Purpose | Route | Permissions |
|--------|------|---------|-------|-------------|
| Dashboard | `Dashboard.tsx` | Main view | `/dashboard` | Authenticated |
| Markets | `Markets.tsx` | Market data | `/markets` | Authenticated |
| Portfolio | `Portfolio.tsx` | Holdings | `/portfolio` | Authenticated |
| Terminal | `Terminal.tsx` | Trading | `/terminal` | Authenticated |
| History | `History.tsx` | Trades | `/history` | Authenticated |
| Settings | `Settings.tsx` | Preferences | `/settings` | Authenticated |
| Live Paper Trading | `LivePaperTrading.tsx` | Paper trading | `/paper-trading` | Authenticated |
| Login | `auth/Login.tsx` | Sign in | `/login` | Public |
| Register | `auth/Register.tsx` | Sign up | `/register` | Public |
| KYC | `auth/KYC.tsx` | Identity | `/kyc` | Authenticated |

### 2. State Management (`frontend/src/store/`)

| Module | File | Purpose | State Type |
|--------|------|---------|------------|
| Auth Store | `authStore.ts` | Authentication | Persistent |
| App Store | `appStore.ts` | App state | Session |
| Trading Store | `tradingStore.ts` | Trading | Real-time |
| WebSocket Store | `wsStore.ts` | WS connection | Session |

### 3. Hooks (`frontend/src/hooks/`)

| Module | File | Purpose | Dependencies |
|--------|------|---------|--------------|
| WebSocket | `useWebSocket.ts` | WS management | Native WS |
| Market Data | `useMarketData.ts` | Data subscription | API |
| Auth | `useAuth.ts` | Auth operations | Auth0 |

---

## Infrastructure Modules

### 1. Docker (`infrastructure/docker/`)

| Module | File | Purpose | Target |
|--------|------|---------|--------|
| Backend | `Dockerfile.backend` | API server | Python 3.11 |
| Frontend Dev | `Dockerfile.frontend` | Dev server | Node 20 |
| Frontend Prod | `Dockerfile.frontend.prod` | Production | Nginx |
| Entrypoint | `entrypoint.sh` | Container init | Bash |
| Nginx Config | `nginx.conf` | Reverse proxy | Nginx |

### 2. Kubernetes (`infrastructure/k8s/`)

| Module | File | Purpose | Type |
|--------|------|---------|------|
| Helm Chart | `charts/agentic-platform/` | Full deployment | Chart |
| Deployment | `deployment.yaml` | App deployment | Manifest |
| ConfigMap | `configmap.yaml` | Configuration | Manifest |
| Secrets | `secrets.yaml` | Sensitive data | Manifest |
| PVC | `pvc.yaml` | Storage | Manifest |

### 3. Observability

| Module | Path | Purpose | Tool |
|--------|------|---------|------|
| Grafana Dashboards | `infrastructure/grafana/dashboards/` | Visualization | Grafana |
| Prometheus Config | `infrastructure/prometheus/` | Metrics | Prometheus |
| Alert Rules | `infrastructure/prometheus/rules/` | Alerting | Prometheus |

---

## Script Modules (`scripts/`)

| Script | File | Purpose | Trigger | Output |
|--------|------|---------|---------|--------|
| Setup Database | `setup_database.py` | DB init | Deploy | Schema |
| Seed Assets | `seed_assets.py` | Asset import | Manual | DB records |
| Seed Users | `seed_users.py` | User import | Manual | DB records |
| Run Paper Trading | `run_paper_trading.py` | Paper trading | Manual | JSON log |
| Live Paper Trading | `live_paper_trading_production.py` | Live demo | Manual/Cron | WS events |
| Run Backtest | `run_unified_backtest.py` | Backtesting | Manual | Report |
| Agent Benchmark | `agent_benchmark.py` | Agent testing | CI | Metrics |
| Download Data | `download_historical_data.py` | Data import | Manual | CSV |
| Setup Revolut | `setup_revolut_keys.py` | Key config | Manual | Config |
| Health Check | `backend/scripts/ops/health_check.py` | Monitoring | Cron | Status |

---

## Dependency Summary

### External Services

| Service | Purpose | Integration | Status |
|---------|---------|-------------|--------|
| **PostgreSQL** | Primary database | `backend/core/database.py` | Required |
| **Redis** | Cache & Events | `backend/core/cache/` | Required |
| **ClickHouse** | Analytics | `backend/storage/` | Required |
| **ChromaDB** | Vector DB | `backend/storage/` | Required |
| **Kafka/Redpanda** | Messaging | `backend/events/` | Optional |
| **Auth0** | Authentication | `backend/core/auth/` | Required |
| **Bitvavo** | Crypto exchange | `backend/execution/` | Optional |
| **Revolut X** | Crypto exchange | `backend/execution/` | Optional |
| **Gemini API** | LLM | `backend/llm/providers/` | Optional |
| **Ollama** | Local LLM | `backend/llm/providers/` | Optional |
| **Prometheus** | Metrics | `backend/observability/` | Required |
| **Grafana** | Dashboards | `infrastructure/grafana/` | Required |

### Internal Dependencies Graph

```
agents → core → storage
  ↓       ↓       ↓
services ← execution → risk
  ↓
api → frontend
```

---

## Testing Coverage

| Module Type | Test Location | Count | Coverage |
|-------------|---------------|-------|----------|
| Unit Tests | `backend/tests/unit/` | 100+ | 85%+ |
| Integration Tests | `backend/tests/integration/` | 80+ | 80%+ |
| E2E Tests | `backend/tests/e2e/` | 10+ | 70%+ |
| Security Tests | `backend/tests/security/` | 20+ | 90%+ |
| Frontend Tests | `frontend/src/**/*.test.tsx` | 50+ | 75%+ |

---

## Quick Reference

### Entry Points by Use Case

| Use Case | Entry Point | Command |
|----------|-------------|---------|
| Development API | `backend/api/main.py` | `uvicorn backend.api.main:app --reload` |
| Production API | `backend/api/main.py` | `uvicorn backend.api.main:app --workers 4` |
| AI Testing | `backend/consciousness_main.py` | `python backend/consciousness_main.py` |
| Full Platform | `backend/main.py` | `python backend/main.py` |
| Paper Trading | `scripts/run_paper_trading.py` | `python scripts/run_paper_trading.py` |
| Frontend Dev | `frontend/src/main.tsx` | `npm run dev` |
| Frontend Prod | `frontend/dist/` | `nginx -g 'daemon off;'` |

### Module Count Summary

| Category | Count | Lines of Code (est.) |
|----------|-------|---------------------|
| Backend Python | 539 | ~45,000 |
| Frontend TypeScript | 292+ | ~25,000 |
| Tests | 232+ | ~20,000 |
| Infrastructure | 39 | ~3,000 |
| Scripts | 94 | ~8,000 |
| **Total** | **1,200+** | **~101,000** |

---

*Last updated: 2026-02-20*
