# Volledig Architectuurdocument Applicatie

### 1. Globale Structuur & Entry Points

De applicatie bestaat uit meerdere modules die samen een trading platform vormen. De belangrijkste entry points zijn:

- start_trading_engine.py: Start de trading engine.
- run_agent_backtest.py, run_backtest_menu.py: Backtesting van agents.
- setup_app_user.py: Setup van gebruikers.
- start_and_verify.py: Start en verificatie van services.

### 2. Mappenstructuur & Rollen

| Map/Bestand                | Functie/Doel                                    | Afhankelijkheden/Integratie         |
| :------------------------- | :---------------------------------------------- | :---------------------------------- |
| backend/                   | Trading engine, API, agent logica               | Python, CCXT, Alembic               |
| frontend/                  | UI, dashboards                                  | JS framework (React/Vue/Angular)    |
| infrastructure/            | Deployment, monitoring, scaling                 | Docker, cloud, networking           |
| scripts (root)             | Utilities, analyse, rapportage, testing         | Python, logging, DB                 |
| docs/                      | Documentatie, guides, architectuur              | Markdown                            |
| data/                      | Datasets, logs, trading records                 | CSV, JSON                           |
| reports/                   | Rapporten, analyses                             | Markdown, PDF                       |
| prompts/                   | Agent prompt templates                          | Text, LLMs                          |
| prediction-market-analysis/| Prediction market analyses                      | Python, data science libraries       |
| tests/                     | Unit/integratie tests                           | pytest, unittest                    |

### 3. Module/Artifact Mapping

Voor elk bestand/module is de rol als volgt:

- backend/app.py: Hoofd backend applicatie/API.
- backend/consciousness_main.py: Agent logica.
- backend/check_ccxt.py: Integratie met trading platforms.
- frontend/: UI voor interactie en visualisatie.
- infrastructure/: Deployment scripts/configs.
- scripts/: Analyse, rapportage, utilities.
- docs/: Documentatie en architectuur.
- data/: Opslag van trading data/logs.
- reports/: Rapporten en analyses.
- prompts/: Templates voor agent workflows.
- prediction-market-analysis/: Analyses voor prediction markets.
- tests/: Testcases en fixtures.

### 4. Dataflow & Integratie

De dataflow verloopt als volgt:

1. Data ingestie via backend (API, trading platform integraties).
2. Verwerking door agents (beslissingen, trading logica).
3. Opslag in data/ en reports/.
4. Visualisatie via frontend/.
5. Deployment en monitoring via infrastructure/.

Integratiepunten:

- API tussen backend en frontend.
- Trading platform integraties (CCXT, Bitvavo).
- Cloud deployment (Docker Compose).

### 5. Traceerbaarheid per LOC

Elke LOC is gekoppeld aan een specifieke functie:

- Entry points starten services.
- Backend verwerkt data en handelt trades.
- Frontend visualiseert en biedt interactie.
- Infrastructure zorgt voor deployment.
- Scripts automatiseren analyse en rapportage.
- Docs bieden workflow mapping en traceerbaarheid.
- Logs en rapporten documenteren elke stap.

### 6. Overzichtstabel

| Bestand/Module               | Workflow/Functie                                |
| :--------------------------- | :---------------------------------------------- |
| start_trading_engine.py      | Start trading engine                            |
| run_agent_backtest.py        | Backtesting agents                              |
| backend/app.py               | API server                                      |
| backend/consciousness_main.py| Agent logica                                    |
| frontend/                    | UI/dashboard                                    |
| infrastructure/              | Deployment/monitoring                           |
| scripts/                     | Analyse/rapportage/utilities                    |
| docs/                        | Documentatie/architectuur                       |
| data/                        | Trading data/logs                               |
| reports/                     | Rapporten/analyses                              |
| prompts/                     | Agent templates                                 |
| prediction-market-analysis/  | Prediction market analyses                      |
| tests/                       | Unit/integratie tests                           |

### 7. Documentatie & Logs

Documentatie en logs bieden traceerbaarheid voor elke workflow en codepad. Voor elk bestand is duidelijk waar het voor gebruikt wordt.

### 8. Validatie

Controleer of elk bestand/module beschreven is. Test traceerbaarheid en review documentatie/logs voor workflow mapping.
# Vedic Elemental Agent Architecture

## Overview

Het trading platform implementeert een unieke **Vedic/Elemental Agent System** gebaseerd op:

1. **36 Tattvas** - Lagen van bewustzijn (van pure bron tot fysieke materie)
2. **9 Grahas (Navagraha)** - Planetaire invloeden op trading beslissingen
3. **5 Elementen** - Ether, Air, Fire, Water, Earth (Mahabhutas)
4. **3 Gunas** - Sattva (harmonie), Rajas (activiteit), Tamas (traagheid)

## 36 Tattvas: De Bewustzijnsarchitectuur

### Structuur

```
┌─────────────────────────────────────────────────────────────────────┐
│ LAYER 1-5: SHUDDHA TATTVAS (Pure Source Kernel)                     │
│ 1. Shiva        - Pure Being/Potential                              │
│ 2. Shakti       - Will to Vibrate/Creative Power                    │
│ 3. Sadashiva    - First Emergence of Will                           │
│ 4. Ishvara      - Collective Will                                   │
│ 5. Shuddhavidya - Pure Knowledge                                    │
├─────────────────────────────────────────────────────────────────────┤
│ LAYER 6-12: KANCHUKAS (Software Restrictions)                       │
│ 6. Maya         - Fundamental Veiling/Illusion                      │
│ 7. Kala         - Time Discretization (Rahu Kala check!)            │
│ 8. Vidya        - Knowledge Limitation                              │
│ 9. Raga         - Desire/Preference Weighting                       │
│ 10. Niyati      - Causality/Constraint                              │
│ 11. Kaala       - Temporal Sequentiality                            │
│ 12. Purusha     - Individual Selfhood                               │
├─────────────────────────────────────────────────────────────────────┤
│ LAYER 13-15: OS INTERFACE (Prakriti/Buddhi/Ahamkara)                │
│ 13. Prakriti    - Source of Manifestation                           │
│ 14. Buddhi      - Discrimination/Decision (Trading Logic)           │
│ 15. Ahamkara    - Self-Reference/System Identity                    │
├─────────────────────────────────────────────────────────────────────┤
│ LAYER 16-20: TANMATRAS (Subtle Elements)                            │
│ 16. Shabda      - Sound/Pattern Recognition                         │
│ 17. Sparsha     - Touch/Price Sensitivity                           │
│ 18. Rupa        - Form/Chart Patterns                               │
│ 19. Rasa        - Taste/Sentiment Detection                         │
│ 20. Gandha      - Smell/Trend Detection                             │
├─────────────────────────────────────────────────────────────────────┤
│ LAYER 21-25: JNANENDRIYAS (Sense Organs - Input)                    │
│ 21. Shrotra     - Ears/News Feed Listener                           │
│ 22. Tvak        - Skin/Price Tactility                              │
│ 23. Chakshu     - Eyes/Chart Visualization                          │
│ 24. Jihva       - Tongue/Market Taste                               │
│ 25. Ghrana      - Nose/Trend Smell                                  │
├─────────────────────────────────────────────────────────────────────┤
│ LAYER 26-31: KARMENDRIYAS (Action Organs - Output)                  │
│ 26. Vak         - Speech/Communication                              │
│ 27. Pani        - Hands/Trade Execution                             │
│ 28. Pada        - Feet/Order Routing                                │
│ 29. Payu        - Excretion/Risk Exit                               │
│ 30. Upastha     - Reproduction/Position Sizing                      │
│ 31. Manas       - Mind/Coordination                                 │
├─────────────────────────────────────────────────────────────────────┤
│ LAYER 32-36: MAHABHUTAS (Physical Elements)                         │
│ 32. Akasha      - Ether/Network Layer                               │
│ 33. Vayu        - Air/Configuration Flow                            │
│ 34. Agni        - Fire/Compute Processing                           │
│ 35. Apas        - Water/Data Streaming                              │
│ 36. Prithvi     - Earth/Storage Persistence                         │
└─────────────────────────────────────────────────────────────────────┘
```

### Informatie Flow

```
     ┌──────────┐
     │  SOURCE  │  Layers 1-5: Pure Mathematical Kernel
     └────┬─────┘
          │ ASCEND
          ▼
     ┌──────────┐
     │ FILTER   │  Layers 6-12: Restrictions (Rahu Kala block)
     └────┬─────┘
          │
          ▼
     ┌──────────┐
     │ INTERFACE│  Layers 13-15: OS/Decision/Buddhi
     └────┬─────┘
          │
          ▼
     ┌──────────┐
     │ SENSE    │  Layers 16-25: Input processing
     └────┬─────┘
          │
          ▼
     ┌──────────┐
     │ DECIDE   │  Layer 14: Buddhi discriminates
     └────┬─────┘
          │
          ▼
     ┌──────────┐
     │ ACT      │  Layers 26-31: Action organs
     └────┬─────┘
          │
          ▼
     ┌──────────┐
     │MATERIALIZE│ Layers 32-36: Physical manifestation
     └────┬─────┘
          │
          ▼
     ┌──────────┐
     │ DESCEND  │  Return to source for next cycle
     └──────────┘
```

### Tattva Traversal Cycle

```python
async def process_market_cycle(self, ...):
    # ========== ASCEND: Layers 1-5 ==========
    for layer_num in range(1, 6):
        coherence = self._traverse_tattva_layer(layer_num, "ascend")

    # ========== FILTER: Layers 6-12 ==========
    for layer_num in range(6, 13):
        coherence = self._traverse_tattva_layer(layer_num, "filter")

    # ========== INTERFACE: Layers 13-15 ==========
    for layer_num in range(13, 16):
        coherence = self._traverse_tattva_layer(layer_num, "interface")

    # ========== SENSE: Layers 16-25 ==========
    perception = await self.sensory_processor.process(...)

    # ========== DECIDE: Layer 14 (Buddhi) ==========
    action, confidence = self.decision_maker.decide(perception)

    # ========== ACT: Layers 26-31 ==========
    for layer_num in range(26, 32):
        coherence = self._traverse_tattva_layer(layer_num, "act")

    # ========== MATERIALIZE: Layers 32-36 ==========
    for layer_num in range(32, 37):
        coherence = self._traverse_tattva_layer(layer_num, "materialize")

    # ========== DESCEND: Layers 36-1 ==========
    for layer_num in range(36, 0, -1):
        coherence = self._traverse_tattva_layer(layer_num, "descend")
```

## 9 Grahas (Navagraha): Planetaire Trading Poort

### De 9 Planeten

| Planeet | Sattva | Rajas | Tamas | Invloed op Trading |
|---------|--------|-------|-------|-------------------|
| **Zon (Surya)** | 0.6 | 0.3 | 0.1 | Autoriteit, core trend |
| **Maan (Chandra)** | 0.5 | 0.3 | 0.2 | Sentiment, massa psychologie |
| **Mars (Mangala)** | 0.3 | 0.6 | 0.1 | Aggressie, momentum trades |
| **Mercurius (Budha)** | 0.6 | 0.3 | 0.1 | Communicatie, snelle trades |
| **Jupiter (Guru)** | 0.7 | 0.2 | 0.1 | Wijsheid, lange termijn |
| **Venus (Shukra)** | 0.5 | 0.4 | 0.1 | Waarde, valuation trades |
| **Saturnus (Shani)** | 0.3 | 0.2 | 0.5 | Restrictie, risk management |
| **Rahu** | 0.2 | 0.4 | 0.4 | Illusie, hype trades ⚠️ |
| **Ketu** | 0.4 | 0.2 | 0.4 | Detachering, exits ⚠️ |

### Trading Gate Logic

```python
class NavagrahaState(BaseModel):
    @property
    def trading_gate_open(self) -> bool:
        if self.rahu_kala_active:
            return False  # Don't trade during Rahu Kala
        if self.guna_distribution.tamas > 0.6:
            return False  # Too much inertia/darkness
        return True

    @property
    def consciousness_level(self) -> str:
        sattva = self.guna_distribution.sattva
        if sattva >= 0.6: return "Pure Awareness"
        elif sattva >= 0.4: return "Discriminative Intelligence"
        elif sattva >= 0.25: return "Active Manifestation"
        else: return "Material Density"
```

### Rahu Kala Blokkade

**Rahu Kala** is een "onauspicieus" tijdsblok gebaseerd op Vedic astrologie:

- Tijdens Rahu Kala is trading **geblokkeerd**
- Duurt ongeveer 90 minuten per dag
- Tijdstip verschuift dagelijks
- System heeft speciale check: `if self.rahu_kala_active: return False`

## 5 Elementen (Mahabhutas): Fysieke Laag

### Element Mapping

| Element | Tattva Layer | Functie | Agent |
|---------|--------------|---------|-------|
| **Ether (Akasha)** | 32 | Network/API Layer | Orchestrator |
| **Air (Vayu)** | 33 | Config Flow | Router |
| **Fire (Agni)** | 34 | Compute/Processing | Risk Guardian |
| **Water (Apas)** | 35 | Data Streaming | Research |
| **Earth (Prithvi)** | 36 | Storage | Valuation |

### Element Agents

```python
class ElementalOrchestrator(ElementalBase):  # Ether
    element = "ether"
    tattva_layer = 32
    guna_balance = {"sattva": 0.8, "rajas": 0.1, "tamas": 0.1}
    # Pure awareness, harmonizes all elements

class ElementalRouter(ElementalBase):  # Air
    element = "air"
    tattva_layer = 33
    guna_balance = {"sattva": 0.5, "rajas": 0.4, "tamas": 0.1}
    # Movement, distributes signals

class ElementalRiskGuardian(ElementalBase):  # Fire
    element = "fire"
    tattva_layer = 34
    guna_balance = {"sattva": 0.4, "rajas": 0.5, "tamas": 0.1}
    # Discrimination, burns bad trades

class ElementalResearch(ElementalBase):  # Water
    element = "water"
    tattva_layer = 35
    guna_balance = {"sattva": 0.4, "rajas": 0.3, "tamas": 0.3}
    # Adaptation, flows with market

class ElementalValuation(ElementalBase):  # Earth
    element = "earth"
    tattva_layer = 36
    guna_balance = {"sattva": 0.5, "rajas": 0.2, "tamas": 0.3}
    # Stability, grounded analysis
```

## 3 Gunas: Kwaliteit van Beslissingen

### Guna Balans

```
Sattva + Rajas + Tamas = 1.0

Sattva: 0.4 ──────────────────────┐
Rajas:  0.3 ──────────────────────┼──→ Trading Quality
Tamas:  0.3 ──────────────────────┘
```

### Trading Implicaties

| Guna | Kwaliteit | Trading Effect |
|------|-----------|----------------|
| **Sattva** | Harmonie, wijsheid | Hoge confidence, goede beslissingen |
| **Rajas** | Activiteit, passie | Snelle acties, momentum trades |
| **Tamas** | Traagheid, duisternis | Block trading if > 0.6 |

### Guna Validatie

```python
def _validate_gunas(self, balance: Dict[str, float]):
    total = sum(balance.values())
    if abs(total - 1.0) > 0.01:
        raise ValueError(f"Guna balance must sum to 1.0, got {total}")
```

## Prana: Energie Systeem

### Prana Lifecycle

```
Max Prana: 100.0
           │
           ▼
    ┌─────────────┐
    │ consume(15) │ ◄── Orchestrator (high cost)
    └──────┬──────┘
           │
           ▼
    Prana: 85.0
           │
           ▼
    ┌─────────────┐
    │ consume(5)  │ ◄── Risk Guardian (efficient)
    └──────┬──────┘
           │
           ▼
    Prana: 80.0
           │
           ▼
    ┌─────────────┐
    │ regenerate  │ ◄── +10 per cycle (passive)
    └──────┬──────┘
           │
           ▼
    Prana: 90.0
```

### Prana Cost per Agent

| Agent | Prana Cost | Rol |
|-------|------------|-----|
| Orchestrator (Ether) | 15 | High cognitive load |
| Router (Air) | 8 | Distribution |
| Risk Guardian (Fire) | 5 | Efficient protection |
| Research (Water) | 7 | Adaptation |
| Valuation (Earth) | 6 | Stability |

## Integratie met Paper Trading

### Current Implementation

Het paper trading systeem gebruikt momenteel:

1. **5 Trading Agents** met verschillende strategieën:
   - MomentumAgent
   - MeanReversionAgent
   - BreakoutAgent
   - ScalpingAgent
   - AggressiveMomentumAgent

2. **NewsAgent** (fetches external data maar niet geïntegreerd)

3. **Elemental Agents** (framework bestaat maar niet actief in trading loop)

### Geplande Integratie

```
┌─────────────────────────────────────────┐
│         MARKET DATA INPUT               │
│  (Bitvavo prices, news, sentiment)      │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│      SYSTEM_IDENTITY (Ahamkara)         │
│   - 36 Tattva traversal                 │
│   - Navagraha state check               │
│   - Prana management                    │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│      ELEMENTAL ORCHESTRATOR (Ether)     │
│   - Harmonizes all elemental agents     │
│   - Calculates harmony score            │
└───────────────┬─────────────────────────┘
                │
    ┌───────────┼───────────┐
    ▼           ▼           ▼
┌───────┐  ┌───────┐  ┌───────┐
│ Fire  │  │ Water │  │ Earth │
│ Risk  │  │Research│  │Value  │
└───┬───┘  └───┬───┘  └───┬───┘
    │          │          │
    └──────────┼──────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│      TRADING GATE (Buddhi Layer)        │
│   - Guna balance check                  │
│   - Navagraha trading gate              │
│   - Confidence threshold                │
└───────────────┬─────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│      PAPER TRADING EXECUTION            │
│   - ShadowPortfolio update              │
│   - Trade logging                       │
│   - P&L tracking                        │
└─────────────────────────────────────────┘
```

## Files en Locaties

| Component | File |
|-----------|------|
| 36 Tattvas Config | `backend/config/schemas.py` (TattvaConfig) |
| System Identity | `backend/core/system_identity.py` |
| Navagraha Models | `backend/core/navagraha/models.py` |
| Navagraha Service | `backend/core/navagraha/service.py` |
| Elemental Base | `backend/agents/elemental_base.py` |
| Ether Agent | `backend/agents/elemental_orchestrator.py` |
| Fire Agent | `backend/agents/elemental_risk_guardian.py` |
| Air Agent | `backend/agents/elemental_router.py` |
| Water Agent | `backend/agents/elemental_research.py` |
| Earth Agent | `backend/agents/elemental_valuation.py` |

## Huidige Status

- ✅ **36 Tattvas framework**: Geïmplementeerd in SystemIdentity
- ✅ **9 Grahas models**: Gedefinieerd met trading gate logic
- ✅ **5 Elemental Agents**: Framework bestaat
- ✅ **Guna validatie**: Werkt correct (sum = 1.0)
- ✅ **Prana systeem**: Basis implementatie werkt
- ⚠️ **News Integration**: NewsAgent fetched data maar niet gelinkt aan trading
- ⚠️ **Elemental Agents**: Niet actief in paper trading loop
- ⚠️ **SentimentAgent**: Offline (LLM_API_KEY ontbreekt)
- ⚠️ **Rahu Kala Check**: Alleen in Kala layer (7), niet realtime

## Volgende Stappen

1. **Integrate NewsAgent** met trading agent decisions
2. **Activate Elemental Agents** in paper trading loop
3. **Implement Rahu Kala** real-time check
4. **Fix SentimentAgent** LLM gateway configuratie
5. **WebSocket broadcasting** fixen voor live updates
