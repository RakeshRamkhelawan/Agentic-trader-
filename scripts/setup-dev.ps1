# Development Environment Setup Script (Windows PowerShell)
# 
# This script sets up everything needed for development
# Usage: .\scripts\setup-dev.ps1

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Agentic Trader - Development Setup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path "pyproject.toml")) {
    Write-Host "[✗] Please run this script from the project root directory" -ForegroundColor Red
    exit 1
}

# 1. Check Python Version
Write-Host "[1/6] Checking Python version..."
$pythonVersion = python --version 2>&1
Write-Host "    Found: $pythonVersion"

# 2. Create Virtual Environment
Write-Host ""
Write-Host "[2/6] Setting up Python virtual environment..."

if (Test-Path "venv") {
    Write-Host "[✓] Virtual environment already exists" -ForegroundColor Green
} else {
    python -m venv venv
    Write-Host "[✓] Created virtual environment" -ForegroundColor Green
}

# Activate virtual environment
& .\venv\Scripts\Activate.ps1
Write-Host "[✓] Activated virtual environment" -ForegroundColor Green

# 3. Install Python Dependencies
Write-Host ""
Write-Host "[3/6] Installing Python dependencies..."

pip install --upgrade pip -q

if (Test-Path "requirements.txt") {
    pip install -r requirements.txt -q
    Write-Host "[✓] Installed production dependencies" -ForegroundColor Green
}

# Install dev dependencies
pip install pre-commit black ruff pytest pytest-asyncio -q
Write-Host "[✓] Installed development tools" -ForegroundColor Green

# 4. Install Pre-commit Hooks
Write-Host ""
Write-Host "[4/6] Installing pre-commit hooks..."

if (Test-Path ".pre-commit-config.yaml") {
    pre-commit install
    Write-Host "[✓] Installed pre-commit hooks" -ForegroundColor Green
    
    Write-Host "    Running initial pre-commit check (this may take a minute)..." -ForegroundColor Blue
    pre-commit run --all-files | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[!] Initial pre-commit check had warnings (this is normal)" -ForegroundColor Yellow
    }
} else {
    Write-Host "[!] .pre-commit-config.yaml not found, skipping" -ForegroundColor Yellow
}

# 5. Setup Environment Files
Write-Host ""
Write-Host "[5/6] Setting up environment files..."

# Backend
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "[✓] Created .env from .env.example" -ForegroundColor Green
        Write-Host "[!] Please edit .env with your actual values!" -ForegroundColor Yellow
    }
} else {
    Write-Host "[✓] .env already exists" -ForegroundColor Green
}

# Frontend
if (Test-Path "frontend") {
    if (-not (Test-Path "frontend/.env")) {
        if (Test-Path "frontend/.env.example") {
            Copy-Item "frontend/.env.example" "frontend/.env"
            Write-Host "[✓] Created frontend/.env from .env.example" -ForegroundColor Green
            Write-Host "[!] Please edit frontend/.env with your actual values!" -ForegroundColor Yellow
        }
    } else {
        Write-Host "[✓] frontend/.env already exists" -ForegroundColor Green
    }
}

# 6. Git Configuration
Write-Host ""
Write-Host "[6/6] Configuring Git..."

if (Test-Path ".git") {
    git config core.hooksPath .git/hooks
    Write-Host "[✓] Git repository configured" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "Current Git status:" -ForegroundColor Blue
    git status -sb
} else {
    Write-Host "[!] Not a Git repository (run 'git init' if needed)" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[✓] Development environment is ready" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host ""
Write-Host "1. Virtual environment is already activated"
Write-Host ""
Write-Host "2. Edit environment variables:"
Write-Host "   notepad .env  (backend)" -ForegroundColor Blue
Write-Host "   notepad frontend/.env  (frontend)" -ForegroundColor Blue
Write-Host ""
Write-Host "3. Start the development server:"
Write-Host "   # Backend" -ForegroundColor Blue
Write-Host "   uvicorn backend.api.main:app --reload" -ForegroundColor Blue
Write-Host ""
Write-Host "   # Frontend (in another terminal)" -ForegroundColor Blue
Write-Host "   cd frontend; npm run dev" -ForegroundColor Blue
Write-Host ""
Write-Host "Useful commands:"
Write-Host "   .\scripts\docker-start.ps1 dev  - Start with Docker"
Write-Host "   pytest backend/tests/           - Run tests"
Write-Host "   black backend/                  - Format code"
Write-Host ""
