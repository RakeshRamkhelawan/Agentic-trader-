#!/bin/bash
#
# Development Environment Setup Script
# 
# This script sets up everything needed for development:
# - Python virtual environment
# - Pre-commit hooks
# - Git configuration
#
# Usage: ./scripts/setup-dev.sh

set -e

echo "=========================================="
echo "Agentic Trader - Development Setup"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[ℹ]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# ============================================================================
# 1. Check Python Version
# ============================================================================
echo "[1/6] Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.13"

if python3 -c "import sys; exit(0 if sys.version_info >= (3, 13) else 1)" 2>/dev/null; then
    print_status "Python $python_version detected (>= 3.13 ✓)"
else
    print_warning "Python $python_version detected (< 3.13)"
    print_info "Some features may not work correctly"
fi

# ============================================================================
# 2. Create Virtual Environment
# ============================================================================
echo ""
echo "[2/6] Setting up Python virtual environment..."

if [ -d "venv" ]; then
    print_status "Virtual environment already exists"
else
    python3 -m venv venv
    print_status "Created virtual environment"
fi

# Activate virtual environment
source venv/bin/activate

print_status "Activated virtual environment"

# ============================================================================
# 3. Install Python Dependencies
# ============================================================================
echo ""
echo "[3/6] Installing Python dependencies..."

pip install --upgrade pip -q

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt -q
    print_status "Installed production dependencies"
fi

if [ -f "requirements-dev.txt" ]; then
    pip install -r requirements-dev.txt -q
    print_status "Installed development dependencies"
else
    # Install essential dev tools
    pip install pre-commit black ruff pytest pytest-asyncio -q
    print_status "Installed default development tools"
fi

# ============================================================================
# 4. Install Pre-commit Hooks
# ============================================================================
echo ""
echo "[4/6] Installing pre-commit hooks..."

if [ -f ".pre-commit-config.yaml" ]; then
    pre-commit install
    print_status "Installed pre-commit hooks"
    
    # Run once to setup
    print_info "Running initial pre-commit check (this may take a minute)..."
    pre-commit run --all-files || {
        print_warning "Initial pre-commit check had warnings (this is normal)"
    }
else
    print_warning ".pre-commit-config.yaml not found, skipping"
fi

# ============================================================================
# 5. Setup Environment Files
# ============================================================================
echo ""
echo "[5/6] Setting up environment files..."

# Backend
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_status "Created .env from .env.example"
        print_warning "Please edit .env with your actual values!"
    else
        print_warning ".env.example not found"
    fi
else
    print_status ".env already exists"
fi

# Frontend
if [ -d "frontend" ]; then
    if [ ! -f "frontend/.env" ]; then
        if [ -f "frontend/.env.example" ]; then
            cp frontend/.env.example frontend/.env
            print_status "Created frontend/.env from .env.example"
            print_warning "Please edit frontend/.env with your actual values!"
        fi
    else
        print_status "frontend/.env already exists"
    fi
fi

# ============================================================================
# 6. Git Configuration
# ============================================================================
echo ""
echo "[6/6] Configuring Git..."

# Check if we're in a git repo
if [ -d ".git" ]; then
    # Set up git hooks path (if needed)
    git config core.hooksPath .git/hooks
    print_status "Git repository configured"
    
    # Show git status
    echo ""
    print_info "Current Git status:"
    git status -sb || true
else
    print_warning "Not a Git repository (run 'git init' if needed)"
fi

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""

print_status "Development environment is ready"
echo ""
echo "Next steps:"
echo ""
echo "1. Activate virtual environment:"
echo "   ${BLUE}source venv/bin/activate${NC}"
echo ""
echo "2. Edit environment variables:"
echo "   ${BLUE}nano .env${NC}  (backend)"
echo "   ${BLUE}nano frontend/.env${NC}  (frontend)"
echo ""
echo "3. Start the development server:"
echo "   ${BLUE}# Backend${NC}"
echo "   ${BLUE}uvicorn backend.api.main:app --reload${NC}"
echo ""
echo "   ${BLUE}# Frontend (in another terminal)${NC}"
echo "   ${BLUE}cd frontend && npm run dev${NC}"
echo ""
echo "4. Run pre-commit checks:"
echo "   ${BLUE}pre-commit run --all-files${NC}"
echo ""
echo "Useful commands:"
echo "  ${BLUE}./scripts/docker-start.sh dev${NC}  - Start with Docker"
echo "  ${BLUE}pytest backend/tests/${NC}          - Run tests"
echo "  ${BLUE}black backend/${NC}                 - Format code"
echo ""

# Deactivate virtual environment
deactivate 2>/dev/null || true
