#!/bin/bash
#
# Security Fix Script for Agentic Trader Frontend
#
# This script helps identify and fix common security issues.
#
# Usage: ./scripts/security-fix.sh

set -e

echo "=========================================="
echo "Agentic Trader - Security Fix Script"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check if .env exists
echo "[1/5] Checking environment configuration..."
if [ ! -f .env ]; then
    print_warning ".env file not found!"
    if [ -f .env.example ]; then
        cp .env.example .env
        print_status "Created .env from .env.example"
        print_warning "Please edit .env and fill in your actual values!"
    else
        print_error ".env.example not found! Cannot create .env"
        exit 1
    fi
else
    print_status ".env file exists"
fi

# Check for hardcoded credentials
echo ""
echo "[2/5] Scanning for hardcoded credentials..."
CREDENTIALS_FOUND=false

# Check for Auth0 credentials in source
if grep -r "auth0.com" src/ --include="*.tsx" --include="*.ts" | grep -v ".env" | grep -v "import.meta.env" > /dev/null 2>&1; then
    print_error "Found hardcoded Auth0 domain in source code!"
    grep -r "auth0.com" src/ --include="*.tsx" --include="*.ts" | grep -v ".env" | grep -v "import.meta.env"
    CREDENTIALS_FOUND=true
fi

if grep -r "clientId.*:" src/ --include="*.tsx" --include="*.ts" | grep -v "import.meta.env" | grep -v "process.env" > /dev/null 2>&1; then
    print_error "Found hardcoded client ID in source code!"
    grep -r "clientId.*:" src/ --include="*.tsx" --include="*.ts" | grep -v "import.meta.env" | grep -v "process.env"
    CREDENTIALS_FOUND=true
fi

if [ "$CREDENTIALS_FOUND" = false ]; then
    print_status "No hardcoded credentials found in source code"
fi

# Check for localStorage token storage
echo ""
echo "[3/5] Checking for insecure token storage..."
if grep -r "localStorage.*token" src/ --include="*.tsx" --include="*.ts" > /dev/null 2>&1; then
    print_warning "Found localStorage token storage (should use httpOnly cookies)"
    grep -r "localStorage.*token" src/ --include="*.tsx" --include="*.ts"
else
    print_status "No insecure localStorage token storage found"
fi

# Run npm audit
echo ""
echo "[4/5] Running npm audit..."
npm audit --audit-level=moderate || true

# Check for security updates
echo ""
echo "[5/5] Checking for security updates..."
npm outdated || true

echo ""
echo "=========================================="
echo "Security Check Complete"
echo "=========================================="
echo ""

if [ "$CREDENTIALS_FOUND" = true ]; then
    print_error "CRITICAL: Hardcoded credentials found!"
    echo ""
    echo "To fix:"
    echo "  1. Move all credentials to .env file"
    echo "  2. Use import.meta.env.VITE_* to access them"
    echo "  3. Never commit .env to git"
    echo ""
    exit 1
else
    print_status "No critical security issues found"
    echo ""
    echo "Next steps:"
    echo "  1. Review .env file and fill in your values"
    echo "  2. Run: npm audit fix"
    echo "  3. Ensure .env is in .gitignore"
    echo ""
fi
