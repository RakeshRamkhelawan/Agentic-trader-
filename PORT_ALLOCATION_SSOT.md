# 🔒 PORT ALLOCATION - SINGLE SOURCE OF TRUTH (SSoT)

> **⚠️ VERPLICHT DOCUMENT**  
> **Status:** CRITICAL  
> **Versie:** 3.0  
> **Laatst bijgewerkt:** 28 februari 2026  
> **Leeswijze:** ELKE AI agent/LLM MOET dit document volledig doornemen voor elke taak met betrekking tot:
> - Docker Compose configuratie
> - Environment variables
> - Netwerk/poort configuratie
> - Infrastructure as Code
> - API endpoints

---

## 🎯 SNELLE REFERENTIE (Quick Reference)

### Core Services (Altijd actief)
| Service | Poort | URL | Env Var |
|---------|-------|-----|---------|
| API Backend | 8000 | http://localhost:8000 | `API_PORT=8000` |
| MCP Broker | 8001 | http://localhost:8001 | `MCP_PORT=8001` |
| PostgreSQL | 5432 | localhost:5432 | `POSTGRES_PORT=5432` |
| Redis | 6379 | localhost:6379 | `REDIS_PORT=6379` |
| Frontend Dev | 3000 | http://localhost:3000 | `FRONTEND_DEV_PORT=3000` |

### Extended Services (Full Stack)
| Service | Poort | URL | Env Var |
|---------|-------|-----|---------|
| ClickHouse HTTP | 5000 | http://localhost:5000 | `CLICKHOUSE_HTTP_PORT=5000` |
| ClickHouse Native | 5001 | localhost:5001 | `CLICKHOUSE_NATIVE_PORT=5001` |
| Redpanda Kafka | 6000 | localhost:6000 | `KAFKA_BROKERS=localhost:6000` |
| Redpanda Admin | 6001 | http://localhost:6001 | `REDPANDA_ADMIN_URL=http://localhost:6001` |
| ChromaDB | 8100 | http://localhost:8100 | `CHROMA_DB_PORT=8100` |
| Grafana | 9000 | http://localhost:9000 | `GRAFANA_PORT=9000` |
| Prometheus | 9090 | http://localhost:9090 | `PROMETHEUS_PORT=9090` |
| Frontend Prod | 3080 | http://localhost:3080 | `FRONTEND_PROD_PORT=3080` |

---

## 🚫 VERBODEN POORTEN (Nooit gebruiken!)

Deze poorten zijn **VERBODEN** en mogen nooit worden toegekend:

| Poort | Reden | Correctie |
|-------|-------|-----------|
| `8123` | ClickHouse HTTP (oud) | Gebruik `5000` |
| `9092` | Redpanda Kafka (oud) | Gebruik `6000` |
| `9644` | Redpanda Admin (oud) | Gebruik `6001` |
| `8001` voor metrics | Metrics server (oud) | Gebruik `9090` |
| `3000` voor Grafana | Grafana (oud) | Gebruik `9000` |
| `8000` voor ChromaDB | ChromaDB (oud) | Gebruik `8100` |

---

## 📋 VERPLICHTE CHECKLIST VOOR AGENTS

Elke AI agent/LLM MOET deze checklist voltooien:

### Voor Docker Compose wijzigingen:
```
□ Heb ik PORT_ALLOCATION_SSOT.md gelezen?
□ Gebruik ik alleen toegestane poorten uit de tabel?
□ Heb ik geen poorten uit de "VERBODEN" lijst gebruikt?
□ Heb ik de juiste mapping: "HOST:CONTAINER"?
□ Voor interne Docker communicatie: gebruik service namen, niet localhost
```

### Voor Environment Variables:
```
□ Heb ik de juiste env var namen gebruikt?
□ Komen de poorten overeen met PORT_ALLOCATION_SSOT.md?
□ Heb ik zowel interne (Docker) als externe (Host) poorten correct?
```

### Voor Code wijzigingen:
```
□ Gebruik ik de Settings class uit backend/core/config/settings.py?
□ Heb ik hardcoded poorten vervangen door environment variabelen?
□ Zijn de default waarden in settings.py consistent met dit document?
```

---

## 🔧 DOCKER COMPOSE POORT MAPPING REGELS

### Basis Regel:
```yaml
ports:
  - "HOST_PORT:CONTAINER_PORT"
```

### Correcte Voorbeelden:

```yaml
# ✅ CORRECT: ClickHouse
clickhouse:
  ports:
    - "5000:8123"  # Host:5000 → Container:8123
  
# ✅ CORRECT: Grafana
grafana:
  ports:
    - "9000:3000"  # Host:9000 → Container:3000

# ✅ CORRECT: Redpanda
redpanda:
  ports:
    - "6000:9092"  # Host:6000 → Container:9092
    - "6001:9644"  # Host:6001 → Container:9644
```

### Foutieve Voorbeelden (NOOIT DOEN!):

```yaml
# ❌ FOUT: Oude ClickHouse poort
clickhouse:
  ports:
    - "8123:8123"  # VERBODEN! Gebruik 5000:8123

# ❌ FOUT: Oude Redpanda poort
redpanda:
  ports:
    - "9092:9092"  # VERBODEN! Gebruik 6000:9092

# ❌ FOUT: Grafana op 3000
grafana:
  ports:
    - "3000:3000"  # VERBODEN! Gebruik 9000:3000
```

---

## 🌐 INTERNE vs EXTERNE POORTEN

### Extern (Host Machine → localhost):
```bash
# Deze poorten gebruik je in je browser of code:
API_URL=http://localhost:8000
CLICKHOUSE_URL=http://localhost:5000
KAFKA_BROKERS=localhost:6000
```

### Intern (Docker Network → service naam):
```bash
# Deze poorten gebruik je binnen Docker:
API_URL=http://api:8000
CLICKHOUSE_URL=http://clickhouse:8123
KAFKA_BROKERS=redpanda:9092
```

### Omrekeningstabel:

| Service | Extern (Host) | Intern (Docker) | Container |
|---------|---------------|-----------------|-----------|
| API | `localhost:8000` | `api:8000` | `8000` |
| ClickHouse HTTP | `localhost:5000` | `clickhouse:8123` | `8123` |
| ClickHouse Native | `localhost:5001` | `clickhouse:9000` | `9000` |
| Redpanda Kafka | `localhost:6000` | `redpanda:9092` | `9092` |
| Redpanda Admin | `localhost:6001` | `redpanda:9644` | `9644` |
| ChromaDB | `localhost:8100` | `chromadb:8000` | `8000` |
| Grafana | `localhost:9000` | `grafana:3000` | `3000` |
| Prometheus | `localhost:9090` | `prometheus:9090` | `9090` |
| PostgreSQL | `localhost:5432` | `postgres:5432` | `5432` |
| Redis | `localhost:6379` | `redis:6379` | `6379` |

---

## 🔑 ENVIRONMENT VARIABLES - VERPLICHTE NAMEN

### Core Services:
```bash
# API
API_PORT=8000
API_HOST=0.0.0.0

# MCP Broker
MCP_PORT=8001
MCP_HOST=0.0.0.0
MCP_BROKER_URL=http://localhost:8001

# Database
POSTGRES_PORT=5432
DATABASE_URL=postgresql+asyncpg://trader:trading_secure@localhost:5432/trading_db

# Cache
REDIS_PORT=6379
REDIS_URL=redis://localhost:6379/0
```

### Extended Services:
```bash
# ClickHouse
CLICKHOUSE_HOST=localhost
CLICKHOUSE_HTTP_PORT=5000      # EXTERNE poort
CLICKHOUSE_NATIVE_PORT=5001    # EXTERNE poort
CLICKHOUSE_PORT=5000           # Legacy (HTTP)
CLICKHOUSE_URL=http://localhost:5000

# Redpanda
KAFKA_BROKERS=localhost:6000
KAFKA_BOOTSTRAP_SERVERS=localhost:6000
REDPANDA_ADMIN_URL=http://localhost:6001

# ChromaDB
CHROMA_DB_HOST=localhost
CHROMA_DB_PORT=8100
CHROMA_DB_URL=http://localhost:8100

# Monitoring
GRAFANA_PORT=9000
PROMETHEUS_PORT=9090
METRICS_PORT=9090
METRICS_SERVER_PORT=9090
```

---

## 📝 CODE VOORBEELDEN

### Python (Backend):
```python
# ✅ CORRECT: Gebruik Settings class
from backend.core.config.settings import settings

# Settings leest automatisch uit .env
kafka_brokers = settings.KAFKA_BOOTSTRAP_SERVERS  # localhost:6000
clickhouse_port = settings.CLICKHOUSE_HTTP_PORT   # 5000

# ✅ CORRECT: Environment variabelen
import os
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
```

### TypeScript (Frontend):
```typescript
// ✅ CORRECT: Gebruik Vite env vars
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8000/ws";
```

### Docker Compose:
```yaml
# ✅ CORRECT: Service definitie
services:
  api:
    ports:
      - "8000:8000"
    environment:
      - CLICKHOUSE_HOST=clickhouse      # Intern: service naam
      - CLICKHOUSE_HTTP_PORT=8123       # Intern: container poort
      - KAFKA_BROKERS=redpanda:9092     # Intern: service:poort
```

---

## 🔍 VALIDATIE COMMANDS

### Poorten controleren:
```bash
# Windows
netstat -ano | findstr :8000

# macOS/Linux
lsof -i :8000
```

### Docker poorten verifiëren:
```bash
# Alle service poorten bekijken
docker-compose ps

# Specifieke service
docker-compose port api 8000
```

### Health checks:
```bash
# API
curl http://localhost:8000/health

# ClickHouse
curl http://localhost:5000/ping

# ChromaDB
curl http://localhost:8100/api/v1/heartbeat

# Grafana
curl http://localhost:9000/api/health
```

---

## ⚠️ COMMON MISTAKES (Veelvoorkomende Fouten)

### Fout 1: Verkeerde omgeving (Intern vs Extern)
```python
# ❌ FOUT: Gebruikt externe poort in Docker
DATABASE_URL = "postgresql://user:pass@localhost:5432/db"

# ✅ CORRECT: Gebruik service naam in Docker
DATABASE_URL = "postgresql://user:pass@postgres:5432/db"
```

### Fout 2: Oude poorten gebruiken
```python
# ❌ FOUT: Oude ClickHouse poort
CLICKHOUSE_PORT = 8123  # Dit is de container poort!

# ✅ CORRECT: Externe poort gebruiken
CLICKHOUSE_HTTP_PORT = 5000  # Host poort
```

### Fout 3: Hardcoded poorten
```python
# ❌ FOUT: Hardcoded
response = requests.get("http://localhost:8000/api/data")

# ✅ CORRECT: Via settings
response = requests.get(f"{settings.API_URL}/api/data")
```

---

## 📚 RELATIES MET ANDERE DOCUMENTEN

| Document | Doel | Relatie |
|----------|------|---------|
| `AGENTS.md` | Algemene agent instructies | Deze SSoT is een verplichte extensie |
| `PORT_ALLOCATION.md` | Gedetailleerde documentatie | Dit is de SSoT versie ervan |
| `.env.example` | Environment template | Moet consistent zijn met dit document |
| `docker-compose*.yml` | Service configuratie | Moet dit document volgen |

---

## 🔒 ENFORCEMENT

### Voor elke PR/code change:
1. **Automatische check:** CI/CD controleert op verboden poorten
2. **Handmatige review:** Reviewer checkt tegen dit document
3. **Agent instructie:** Elke LLM/agent moet dit document citeren bij wijzigingen

### Verplichte vermelding in commits:
```
Poort wijziging volgens PORT_ALLOCATION_SSOT.md v3.0
- Gewijzigd: ClickHouse 8123 → 5000
- Reden: Grafana conflict opgelost
```

---

## 🔄 VERSIE BEHEER

| Versie | Datum | Wijzigingen |
|--------|-------|-------------|
| 1.0 | 20-02-2026 | Initiële allocatie |
| 2.0 | 28-02-2026 | Conflicten opgelost |
| 3.0 | 28-02-2026 | SSoT document gemaakt |

---

## ✅ AGENT BEVESTIGING

> **Deze sectie moet worden gekopieerd naar elke PR/code change die poorten raakt:**

```markdown
## Port Allocation Checklist
- [ ] Ik heb PORT_ALLOCATION_SSOT.md v3.0 gelezen
- [ ] Alle poorten zijn volgens de specificatie
- [ ] Geen verboden poorten gebruikt
- [ ] Interne/externe poorten correct onderscheiden
- [ ] Environment variabelen consistent
```

---

**⚠️ BELANGRIJK:** Dit document is de **enige bron van waarheid**. Bij twijfel, raadpleeg dit document. Bij conflicten, wijzig dit document niet zonder goedkeuring.

*Laatst bijgewerkt: 28 februari 2026*  
*Auteur: Agentic Trader Platform Team*  
*Status: CRITICAL - VERPLICHT*
