# Quick Start - Agentic Trader Platform

## Prerequisites
- Python 3.13+ installed
- Node.js 18+ installed
- Redis running on localhost:6379

## Step 1: Start Redis (if not running)
```powershell
# If you have Redis installed locally, start it:
redis-server

# Or use Docker:
docker run -d -p 6379:6379 redis:7-alpine
```

## Step 2: Configure Environment

### Backend (.env file in root directory)
Create a file named `.env` in the project root:
```env
AUTH_DISABLED=true
REDIS_URL=redis://localhost:6380/0
DATABASE_URL=postgresql+asyncpg://trader:trading_secure@localhost:5433/trading_db
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8124
```

### Frontend (already configured)
The frontend `.env` file should contain:
```env
VITE_API_URL=http://localhost:8005
VITE_WS_URL=ws://localhost:8005/ws/public
```

## Step 3: Start Backend

Open **PowerShell Terminal 1**:
```powershell
cd C:\Users\rsram\Downloads\agentic_trader_platform_1734_20260109_210621
$env:AUTH_DISABLED = "true"
$env:REDIS_URL = "redis://localhost:6380/0"
python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8005 --reload
```

Wait for:
```
INFO:     Uvicorn running on http://0.0.0.0:8005
```

## Step 4: Start Frontend

Open **PowerShell Terminal 2**:
```powershell
cd C:\Users\rsram\Downloads\agentic_trader_platform_1734_20260109_210621\frontend
npm run dev -- --port 3005
```

Wait for:
```
VITE v7.x.x  ready in xxx ms

➜  Local:   http://localhost:3005/
```

## Step 5: Access the Application

Open your browser to: **http://localhost:3005**

You should see:
- "Development Mode - Authentication Disabled" banner at top
- Dashboard loading with mock data
- No auth errors in console

## Troubleshooting

### Port already in use
```powershell
# Kill processes on port 8005
netstat -ano | findstr :8005
taskkill /F /PID <PID>
```

### Backend won't start
Check Redis is running:
```powershell
redis-cli ping
# Should return: PONG
```

### Frontend build errors
```powershell
cd frontend
npm install
npm run build
```

## What Works

✅ Authentication bypass in dev mode
✅ WebSocket public endpoint
✅ API endpoints (with mock data if DB unavailable)
✅ Frontend build and hot reload
✅ Dashboard, Markets, Portfolio pages
✅ Trading Chart (with WebSocket)
✅ Agent Status display

## API Endpoints

Once running, access:
- API Docs: http://localhost:8005/docs
- Health Check: http://localhost:8005/api/v1/health
- Config: http://localhost:8005/api/v1/config

## Production Mode

For production with Auth0:
1. Set up Auth0 tenant
2. Add credentials to frontend `.env`:
   ```env
   VITE_AUTH0_DOMAIN=your-tenant.auth0.com
   VITE_AUTH0_CLIENT_ID=your-client-id
   VITE_AUTH0_AUDIENCE=https://api.your-domain.com
   ```
3. Set backend `.env`:
   ```env
   AUTH0_DOMAIN=your-tenant.auth0.com
   AUTH0_API_AUDIENCE=https://api.your-domain.com
   AUTH0_ISSUER=https://your-tenant.auth0.com/
   ```
4. Remove or set `AUTH_DISABLED=false`
