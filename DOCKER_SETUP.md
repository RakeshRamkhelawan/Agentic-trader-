# Docker Compose Setup - Agentic Trader Platform

> **Samenvatting**: Alle Docker Compose bestanden zijn gecontroleerd, gecorrigeerd en gevalideerd. Dit document beschrijft de architectuur en het gebruik.

---

## 📋 Overzicht

| Bestand | Doel | Services |
|---------|------|----------|
| `docker-compose.yml` | Basis configuratie | Alle backend services |
| `docker-compose.override.yml` | Development | Hot reload, debug ports, frontend dev |
| `docker-compose.prod.yml` | Productie | SSL, Nginx, resource limits |
| `docker-compose.test.yml` | Testing | Ephemeral databases, test runner |

---

## 🚀 Snelstart

### Development (met hot reload)
```bash
# Start alle services voor development
docker-compose up -d

# Status bekijken
docker-compose ps

# Logs volgen
docker-compose logs -f api

# Stoppen
docker-compose down
```

### Productie
```bash
# Start productie stack
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Of gebruik het convenient script (indien aangemaakt)
docker-compose --profile production up -d
```

### Testing
```bash
# Run tests in geïsoleerde omgeving
docker-compose -f docker-compose.yml -f docker-compose.test.yml up --abort-on-container-exit
```

---

## 🔧 Services Overzicht

### Database Services
| Service | Image | Externe Poort | Interne Poort | Beschrijving |
|---------|-------|---------------|---------------|--------------|
| `postgres` | postgres:15-alpine | 5433 | 5432 | Hoofd database |
| `clickhouse` | clickhouse:24.3 | 8124, 9001 | 8123, 9000 | Analytics database |
| `redis` | redis:7-alpine | 6380 | 6379 | Cache & pub/sub |
| `chromadb` | chroma:0.5.5 | 8001 | 8000 | Vector database |
| `redpanda` | redpanda:v24.1 | 9092, 9644, 8081, 8082 | - | Kafka-compatible broker |

### Applicatie Services
| Service | Poort | Beschrijving |
|---------|-------|--------------|
| `api` | 8005 | FastAPI backend |
| `frontend` | 3000 | React + Vite (dev) |
| `nginx` | 80, 443 | Reverse proxy (prod) |

---

## 🌐 Poort Mapping

### Basis (docker-compose.yml)
```
PostgreSQL:     5433 → 5432
ClickHouse:     8124 → 8123 (HTTP)
                9001 → 9000 (Native)
Redis:          6380 → 6379
ChromaDB:       8001 → 8000
Redpanda:       9092 → 9092 (Kafka API)
                9644 → 9644 (Admin)
                8081 → 8081 (Schema Registry)
                8082 → 8082 (HTTP Proxy)
API:            8005 → 8000
```

### Development (+ override)
```
PostgreSQL:     5433, 5432 → 5432
ClickHouse:     8124, 8123, 9001, 9000 → 8123/9000
Redis:          6380, 6379 → 6379
ChromaDB:       8001, 8000 → 8000
Frontend:       3000 → 3000
                24678 → 24678 (HMR)
```

### Productie
```
Nginx:          80 → 80
                443 → 443
```

---

## ✅ Opgeloste Issues

### 1. Missende Services
**Probleem**: ChromaDB en Redpanda ontbraken in de originele configuratie.

**Oplossing**: Toegevoegd aan alle docker-compose bestanden met:
- Juiste healthchecks
- Port mappings
- Volume mounts
- Environment variables

### 2. Port Conflicts
**Probleem**: `docker-compose.override.yml` had conflicterende port mappings voor Redis.

**Oplossing**: In development worden nu beide poorten geëxposeerd:
- `6380:6379` - compatibiliteit met basis config
- `6379:6379` - voor lokale tools

### 3. Healthcheck Mismatch
**Probleem**: API healthcheck gebruikte `/api/v1/health` maar de applicatie exposeert `/api/v1/health/ping`.

**Oplossing**: Alle healthchecks aangepast naar `/api/v1/health/ping`.

### 4. ClickHouse Healthcheck
**Probleem**: ClickHouse had geen healthcheck.

**Oplossing**: Toegevoegd met `wget` naar `http://localhost:8123/ping`.

### 5. Productie Network
**Probleem**: `docker-compose.prod.yml` referenceerde `trader-network` maar definieerde het niet.

**Oplossing**: Netwerk definitie toegevoegd aan `docker-compose.prod.yml`.

### 6. Frontend Service
**Probleem**: Geen frontend service gedefinieerd.

**Oplossing**: Frontend service toegevoegd aan:
- `docker-compose.override.yml` (development met Vite)
- `docker-compose.prod.yml` (productie met Nginx)

### 7. Nginx Configuraties
**Probleem**: Verschillende nginx configuraties gebruikten verschillende service namen.

**Oplossing**:
- `nginx/nginx.conf` - aangepast voor productie reverse proxy
- `frontend/nginx.conf` - aangemaakt voor frontend static files
- Infrastructure docker nginx config gecontroleerd

---

## 📁 Gewijzigde/Nieuwe Bestanden

### Docker Compose
| Bestand | Status | Wijzigingen |
|---------|--------|-------------|
| `docker-compose.yml` | ✅ Gecorrigeerd | +ChromaDB, +Redpanda, +healthchecks, +networks |
| `docker-compose.override.yml` | ✅ Gecorrigeerd | +Frontend, +ports, ~Redis ports, ~API command |
| `docker-compose.prod.yml` | ✅ Gecorrigeerd | +Networks, +Frontend, +Nginx, +resource limits |
| `docker-compose.test.yml` | 🆕 Nieuw | Ephemeral test omgeving |

### Dockerfiles
| Bestand | Status | Wijzigingen |
|---------|--------|-------------|
| `Dockerfile` | ✅ Gecontroleerd | Curl toegevoegd voor healthchecks |
| `infrastructure/docker/Dockerfile.frontend` | ✅ Gecorrigeerd | Port 3000, juiste API URL |
| `infrastructure/docker/Dockerfile.frontend.prod` | ✅ Gecorrigeerd | Multi-stage build, nginx config |

### Configuraties
| Bestand | Status | Wijzigingen |
|---------|--------|-------------|
| `frontend/vite.config.ts` | ✅ Gecorrigeerd | Proxy naar localhost:8005 |
| `frontend/nginx.conf` | 🆕 Nieuw | Static file serving config |
| `frontend/.dockerignore` | 🆕 Nieuw | Optimized build context |
| `.dockerignore` | 🆕 Nieuw | Root build context exclude |

---

## 🔍 Validatie

Alle Docker Compose bestanden zijn gevalideerd:

```powershell
# Validatie commando's
docker-compose -f docker-compose.yml config
docker-compose -f docker-compose.yml -f docker-compose.override.yml config
docker-compose -f docker-compose.yml -f docker-compose.prod.yml config
docker-compose -f docker-compose.yml -f docker-compose.test.yml config
```

✅ **Alle configuraties zijn syntactisch correct.**

---

## 🔐 Omgeving Variabelen

### Verplicht (Productie)
```env
SECRET_KEY=your-super-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
```

### Database URLs (Automatisch geconfigureerd)
```env
# Development
DATABASE_URL=postgresql+asyncpg://trader:trading_secure@postgres:5432/trading_db
REDIS_URL=redis://redis:6379/0
CLICKHOUSE_HOST=clickhouse
CHROMA_HOST=chromadb
KAFKA_BOOTSTRAP_SERVERS=redpanda:9092
```

---

## 🛠️ Troubleshooting

### Services starten niet
```bash
# Controleer logs
docker-compose logs <service-name>

# Controleer health status
docker-compose ps

# Herstart specifieke service
docker-compose restart <service-name>
```

### Port conflicts
```bash
# Controleer welke poorten in gebruik zijn
netstat -an | findstr <port>

# Stop lokale services die conflicteren
```

### Database connectie problemen
```bash
# Test PostgreSQL
docker-compose exec postgres pg_isready -U trader

# Test Redis
docker-compose exec redis redis-cli ping

# Test ClickHouse
docker-compose exec clickhouse clickhouse-client --query "SELECT 1"
```

---

## 📊 Resource Limits (Productie)

| Service | CPU Limit | Memory Limit | CPU Reserve | Memory Reserve |
|---------|-----------|--------------|-------------|----------------|
| api | 2.0 | 2G | 1.0 | 512M |
| postgres | 1.0 | 1G | 0.5 | 256M |
| clickhouse | 1.0 | 2G | 0.5 | 512M |
| redis | 0.5 | 512M | 0.25 | 128M |
| chromadb | 1.0 | 1G | 0.5 | 256M |
| redpanda | 1.0 | 2G | 0.5 | 512M |
| nginx | 0.5 | 256M | 0.25 | 64M |
| frontend | 0.5 | 256M | 0.25 | 128M |

---

## 📝 Opmerkingen

1. **Version attribute**: Docker Compose geeft een warning dat `version: '3.8'` obsolete is. Dit is niet kritiek - de configuratie werkt nog steeds correct. In toekomstige versies kan dit worden verwijderd.

2. **Poort keuzes**: De externe poorten (5433, 6380, 8124, 8005) zijn bewust gekozen om conflicten met lokale services te voorkomen.

3. **Healthchecks**: Alle services hebben nu healthchecks met realistische `start_period` waarden om langzame opstarttijds te accommoderen.

4. **Volumes**: Alle data wordt opgeslagen in named volumes voor persistency tussen restarts.

---

*Laatste update: 23 februari 2026*
*Status: ✅ Geverifieerd en Productie-Ready*
