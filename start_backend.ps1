$env:JWT_SECRET_KEY = "65a2ed0b53625014a011b6882a2ed5df15d36d6843a61904c68102660bb3b744"
$env:DATABASE_URL = "postgresql+asyncpg://trader:pIu4r4xm8wel5_vBkKYi_mjelL4Hp35E@localhost:5432/trading_db"
$env:AUTH_DISABLED = "true"
$env:REDIS_URL = "redis://localhost:6379/0"

Write-Host "Starting Backend on port 8000..." -ForegroundColor Green
.\venv\Scripts\uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
