# Docker Troubleshooting Guide

Common Docker issues and solutions for the Agentic Trader Platform.

## Quick Diagnostics

```bash
# Check all services
docker compose ps

# View logs
docker compose logs -f api-server
docker compose logs --tail 50 redis

# Check resource usage
docker stats
```

## Common Issues

### Port Already in Use

**Error:** `bind: address already in use`

**Fix:**
```bash
# Find process using port
netstat -ano | findstr :8000
# or
lsof -i :8000

# Kill process or change port in docker-compose.yml
```

### Database Connection Refused

**Error:** `Connection refused to postgres:5432`

**Fix:**
```bash
# Check if postgres is running
docker compose ps

# Check postgres logs
docker compose logs postgres

# Restart postgres
docker compose restart postgres

# Wait for ready
docker exec agentic_trader_db pg_isready
```

### Redis Connection Error

**Error:** `Error connecting to Redis`

**Fix:**
```bash
# Test Redis
docker exec agentic_trader_redis redis-cli ping

# Should return: PONG

# If not, restart
docker compose restart redis
```

### api-server Health Check Fails

**Error:** `curl: not found` in health check

**Fix:**
```bash
# Rebuild with curl
docker compose build --no-cache api-server
docker compose up -d --build api-server
```

### Container Exits Immediately

**Diagnose:**
```bash
# Check exit code
docker compose ps

# View logs
docker compose logs <service>

# Check environment
docker compose config
```

## Volume Issues

### Reset Everything

```bash
# Stop all
docker compose down

# Remove volumes (WARNING: data loss)
docker compose down -v

# Rebuild from scratch
docker compose up -d --build
```

### Clean Up

```bash
# Remove unused containers
docker container prune

# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune
```

## Performance

### Slow Builds

```bash
# Use BuildKit
export DOCKER_BUILDKIT=1

# Build specific service
docker compose build api-server
```

### High Memory Usage

```bash
# Check memory
docker stats --no-stream

# Limit memory in docker-compose.yml
services:
  api-server:
    deploy:
      resources:
        limits:
          memory: 2G
```

## Networking

### Services Can't Connect

```bash
# Check network
docker network ls
docker network inspect <network_name>

# Test connectivity
docker exec api-server ping postgres
docker exec api-server redis-cli -h redis ping
```

## Environment Variables

### Check Config

```bash
# View effective config
docker compose config

# Check env in container
docker exec api-server env | grep DATABASE
```
