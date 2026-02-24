# Docker Deployment Guide

> **Production-Ready Containerization for Agentic Trader Platform**

---

## 🎯 Quick Start

### Prerequisites
- Docker Engine 24.0+
- Docker Compose 2.0+
- 4GB RAM minimum (8GB recommended)

### 1-Minute Start
```bash
# Clone repository
git clone <your-repo>
cd agentic_trader_platform

# Copy environment file
cp .env.example .env

# Start all services
./scripts/docker-start.sh dev

# Or on Windows
.\scripts\docker-start.ps1 dev
```

**Services will be available at:**
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/v1/health
- Redis: redis://localhost:6379

---

## 📁 Docker Files Overview

| File | Purpose |
|------|---------|
| `Dockerfile` | Multi-stage build for API service |
| `docker-compose.yml` | Base orchestration (Redis + API) |
| `docker-compose.override.yml` | Development overrides (hot reload) |
| `docker-compose.prod.yml` | Production settings (SSL, limits) |
| `.dockerignore` | Exclude files from build context |
| `redis.conf` | Redis production configuration |
| `nginx/nginx.conf` | Reverse proxy with rate limiting |

---

## 🚀 Deployment Modes

### Development Mode (Hot Reload)
```bash
# Automatic code reload on file changes
./scripts/docker-start.sh dev

# View logs
docker-compose logs -f api

# Stop
docker-compose down
```

**Features:**
- Hot code reload (no restart needed)
- Debug logging
- Redis exposed on port 6379
- Volume mounting for live editing

### Production Mode
```bash
# 1. Configure environment
cp .env.example .env
nano .env  # Edit with production values

# 2. Generate secret key
openssl rand -hex 32
# Add to .env: SECRET_KEY=your-generated-key

# 3. Start production stack
./scripts/docker-start.sh prod

# 4. Check status
docker-compose ps
docker-compose logs -f api
```

**Production Features:**
- Resource limits (CPU/memory)
- SSL/TLS termination
- Rate limiting
- Log rotation
- Health checks
- Non-root user

---

## 📊 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         CLIENTS                              │
├─────────────────────────────────────────────────────────────┤
│  React Dashboard    curl/python scripts    Claude Desktop   │
│       │                    │                     │          │
│       └────────────────────┼─────────────────────┘          │
│                            │                                │
│                     Nginx (port 80/443)                     │
│                     SSL + Rate Limiting                     │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────┐
│                    DOCKER NETWORK                          │
├────────────────────────────┼────────────────────────────────┤
│                            ▼                                │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  FastAPI Container (trader-api)                     │   │
│  │  • Uvicorn workers (4)                              │   │
│  │  • Direct Python imports                            │   │
│  │  • NumPy vectorization                              │   │
│  │  • Port: 8000                                       │   │
│  └────────────────────┬────────────────────────────────┘   │
│                       │                                     │
│                       │ Redis Protocol                      │
│                       ▼                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Redis Container (trader-redis)                     │   │
│  │  • Cache + Session store                            │   │
│  │  • Persistent storage (volume)                      │   │
│  │  • Port: 6379 (internal)                            │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Configuration

### Environment Variables

Create `.env` file from `.env.example`:

```bash
# Required
REDIS_URL=redis://redis:6379/0
LOG_LEVEL=INFO

# Security (generate these!)
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)

# Performance
UVICORN_WORKERS=4
MAX_WORKERS=4
ENABLE_CACHE=true
ENABLE_PARALLEL=true
```

### Resource Limits

```yaml
# docker-compose.prod.yml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
    reservations:
      cpus: '1.0'
      memory: 512M
```

---

## 🔒 Security Best Practices

### 1. Secrets Management
```bash
# Generate strong secrets
openssl rand -hex 32 > .secret_key

# Use Docker Secrets (Swarm mode)
echo "your-secret" | docker secret create api_secret -
```

### 2. SSL/TLS Certificates
```bash
# Option A: Let's Encrypt (recommended)
certbot certonly --standalone -d your-domain.com

# Copy certificates
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/cert.pem
cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/key.pem
```

### 3. Firewall Rules
```bash
# Allow only necessary ports
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw enable
```

---

## 📈 Monitoring

### Health Checks
```bash
# API health
curl http://localhost:8000/api/v1/health

# Redis health
docker-compose exec redis redis-cli ping

# All services
docker-compose ps
```

### Logs
```bash
# Follow API logs
docker-compose logs -f api

# All services
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100 api
```

### Metrics (Prometheus/Grafana)
```yaml
# Add to docker-compose.yml
prometheus:
  image: prom/prometheus
  volumes:
    - ./prometheus:/etc/prometheus
  ports:
    - "9090:9090"
```

---

## 🔄 Updates & Maintenance

### Update Application
```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose up --build -d

# Verify
docker-compose ps
```

### Backup Data
```bash
# Backup Redis
docker-compose exec redis redis-cli BGSAVE
cp redis_data/dump.rdb backups/redis-$(date +%Y%m%d).rdb

# Backup logs
tar -czf backups/logs-$(date +%Y%m%d).tar.gz logs/
```

### Cleanup
```bash
# Remove unused containers/images
docker system prune -f

# Deep clean (WARNING: removes all volumes!)
./scripts/docker-start.sh clean
```

---

## 🐛 Troubleshooting

### Service Won't Start
```bash
# Check logs
docker-compose logs api

# Check for port conflicts
netstat -tlnp | grep 8000

# Restart with fresh build
docker-compose down
docker-compose up --build -d
```

### Redis Connection Failed
```bash
# Check Redis status
docker-compose exec redis redis-cli ping

# Restart Redis
docker-compose restart redis

# Check network
docker network ls
docker network inspect agentic_trader_platform_trader-network
```

### Performance Issues
```bash
# Check resource usage
docker stats

# Scale workers
UVICORN_WORKERS=8 docker-compose up -d

# Profile with py-spy
docker-compose exec api py-spy top --pid 1
```

---

## 🌍 Cloud Deployment

### Google Cloud Run
```bash
# Build image
gcloud builds submit --tag gcr.io/PROJECT-ID/trader-api

# Deploy
gcloud run deploy trader-api \
  --image gcr.io/PROJECT-ID/trader-api \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars="REDIS_URL=redis://..."
```

### AWS ECS
```bash
# Create cluster
aws ecs create-cluster --cluster-name trader-cluster

# Deploy service
aws ecs create-service \
  --cluster trader-cluster \
  --service-name trader-api \
  --task-definition trader-task \
  --desired-count 2
```

### VPS (DigitalOcean/Linode)
```bash
# On server:
git clone <your-repo>
cd agentic_trader_platform
./scripts/docker-start.sh prod

# Setup systemd service
sudo cp scripts/trader.service /etc/systemd/system/
sudo systemctl enable trader
sudo systemctl start trader
```

---

## 🎓 Best Practices

### 1. Always Use .env
Never commit secrets to git:
```bash
# .gitignore
.env
.env.local
*.pem
*.key
```

### 2. Version Pinning
Use specific versions in production:
```dockerfile
FROM python:3.12.3-slim  # Not just 3.12
```

### 3. Health Checks
Always define health checks:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health/ping"]
  interval: 30s
  timeout: 10s
  retries: 3
```

### 4. Log Aggregation
Centralize logs with:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Datadog
- Splunk
- CloudWatch (AWS)

---

## ✅ Production Checklist

- [ ] Environment variables configured (.env)
- [ ] Secret keys generated (openssl)
- [ ] SSL certificates installed
- [ ] Firewall configured (ufw/iptables)
- [ ] Resource limits set
- [ ] Log rotation enabled
- [ ] Health checks configured
- [ ] Monitoring setup (Prometheus/Grafana)
- [ ] Backup strategy implemented
- [ ] Documentation updated
- [ ] Team trained on deployment process

---

## 📞 Support

**Common Commands:**
```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Logs
docker-compose logs -f

# Restart
docker-compose restart api

# Shell access
docker-compose exec api bash

# Redis CLI
docker-compose exec redis redis-cli
```

---

*Document Version: 1.0*
*Last Updated: February 22, 2026*
*Status: Production Ready* ✅
