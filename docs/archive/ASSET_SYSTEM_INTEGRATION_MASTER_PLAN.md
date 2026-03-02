# Agentic Trader: Asset System Integration Master Plan (v2.1)

## Executive Summary
Dit document dient als het definitieve masterplan voor de opschaling van het Agentic Trader platform van 10 naar 448+ assets. Het corrigeert feitelijke onjuistheden, adresseert kritieke gaten in performance, multi-tenancy en opslag, en biedt een roadmap voor een productie-ready, tiered market data architectuur.

---

## 1. Huidige Staat & Gap Analysis

### 1.1 Technische Realiteit
*   **Frontend:** Vite + React 19.
*   **Backend:** Async-first FastAPI architectuur (AsyncSession verplicht).
*   **Caching:** Redis v7.2-alpine (Patroon: `markets:*`).
*   **Status:** "Infrastructure Ready" is het startpunt; 18+ componenten zijn in ontwikkeling.

### 1.2 Kritieke Hiaten (Audit v2.1)
1.  **Rate Limiting:** Bitvavo API limiet management (~1000 req/min).
2.  **Categorisatie:** Dynamische verrijking via CoinGecko API.
3.  **Frontend Scalability:** Renderen van 448+ assets zonder DOM-lag.
4.  **Storage Explosion:** ClickHouse management voor 448 assets op hoge frequentie.
5.  **Multi-Tenant Isolation:** Scheiding van watchlists per gebruiker/tenant.

---

## 2. Doelarchitectuur v2.1

### 2.1 Database Schema (Multi-Tenant & Async)
```python
# agent_asset_watchlist tabel (Update)
CREATE TABLE agent_asset_watchlist (
    id SERIAL PRIMARY KEY,
    tenant_id UUID NOT NULL,                   -- Kritiek voor isolatie
    agent_id VARCHAR(50) NOT NULL,
    asset_symbol VARCHAR(20) NOT NULL,
    priority INTEGER DEFAULT 1,
    added_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (asset_symbol) REFERENCES assets(symbol)
);
```

### 2.2 Tiered Caching & Dynamic Promotion (Heatmap Engine)
Het systeem is niet langer statisch. Een **Heatmap Engine** monitort:
*   **Volume Spikes:** Assets met >200% volume stijging in 1u worden gepromoveerd naar Tier 1.
*   **Agent Interest:** Assets die door >3 agents gevolgd worden, gaan automatisch naar Tier 1.
*   **Demotie:** Assets die 24u geen activiteit/interesse hebben, zakken terug naar Tier 3.

---

## 3. Data Storage & Reproduceerbaarheid

### 3.1 Decision-Triggered High-Resolution Logging
Om ClickHouse-overbelasting te voorkomen en toch reproduceerbaarheid te garanderen:
1.  **General Universe (Tier 2/3):** Alleen 1-minuut OHLCV aggregaten opslaan.
2.  **Active Assets (Tier 1):** Bewaar ruwe ticks gedurende een rollend venster van 7 dagen.
3.  **Trade Logging:** Zodra een agent een beslissing neemt (Buy/Sell), worden de ruwe ticks van dat asset vanaf *T-30 min* tot *T+2u* permanent opgeslagen. Dit garandeert dat elke transactie 100% reproduceerbaar is zonder miljoenen onnodige ticks op te slaan.

---

## 4. Frontend: High-Performance Asset Selector

### 4.1 Virtualization & Search
Om de Bitvavo-stijl lijst van 448+ assets soepel te tonen:
*   **List Virtualization:** Gebruik van `react-window` voor de asset-lijst (enkel de zichtbare items in de DOM).
*   **Debounced Search:** Zoekopdrachten worden pas na 200ms getriggerd om de UI responsive te houden.
*   **Categorized Tabs:** Sneltoetsen naar Layer 1, DeFi, Meme etc. om de navigatie door 448 assets te versnellen.

---

## 5. Roadmap & Fasering

### Fase 1: Foundation & DevEx (Week 1)
- [ ] Alembic migraties (incl. `tenant_id`).
- [ ] **Snapshot-Based Workflow:** Script voor het wekelijks downloaden van een geanonimiseerde DB-dump (PostgreSQL + ClickHouse) voor lokale development.
- [ ] Async Seed script met CoinGecko integratie.

### Fase 2: Real-time Pipeline (Week 2)
- [ ] `TieredMarketDataService` met Rate Limiting.
- [ ] Implementatie **Heatmap Engine** voor automatische Tier-shifty.
- [ ] WebSocket prijs-pushes voor Tier 1.

### Fase 3: Storage & Intelligence (Week 3)
- [ ] ClickHouse **Decision-Triggered Logging** logica.
- [ ] AgentContextBuilder integratie.
- [ ] Redpanda/Kafka event streaming voor market events.

---

## 6. Operational Excellence & Backup

### 6.1 Backup & Disaster Recovery
*   **PostgreSQL:** Dagelijkse `pg_dump` naar `/backups`.
*   **WAL Archiving:** Ingeschakeld voor Point-in-Time recovery.
*   **Snapshot Service:** Genereert wekelijks de development-ready dumps voor het team.

### 6.2 Monitoring (Grafana)
*   **Sync Lag per Tier.**
*   **ClickHouse Storage Growth Rate.**
*   **Heatmap Promotion/Demotion events.**

---

## 7. Succes Criteria (v2.1)
- [ ] < 2s latency voor Tier 1 updates.
- [ ] 60fps scrolling door 448+ assets in de frontend.
- [ ] 100% reproduceerbaarheid van agent-beslissingen via trade-triggered logging.
- [ ] Multi-tenant isolatie geverifieerd in de database laag.
- [ ] Geen IP-blocks van exchanges door actieve rate limiting.
