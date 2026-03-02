# 🐳 Docker Setup - Agentic Trader Platform

Complete Docker containerization for the Agentic Trader Platform with full-stack deployment support.

## 📁 Structure

```
├── docker-compose.yml              # Base configuration (dev + infra)
├── docker-compose.override.yml     # Development overrides
├── docker-compose.prod.yml         # Production configuration
├── .dockerignore                   # Files to exclude from Docker context
├── infrastructure/docker/
│   ├── Dockerfile.backend          # Python/FastAPI backend
│   ├── Dockerfile.frontend         # React development
│   ├── Dockerfile.frontend.prod    # Nginx production
│   ├── nginx.conf                  # Nginx configuration
│   └── entrypoint.sh               # Backend startup script
└── scripts/
    ├── docker-dev.sh               # Development helper script
    └── docker-prod.sh              # Production deployment script
```

## 🚀 Quick Start

### Development

```bash
# Start all services (backend + frontend + infrastructure)
./scripts/docker-dev.sh start

# Or use docker-compose directly
docker-compose up -d
```

**Services will be available at:**
- 🌐 Frontend: http://localhost:5173
- 🔌 API: http://localhost:8000
- 📚 API Docs: http://localhost:8000/docs
- 📊 Prometheus: http://localhost:9091
- 📈 Grafana: http://localhost:3100
- 🚀 Redpanda Console: http://localhost:8081

### Production

```bash
# Deploy to production
./scripts/docker-prod.sh deploy

# Or use docker-compose directly
docker-compose -f docker-compose.prod.yml up -d
```

## 🔧 Development Commands

```bash
# Start all services
./scripts/docker-dev.sh start

# Stop all services
./scripts/docker-dev.sh stop

# Restart services
./scripts/docker-dev.sh restart

# Rebuild images
./scripts/docker-dev.sh build

# View logs
./scripts/docker-dev.sh logs

# Open shell in backend
./scripts/docker-dev.sh shell api-server

# Open shell in frontend
./scripts/docker-dev.sh shell frontend

# Run tests
./scripts/docker-dev.sh test

# Run database migrations
./scripts/docker-dev.sh migrate

# Start only frontend
./scripts/docker-dev.sh frontend

# Start only backend
./scripts/docker-dev.sh backend

# Reset all data (⚠️ DESTRUCTIVE)
./scripts/docker-dev.sh reset

# Clean up Docker resources
./scripts/docker-dev.sh clean
```

## 🏭 Production Commands

```bash
# Deploy production stack
./scripts/docker-prod.sh deploy

# Stop production
./scripts/docker-prod.sh stop

# Rolling update
./scripts/docker-prod.sh update

# Backup databases
./scripts/docker-prod.sh backup

# Restore from backup
./scripts/docker-prod.sh restore ./backups/20240101_120000

# Check health
./scripts/docker-prod.sh health
```

## 🏗️ Services

### Infrastructure Layer

| Service | Description | Port | Purpose |
|---------|-------------|------|---------|
| **postgres** | PostgreSQL + TimescaleDB | 5456 | Primary database |
| **redis** | Cache & Event Bus | 6380 | Sessions, pub/sub |
| **clickhouse** | TimeSeries DB | 8124 | Analytics & metrics |
| **chromadb** | Vector Database | 8005 | Semantic search |
| **redpanda** | Message Broker | 9094 | Event streaming |
| **redpanda-console** | Kafka UI | 8081 | Message management |
| **prometheus** | Metrics | 9091 | Monitoring |
| **grafana** | Visualization | 3100 | Dashboards |

### Application Layer

| Service | Description | Port | Purpose |
|---------|-------------|------|---------|
| **api-server** | FastAPI Backend | 8000 | REST API + WebSocket |
| **federated-triad** | AI Agents | 8001 | Federated Triad service |
| **frontend** | React App | 5173 | Web UI (dev) |
| **frontend-prod** | Nginx | 80/443 | Web UI (prod) |

## 🔐 Environment Variables

### Required

Create a `.env` file:

```env
# Database
DATABASE_URL=postgresql+asyncpg://trader:trading_secure@postgres:5432/trading_db

# Redis
REDIS_URL=redis://redis:6379/0

# ClickHouse
CLICKHOUSE_HOST=clickhouse
CLICKHOUSE_HTTP_PORT=8123  # Intern in container
# Extern: localhost:5000 (zie PORT_ALLOCATION.md)
CLICKHOUSE_USER=trader
CLICKHOUSE_PASSWORD=trading_secure

# External APIs (required for trading)
DEEPSEEK_API_KEY=your_key_here
BITVAVO_API_KEY=your_key_here
BITVAVO_API_SECRET=your_secret_here
```

### Production (.env.prod)

```env
# Security
SECRET_KEY=your-super-secret-key
JWT_SECRET=your-jwt-secret

# Production DB credentials
DB_USER=trader
DB_PASSWORD=strong-production-password
DB_NAME=trading_db

# Production ClickHouse
CLICKHOUSE_PASSWORD=strong-production-password

# Monitoring
GRAFANA_ADMIN_PASSWORD=admin-password
```

## 🏭 Production Deployment

### Prerequisites

1. Server with Docker 20.10+ and Docker Compose 2.0+
2. Domain name configured
3. SSL certificates (optional, can use Let's Encrypt)

### Deployment Steps

```bash
# 1. Clone repository
git clone https://github.com/yourorg/agentic-trader.git
cd agentic-trader

# 2. Create production environment file
cp .env.example .env.prod
# Edit .env.prod with production values

# 3. Deploy
./scripts/docker-prod.sh deploy

# 4. Run migrations
./scripts/docker-dev.sh migrate

# 5. Check health
./scripts/docker-prod.sh health
```

### SSL with Let's Encrypt

```bash
# Install certbot
docker run -it --rm \
  -v "/etc/letsencrypt:/etc/letsencrypt" \
  -v "/var/lib/letsencrypt:/var/lib/letsencrypt" \
  certbot/certbot certonly --standalone -d yourdomain.com

# Mount certificates in docker-compose.prod.yml
```

## 📊 Monitoring

### Health Checks

All services include health checks:

```bash
# Check API health
curl http://localhost:8000/health

# Check all services
docker-compose ps
```

### Logs

```bash
# All services
./scripts/docker-dev.sh logs

# Specific service
docker-compose logs -f api-server

# Last 100 lines
docker-compose logs --tail=100 api-server
```

### Metrics

- **Prometheus**: http://localhost:9091
- **Grafana**: http://localhost:3100 (admin/admin)

## 🔧 Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs <service-name>

# Restart service
docker-compose restart <service-name>

# Rebuild and restart
docker-compose up -d --build <service-name>
```

### Database connection issues

```bash
# Check postgres is healthy
docker-compose ps postgres

# Connect to postgres
docker-compose exec postgres psql -U trader -d trading_db

# Reset database (⚠️ DESTRUCTIVE)
./scripts/docker-dev.sh reset
```

### Frontend build errors

```bash
# Clear node_modules
docker-compose down -v
rm -rf frontend/node_modules
./scripts/docker-dev.sh start
```

### Out of disk space

```bash
# Clean up Docker resources
docker system prune -a --volumes

# Clean up specific to this project
./scripts/docker-dev.sh clean
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         NGINX (80/443)                          │
│                    ┌──────────┴──────────┐                     │
│                    ▼                      ▼                     │
│              ┌──────────┐           ┌──────────┐               │
│              │ Frontend │           │   API    │               │
│              │  (React) │           │ (FastAPI)│               │
│              └──────────┘           └────┬─────┘               │
└──────────────────────────────────────────┼──────────────────────┘
                                           │
                    ┌──────────────────────┼──────────────────────┐
                    │                      │                      │
                    ▼                      ▼                      ▼
            ┌───────────┐         ┌───────────┐         ┌───────────┐
            │  Redis    │         │ PostgreSQL│         │ClickHouse │
            │ (Cache)   │         │  (Data)   │         │ (Analytics)│
            └───────────┘         └───────────┘         └───────────┘
                    │                      │                      │
                    └──────────────────────┼──────────────────────┘
                                           │
                                    ┌──────┴──────┐
                                    │  Federated  │
                                    │   Triad AI  │
                                    └─────────────┘
```

## 📝 Notes

- **Hot Reload**: Backend and frontend support hot reload in development
- **Volumes**: Source code is mounted as volumes for development
- **Network**: All services communicate via `agentic-trader-network`
- **Security**: Production uses non-root users and read-only filesystems

## 📚 Additional Resources

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/docker/)
- [Vite Deployment](https://vitejs.dev/guide/static-deploy.html)
