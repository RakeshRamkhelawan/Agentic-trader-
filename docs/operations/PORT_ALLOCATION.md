# Agentic Trader Platform - Complete Port Allocation Reference

> **Laatst bijgewerkt:** 28 februari 2026
> **Versie:** 2.1
> **Status:** Production Ready

---

## 📋 Overzicht Port Ranges

| Range | Categorie | Beschrijving |
|-------|-----------|--------------|
| **8000-8099** | Core Application Services | API backends, microservices |
| **8100-8199** | Vector & AI Services | ChromaDB, Ollama, ML services |
| **5000-5099** | Databases | PostgreSQL, ClickHouse, etc. |
| **6000-6099** | Cache & Message Brokers | Redis, Redpanda/Kafka |
| **3000-3099** | Frontend Services | React dev server, preview |
| **9000-9099** | Monitoring & Observability | Prometheus, Grafana, Jaeger |
| **10000-10999** | Optional/Developer Tools | PgAdmin, Redis Insight, etc. |

---

## 🔧 Core Application Services (8000-8099)

### API Backend (Primary)
| Attribuut | Waarde |
|-----------|--------|
| **Service** | `agentic_trader_api` |
| **Type** | FastAPI (ASGI) |
| **Container Port** | `8000` |
| **Host Port** | `8000` |
| **Environment** | All (dev/staging/prod) |
| **URL** | http://localhost:8000 |
| **Health Check** | http://localhost:8000/health |
| **API Docs** | http://localhost:8000/docs |
| **WebSocket** | ws://localhost:8000/ws |
| **Metrics** | http://localhost:8000/metrics |

**Omgevingsvariabelen:**
```bash
API_PORT=8000
API_HOST=0.0.0.0
METRICS_PORT=9090
```

### MCP Broker (Tool Execution Service)
| Attribuut | Waarde |
|-----------|--------|
| **Service** | `agentic_trader_mcp_broker` |
| **Container Port** | `8001` |
| **Host Port** | `8001` |
| **Type** | MCP ToolBroker for agents |
| **URL** | http://localhost:8001 |
| **Health Check** | http://localhost:8001/health |
| **Docker Compose** | `docker-compose.mcp.yml` |

**Omgevingsvariabelen:**
```bash
MCP_PORT=8001
MCP_HOST=0.0.0.0
MCP_BROKER_URL=http://localhost:8001
MCP_LOG_LEVEL=INFO
```

---

## 🧠 Vector & AI Services (8100-8199)

### ChromaDB (Vector Database)
| Attribuut | Waarde |
|-----------|--------|
| **Service** | `agentic_trader_chromadb` |
| **Container Port** | `8000` |
| **Host Port** | `8100` |
| **Type** | Vector DB for RAG |
| **URL** | http://localhost:8100 |
| **API Endpoint** | http://localhost:8100/api/v1 |
| **Heartbeat** | http://localhost:8100/api/v1/heartbeat |

**Omgevingsvariabelen:**
```bash
CHROMA_DB_HOST=localhost
CHROMA_DB_PORT=8100
CHROMA_DB_URL=http://localhost:8100
```

### Ollama (LLM Inference - Optional)
| Attribuut | Waarde |
|-----------|--------|
| **Service** | `agentic_trader_ollama` |
| **Container Port** | `11434` |
| **Host Port** | `11434` |
| **Type** | Local LLM inference |
| **URL** | http://localhost:11434 |
| **API** | http://localhost:11434/api/generate |

**Omgevingsvariabelen:**
```bash
OLLAMA_HOST=http://localhost:11434
OLLAMA_BASE_URL=http://localhost:11434
LLM_PROVIDER=ollama
```

---

## 💾 Database Services (5000-5099)

### PostgreSQL (Primary Database)
| Attribuut | Waarde |
|-----------|--------|
| **Service** | `agentic_trader_postgres` |
| **Container Port** | `5432` |
| **Host Port** | `5432` |
| **Type** | Primary relational DB |
| **Default Database** | `trading_db` |
| **Default User** | `trader` |
| **Connection String** | `postgresql://trader:trading_secure@localhost:5432/trading_db` |

**Omgevingsvariabelen:**
```bash
DATABASE_URL=postgresql+asyncpg://trader:trading_secure@localhost:5432/trading_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=trading_db
POSTGRES_USER=trader
POSTGRES_PASSWORD=trading_secure
```

### PostgreSQL (Test Database)
| Attribuut | Waarde |
|-----------|--------|
| **Database** | `trading_test_db` |
| **User** | `test` |
| **Password** | `test_password` |
| **Connection String** | `postgresql+asyncpg://test:test_password@localhost:5432/trading_test_db` |
| **Docker Compose** | `docker-compose.test.yml` |

### ClickHouse (Analytics Database)
| Attribuut | Waarde |
|-----------|--------|
| **Service** | `agentic_trader_clickhouse` |
| **HTTP Port** | `8123` (host: `5000`) |
| **Native Port** | `9000` (host: `5001`) |
| **Type** | Time-series analytics |
| **HTTP URL** | http://localhost:5000 |
| **Native Protocol** | `localhost:5001` |
| **Health Check** | http://localhost:5000/ping |

**Omgevingsvariabelen:**
```bash
CLICKHOUSE_HOST=localhost
CLICKHOUSE_HTTP_PORT=5000
CLICKHOUSE_NATIVE_PORT=5001
CLICKHOUSE_URL=http://localhost:5000
```

---

## ⚡ Cache & Message Brokers (6000-6099)

### Redis (Cache, Sessions, Pub/Sub)
| Attribuut | Waarde |
|-----------|--------|
| **Service** | `agentic_trader_redis` |
| **Container Port** | `6379` |
| **Host Port** | `6379` |
| **Type** | Cache, Event Bus, Sessions |
| **Protocol** | Redis |
| **Connection** | `redis://localhost:6379/0` |

**Omgevingsvariabelen:**
```bash
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### Redpanda (Kafka-Compatible Message Broker)
| Attribuut | Waarde |
|-----------|--------|
| **Service** | `agentic_trader_redpanda` |
| **Kafka API** | `9092` (host: `6000`) |
| **Admin API** | `9644` (host: `6001`) |
| **RPC** | `33145` (intern) |
| **Type** | Message broker |
| **Kafka URL** | `localhost:6000` |
| **Admin URL** | http://localhost:6001 |

**Omgevingsvariabelen:**
```bash
KAFKA_BROKERS=localhost:6000
KAFKA_BOOTSTRAP_SERVERS=localhost:6000
REDPANDA_ADMIN_URL=http://localhost:6001
```

---

## 🎨 Frontend Services (3000-3099)

### Frontend (Development - Vite)
| Attribuut | Waarde |
|-----------|--------|
| **Service** | `agentic_trader_frontend_dev` |
| **Container Port** | `5173` |
| **Host Port** | `3000` |
| **Type** | Vite dev server |
| **URL** | http://localhost:3000 |
| **HMR Port** | `3001` (WebSocket) |

**Omgevingsvariabelen:**
```bash
VITE_DEV_SERVER_PORT=3000
VITE_HMR_PORT=3001
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

### Frontend (Production - Nginx)
| Attribuut | Waarde |
|-----------|--------|
| **Service** | `agentic_trader_frontend` |
| **Container Port** | `80` |
| **Host Port** | `3080` |
| **Type** | Production build via Nginx |
| **URL** | http://localhost:3080 |

### Frontend (Preview)
| Attribuut | Waarde |
|-----------|--------|
| **Host Port** | `3002` |
| **Type** | Vite preview server |
| **Command** | `npm run preview` |

---

## 📊 Monitoring & Observability (9000-9099)

### Prometheus (Metrics)
| Attribuut | Waarde |
|-----------|--------|
| **Service** | `agentic_trader_prometheus` |
| **Container Port** | `9090` |
| **Host Port** | `9090` |
| **Type** | Metrics collection |
| **URL** | http://localhost:9090 |
| **API** | http://localhost:9090/api/v1 |

**Configuratie:**
```yaml
# infrastructure/prometheus/prometheus.yml
global:
  scrape_interval: 15s
scrape_configs:
  - job_name: 'agentic-trader-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: /metrics
```

### Grafana (Dashboards)
| Attribuut | Waarde |
|-----------|--------|
| **Service** | `agentic_trader_grafana` |
| **Container Port** | `3000` |
| **Host Port** | `9000` |
| **Type** | Visualization |
| **URL** | http://localhost:9000 |
| **Default User** | `admin` |
| **Default Password** | `admin` (wijzigen bij eerste login!) |

**Configuratie:**
```bash
GF_SECURITY_ADMIN_USER=admin
GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
GF_SERVER_ROOT_URL=http://localhost:9000
```

### Jaeger (Distributed Tracing)
| Attribuut | Waarde |
|-----------|--------|
| **Service** | `agentic_trader_jaeger` |
| **UI Port** | `16686` (host: `9001`) |
| **Collector** | `14250` (intern) |
| **Type** | Distributed tracing |
| **URL** | http://localhost:9001 |

**Omgevingsvariabelen:**
```bash
JAEGER_ENDPOINT=http://localhost:14268/api/traces
JAEGER_UI_URL=http://localhost:9001
```

---

## 🌐 Reverse Proxy (Nginx)

### Nginx (Production)
| Attribuut | Waarde |
|-----------|--------|
| **Service** | `agentic_trader_nginx` |
| **HTTP Port** | `80` |
| **HTTPS Port** | `443` |
| **Type** | Reverse proxy, SSL termination |
| **HTTP URL** | http://localhost |
| **HTTPS URL** | https://localhost |

**Routes:**
| Path | Target | Beschrijving |
|------|--------|--------------|
| `/` | `frontend:80` | React app |
| `/api` | `api:8000` | API endpoints |
| `/ws` | `api:8000` | WebSocket |
| `/grafana` | `grafana:3000` | Monitoring (intern) |
| `/prometheus` | `prometheus:9090` | Metrics (intern) |

---

## 🛠️ Optional/Developer Tools (10000-10999)

### PgAdmin (PostgreSQL GUI)
| Attribuut | Waarde |
|-----------|--------|
| **Service** | `agentic_trader_pgadmin` |
| **Container Port** | `80` |
| **Host Port** | `10000` |
| **Type** | Database GUI |
| **URL** | http://localhost:10000 |
| **Default Email** | `admin@agentictrader.com` |
| **Default Password** | `admin` |

**Configuratie:**
```bash
PGADMIN_DEFAULT_EMAIL=admin@agentictrader.com
PGADMIN_DEFAULT_PASSWORD=admin
```

### Redis Insight (Redis GUI)
| Attribuut | Waarde |
|-----------|--------|
| **Service** | `agentic_trader_redis_insight` |
| **Container Port** | `8001` |
| **Host Port** | `10001` |
| **Type** | Redis visualization |
| **URL** | http://localhost:10001 |

### Storybook (Component Development)
| Attribuut | Waarde |
|-----------|--------|
| **Service** | `agentic_trader_storybook` |
| **Host Port** | `6006` |
| **Type** | UI component docs |
| **URL** | http://localhost:6006 |
| **Command** | `npm run storybook` |

---

## 📋 Complete Port Allocatie Tabel

### Kern Stack (`docker-compose.yml`)

| Poort | Service | Protocol | Beschrijving |
|-------|---------|----------|--------------|
| `8000` | API Backend | HTTP/WebSocket | FastAPI applicatie |
| `5432` | PostgreSQL | PostgreSQL | Primaire database |
| `6379` | Redis | Redis | Cache & events |

### Extended Stack (`docker-compose.full.yml`)

| Poort | Service | Protocol | Beschrijving |
|-------|---------|----------|--------------|
| `8000` | API Backend | HTTP/WebSocket | FastAPI applicatie |
| `5432` | PostgreSQL | PostgreSQL | Primaire database |
| `6379` | Redis | Redis | Cache & events |
| `5000` | ClickHouse | HTTP | Analytics HTTP interface |
| `5001` | ClickHouse | Native | Analytics native protocol |
| `6000` | Redpanda | Kafka | Message broker |
| `6001` | Redpanda | HTTP | Admin API |
| `8100` | ChromaDB | HTTP | Vector database |
| `9000` | Grafana | HTTP | Dashboards |
| `9090` | Prometheus | HTTP | Metrics |
| `3080` | Frontend Prod | HTTP | Production build |
| `80` | Nginx | HTTP | Reverse proxy |
| `443` | Nginx | HTTPS | SSL reverse proxy |

### MCP Stack (`docker-compose.mcp.yml`)

| Poort | Service | Protocol | Beschrijving |
|-------|---------|----------|--------------|
| `8001` | MCP Broker | HTTP | Tool execution service |

### Development Tools (Optioneel)

| Poort | Service | Protocol | Beschrijving |
|-------|---------|----------|--------------|
| `3000` | Frontend Dev | HTTP | Vite dev server |
| `3001` | Vite HMR | WebSocket | Hot reload |
| `3002` | Vite Preview | HTTP | Preview server |
| `6006` | Storybook | HTTP | Component docs |
| `10000` | PgAdmin | HTTP | PostgreSQL GUI |
| `10001` | Redis Insight | HTTP | Redis GUI |
| `11434` | Ollama | HTTP | Local LLM |

---

## 🔧 Omgevingsvariabelen Configuratie

### `.env` Bestand Template

```bash
# ============================================
# CORE APPLICATION
# ============================================
API_PORT=8000
API_HOST=0.0.0.0
METRICS_PORT=9090

# ============================================
# MCP BROKER
# ============================================
MCP_PORT=8001
MCP_HOST=0.0.0.0
MCP_BROKER_URL=http://localhost:8001
MCP_LOG_LEVEL=INFO
MCP_ENABLED=true

# ============================================
# DATABASE - PostgreSQL
# ============================================
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=trading_db
POSTGRES_USER=trader
POSTGRES_PASSWORD=trading_secure
DATABASE_URL=postgresql+asyncpg://trader:trading_secure@localhost:5432/trading_db

# ============================================
# ANALYTICS - ClickHouse
# ============================================
CLICKHOUSE_HOST=localhost
CLICKHOUSE_HTTP_PORT=5000
CLICKHOUSE_NATIVE_PORT=5001
CLICKHOUSE_URL=http://localhost:5000

# ============================================
# CACHE - Redis
# ============================================
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_URL=redis://localhost:6379/0

# ============================================
# MESSAGE BROKER - Redpanda
# ============================================
KAFKA_BROKERS=localhost:6000
KAFKA_BOOTSTRAP_SERVERS=localhost:6000
REDPANDA_ADMIN_URL=http://localhost:6001

# ============================================
# VECTOR DATABASE - ChromaDB
# ============================================
CHROMA_DB_HOST=localhost
CHROMA_DB_PORT=8100
CHROMA_DB_URL=http://localhost:8100
CHROMA_HOST=localhost  # Legacy naam
CHROMA_PORT=8100       # Legacy naam

# ============================================
# FRONTEND
# ============================================
FRONTEND_DEV_PORT=3000
FRONTEND_PROD_PORT=3080
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws

# ============================================
# MONITORING
# ============================================
PROMETHEUS_PORT=9090
GRAFANA_PORT=9000
GRAFANA_PASSWORD=admin
JAEGER_PORT=9001

# ============================================
# AI/ML (Optional)
# ============================================
OLLAMA_HOST=http://localhost:11434
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
LLM_PROVIDER=deepseek  # of: openai, gemini, ollama

# ============================================
# DEVELOPER TOOLS (Optional)
# ============================================
PGADMIN_PORT=10000
PGADMIN_DEFAULT_EMAIL=admin@agentictrader.com
PGADMIN_DEFAULT_PASSWORD=admin
REDIS_INSIGHT_PORT=10001
```

---

## 🐳 Docker Network Communicatie

### Interne Docker DNS Namen

Binnen het Docker netwerk gebruik je service namen in plaats van `localhost`:

| Bron | Doel | Connection String |
|------|------|-------------------|
| API | PostgreSQL | `postgresql://trader:trading_secure@postgres:5432/trading_db` |
| API | ClickHouse | `http://clickhouse:8123` |
| API | Redis | `redis://redis:6379/0` |
| API | ChromaDB | `http://chromadb:8000` |
| API | Redpanda | `redpanda:9092` |
| API | MCP Broker | `http://mcp-broker:8001` |
| Frontend | API | `http://api:8000` |
| Nginx | API | `http://api:8000` |
| Nginx | Frontend | `http://frontend:80` |
| Nginx | Grafana | `http://grafana:3000` |
| Prometheus | API | `http://api:8000` |

### Docker Compose Networks

```yaml
# docker-compose.yml
networks:
  agentic_trader_network:
    driver: bridge

# docker-compose.full.yml
networks:
  trader-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

---

## 🚀 Quick Start Commands

### Start Core Stack
```bash
docker-compose up -d
```

### Start Full Stack
```bash
docker-compose -f docker-compose.full.yml up -d
```

### Start with MCP Broker
```bash
docker-compose -f docker-compose.yml -f docker-compose.mcp.yml up -d
```

### Start Test Stack
```bash
docker-compose -f docker-compose.yml -f docker-compose.full.yml -f docker-compose.test.yml up -d
```

### Start Production Stack
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Status Controleren
```bash
# Alle running containers
docker-compose ps

# Poorten in gebruik
docker-compose port <service_name>

# Logs bekijken
docker-compose logs -f <service_name>
```

---

## 🚨 Port Conflict Resolutie

### Controleren welke proces een poort gebruikt

**Windows:**
```powershell
# Zoek proces op poort
netstat -ano | findstr :8000

# Toon proces details
tasklist | findstr <PID>

# Stop proces
taskkill /PID <PID> /F
```

**macOS/Linux:**
```bash
# Zoek proces op poort
lsof -i :8000

# Stop proces
kill -9 <PID>
```

### Poort wijzigen in docker-compose.yml

```yaml
services:
  api:
    ports:
      - "8001:8000"  # Host:8001 → Container:8000

  postgres:
    ports:
      - "5433:5432"  # Host:5433 → Container:5432

  redis:
    ports:
      - "6380:6379"  # Host:6380 → Container:6379
```

**Vergeet niet om je `.env` bestand aan te passen:**
```bash
DATABASE_URL=postgresql://trader:trading_secure@localhost:5433/trading_db
REDIS_URL=redis://localhost:6380/0
```

---

## 📚 Gerelateerde Documentatie

- [DOCKER_SETUP.md](DOCKER_SETUP.md) - Volledige Docker setup handleiding
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Production deployment
- [docker-compose.yml](docker-compose.yml) - Core services
- [docker-compose.full.yml](docker-compose.full.yml) - Full stack
- [docker-compose.prod.yml](docker-compose.prod.yml) - Production overrides
- [docker-compose.mcp.yml](docker-compose.mcp.yml) - MCP Broker
- [docker-compose.test.yml](docker-compose.test.yml) - Test configuration

---

*Document aangemaakt: 28 februari 2026*
*Auteur: Agentic Trader Platform Team*
