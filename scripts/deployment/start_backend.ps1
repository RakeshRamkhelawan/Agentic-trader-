# Backend Startup Script for Agentic Trader Platform
# This script starts the backend API server with correct environment variables

# Set environment variables
$env:PYTHONPATH = "."
$env:DATABASE_URL = "postgresql+asyncpg://trader:trading_secure@localhost:5432/trading_db"
$env:REDIS_URL = "redis://localhost:6379/0"
$env:CLICKHOUSE_HOST = "localhost"
$env:CLICKHOUSE_PORT = "8123"
$env:CHROMA_HOST = "localhost"
$env:CHROMA_PORT = "8005"
$env:KAFKA_BOOTSTRAP_SERVERS = "localhost:9092"
$env:LOG_LEVEL = "INFO"
$env:SECRET_KEY = "dev-secret-key"
$env:JWT_SECRET_KEY = "dev-jwt-secret"
$env:UVICORN_WORKERS = "1"

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "  Agentic Trader - Backend Startup" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Environment configured:" -ForegroundColor Yellow
Write-Host "  - Database: localhost:5432"
Write-Host "  - Redis: localhost:6379"
Write-Host "  - ClickHouse: localhost:8123"
Write-Host "  - ChromaDB: localhost:8005"
Write-Host "  - API Port: 8005"
Write-Host ""
Write-Host "Starting uvicorn server..." -ForegroundColor Green
Write-Host ""

# Start uvicorn with single worker for debugging
python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8005 --reload --log-level info
