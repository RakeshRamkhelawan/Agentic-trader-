# PRD: Agentic Trader V18 - Realistische Implementatie

**Auteur:** Kimi Code CLI  
**Datum:** 25 Feb 2026  
**Versie:** V18  
**Status:** IN DEVELOPMENT  

**Wijzigingen na Reality Check:**  
> Na analyse bleek dat veel "gaps" al bestonden. Dit document beschrijft de ECHTE werkzaamheden die nog nodig zijn om bestaande componenten te verbinden en stabiliseren.

---

## 1. Situatie Analyse (WERKELIJKE Status)

### 1.1 Wat BESTAAT Al (Niet Opnieuw Bouwen!)

| Component | Locatie | Status | Actie Nodig |
|-----------|---------|--------|-------------|
| **MCP Server** | `backend/mcp_broker/server.py` | Functional | Wire naar agents |
| **VedAstro Module** | `backend/vedastro/` (9 files) | Complete | Expose als MCP tools |
| **MCP Tools** | `backend/mcp_broker/tools/` | 15+ tools | Al geregistreerd |
| **Backtest Engines** | `backend/backtest/` | V8-V17 | Gebruiken, niet bouwen |
| **Risk System** | `backend/risk/` | VaR, Kelly | Al geïntegreerd |
| **Event Bus** | `backend/events/` | Redis Streams | Al operationeel |

### 1.2 Wat MOET Echt Gebeuren (De Echte Gaps)

```
┌────────────────────────────────────────────────────────────────┐
│  DE ECHTE GAPS (Solo Developer, 8 weken)                       │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Week 1-2: VERBINDEN                                           │
│  ├── AgentWithTools base class [80% DONE]                      │
│  │   └── backend/agents/agent_with_tools.py [CREATED]          │
│  ├── Wire agents naar MCP server [TODO]                        │
│  └── VedAstro tools registratie [TODO]                         │
│                                                                │
│  Week 3: EXPOSEN                                               │
│  ├── VedAstro → MCP tools wrapper [VERIFIED EXISTS]            │
│  │   └── backend/mcp_broker/tools/vedastro_tools.py            │
│  └── Tool semantic registry [TODO]                             │
│                                                                │
│  Week 4: INFRASTRUCTUUR                                        │
│  ├── PriceFeedService check [VERIFY EXISTS]                    │
│  └── MCP broker monitoring [TODO]                              │
│                                                                │
│  Week 5-6: EXCHANGE & TESTEN                                   │
│  ├── Revolut X MCP wrapper [TODO]                              │
│  ├── Paper trading integratie [VERIFY EXISTS]                  │
│  └── End-to-end tests [TODO]                                   │
│                                                                │
│  Week 7: SECURITY                                              │
│  ├── 22 GitHub security alerts [PRIORITY]                      │
│  ├── OWASP hardening                                           │
│  └── Dependency audit                                          │
│                                                                │
│  Week 8: MONITORING                                            │
│  ├── Grafana dashboards                                        │
│  └── Alerting                                                  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 2. Week 1-2: AgentWithTools Implementatie

### 2.1 Wat is Gedaan

```python
# backend/agents/agent_with_tools.py - CREATED
class AgentWithTools(BaseAgent):
    """
    Base agent with ToolBroker integration.
    
    Agents kunnen nu tools aanroepen via MCP:
    
    Usage:
        class MyAgent(AgentWithTools):
            async def analyze(self, features, context):
                signal = await self.call_tool(
                    "vedastro__generate_signal",
                    {"symbol": "BTC", "current_price": 45000}
                )
                return {"action": signal["recommendation"]}
    """
    
    async def call_tool(self, tool_name: str, params: dict) -> dict:
        """Call any MCP tool via ToolBroker."""
        return await self.tool_broker.call_tool(tool_name, params)
```

**Test Resultaten:**
```
✅ AgentWithTools Import
✅ Agent Instantiation  
✅ VedAstro Tools Import
✅ MCP Server Imports
✅ Bestaande VedAstro Module
✅ Async Tool Call

6/6 tests geslaagd
```

### 2.2 Wat Moet Nog

1. **Concrete agent implementaties** maken die `AgentWithTools` extenden:
   - `VedAstroSignalAgent` - Vedic astrology signal generator
   - `ElementalConsensusAgent` - 4-element voting agent
   - `RiskCheckAgent` - Risk-aware decision agent

2. **Agent ↔ MCP Server wiring**:
   ```python
   # In agent startup:
   agent = VedAstroSignalAgent(
       agent_name="vedastro_oracle",
       tool_broker_url="http://mcp-broker:8001"
   )
   ```

---

## 3. Week 3: VedAstro Exposen

### 3.1 Wat Bestaat Al

**`backend/mcp_broker/tools/vedastro_tools.py`:**
```python
@circuit_breaker(failure_threshold=5, timeout_seconds=30)
@vedastro_retry
async def vedastro_generate_signal(
    symbol: str, 
    current_price: float, 
    ctx: Context = None
) -> dict[str, Any]:
    """Generate trading signal from astrological data."""
    orchestrator = _get_astro_orchestrator()
    astro_analysis = await orchestrator.analyze_asset(
        symbol=symbol, 
        current_price=current_price
    )
    return {
        "signal": signal_str,
        "confidence": signal.confidence,
        "strength_score": signal.strength_score,
        ...
    }
```

**Beschikbare VedAstro Tools:**
- `vedastro_generate_signal` - Trading signal generatie
- `vedastro_get_dasha` - Planetary period analysis
- `vedastro_get_transits` - Real-time transit berekening

### 3.2 Wat Moet Nog

1. **Server registratie verifiëren** in `backend/mcp_broker/server.py`:
   ```python
   mcp = FastMCP("AgenticTraderBroker")
   
   @mcp.tool(name="vedastro__generate_signal")
   async def vedastro_generate_signal_tool(...):
       return await vedastro_generate_signal(...)
   ```

2. **Tool registry** met semantic search:
   ```python
   # ToolBroker kan tools zoeken op beschrijving
   tool = tool_registry.find_tool("get vedic astrology signal")
   # Returns: vedastro_generate_signal
   ```

---

## 4. Week 4: Infrastructuur Check

### 4.1 PriceFeedService

**Vraag:** Bestaat deze al?
```bash
# Check of deze service al bestaat
find backend -name "*price*" -o -name "*feed*" | head -20
```

**Waarschijnlijke locaties:**
- `backend/services/price_feed.py`
- `backend/data/price_service.py`
- `backend/market/price_feed.py`

**Als het mist:**
```python
# Snelle implementatie
class PriceFeedService:
    """Unified price feed from multiple sources."""
    
    async def get_price(self, symbol: str, source: str = "primary") -> float:
        """Get latest price for symbol."""
        # Priority: live feed → cache → fetch
        pass
```

### 4.2 MCP Broker Monitoring

**Metrics die nodig zijn:**
- Tool call latency per tool
- Tool error rate
- Circuit breaker state changes
- Agent tool usage patterns

---

## 5. Week 5-6: Exchange & Testen

### 5.1 Revolut X MCP Wrapper

**Pattern (gelijk aan bestaande tools):**
```python
# backend/mcp_broker/tools/revolut_tools.py
@circuit_breaker(failure_threshold=3)
async def revolut_place_order(
    symbol: str,
    side: str,
    quantity: float,
    order_type: str = "market"
) -> dict:
    """Place order via Revolut X API."""
    # Use existing backend/integrations/revolut.py
    pass

@mcp.tool(name="revolut__place_order")
async def revolut_place_order_tool(...):
    return await revolut_place_order(...)
```

### 5.2 Paper Trading Check

**Bestaat al:** `backend/execution/paper_trading.py`  
**Nodig:** Integratie met MCP broker zodat agents paper trades kunnen uitvoeren

---

## 6. Week 7: Security (KRITIEK)

### 6.1 22 Open Security Issues

**Prioriteit:** HIGH  
**Bron:** GitHub Security Alerts (Dependabot)

**Actieplan:**
```bash
# 1. Lijst ophalen
gh security-alert list --repo owner/repo

# 2. Critical/High fixes eerst
pip audit --desc  # check dependencies

# 3. OWASP check
bandit -r backend/
safety check

# 4. Automatisch in CI
github-actions: security.yml
```

### 6.2 OWASP Hardening Checklist

- [ ] Input validatie op alle MCP tool inputs
- [ ] Rate limiting op tool calls
- [ ] Authentication voor MCP endpoints
- [ ] Secrets management (geen hardcoded keys)
- [ ] Audit logging voor alle trades

---

## 7. Week 8: Monitoring

### 7.1 Grafana Dashboards

**Dashboards die nodig zijn:**
1. **MCP Broker Health**
   - Tool call volume per tool
   - Latency percentiles
   - Circuit breaker states

2. **Agent Performance**
   - Analysis throughput
   - Decision accuracy (vs outcome)
   - Tool usage patterns

3. **Trading Performance**
   - P&L by agent
   - Signal accuracy
   - Execution slippage

### 7.2 Alerting

```yaml
alerts:
  - name: MCPBrokerDown
    condition: up{mcp_broker} == 0
    severity: critical
    
  - name: HighToolErrorRate
    condition: rate(tool_errors[5m]) > 0.1
    severity: warning
    
  - name: VedAstroCircuitOpen
    condition: vedastro_circuit_breaker_state == 1
    severity: warning
```

---

## 8. Solo Developer Strategie

### 8.1 Weekelijkse Flow

**Maandag:** Planning + enkele deep-focus uren  
**Dinsdag-Woensdag:** Implementatie (tools/agent/logica)  
**Donderdag:** Testen + fixen  
**Vrijdag:** Documentatie + deployment prep  
**Weekend:** Rust + achtergrond denken

### 8.2 Automatische Gates

**Pre-commit hooks:**
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: test-gaps
        name: Run real gaps test
        entry: python scripts/test_real_gaps.py
        language: system
        pass_filenames: false
```

**CI/CD minimal:**
```yaml
# .github/workflows/ci.yml
- name: Test Real Gaps
  run: python scripts/test_real_gaps.py
  
- name: Security Scan  
  run: |
    bandit -r backend/ -f json -o bandit.json
    safety check
```

### 8.3 Documentatie voor Zelf

**Elke week een `.md` file:**
```
docs/week-1-agent-with-tools.md
docs/week-2-mcp-wiring.md
docs/week-3-vedastro-expose.md
...
```

**Structuur per week:**
1. Wat was het doel?
2. Wat is bereikt?
3. Wat werkte niet?
4. Wat is de volgende stap?

---

## 9. Definition of Done (V18)

### 9.1 Must Have (MVP)

- [x] `AgentWithTools` base class werkt
- [ ] Minstens 3 concrete agent implementaties
- [ ] VedAstro tools geregistreerd in MCP server
- [ ] Agent kan VedAstro signal ophalen
- [ ] Paper trading via MCP tools
- [ ] 22 security issues opgelost
- [ ] MCP broker monitoring dashboard

### 9.2 Should Have

- [ ] Tool semantic registry
- [ ] Revolut X MCP wrapper
- [ ] E2E test suite
- [ ] Grafana alerting

### 9.3 Nice to Have

- [ ] Multi-exchange support
- [ ] Advanced tool chaining
- [ ] LLM-based tool selection

---

## 10. Test Strategie

### 10.1 Test Piramide

```
         /\
        /  \     E2E Tests (1-2)
       /____\      - Full trading flow
      /      \     - Agent → MCP → Execution
     /________\
    /          \   Integration Tests (5-10)
   /____________\    - Agent + ToolBroker
  /              \   - MCP server + VedAstro
 /________________\
/                  \  Unit Tests (20-50)
/____________________\  - ToolBrokerClient
                        - Individual tools
```

### 10.2 Critical Test Path

```python
# scripts/test_critical_path.py
async def test_full_flow():
    """Test: Agent → MCP → VedAstro → Signal"""
    
    # 1. Start agent
    agent = VedAstroSignalAgent()
    
    # 2. Analyze calls tool
    result = await agent.analyze(
        features={"symbol": "BTC", "price": 45000},
        context={}
    )
    
    # 3. Verify signal received
    assert "signal" in result
    assert "confidence" in result
```

---

## 11. Conclusie

### Wat We Echt Gaan Doen

| Wat de User Dacht | Wat Echt Moet Gebeuren |
|-------------------|------------------------|
| MCP server bouwen | Wire bestaande server naar agents |
| VedAstro module bouwen | Expose bestaande code als tools |
| Backtest engine bouwen | Gebruik bestaande V8-V17 |
| Multi-team planning | Solo developer, 8 weken |

### Succes Criteria

1. **Technisch:** AgentWithTools werkt, VedAstro tools bereikbaar, security issues opgelost
2. **Functioneel:** Agent kan vedastro signal ophalen en trading decision maken
3. **Operationeel:** MCP broker monitored, alerts werken

### Volgende Stap

Start Week 1 met **concrete agent implementaties** die de `AgentWithTools` base class gebruiken.

---

**Document Versie:** 1.0  
**Laatste Update:** 2026-02-25  
**Status:** Reality check complete, implementatie gestart
