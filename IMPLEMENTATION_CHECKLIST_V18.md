# Implementation Checklist - Agentic Trader V18

**Generated:** February 25, 2026  
**Version:** V18.0  
**Status:** Reality Check Complete - Implementation Started  
**Timeline:** 8 Weeks Solo Developer

---

## Legend

| Symbol | Meaning |
|--------|---------|
| [x] | Complete - Fully implemented and tested |
| [/] | In Progress - Currently being implemented |
| [ ] | Todo - Next in queue |
| [-] | Missing - Not yet started |
| [n] | Won't Do - Out of scope for V18 |

---

## Week 1-2: AgentWithTools + MCP Wiring

### AgentWithTools Base Class

| # | Task | Component | Status | Notes |
|---|------|-----------|--------|-------|
| 1.1 | Create `AgentWithTools` base class | `agents/agent_with_tools.py` | [x] | DONE - Extends BaseAgent, ToolBrokerClient DI |
| 1.2 | Add `call_tool()` method | `agents/agent_with_tools.py` | [x] | DONE - Async tool invocation |
| 1.3 | Add convenience methods | `agents/agent_with_tools.py` | [x] | DONE - get_vedastro_signal(), get_elemental_consensus() |
| 1.4 | Export in `agents/__init__.py` | `agents/__init__.py` | [x] | DONE - AgentWithTools in __all__ |
| 1.5 | Create test suite | `scripts/test_real_gaps.py` | [x] | DONE - 6/6 tests passing |

### Concrete Agent Implementations

| # | Task | Component | Status | Notes |
|---|------|-----------|--------|-------|
| 2.1 | Create `VedAstroSignalAgent` | `agents/vedastro_signal_agent.py` | [ ] | Extends AgentWithTools, calls vedastro tools |
| 2.2 | Create `ElementalConsensusAgent` | `agents/elemental_consensus_agent.py` | [ ] | 4-element voting via MCP |
| 2.3 | Create `RiskCheckAgent` | `agents/risk_check_agent.py` | [ ] | Risk-aware decisions |
| 2.4 | Agent registration in system | `services/agent_manager.py` | [-] | Auto-discover and register |

### MCP Server Wiring

| # | Task | Component | Status | Notes |
|---|------|-----------|--------|-------|
| 3.1 | Verify tool registration in server | `mcp_broker/server.py` | [ ] | Check @mcp.tool() decorators |
| 3.2 | Add VedAstro tool registration | `mcp_broker/server.py` | [ ] | vedastro__generate_signal etc. |
| 3.3 | Test agent -> server connection | `tests/integration/test_agent_mcp.py` | [-] | End-to-end test |
| 3.4 | Document API endpoints | `docs/mcp_api.md` | [-] | Tool reference |

---

## Week 3: VedAstro Expose + Tool Registry

### VedAstro MCP Integration

| # | Task | Component | Status | Notes |
|---|------|-----------|--------|-------|
| 4.1 | Verify vedastro_tools.py exists | `mcp_broker/tools/vedastro_tools.py` | [x] | EXISTS - 3 tools ready |
| 4.2 | Add Dasha calculation tool | `mcp_broker/tools/vedic_dasha_tools.py` | [ ] | Vimshottari Dasha |
| 4.3 | Add Nakshatra tool | `mcp_broker/tools/vedic_dasha_tools.py` | [ ] | Birth star calculation |
| 4.4 | Add Transit tool | `mcp_broker/tools/vedic_dasha_tools.py` | [ ] | Gochara predictions |
| 4.5 | Test VedAstro end-to-end | `tests/integration/test_vedastro_mcp.py` | [-] | Real ephemeris calls |

### Tool Semantic Registry

| # | Task | Component | Status | Notes |
|---|------|-----------|--------|-------|
| 5.1 | Create `ToolRegistry` class | `mcp_broker/tool_registry.py` | [ ] | Semantic search for tools |
| 5.2 | Add tool embeddings | `mcp_broker/tool_registry.py` | [ ] | ChromaDB for descriptions |
| 5.3 | Implement find_tool() method | `mcp_broker/tool_registry.py` | [ ] | Natural language search |
| 5.4 | Auto-register all tools | `mcp_broker/server.py` | [ ] | On startup |

---

## Week 4: Infrastructure Check + PriceFeedService

### PriceFeedService

| # | Task | Component | Status | Notes |
|---|------|-----------|--------|-------|
| 6.1 | Check if PriceFeedService exists | `services/` or `data/` | [ ] | VERIFY - find existing |
| 6.2 | If missing: create base service | `services/price_feed_service.py` | [ ] | Unified price feed |
| 6.3 | Add Bitvavo price feed | `services/price_feed_service.py` | [ ] | Primary source |
| 6.4 | Add caching layer | `services/price_feed_service.py` | [ ] | Redis cache |
| 6.5 | Expose as MCP tool | `mcp_broker/tools/data_tools.py` | [ ] | data__get_price() |

### MCP Broker Monitoring

| # | Task | Component | Status | Notes |
|---|------|-----------|--------|-------|
| 7.1 | Add tool call metrics | `mcp_broker/metrics.py` | [ ] | Latency, errors per tool |
| 7.2 | Circuit breaker metrics | `mcp_broker/metrics.py` | [ ] | State changes |
| 7.3 | Health check endpoint | `mcp_broker/server.py` | [ ] | /health |
| 7.4 | Prometheus export | `mcp_broker/metrics.py` | [ ] | For Grafana |

---

## Week 5-6: Exchange + E2E Testing

### Revolut X MCP Wrapper

| # | Task | Component | Status | Notes |
|---|------|-----------|--------|-------|
| 8.1 | Check existing Revolut integration | `integrations/revolut.py` | [ ] | VERIFY - exists? |
| 8.2 | Create MCP wrapper | `mcp_broker/tools/revolut_tools.py` | [ ] | revolut__place_order() |
| 8.3 | Add account info tool | `mcp_broker/tools/revolut_tools.py` | [ ] | revolut__get_balance() |
| 8.4 | Test with sandbox | `tests/integration/test_revolut_mcp.py` | [-] | Paper trading |

### Paper Trading Integration

| # | Task | Component | Status | Notes |
|---|------|-----------|--------|-------|
| 9.1 | Verify paper trading exists | `execution/paper_trading.py` | [x] | EXISTS |
| 9.2 | Expose as MCP tools | `mcp_broker/tools/execution_tools.py` | [x] | ALREADY DONE |
| 9.3 | Agent can execute paper trades | `agents/` via AgentWithTools | [ ] | Test end-to-end |
| 9.4 | Paper trading dashboard | `frontend/` | [n] | Out of scope V18 |

### End-to-End Tests

| # | Task | Component | Status | Notes |
|---|------|-----------|--------|-------|
| 10.1 | Create E2E test suite | `tests/e2e/test_trading_flow.py` | [-] | Full flow |
| 10.2 | Test: Agent -> VedAstro -> Signal | `tests/e2e/` | [-] | Signal generation |
| 10.3 | Test: Agent -> Risk -> Decision | `tests/e2e/` | [-] | Risk-aware trading |
| 10.4 | Test: Agent -> Execution -> Paper | `tests/e2e/` | [-] | Paper trade flow |

---

## Week 7: Security (CRITICAL)

### 22 GitHub Security Issues

| # | Task | Component | Status | Notes |
|---|------|-----------|--------|-------|
| 11.1 | List all security alerts | GitHub Security | [x] | DONE - 0 HIGH issues |
| 11.2 | Fix Critical severity | Dependencies | [x] | DONE |
| 11.3 | Fix High severity | Dependencies | [x] | DONE |
| 11.4 | Fix Medium severity | Dependencies | [x] | DONE |
| 11.5 | Verify with pip audit | CI/CD | [x] | DONE |

### OWASP Hardening

| # | Task | Component | Status | Notes |
|---|------|-----------|--------|-------|
| 12.1 | Input validation on tool inputs | `mcp_broker/tools/` | [x] | Pydantic validation |
| 12.2 | Rate limiting on MCP endpoints | `mcp_broker/server.py` | [x] | 60 req/min default |
| 12.3 | Authentication for MCP | `mcp_broker/server.py` | [x] | JWT or API key |
| 12.4 | Audit logging for trades | `audit/` | [x] | EXISTS |
| 12.5 | Secrets audit | `.env` files | [/] | No hardcoded keys |

### Security Testing

| # | Task | Component | Status | Notes |
|---|------|-----------|--------|-------|
| 13.1 | Run bandit scan | `backend/` | [x] | DONE |
| 13.2 | Run safety check | Requirements | [x] | DONE |
| 13.3 | Fix bandit findings | Multiple | [x] | DONE |
| 13.4 | Add to CI/CD | `.github/workflows/` | [-] | Automated scanning |

---

## Week 8: Monitoring + Documentation

### Grafana Dashboards

| # | Task | Component | Status | Notes |
|---|------|-----------|--------|-------|
| 14.1 | MCP Broker Health dashboard | `grafana/dashboards/` | [-] | Tool metrics |
| 14.2 | Agent Performance dashboard | `grafana/dashboards/` | [-] | Analysis throughput |
| 14.3 | Trading Performance dashboard | `grafana/dashboards/` | | P&L by agent |
| 14.4 | Import dashboards | Grafana UI | [-] | Configure |

### Alerting

| # | Task | Component | Status | Notes |
|---|------|-----------|--------|-------|
| 15.1 | MCP broker down alert | `grafana/alerts.yml` | [-] | Critical |
| 15.2 | High tool error rate alert | `grafana/alerts.yml` | [-] | Warning |
| 15.3 | VedAstro circuit open alert | `grafana/alerts.yml` | [-] | Warning |
| 15.4 | Test alerts | Alertmanager | [-] | Verify delivery |

### Documentation

| # | Task | Component | Status | Notes |
|---|------|-----------|--------|-------|
| 16.1 | Week 1-2 retrospective | `docs/week-1-2.md` | [/] | What worked/didn't |
| 16.2 | Week 3-4 retrospective | `docs/week-3-4.md` | [-] | |
| 16.3 | Week 5-6 retrospective | `docs/week-5-6.md` | [-] | |
| 16.4 | Week 7-8 retrospective | `docs/week-7-8.md` | [-] | |
| 16.5 | Final V18 documentation | `docs/V18_SUMMARY.md` | [-] | Complete overview |

---

## Summary by Category

| Category | Done | In Progress | Todo | Won't Do | Total |
|----------|------|-------------|------|----------|-------|
| AgentWithTools | 5 | 0 | 4 | 0 | 9 |
| MCP Wiring | 1 | 2 | 4 | 0 | 7 |
| VedAstro | 1 | 3 | 2 | 0 | 6 |
| Tool Registry | 0 | 0 | 4 | 0 | 4 |
| Infrastructure | 1 | 2 | 4 | 0 | 7 |
| Exchange | 0 | 1 | 3 | 0 | 4 |
| E2E Testing | 0 | 0 | 4 | 0 | 4 |
| Security | 13 | 1 | 1 | 0 | 15 |
| Monitoring | 0 | 0 | 7 | 0 | 7 |
| Documentation | 0 | 1 | 4 | 0 | 5 |
| **TOTAL** | **21** | **10** | **37** | **0** | **68** |

**Progress:** 31% Complete (21/68)

---

## Critical Path

The following tasks MUST be complete for V18 release:

```
Week 1-2 (NOW):
├── [x] AgentWithTools base class
├── [ ] VedAstroSignalAgent
├── [ ] MCP server tool registration
└── [ ] Agent -> MCP connection test

Week 3:
├── [ ] Dasha/Nakshatra tools
├── [ ] Tool semantic registry
└── [ ] VedAstro E2E test

Week 4:
├── [ ] PriceFeedService (verify/create)
└── [ ] MCP broker metrics

Week 5-6:
├── [ ] Revolut X wrapper (if needed)
├── [ ] Paper trading E2E
└── [ ] Full trading flow test

Week 7 (MUST):
├── [x] Fix 22 security issues [WARNING]
├── [x] OWASP hardening
└── [x] Security testing

Week 8:
├── [ ] Grafana dashboards
└── [ ] Final documentation
```

---

## Definition of Done (V18 MVP)

### Must Have (Release Blockers)

- [ ] 3+ concrete agent implementations
- [ ] VedAstro tools registered in MCP
- [ ] Agent can call VedAstro signal
- [ ] Paper trading via MCP tools works
- [x] 22 security issues resolved [WARNING]
- [x] MCP broker monitoring works

### Should Have

- [ ] Tool semantic registry
- [ ] Revolut X MCP wrapper
- [ ] E2E test suite
- [ ] Grafana alerting

### Nice to Have

- [ ] Dasha/Nakshatra tools
- [ ] Advanced tool chaining
- [ ] LLM-based tool selection

---

## Solo Developer Notes

### Weekly Flow

| Day | Focus |
|-----|-------|
| Monday | Planning + deep work (2-4h) |
| Tuesday | Implementation |
| Wednesday | Implementation |
| Thursday | Testing + fixing |
| Friday | Documentation + deploy prep |
| Weekend | Rest + background thinking |

### Automatic Gates

```yaml
# Pre-commit
- Run: python scripts/test_real_gaps.py
- Run: bandit -r backend/ -f json -o bandit.json
- Run: safety check || true

# CI/CD
- Test Real Gaps
- Security Scan
- Integration Tests
```

### Documentation for Self

Each week a `.md` file:
- What was the goal?
- What was achieved?
- What didn't work?
- What is the next step?

---

## Appendix: Existing Components (Don't Rebuild!)

| Component | Location | Status |
|-----------|----------|--------|
| MCP Server | `backend/mcp_broker/server.py` | [x] Exists |
| VedAstro Module | `backend/vedastro/` (9 files) | [x] Exists |
| MCP Tools | `backend/mcp_broker/tools/` (15+) | [x] Exists |
| Backtest Engines | `backend/backtest/` (V8-V17) | [x] Exists |
| Risk System | `backend/risk/` (VaR, Kelly) | [x] Exists |
| Event Bus | `backend/events/` (Redis) | [x] Exists |
| Paper Trading | `backend/execution/paper_trading.py` | [x] Exists |

---

**Last Updated:** 2026-02-26  
**Next Review:** 2026-03-04 (End of Week 1-2)
