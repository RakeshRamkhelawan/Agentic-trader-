# =============================================================================
# PORT CONFIGURATION SWITCHER (PowerShell)
# Switch between default and alternative port configurations
# =============================================================================

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("default", "alt", "check")]
    [string]$Mode = "check"
)

$altConfig = @"
version: '3.8'

services:
  api-server:
    build:
      target: development
    ports:
      - "9000:8000"
    environment:
      - ENVIRONMENT=development
      - DEBUG=true
      - LOG_LEVEL=DEBUG
      - ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:5173","http://localhost:6173","http://127.0.0.1:6173"]
      - CORS_ORIGINS=["http://localhost:3000","http://localhost:5173","http://localhost:6173"]
    volumes:
      - ./backend:/app/backend:cached
      - ./scripts:/app/scripts:cached
      - ./data:/app/data:cached
      - backend_venv:/opt/venv
    command: uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir /app/backend
    healthcheck:
      disable: false

  frontend:
    build:
      dockerfile: ../infrastructure/docker/Dockerfile.frontend
    ports:
      - "6173:5173"
    environment:
      - NODE_ENV=development
      - VITE_API_URL=http://localhost:9000
      - VITE_WS_URL=ws://localhost:9000/ws
      - CHOKIDAR_USEPOLLING=true
    volumes:
      - ./frontend:/app:cached
      - frontend_node_modules:/app/node_modules
    command: sh -c "npm install && npm run dev -- --host 0.0.0.0 --port 5173"

  postgres:
    image: postgres:15-alpine
    ports:
      - "6456:5432"
    environment:
      - POSTGRES_USER=trader
      - POSTGRES_PASSWORD=trading_secure
      - POSTGRES_DB=trading_db
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data
    healthcheck:
      disable: false

  redis:
    ports:
      - "7380:6379"

  clickhouse:
    ports:
      - "9124:8123"
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G

  chromadb:
    ports:
      - "9005:8000"
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M

  redpanda:
    ports:
      - "10094:9092"
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G

  redpanda-console:
    ports:
      - "9081:8080"
    profiles:
      - monitoring

  prometheus:
    ports:
      - "10091:9090"
    profiles:
      - monitoring

  grafana:
    ports:
      - "4100:3000"
    profiles:
      - monitoring

  federated-triad:
    ports:
      - "10001:8001"

volumes:
  backend_venv:
  frontend_node_modules:
  postgres_dev_data:
"@

$defaultConfig = @"
version: '3.8'

services:
  api-server:
    build:
      target: development
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=development
      - DEBUG=true
      - LOG_LEVEL=DEBUG
      - ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:5173","http://127.0.0.1:5173"]
      - CORS_ORIGINS=["http://localhost:3000","http://localhost:5173","http://127.0.0.1:5173"]
    volumes:
      - ./backend:/app/backend:cached
      - ./scripts:/app/scripts:cached
      - ./data:/app/data:cached
      - backend_venv:/opt/venv
    command: uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir /app/backend
    healthcheck:
      disable: false

  frontend:
    build:
      dockerfile: ../infrastructure/docker/Dockerfile.frontend
    ports:
      - "5173:5173"
    environment:
      - NODE_ENV=development
      - VITE_API_URL=http://localhost:8000
      - VITE_WS_URL=ws://localhost:8000/ws
      - CHOKIDAR_USEPOLLING=true
    volumes:
      - ./frontend:/app:cached
      - frontend_node_modules:/app/node_modules
    command: sh -c "npm install && npm run dev -- --host 0.0.0.0 --port 5173"

  postgres:
    image: postgres:15-alpine
    ports:
      - "5456:5432"
    environment:
      - POSTGRES_USER=trader
      - POSTGRES_PASSWORD=trading_secure
      - POSTGRES_DB=trading_db
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data
    healthcheck:
      disable: false

  redis:
    ports:
      - "6380:6379"

  clickhouse:
    ports:
      - "8124:8123"
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G

  chromadb:
    ports:
      - "8005:8000"
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M

  redpanda:
    ports:
      - "9094:9092"
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G

  redpanda-console:
    ports:
      - "8081:8080"
    profiles:
      - monitoring

  prometheus:
    ports:
      - "9091:9090"
    profiles:
      - monitoring

  grafana:
    ports:
      - "3100:3000"
    profiles:
      - monitoring

  federated-triad:
    ports:
      - "8001:8001"

volumes:
  backend_venv:
  frontend_node_modules:
  postgres_dev_data:
"@

function Show-PortStatus {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "  PORT CONFLICT CHECKER" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan

    $ports = @(
        @{Port=8000; Name="API Server"},
        @{Port=8001; Name="Federated Triad"},
        @{Port=5173; Name="Frontend"},
        @{Port=5456; Name="PostgreSQL"},
        @{Port=6380; Name="Redis"},
        @{Port=8124; Name="ClickHouse"},
        @{Port=8005; Name="ChromaDB"},
        @{Port=9094; Name="Redpanda"},
        @{Port=9091; Name="Prometheus"},
        @{Port=3100; Name="Grafana"}
    )

    $inUse = 0
    foreach ($p in $ports) {
        $port = $p.Port
        $name = $p.Name

        try {
            $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Any, $port)
            $listener.Start()
            $listener.Stop()
            Write-Host "  PORT $port ($name): " -NoNewline
            Write-Host "AVAILABLE" -ForegroundColor Green
        } catch {
            Write-Host "  PORT $port ($name): " -NoNewline
            Write-Host "OCCUPIED" -ForegroundColor Red
            $inUse++
        }
        Start-Sleep -Milliseconds 50
    }

    Write-Host "`n" -NoNewline
    if ($inUse -eq 0) {
        Write-Host "  All ports available! Use default ports.`n" -ForegroundColor Green
        return $true
    } else {
        Write-Host "  WARNING: $inUse ports are occupied! Use alternative ports.`n" -ForegroundColor Yellow
        return $false
    }
}

function Switch-ToAltPorts {
    Write-Host "`n========================================" -ForegroundColor Magenta
    Write-Host "  SWITCHING TO ALTERNATIVE PORTS" -ForegroundColor Magenta
    Write-Host "========================================`n" -ForegroundColor Magenta

    # Backup if not already exists
    if (-not (Test-Path "docker-compose.override.yml.backup")) {
        Copy-Item "docker-compose.override.yml" "docker-compose.override.yml.backup"
        Write-Host "  Backup created: docker-compose.override.yml.backup`n" -ForegroundColor Gray
    }

    $altConfig | Out-File -FilePath "docker-compose.override.yml" -Encoding UTF8

    Write-Host "  Alternative ports configured:`n" -ForegroundColor Green
    Write-Host "  Service             Old Port    New Port"
    Write-Host "  -----------------------------------------"
    Write-Host "  API Server          8000    →   " -NoNewline; Write-Host "9000" -ForegroundColor Green
    Write-Host "  Frontend            5173    →   " -NoNewline; Write-Host "6173" -ForegroundColor Green
    Write-Host "  PostgreSQL          5456    →   " -NoNewline; Write-Host "6456" -ForegroundColor Green
    Write-Host "  Redis               6380    →   " -NoNewline; Write-Host "7380" -ForegroundColor Green
    Write-Host "  ClickHouse HTTP     8124    →   " -NoNewline; Write-Host "9124" -ForegroundColor Green
    Write-Host "  ChromaDB            8005    →   " -NoNewline; Write-Host "9005" -ForegroundColor Green
    Write-Host "  Redpanda            9094    →   " -NoNewline; Write-Host "10094" -ForegroundColor Green
    Write-Host "  Redpanda Console    8081    →   " -NoNewline; Write-Host "9081" -ForegroundColor Green
    Write-Host "  Prometheus          9091    →   " -NoNewline; Write-Host "10091" -ForegroundColor Green
    Write-Host "  Grafana             3100    →   " -NoNewline; Write-Host "4100" -ForegroundColor Green
    Write-Host "  Federated Triad     8001    →   " -NoNewline; Write-Host "10001" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Access URLs:"
    Write-Host "  Frontend: " -NoNewline; Write-Host "http://localhost:6173" -ForegroundColor Cyan
    Write-Host "  API:      " -NoNewline; Write-Host "http://localhost:9000" -ForegroundColor Cyan
    Write-Host "  Docs:     " -NoNewline; Write-Host "http://localhost:9000/docs" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Run 'make start' or 'docker compose up -d' to start." -ForegroundColor Yellow
    Write-Host ""
}

function Switch-ToDefaultPorts {
    Write-Host "`n========================================" -ForegroundColor Blue
    Write-Host "  RESTORING DEFAULT PORTS" -ForegroundColor Blue
    Write-Host "========================================`n" -ForegroundColor Blue

    if (Test-Path "docker-compose.override.yml.backup") {
        Copy-Item "docker-compose.override.yml.backup" "docker-compose.override.yml"
        Remove-Item "docker-compose.override.yml.backup"
        Write-Host "  Restored from backup.`n" -ForegroundColor Green
    } else {
        $defaultConfig | Out-File -FilePath "docker-compose.override.yml" -Encoding UTF8
        Write-Host "  Created default configuration.`n" -ForegroundColor Green
    }

    Write-Host "  Default ports restored:`n" -ForegroundColor Green
    Write-Host "  Service             Port"
    Write-Host "  ------------------------"
    Write-Host "  API Server          8000"
    Write-Host "  Frontend            5173"
    Write-Host "  PostgreSQL          5456"
    Write-Host "  Redis               6380"
    Write-Host "  ClickHouse HTTP     8124"
    Write-Host "  ChromaDB            8005"
    Write-Host "  Redpanda            9094"
    Write-Host "  Prometheus          9091"
    Write-Host "  Grafana             3100"
    Write-Host ""
    Write-Host "  Access URLs:"
    Write-Host "  Frontend: http://localhost:5173"
    Write-Host "  API:      http://localhost:8000"
    Write-Host "  Docs:     http://localhost:8000/docs"
    Write-Host ""
    Write-Host "  Run 'make start' or 'docker compose up -d' to start." -ForegroundColor Yellow
    Write-Host ""
}

# Main execution
switch ($Mode) {
    "check" {
        $allAvailable = Show-PortStatus
        Write-Host "`nUSAGE:" -ForegroundColor White
        Write-Host "  .\scripts\switch-ports.ps1 -Mode alt     # Use alternative ports" -ForegroundColor Gray
        Write-Host "  .\scripts\switch-ports.ps1 -Mode default # Use default ports" -ForegroundColor Gray
        Write-Host "  .\scripts\switch-ports.ps1 -Mode check   # Check port status" -ForegroundColor Gray
        Write-Host ""
        if (-not $allAvailable) {
            $response = Read-Host "Ports are occupied. Switch to alternative ports? (y/n)"
            if ($response -eq 'y' -or $response -eq 'Y') {
                Switch-ToAltPorts
            }
        }
    }
    "alt" { Switch-ToAltPorts }
    "default" { Switch-ToDefaultPorts }
}
