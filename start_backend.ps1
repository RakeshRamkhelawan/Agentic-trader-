# Start Backend API Server
Write-Host "Starting Backend API Server on port 8000..." -ForegroundColor Green
python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
