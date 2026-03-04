#!/usr/bin/env pwsh
# =============================================================================
# DOCKER PORT CHECKER
# Controleert welke poorten al bezet zijn en suggereert alternatieven
# =============================================================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  DOCKER PORT CONFLICT CHECKER" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Poorten uit docker-compose.yml
$dockerPorts = @(
    @{ Service="Redpanda"; Port=9094; Protocol="TCP"; Description="Kafka API" },
    @{ Service="Redpanda Console"; Port=8081; Protocol="TCP"; Description="Web UI" },
    @{ Service="ClickHouse HTTP"; Port=8124; Protocol="TCP"; Description="HTTP interface" },
    @{ Service="ClickHouse Native"; Port=9001; Protocol="TCP"; Description="Native protocol" },
    @{ Service="PostgreSQL"; Port=5456; Protocol="TCP"; Description="Database" },
    @{ Service="Redis"; Port=6380; Protocol="TCP"; Description="Cache" },
    @{ Service="ChromaDB"; Port=8005; Protocol="TCP"; Description="Vector DB" },
    @{ Service="Prometheus"; Port=9091; Protocol="TCP"; Description="Metrics" },
    @{ Service="Grafana"; Port=3100; Protocol="TCP"; Description="Dashboards" },
    @{ Service="API Server"; Port=8000; Protocol="TCP"; Description="FastAPI Backend" },
    @{ Service="Federated Triad"; Port=8001; Protocol="TCP"; Description="AI Service" },
    @{ Service="Frontend"; Port=5173; Protocol="TCP"; Description="React Dev" },
    @{ Service="Frontend Alt"; Port=3000; Protocol="TCP"; Description="React Alt" },
    @{ Service="Frontend Prod"; Port=80; Protocol="TCP"; Description="Nginx HTTP" },
    @{ Service="Frontend Prod SSL"; Port=443; Protocol="TCP"; Description="Nginx HTTPS" }
)

Write-Host "Checking $($dockerPorts.Count) ports..." -ForegroundColor Yellow
Write-Host ""

$conflicts = @()
$available = @()

foreach ($item in $dockerPorts) {
    $port = $item.Port
    $service = $item.Service

    # Check if port is in use
    $connection = $null
    try {
        $connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -First 1
    } catch {
        # Port not found, means it's available
    }

    if ($connection) {
        $process = Get-Process -Id $connection.OwningProcess -ErrorAction SilentlyContinue
        $processName = if ($process) { $process.ProcessName } else { "Unknown" }

        Write-Host "❌ Port $port`t- $service `t[IN USE by $processName]" -ForegroundColor Red

        $conflicts += [PSCustomObject]@{
            Service = $service
            Port = $port
            Process = $processName
            PID = $connection.OwningProcess
            Description = $item.Description
        }
    } else {
        Write-Host "✅ Port $port`t- $service `t[AVAILABLE]" -ForegroundColor Green

        $available += $item
    }
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($conflicts.Count -eq 0) {
    Write-Host "All ports are available! You can start Docker without conflicts." -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "Found $($conflicts.Count) port conflicts!" -ForegroundColor Yellow
    Write-Host ""

    Write-Host "Conflicting Ports:" -ForegroundColor Red
    $conflicts | Format-Table -AutoSize | Out-String | Write-Host -ForegroundColor Red

    Write-Host ""
    Write-Host "Suggested Alternative Ports:" -ForegroundColor Cyan
    Write-Host ""

    foreach ($conflict in $conflicts) {
        $originalPort = $conflict.Port
        $suggestedPort = $originalPort + 1000

        # Check if suggested port is available
        $suggestedInUse = $false
        try {
            $suggestedConnection = Get-NetTCPConnection -LocalPort $suggestedPort -ErrorAction SilentlyContinue
            if ($suggestedConnection) { $suggestedInUse = $true }
        } catch {}

        if ($suggestedInUse) {
            $suggestedPort = $originalPort + 2000
        }

        Write-Host "  $($conflict.Service):" -ForegroundColor White
        Write-Host "    Original: $originalPort" -ForegroundColor Red
        Write-Host "    Suggested: $suggestedPort" -ForegroundColor Green
        Write-Host ""
    }

    Write-Host ""
    Write-Host "To resolve conflicts, you can:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "1. Stop the conflicting services" -ForegroundColor White
    Write-Host "2. Modify docker-compose.yml to use different ports" -ForegroundColor White
    Write-Host "3. Use port mapping: -p <new-port>:<container-port>" -ForegroundColor White
    Write-Host ""
}

# Check Docker itself
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  DOCKER STATUS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

try {
    $dockerInfo = docker info 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Docker is running" -ForegroundColor Green

        # Check existing containers
        $containers = docker ps --format "{{.Names}}" 2>$null
        if ($containers) {
            Write-Host ""
            Write-Host "Existing containers:" -ForegroundColor Yellow
            $containers | ForEach-Object { Write-Host "  - $_" -ForegroundColor White }
        } else {
            Write-Host ""
            Write-Host "No running containers" -ForegroundColor Green
        }
    } else {
        Write-Host "Docker is not running! Please start Docker Desktop." -ForegroundColor Red
        Write-Host ""
    }
} catch {
    Write-Host "Docker is not installed or not running!" -ForegroundColor Red
    Write-Host ""
}

# Check if our specific containers already exist
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AGENTIC TRADER CONTAINERS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ourContainers = docker ps -a --filter "name=agentic" --format "{{.Names}}|{{.Status}}|{{.Ports}}" 2>$null
if ($ourContainers) {
    Write-Host "Found existing Agentic Trader containers:" -ForegroundColor Yellow
    Write-Host ""
    $ourContainers | ForEach-Object {
        $parts = $_ -split "\|"
        Write-Host "  📦 $($parts[0]) [$($parts[1])]" -ForegroundColor White
        if ($parts[2]) {
            Write-Host "     Ports: $($parts[2])" -ForegroundColor DarkGray
        }
    }
    Write-Host ""
    Write-Host "Run 'make clean' to remove existing containers." -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host "No existing Agentic Trader containers found" -ForegroundColor Green
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
