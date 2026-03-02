#!/bin/bash
# Pre-commit runner script for Agentic Trader Platform
# Usage: ./scripts/run_precommit.sh [options]

set -e

echo "========================================="
echo "Agentic Trader Platform - Pre-commit Runner"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    echo -e "${YELLOW}pre-commit not found. Installing...${NC}"
    pip install pre-commit
fi

# Install hooks if not already installed
if [ ! -f .git/hooks/pre-commit ]; then
    echo -e "${YELLOW}Installing pre-commit hooks...${NC}"
    pre-commit install
    echo -e "${GREEN}Hooks installed successfully${NC}"
    echo ""
fi

# Parse arguments
MODE=${1:-"all"}

show_help() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  all       Run all hooks on all files (default)"
    echo "  staged    Run hooks on staged files only"
    echo "  security  Run security checks only"
    echo "  lint      Run linting checks only"
    echo "  fix       Run with auto-fixes enabled"
    echo "  help      Show this help message"
    echo ""
}

case "$MODE" in
    "help"|"-h"|"--help")
        show_help
        exit 0
        ;;
    
    "all")
        echo -e "${YELLOW}Running all hooks on all files...${NC}"
        echo "This may take a few minutes..."
        echo ""
        pre-commit run --all-files
        ;;
    
    "staged")
        echo -e "${YELLOW}Running hooks on staged files only...${NC}"
        pre-commit run
        ;;
    
    "security")
        echo -e "${YELLOW}Running security checks only...${NC}"
        pre-commit run bandit-security --all-files
        pre-commit run check-hardcoded-secrets --all-files
        pre-commit run check-sql-injection --all-files
        ;;
    
    "lint")
        echo -e "${YELLOW}Running linting checks only...${NC}"
        pre-commit run black --all-files
        pre-commit run ruff --all-files
        pre-commit run isort --all-files
        pre-commit run mypy --all-files
        ;;
    
    "fix")
        echo -e "${YELLOW}Running with auto-fixes...${NC}"
        echo "Applying automatic fixes where possible..."
        echo ""
        
        # Run black with fix
        echo "Running Black formatter..."
        black backend/ --line-length=100 || true
        
        # Run ruff with fix
        echo "Running Ruff linter..."
        ruff check backend/ --fix || true
        
        # Run isort
        echo "Running isort..."
        isort backend/ --profile=black || true
        
        # Run pre-commit
        echo ""
        echo "Running pre-commit..."
        pre-commit run --all-files
        ;;
    
    *)
        echo -e "${RED}Unknown option: $MODE${NC}"
        show_help
        exit 1
        ;;
esac

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "========================================="
    echo -e "${GREEN}✅ All checks passed!${NC}"
    echo "========================================="
    echo ""
    echo "You can now commit your changes:"
    echo "  git add ."
    echo "  git commit -m 'Your commit message'"
    echo ""
    exit 0
else
    echo ""
    echo "========================================="
    echo -e "${RED}❌ Some checks failed${NC}"
    echo "========================================="
    echo ""
    echo "Please fix the issues above and try again."
    echo ""
    echo "To auto-fix some issues, run:"
    echo "  $0 fix"
    echo ""
    exit 1
fi
