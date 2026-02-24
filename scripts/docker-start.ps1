# Docker startup script for Agentic Trader Platform (Windows PowerShell)
#
# Usage:
#   .\scripts\docker-start.ps1          # Start all services
#   .\scripts\docker-start.ps1 dev      # Start with hot reload
#   .\scripts\docker-start.ps1 prod     # Start production mode
#   .\scripts\docker-start.ps1 stop     # Stop all services
#   .\scripts\docker-start.ps1 logs     # View logs

param(
    [Parameter(Position=0)]
    [ValidateSet("dev", "prod", "stop", "logs", "restart", "build", "clean", "migrate")]
    [string]$Command = "dev"
)

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

function Write-Status($message) {
    Write-Host "[INFO] $message" -ForegroundColor Green
}

function Write-Warning($message) {
    Write-Host "[WARN] $message" -ForegroundColor Yellow
}

function Write-Error($message) {
    Write-Host "[ERROR] $message" -ForegroundColor Red
}

function Test-Docker {
    try {
        $null = docker version 2>$null
        $null = docker-compose version 2>$null
        Write-Status "Docker and Docker Compose are installed"
        return $true
    } catch {
        Write-Error "Docker or Docker Compose is not installed or not running"
        return $false
    }
}

function Setup-Directories {
    Write-Status "Creating necessary directories..."
    $directories = @("logs", "data", "cache", "redis_data", "nginx\logs", "nginx\ssl")
    foreach ($dir in $directories) {
        if (!(Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }
    Write-Status "Directories created"
}

function Start-Dev {
    Write-Status "Starting in DEVELOPMENT mode with hot reload..."

    if (!(Test-Docker)) { exit 1 }
    Setup-Directories

    # Copy .env.example if .env doesn't exist
    if (!(Test-Path ".env")) {
        Write-Warning ".env file not found, copying from .env.example"
        Copy-Item ".env.example" ".env"
    }

    docker-compose up --build -d

    Write-Status "Services started!"
    Write-Host ""
    Write-Host "API Documentation: http://localhost:8000/docs"
    Write-Host "Health Check:      http://localhost:8000/api/v1/health"
    Write-Host "Redis:             redis://localhost:6379"
    Write-Host ""
    Write-Host "View logs: docker-compose logs -f api"
}

function Start-Prod {
    Write-Status "Starting in PRODUCTION mode..."

    if (!(Test-Docker)) { exit 1 }
    Setup-Directories

    # Check if .env exists
    if (!(Test-Path ".env")) {
        Write-Error ".env file not found! Please create it from .env.example"
        Write-Error "  Copy-Item .env.example .env"
        Write-Error "Then edit .env with your production settings"
        exit 1
    }

    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d

    Write-Status "Production services started!"
}

function Stop-Services {
    Write-Status "Stopping all services..."
    docker-compose down
    Write-Status "Services stopped"
}

function View-Logs {
    docker-compose logs -f api
}

function Restart-Services {
    Stop-Services
    Start-Dev
}

function Build-Images {
    Write-Status "Building Docker images..."
    docker-compose build
}

function Clean-Up {
    Write-Status "Cleaning up Docker resources..."
    docker-compose down -v --remove-orphans
    docker system prune -f
    Write-Status "Cleanup complete"
}

# Main command handler
switch ($Command) {
    "dev" { Start-Dev }
    "prod" { Start-Prod }
    "stop" { Stop-Services }
    "logs" { View-Logs }
    "restart" { Restart-Services }
    "build" { Build-Images }
    "clean" { Clean-Up }
    default {
        Write-Host "Usage: .\scripts\docker-start.ps1 {dev|prod|stop|logs|restart|build|clean}"
        Write-Host ""
        Write-Host "Commands:"
        Write-Host "  dev       Start in development mode (default)"
        Write-Host "  prod      Start in production mode"
        Write-Host "  stop      Stop all services"
        Write-Host "  logs      View API logs"
        Write-Host "  restart   Restart services"
        Write-Host "  build     Build Docker images"
        Write-Host "  clean     Clean up Docker resources"
    }
}
