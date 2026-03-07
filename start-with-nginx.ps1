# Start Agentic Trader with Nginx Reverse Proxy

Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Starting Agentic Trader with Nginx" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Check if infrastructure is running
$postgres = docker ps -q -f name=agentic_trader_postgres
if (-not $postgres) {
    Write-Host "[DOCKER] Starting Docker infrastructure..." -ForegroundColor Yellow
    docker-compose -f docker/docker-compose.full.yml up -d postgres clickhouse chromadb redpanda
    Start-Sleep -Seconds 10
}

# Check redis
$redis = docker ps -q -f name=agentic_trader_redis
if (-not $redis) {
    Write-Host "[DOCKER] Starting Redis..." -ForegroundColor Yellow
    docker start agentic_trader_redis
}

# Create frontend env
$envContent = @"
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
"@
$envContent | Out-File -FilePath "frontend/.env.local" -Encoding UTF8 -Force

# Start Backend
Write-Host ""
Write-Host "[BACKEND] Starting on port 8001..." -ForegroundColor Yellow
$backendProcess = Start-Process -FilePath "powershell" -ArgumentList "-Command", "cd '$PWD'; `$env:PYTHONPATH='$PWD'; .\venv\Scripts\activate; uvicorn backend.api.main:app --reload --port 8001 --host 0.0.0.0" -PassThru -WindowStyle Hidden
Write-Host "[OK] Backend started (PID: $($backendProcess.Id))" -ForegroundColor Green

# Wait for backend
Start-Sleep -Seconds 5

# Start Frontend
Write-Host ""
Write-Host "[FRONTEND] Starting on port 5173..." -ForegroundColor Yellow
$frontendProcess = Start-Process -FilePath "powershell" -ArgumentList "-Command", "cd '$PWD\frontend'; npm run dev -- --port 5173" -PassThru -WindowStyle Hidden
Write-Host "[OK] Frontend started (PID: $($frontendProcess.Id))" -ForegroundColor Green

# Wait for frontend
Start-Sleep -Seconds 5

# Start Nginx
Write-Host ""
Write-Host "[NGINX] Starting..." -ForegroundColor Yellow
docker run -d --name agentic_trader_nginx -p 80:80 -p 8000:8000 --add-host=host.docker.internal:host-gateway -v "${PWD}/infrastructure/nginx/nginx-dev.conf:/etc/nginx/nginx.conf:ro" --network agentic_trader_platform_1734_20260109_210621_trader-network nginx:alpine
Write-Host "[OK] Nginx started" -ForegroundColor Green

# Save PIDs
@"
Backend PID: $($backendProcess.Id)
Frontend PID: $($frontendProcess.Id)
Backend Port: 8001 (via nginx on 8000)
Frontend Port: 5173 (via nginx on 80)
"@ | Out-File -FilePath ".service-pids" -Encoding UTF8

Write-Host ""
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  ALL SERVICES STARTED!" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "  URLs:" -ForegroundColor Yellow
Write-Host "     • Main App:     http://localhost" -ForegroundColor White
Write-Host "     • API:          http://localhost:8000" -ForegroundColor White
Write-Host "     • API Docs:     http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "  [STOP] To stop: .\stop-services.ps1" -ForegroundColor Red
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan

# Monitor
while ($true) {
    Start-Sleep -Seconds 5
    $backendRunning = Get-Process -Id $backendProcess.Id -ErrorAction SilentlyContinue
    $frontendRunning = Get-Process -Id $frontendProcess.Id -ErrorAction SilentlyContinue

    if (-not $backendRunning) {
        Write-Host "[WARNING] Backend stopped!" -ForegroundColor Red
        break
    }
    if (-not $frontendRunning) {
        Write-Host "[WARNING] Frontend stopped!" -ForegroundColor Red
        break
    }
}
