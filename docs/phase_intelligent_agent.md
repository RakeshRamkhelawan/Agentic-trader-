# Phase 2: Intelligent Agent Build Spec (Production Ready)

Dit document is de **definitieve drop-in build spec** voor een LLM-builder om de `agentic_trader_platform` om te vormen tot een volledig autonome, OODA-gedreven multi-agent trading-AGI.

---

## 1. Doel & Scope

**Doel:**
Bouw bovenop de bestaande codebase een productie-klare, real-time, multi-agent tradingarchitectuur die:
- Continu een **OODA-loop** draait (Observe → Orient → Decide → Act) op live marktdata.
- Een “trading firm in a box” simuleert met gespecialiseerde LLM-agents (Data Scout, Analyst, Risk Manager, Trader, **Fund Manager**, **Researcher**).
- Een wiskundige cognitieve kern (**SystemIdentity** + **MemorySystem**) gebruikt als “brein”.
- Volledige **Governance, Monitoring & Failure Modes** integreert.

**Constraints:**
- Behoud bestaande backend-structuur, eventsysteem, cognitieve core en tests.
- Nieuwe modules moeten consistente stijl (type hints, docstrings, tests) volgen.
- Geen breaking changes aan publieke API's.

---

## 2. Huidige Kernarchitectuur (Context)

De repo bevat reeds een uitgebreide cognitieve kern. Deze bestanden dienen als fundament en mogen **niet** worden verwijderd of herschreven zonder reden.

### 2.1 Core Cognitive Layer
Locatie: `backend/core/`
- `frequency_analysis.py`: FFT-analyse van marktsignalen.
- `sensory_processor.py`: Verwerkt inputkanalen (prijs, volume, orderboek, sentiment).
- `memory_system.py`: Similarity-based clustering en trace opslag.
- `decision_discriminator.py`: Berekent confidence scores o.b.v. coherence en phase alignment.
- `system_identity.py`: De centrale orkestrator van perceptie en identiteit.

### 2.2 Agents & ReAct Basis
Locatie: `backend/agents/`
- `base_agent.py`: Abstracte basisklasse met `think()`, `act()`, en `ask_llm()`.
- `sentiment_agent.py`: Bestaande implementatie voor sentimentanalyse.

---

## 3. Nieuwe Architectuurlaag: OODA Loop Orchestratie

### 3.1 [NEW] OODA Orchestrator
**Bestand:** `backend/orchestration/ooda_coordinator.py`

**Doel:** De centrale loop die de cognitieve core en agents aanstuurt.

**Klasse:** `OODALoopCoordinator`
- **Dependencies:**
  - `SystemIdentity`, `SensoryProcessor`, `MemorySystem`
  - Agents: `DataScoutAgent`, `AnalystAgent`, `RiskManagerAgent`, `TraderAgent`, `FundManagerAgent`
  - `ExecutionEngine`, `VectorMemory`
- **Interface (Async):**
  ```python
  class OODALoopCoordinator:
      async def observe(self) -> dict: ...
      async def orient(self, observation: dict) -> dict: ...
      async def decide(self, orientation: dict) -> dict: ...
      async def act(self, decision: dict) -> dict: ...
      async def run_loop(self): ... # Interval of event-driven
  ```

---

## 4. RAG / Vector Memory Layer

### 4.1 [NEW] Vector Memory
**Bestand:** `backend/rag/vector_memory.py`

**Doel:** Opslag van strategische kennis en historische scenario's m.b.v. `pgvector`.

**Model:** `TradingKnowledge` (SQLAlchemy)
- Kolommen: `id`, `content`, `embedding` (vector), `category`, `asset`, `timestamp`.

**Functionaliteit:**
- Opslaan van Strategy Playbooks en Macro Events.
- Similarity search o.b.v. embeddings (zonder directe LLM dependency).
- Wordt aangeroepen in de **Orient** fase van de OODA loop.

---

## 5. Multi-Agent “Trading Firm” Laag

### 5.1 [NEW] DataScoutAgent
**Bestand:** `backend/agents/data_scout_agent.py`
**Rol:** Observe
- Verzamelt live data (ticks, orderboek, funding) en externe data (nieuws).
- Normaliseert data voor de `SensoryProcessor`.
- **Eis:** Leest alleen uit gestandaardiseerde bronnen (zie §10 Data Layer).

### 5.2 [NEW] AnalystAgent
**Bestand:** `backend/agents/analyst_agent.py`
**Rol:** Orient
- **TechnicalAnalyst:** Berekent indicatoren (RSI, MACD, Bollinger).
- **SentimentAnalyst:** Aggregeert nieuws/tweets tot scores.
- Output: Gestandaardiseerd signaal met confidence score.

### 5.3 [NEW] RiskManagerAgent
**Bestand:** `backend/agents/risk_manager_agent.py`
**Rol:** Decide (Constraints)
- Valideert voorgestelde trades tegen portfolio policies (max drawdown, exposure limits).
- Geeft `GO` / `NO-GO` met redenatie.

### 5.4 [NEW] TraderAgent
**Bestand:** `backend/agents/trader_agent.py`
**Rol:** Decide (Execution Plan)
- Synthetiseert signalen van Analyst en RiskManager.
- Formuleert concreet orderplan (Entry, Exit, Stop-Loss).

### 5.5 [NEW] FundManagerAgent
**Bestand:** `backend/agents/fund_manager_agent.py`
**Rol:** Decide (Portfolio Allocation)
- Luistert naar voorstellen van meerdere `TraderAgent` instanties.
- Aggregatie op portfolioniveau (exposure over assets/strategies).
- Bevoegdheid: Kan trades blokkeren, downsizen of heralloceren voor optimale risk/reward.

### 5.6 [NEW] ResearcherAgents (Bull/Bear)
**Bestand:** `backend/agents/researcher_bull_agent.py` / `_bear_agent.py`
**Rol:** Orient (Debate)
- Genereren tegengestelde theses op basis van dezelfde context.
- Output: Gestructureerd debat dat dient als extra input voor de `TraderAgent`.

---

## 6. Execution Layer: Hot Path

### 6.1 [NEW] FastConfig Bridge
**Bestand:** `backend/execution/fast_config.py`
**Doel:** Zero-copy bridge tussen Cold Path (LLM) en Hot Path (Order Execution).
- Gebruikt memory-mapped file of shared memory struct.

### 6.2 [NEW] HotPathEngine
**Bestand:** `backend/execution/hot_path_engine.py`
**Doel:** Low-latency execution zonder LLM calls.
- Leest beslissingen uit `FastConfig`.
- Voert risk-checks en validaties uit in microseconden.
- Stuurt orders naar exchange.

---

## 7. Governance, Monitoring & Failure Modes

### 7.1 Observability & Logging
- **DecisionAuditLog:** Centrale tabel (of ClickHouse) die elke OODA-cyclus logt met een unieke `trace_id`.
    - Input Snapshot (Markt + Portfolio)
    - RAG Bronnen
    - Agent Outputs
    - Final Decision & ExecutionOutcome

### 7.2 Agent Failure Modes & Watchdogs
- **Max Iterations:** Harde limiet op `observe/orient/decide` loops om infinite loops te voorkomen.
- **WatchdogAgent:**
    - Monitort hartslag van `OODALoopCoordinator` en `HotPathEngine`.
    - Activeert **Circuit Breaker** bij timeouts of error spikes.

### 7.3 Governance / RBAC
- **Trading Mode:** `TRADING_MODE` (notify/auto) mag alleen via gecontroleerde deployment pipeline of admin-panel gewijzigd worden.

### 7.4 Evaluation Datasets
- **Release Gate:** Nieuwe agent-versies moeten slagen voor een backtest set (Crash, Gap-up, Flash-illiquidity).

---

## 8. Human-in-the-Loop & Config

### 8.1 Notify-Only Mode
- **Systeem:** Stuurt `trade_proposal` events via EventBus.
- **UI:** Gebruiker keurt goed/af.
- **Config:** `TRADING_MODE = "notify_only" | "auto_limited" | "auto_full"`

---

## 9. Validatie & Tests

### 9.1 Nieuwe Test Suites
- `backend/tests/test_ooda_coordinator.py`: Simulatie van OODA flow.
- `backend/tests/test_agents_specialized.py`: Unit tests voor elke agent rol.
- `backend/tests/test_execution_hotpath.py`: Performance tests voor FastConfig/HotPath.
- `backend/tests/test_rag_vector_memory.py`: Vector search correctheid.

### 9.2 Integratie
- End-to-End test: Market Tick -> OODA -> Order -> Execution -> Memory Update.

---

## 10. Data- en Configlaag & NFRs

### 10.1 Gestandaardiseerde Data Layer
- **Schema's:**
    - `market_tick`: {symbol, price, volume, timestamp, side} (Postgres/TimescaleDB)
    - `orderbook_snapshot`: {symbol, bids, asks, timestamp} (Redis)
    - `portfolio_state`: {asset, balance, exposure, open_orders} (Redis)
- **Regel:** Agents lezen NOOIT direct van exchange API's, altijd via deze genormaliseerde laag.

### 10.2 Config & Policy Store
- **Centrale Config:** Eén bron voor risk-limits, OODA-interval, actieve agents.
- **Eis:** Geen hardcoded values in agent code.

### 10.3 Non-Functional Requirements (NFRs)
- **Latency:**
    - Cold Path: < 100ms
    - Hot Path: < 1ms
- **Reliability:** 99.9% Uptime voor OODA Loop.
- **Fallback:** Bij LLM failure -> Safe Mode (Risk Reductie / Flat).

### 10.4 Rollout Strategie
- Backtest -> Paper Trading -> Small-Size Live -> Full-Size.

---

## 11. Security & Tool Governance

### 11.1 Tool Toegang
- **Execute Trade:** Alleen toegankelijk voor `TraderAgent` en `HotPathEngine`.
- **Guardrails:** Asset allowlist en max position size afgedwongen in code.

### 11.2 Prompt Injection Mitigatie
- **Bronvermelding:** Agents moeten bron & datum rapporteren bij RAG gebruik.
- **Validatie:** Tegenstrijdige bronnen moeten expliciet gesignaleerd worden.

---

## 12. Documentatie & Schema's

### 12.1 Type Definities (Pydantic)
- `Observation`: Input data snapshot.
- `Orientation`: Verrijkte context met RAG & analyses.
- `Decision`: Gestructureerd besluit (Action, Asset, Size, Rationale).
- `ExecutionPlan`: Technische uitvoeringdetails (OrderType, TIF).
- `ExecutionOutcome`: Resultaat van de trade.

### 12.2 Event Schema's
- `market_tick`, `news_event`
- `trade_proposal`, `trade_executed`
- `risk_alert`, `system_health`

---

## 13. Richtlijnen voor de Bouwer

1.  **Reuse:** Gebruik de bestaande `SystemIdentity`, `MemorySystem` en `BaseAgent` als fundament.
2.  **Strict Typing:** Gebruik de gedefinieerde Pydantic models voor alle interfaces.
3.  **Explainability:** Log elke `think()` stap en RAG source naar `DecisionAuditLog`.
4.  **Safety First:** Hot Path is deterministisch. Geen LLM in execution loop.
5.  **Governance:** Implementeer Circuit Breakers en Watchdogs vanaf dag 1.
