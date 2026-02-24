# Agentic Trader Platform - Production Deployment Guide

> Complete guide for deploying the Agentic Trader Platform in production with SSL/TLS and Auth0 authentication.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Configuration](#configuration)
4. [SSL/TLS Setup](#ssltls-setup)
5. [Auth0 Configuration](#auth0-configuration)
6. [Production Deployment](#production-deployment)
7. [Monitoring](#monitoring)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 20.04+ recommended) or Windows with Docker Desktop
- **RAM**: Minimum 8GB, Recommended 16GB
- **Disk**: Minimum 50GB free space
- **CPU**: 4 cores minimum

### Software Requirements
- Docker 24.0+ & Docker Compose 2.0+
- OpenSSL (for SSL certificate generation)
- Git

## Quick Start

### 1. Clone and Setup
```bash
git clone <repository-url>
cd agentic_trader_platform_1734
cp .env.example .env
```

### 2. Start Infrastructure Services
```bash
# Start all services (without SSL)
docker-compose up -d

# Or with SSL enabled (see SSL setup below)
docker-compose --profile ssl up -d
```

### 3. Verify Installation
```bash
# Check all services are running
docker-compose ps

# Test API
curl http://localhost:8003/api/v1/health/ping

# Access Frontend
# Open http://localhost:3000 in your browser
```

## Configuration

### Environment Variables (.env)

Copy `.env.example` to `.env` and configure:

```bash
# Required: Security Keys (generate strong random strings)
SECRET_KEY=your-super-secret-key-here-min-32-characters
JWT_SECRET_KEY=your-jwt-secret-key-here-min-32-characters

# Required for Auth: Set to 'false' for production
AUTH_DISABLED=false

# Auth0 Configuration (see Auth0 section below)
AUTH0_DOMAIN=your-domain.auth0.com
AUTH0_CLIENT_ID=your-auth0-client-id
AUTH0_CLIENT_SECRET=your-auth0-client-secret
AUTH0_AUDIENCE=https://your-domain.auth0.com/api/v2/
AUTH0_CALLBACK_URL=https://yourdomain.com/callback

# SSL Configuration
SSL_ENABLED=false  # Set to 'true' after SSL setup

# Frontend URLs
VITE_API_URL=https://yourdomain.com  # Use HTTPS in production
VITE_WS_URL=wss://yourdomain.com/ws/public
```

## SSL/TLS Setup

### Option 1: Self-Signed Certificates (Development/Testing)

```bash
# Linux/Mac
./setup_ssl.sh yourdomain.com

# Windows
.\setup_ssl.ps1 yourdomain.com
```

Then enable SSL:
```bash
# Update .env
SSL_ENABLED=true

# Start with SSL profile
docker-compose --profile ssl up -d
```

### Option 2: Let's Encrypt (Production)

```bash
# Install certbot
sudo apt-get install certbot

# Generate certificates
sudo certbot certonly --standalone -d yourdomain.com

# Copy certificates to nginx/ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/key.pem
sudo chmod 644 nginx/ssl/cert.pem
sudo chmod 600 nginx/ssl/key.pem

# Enable SSL
# Update .env: SSL_ENABLED=true

# Start with SSL
docker-compose --profile ssl up -d
```

### Option 3: Existing Certificates

Place your existing certificate files in `nginx/ssl/`:
- `cert.pem` - Certificate (including intermediate chain)
- `key.pem` - Private key

## Auth0 Configuration

### 1. Create Auth0 Account
1. Sign up at [auth0.com](https://auth0.com)
2. Create a new Application (Regular Web Application)
3. Configure Allowed Callback URLs: `https://yourdomain.com/callback`
4. Configure Allowed Logout URLs: `https://yourdomain.com`
5. Configure Allowed Web Origins: `https://yourdomain.com`

### 2. Get Credentials
From your Auth0 Application settings, copy:
- **Domain**: `your-domain.auth0.com`
- **Client ID**: From application settings
- **Client Secret**: From application settings
- **Audience**: API identifier (create an API in Auth0 dashboard)

### 3. Configure Environment
```bash
# .env file
AUTH0_DOMAIN=your-domain.auth0.com
AUTH0_CLIENT_ID=your-client-id
AUTH0_CLIENT_SECRET=your-client-secret
AUTH0_AUDIENCE=https://your-domain.auth0.com/api/v2/
AUTH0_CALLBACK_URL=https://yourdomain.com/callback
AUTH_DISABLED=false
```

### 4. Frontend Configuration
The frontend will automatically use Auth0 when `AUTH_DISABLED=false` and credentials are provided.

## Production Deployment

### Step 1: Prepare Server
```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
sudo apt-get install docker.io docker-compose -y
sudo usermod -aG docker $USER
```

### Step 2: Deploy Application
```bash
# Clone repository
git clone <repository-url>
cd agentic_trader_platform_1734

# Copy and configure environment
cp .env.example .env
# Edit .env with production values

# Setup SSL (Let's Encrypt)
./setup_ssl.sh yourdomain.com

# Start all services
docker-compose --profile ssl up -d
```

### Step 3: Verify Deployment
```bash
# Check services
docker-compose ps

# Check logs
docker-compose logs -f api
docker-compose logs -f frontend

# Test health endpoints
curl https://yourdomain.com/api/v1/health/ping
```

### Step 4: Database Migrations
```bash
# Run migrations (if needed)
docker-compose exec api alembic upgrade head
```

## Monitoring

### Health Checks
All services include health checks:
- **API**: `https://yourdomain.com/api/v1/health/ping`
- **Frontend**: `https://yourdomain.com`
- **PostgreSQL**: Internal health check
- **Redis**: Internal health check
- **ClickHouse**: Internal health check
- **ChromaDB**: Internal health check

### Viewing Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api

# Last 100 lines
docker-compose logs --tail=100 api
```

### Resource Usage
```bash
# Container stats
docker stats

# System resources
docker system df
```

## Troubleshooting

### Service Won't Start
```bash
# Check logs
docker-compose logs <service-name>

# Restart service
docker-compose restart <service-name>

# Rebuild and restart
docker-compose up -d --build <service-name>
```

### Port Conflicts
If you see "port already allocated" errors:
```bash
# Check what's using the port
sudo netstat -tulpn | grep :8003

# Change ports in docker-compose.yml if needed
```

### Database Connection Issues
```bash
# Verify PostgreSQL is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres psql -U trader -d trading_db -c "SELECT 1"
```

### SSL Certificate Issues
```bash
# Verify certificates exist
ls -la nginx/ssl/

# Check certificate validity
openssl x509 -in nginx/ssl/cert.pem -text -noout

# Test SSL connection
openssl s_client -connect localhost:443 -servername yourdomain.com
```

### Auth0 Login Issues
1. Verify Auth0 credentials in `.env`
2. Check Allowed Callback URLs in Auth0 dashboard
3. Check browser console for CORS errors
4. Verify `AUTH_DISABLED=false` in `.env`

## Security Best Practices

1. **Change Default Secrets**: Update `SECRET_KEY` and `JWT_SECRET_KEY`
2. **Use HTTPS**: Always enable SSL in production
3. **Firewall**: Only expose ports 80, 443, and 8003 (if needed)
4. **Regular Updates**: Keep Docker images updated
5. **Backup**: Regularly backup PostgreSQL and ClickHouse data

## Backup and Restore

### Backup
```bash
# PostgreSQL
docker-compose exec postgres pg_dump -U trader trading_db > backup.sql

# ClickHouse
docker-compose exec clickhouse clickhouse-client --query "BACKUP ALL TO File('/backups/backup.zip')"
```

### Restore
```bash
# PostgreSQL
docker-compose exec -T postgres psql -U trader trading_db < backup.sql
```

## Service Ports

| Service | Internal Port | External Port | Notes |
|---------|--------------|---------------|-------|
| Frontend | 80 | 3000 | React app via Nginx |
| API | 8000 | 8003 | FastAPI backend |
| PostgreSQL | 5432 | 5433 | Main database |
| Redis | 6379 | 6380 | Cache & sessions |
| ClickHouse | 8123 | 8124 | Analytics DB |
| ChromaDB | 8000 | 8001 | Vector DB |
| Redpanda | 9092 | 9093 | Kafka API |
| Ollama | 11434 | 11435 | Local LLM inference |
| Prediction Intelligence | 8002 | 8002 | Kalshi/Polymarket signals |
| Nginx (SSL) | 443 | 443 | HTTPS reverse proxy |

## LLM Configuration (Ollama)

### Option 1: Local Ollama (Recommended for Privacy)

Start Ollama with the LLM profile:
```bash
# Start with Ollama
docker-compose --profile llm up -d ollama

# Download a model (e.g., Llama 3.2)
docker-compose exec ollama ollama pull llama3.2

# Or for larger model
docker-compose exec ollama ollama pull llama3:8b
```

Update `.env`:
```bash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2
```

### Option 2: OpenAI
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=your-openai-api-key
```

### Option 3: DeepSeek
```bash
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your-deepseek-api-key
```

## Prediction Market Intelligence (Optional)

This optional microservice provides trading signals based on Kalshi and Polymarket prediction market data.

### Features
- **Maker/Taker Analysis** - Identify market advantages
- **Volume Trend Detection** - Spot unusual trading activity
- **Signal Generation** - 7 signal types with confidence scoring
- **Statistical Analysis** - T-tests, chi-square, effect size calculations

### Start Prediction Intelligence
```bash
# Start with prediction profile
docker-compose --profile prediction up -d

# Verify it's running
curl http://localhost:8002/health
```

### API Endpoints
| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check |
| `GET /api/v1/signals` | List trading signals |
| `POST /api/v1/analysis/run` | Submit analysis job |
| `GET /api/v1/analysis/{id}` | Get analysis result |

### Configuration
```bash
# .env file
PREDICTION_INTELLIGENCE_URL=http://prediction-intelligence:8002

# Optional: API keys for data sources
KALSHI_API_KEY=your-kalshi-api-key
POLYMARKET_API_KEY=your-polymarket-api-key
```

## Support

For issues and questions:
- Check logs: `docker-compose logs -f`
- Review configuration: `docker-compose config`
- Consult documentation in `docs/` folder
