# Port Allocation Single Source of Truth (SSoT)

> **Systeem voor het enforce'n van consistente poortallocatie in het Agentic Trader Platform**

---

## 📋 Overzicht

Dit systeem zorgt ervoor dat **alle** AI agents, LLMs, en ontwikkelaars dezelfde poortallocatie gebruiken. Het voorkomt conflicten en inconsistenties tussen services.

### Bestanden in dit systeem:

| Bestand | Doel | Status |
|---------|------|--------|
| `PORT_ALLOCATION_SSOT.md` | **Enige bron van waarheid** voor poorten | 🔴 Verplicht lezen |
| `PORT_ALLOCATION.md` | Gedetailleerde documentatie | 🟡 Referentie |
| `scripts/validate_port_allocation.py` | Validatiescript | 🟢 Automatisch |
| `.pre-commit-config.yaml` | Pre-commit hooks | 🟢 Automatisch |

---

## 🚀 Snel Starten

### Voor AI Agents/LLMs:

```
1. LEES EERST: PORT_ALLOCATION_SSOT.md
2. Gebruik ALLEEN poorten uit de toegestane lijst
3. Gebruik NOOIT verboden poorten (8123, 9092, 9644 voor host)
4. Valideer je wijzigingen met: python scripts/validate_port_allocation.py
```

### Voor Ontwikkelaars:

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Handmatig valideren
python scripts/validate_port_allocation.py

# Pre-commit handmatig draaien
pre-commit run --all-files
```

---

## 🎯 Toegestane Poorten

### Core Services (Altijd):
```
API:              8000
MCP Broker:       8001
PostgreSQL:       5432
Redis:            6379
Frontend Dev:     3000
```

### Extended Services (Full Stack):
```
ClickHouse HTTP:  5000
ClickHouse Native: 5001
Redpanda Kafka:   6000
Redpanda Admin:   6001
ChromaDB:         8100
Grafana:          9000
Prometheus:       9090
Frontend Prod:    3080
```

---

## 🚫 Verbidden Poorten (Host)

Deze poorten mogen **NOOIT** worden gebruikt voor host mappings:

| Poort | Service | Juiste Poort |
|-------|---------|--------------|
| 8123 | ClickHouse HTTP | **5000** |
| 9092 | Redpanda Kafka | **6000** |
| 9644 | Redpanda Admin | **6001** |
| 3000 | Grafana | **9000** |

---

## 🔧 Docker Compose Mapping

### Correct:
```yaml
services:
  clickhouse:
    ports:
      - "5000:8123"  # ✅ Host:5000 → Container:8123

  redpanda:
    ports:
      - "6000:9092"  # ✅ Host:6000 → Container:9092
```

### Fout:
```yaml
services:
  clickhouse:
    ports:
      - "8123:8123"  # ❌ VERBODEN!
```

---

## 📝 Environment Variables

### Verplichte namen:
```bash
# Core
API_PORT=8000
MCP_PORT=8001
POSTGRES_PORT=5432
REDIS_PORT=6379

# Extended
CLICKHOUSE_HTTP_PORT=5000
CLICKHOUSE_NATIVE_PORT=5001
KAFKA_BROKERS=localhost:6000
CHROMA_DB_PORT=8100
GRAFANA_PORT=9000
```

---

## 🔍 Validatie

### Pre-commit hook (Automatisch):
- Wordt uitgevoerd bij elke commit
- Controleert docker-compose*.yml, .env*, en Python files
- **BLOCKING** - Commits worden geweigerd bij fouten

### Handmatig:
```bash
python scripts/validate_port_allocation.py
```

### Output:
```
✅ All port allocations are valid!

Core ports:
  API: 8000, MCP: 8001, Postgres: 5432, Redis: 6379
Extended:
  ClickHouse: 5000/5001, Redpanda: 6000/6001, ChromaDB: 8100
Monitoring:
  Grafana: 9000, Prometheus: 9090
```

---

## ⚠️ Foutmeldingen

```
❌ PORT ALLOCATION VIOLATIONS FOUND:

  📁 docker-compose.yml:15
     Line 15: Forbidden host port 8123 (ClickHouse HTTP - use 5000 instead)

⚠️  These violations must be fixed according to PORT_ALLOCATION_SSOT.md
📖 Read: PORT_ALLOCATION_SSOT.md
```

---

## 🔄 Updates

### Poorten wijzigen:
1. Update `PORT_ALLOCATION_SSOT.md`
2. Update `PORT_ALLOCATION.md`
3. Update validatiescript
4. Werk alle configuratiebestanden bij
5. Communiceer wijziging aan team

### Nieuwe service toevoegen:
1. Kies vrije poort uit range in SSOT
2. Documenteer in SSOT
3. Update validatiescript
4. Test met validatiescript

---

## 📞 Support

Bij vragen over poortallocatie:
1. Raadpleeg `PORT_ALLOCATION_SSOT.md`
2. Check dit document
3. Vraag hulp aan team lead

---

**Laatst bijgewerkt:** 28 februari 2026
**Versie:** 3.0
**Status:** CRITICAL
