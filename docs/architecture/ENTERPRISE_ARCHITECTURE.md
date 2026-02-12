# ENTERPRISE ARCHITECTURE V3.0 - Agentic Trader Platform (Samkhya-Inspired)

## 1. System Overview (Samkhya-Inspired)
Dit document beschrijft de architectuur van een institutioneel handelssysteem, nu diep geïntegreerd met de Samkhya-filosofie van Purusha en Prakriti, en de drie Gunas. Het platform functioneert als een microkosmos van de manifeste realiteit, met bewustzijn als de stille getuige en de natuur als de actieve kracht.

---

## 2. Component Architecture (Samkhya Microservices)

### 2.0. The Purusha Layer (Witness Consciousness)
*   **Intent Monitor Service (`backend/services/intent_monitor.py`):**
    *   **Rol:** De ultieme, stille waarnemer. Reflecteert de oorspronkelijke intentie/doel van het systeem (bijv. "Safe and Profitable Growth").
    *   **Functie:** Meet de algehele Guna-balans van Prakriti (de manifeste wereld van het systeem) en visualiseert hoe deze afwijkt van de Purusha's zuivere intentie.
    *   **Output:** Geen actieve instructies. Dient als een "spiegel van bewustzijn" voor de Mahat (Orchestrator).

### 2.1. The Prakriti Layers (Manifest Nature)

#### 2.1.1. The Mahat / Buddhi Layer (Intellect - Cognitive Orchestrator)
*   **Cognitive Orchestrator (`backend/services/cognitive_orchestrator.py`):**
    *   **Rol:** De intelligentie die Prakriti stuurt. Interpreteert Guna-vectoren van inkomende data.
    *   **Functie:** Dynamische Guna-Balancing. Activeert/de-activeert agents op basis van globale Guna-vibratie en Purusha's intentie. Stuurt timers en events.
    *   **Output:** Directives aan Manas (Agents), Order Intents.

#### 2.1.2. The Ahamkara Layer (Ego/Identity - Agent Profiles)
*   **Agent Registry (`backend/core/agent_registry.py`):**
    *   **Rol:** Definieert de unieke "identiteit" van elke agent, inclusief hun dominante Guna-compositie.
    *   **Functie:** Laadt agentprofielen (Mahabhuta, Guna-verhouding, system_directive, allowed_tools).

#### 2.1.3. The Manas Layer (Mind - Agents)
*   **Research Agent (`backend/services/research_agent.py` - Rajas Dominant):**
    *   **Rol:** Zoekt en analyseert externe informatie (nieuws, social media). Zeer actief, beweeglijk.
    *   **Guna:** Voornamelijk Rajas.
*   **Macro Agent (`backend/services/macro_agent.py` - Tamas/Sattva):**
    *   **Rol:** Analyseert langetermijntrends, stabiliteit, historische context.
    *   **Guna:** Tamas (diepte, structuur) en Sattva (objectiviteit).
*   **Valuation Agent (`backend/services/valuation_agent.py` - Tamas Dominant):**
    *   **Rol:** Bepaalt de intrinsieke waarde van assets, kijkt naar fundamentele structuren.
    *   **Guna:** Voornamelijk Tamas (structuur, inertie).

#### 2.1.4. The Tanmatras Layer (Subtle Elements - Data Processing)
*   **Guna Quantifier Service (`backend/core/guna_quantifier.py`):**
    *   **Rol:** Meet de "vibratie" (Guna-compositie) van elke binnenkomende data-eenheid (Market Tick, News Article).
    *   **Functie:** Kwantificeert Sattva, Rajas, Tamas per data-item.
    *   **Output:** `GunaVector` (`{sattva: 0.x, rajas: 0.y, tamas: 0.z}`)

#### 2.1.5. The Mahabhutas Layer (Gross Elements - Agent Functies)
*   **Memory Agent (Water - Jala):** (`cognitive_orchestrator.py`): Retentie, flow van kennis (Sattva/Tamas).
*   **Regime Detector (Vuur - Agni):** (`cognitive_orchestrator.py`): Transformatie van data in strategische richting (Rajas/Sattva).
*   **Risk Engine (Vuur - Agni):** (`backend/risk/validators.py`): Purificatie, blokkeert ongewenste actie (Rajas/Sattva).
*   **Execution Gateway (Aarde - Prithvi):** (`backend/services/execution_gateway.py`): Fysieke manifestatie van orders (Tamas/Rajas).

#### 2.1.6. Infrastructure (Karma - Action & Experience)
*   **Message Broker (Redpanda):** De universele drager van informatie (Akasha - Ether).
*   **TimeSeries DB (ClickHouse):** De onveranderlijke record van acties en observaties (Prithvi - Aarde).
*   **Vector DB (Chroma/Weaviate):** De rivier van herinneringen (Jala - Water).

---

## 3. Data Flow & Guna Dynamics

### 3.1. Inkomende Informatie (Externe Lucht)
1.  **Externa Data (News, Market Ticks, Macro-economie):** Wordt ingevoerd.
2.  **Guna Quantifier:** Meet de Sattva, Rajas, Tamas vibratie van de data. Voegt een `GunaVector` toe aan de data.
3.  **Message Broker:** Publiceert data met `GunaVector` naar relevante Kafka topics.

### 3.2. De Cognitieve Loop (Interne Akasha/Agni)
1.  **Cognitive Orchestrator:** Consumeert alle Kafka-berichten met `GunaVector`.
2.  **Dynamic Guna Balancing:** De Orchestrator berekent de globale Guna-balans van het systeem.
    *   Vergelijkt met de `IntentMonitor` (Purusha's reflectie).
    *   Pas actiepatroon aan: Is de markt te 'Rajasic'? Activeer dan meer 'Tamasic' agents.
3.  **Agent Activation:** De Orchestrator routeert berichten naar agents wiens `guna_composition` het meest matcht met de Guna-vibratie van het event én de gewenste globale Guna-balans.
    *   Bijv: Een 'Rajasic' nieuwsbericht in een te 'Rajasic' markt? Stuur het naar de 'Tamasic' Valuation Agent voor een reality-check.
4.  **Agent Action (Manas/Ahamkara):** De geactiveerde agent (bijv. Research) voert zijn taak uit (LLM-analyse, calculatie) en genereert nieuwe `SIGNAL` berichten, nu met zijn eigen `guna_composition` stempel.

### 3.3. Besluitvorming en Actie (Interne Prithvi/Jala)
1.  **Risk Engine:** Ontvangt `ORDER_INTENT` met GunaVector. Past Guna-gebaseerde risicoregels toe (Tamas voor stabiliteit).
2.  **Execution Gateway:** Manifesteert de order in de buitenwereld.

---

## 4. Purusha's Reflectie & Prakriti's Aanpassing
*   De `IntentMonitor` (Purusha's spiegel) toont de voortdurende Guna-balans van het systeem.
*   Als deze balans afwijkt van de ideale staat (gedefinieerd door de 'Intent Monitor'), zal de `CognitiveOrchestrator` (Buddhi) zijn acties en de activatie van agents aanpassen om Prakriti terug in lijn te brengen met de Purusha's waargenomen intentie.

Dit is een fundamentele verandering die het platform op een geheel nieuw, filosofisch gelaagd niveau brengt.
