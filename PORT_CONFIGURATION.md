# Agentic Trader - Port Configuration

## New Port Assignments (Conflict-Free)

| Service | Old Port | New Port | Status |
|---------|----------|----------|--------|
| Backend API | 8000 | **8005** | ✅ Free |
| Frontend | 3002 | **3005** | ✅ Free |
| PostgreSQL | 5432 | **5433** | ✅ Free |
| Redis | 6379 | **6380** | ✅ Free |
| ClickHouse | 8123 | **8124** | ✅ Free |
| WebSocket | 8000/ws | **8005/ws** | ✅ Free |

## Conflicting Services Detected
- SanskritiSetu uses port 8000
- PostgreSQL already on 5432
- Redis already on 6379
- ClickHouse already on 8123

## Files Updated
1. `docker-compose.yml` - Container port mappings
2. `frontend/.env` - API and WebSocket URLs
3. `frontend/.env.example` - Template for new setups
4. `.env` (root) - Backend environment variables
5. `.env.example` (root) - Backend template
6. `.env.prod` - Production configuration
7. `QUICK_START.md` - Documentation
