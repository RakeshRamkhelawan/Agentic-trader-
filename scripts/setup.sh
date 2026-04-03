#!/bin/bash
# =============================================================================
# SETUP SCRIPT - Agentic Trader Platform
# One-command setup for new installations
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    local missing=()

    # Check Docker
    if ! command -v docker &> /dev/null; then
        missing+=("docker")
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        missing+=("docker-compose")
    fi

    # Check Git
    if ! command -v git &> /dev/null; then
        missing+=("git")
    fi

    if [ ${#missing[@]} -ne 0 ]; then
        log_error "Missing prerequisites: ${missing[*]}"
        log_info "Please install the missing tools and try again"
        exit 1
    fi

    log_success "All prerequisites met"
}

# Create environment file
setup_environment() {
    log_info "Setting up environment..."

    cd "$PROJECT_ROOT"

    if [ -f .env ]; then
        log_warn ".env file already exists"
        read -p "Overwrite? (y/N): " confirm
        if [ "$confirm" != "y" ]; then
            log_info "Keeping existing .env"
            return
        fi
    fi

    # Generate random secrets
    local jwt_secret=$(openssl rand -hex 32 2>/dev/null || head /dev/urandom | tr -dc A-Za-z0-9 | head -c 64)
    local postgres_password=$(openssl rand -hex 16 2>/dev/null || head /dev/urandom | tr -dc A-Za-z0-9 | head -c 32)

    cat > .env << EOF
# Agentic Trader Platform - Environment Configuration
# Generated: $(date)

# =============================================================================
# CORE SETTINGS
# =============================================================================
API_PORT=8099
API_HOST=0.0.0.0
LOG_LEVEL=INFO

# Trading Mode: 'paper' for simulation, 'live' for real trading
TRADING_MODE=paper

# =============================================================================
# SECURITY (KEEP SECRET!)
# =============================================================================
JWT_SECRET_KEY=$jwt_secret
POSTGRES_PASSWORD=$postgres_password

# =============================================================================
# DATABASE
# =============================================================================
POSTGRES_USER=trader
POSTGRES_DB=trading_db
POSTGRES_PORT=5454
DATABASE_URL=postgresql+asyncpg://trader:$postgres_password@localhost:5454/trading_db

# =============================================================================
# REDIS
# =============================================================================
REDIS_PORT=6399
REDIS_URL=redis://localhost:6399/0

# =============================================================================
# FRONTEND
# =============================================================================
FRONTEND_DEV_PORT=5199
VITE_API_URL=http://localhost:8099
VITE_WS_URL=ws://localhost:8099/ws
VITE_DEMO_MODE=true

# =============================================================================
# EXTERNAL APIs (Optional - only needed for live trading)
# =============================================================================
# BITVAVO_API_KEY=your_bitvavo_api_key
# BITVAVO_API_SECRET=your_bitvavo_api_secret

# =============================================================================
# LLM CONFIGURATION
# =============================================================================
LLM_PROVIDER=deepseek
# DEEPSEEK_API_KEY=your_deepseek_key
# OPENAI_API_KEY=your_openai_key

# =============================================================================
# AUTH0 (Optional - for production auth)
# =============================================================================
AUTH_DISABLED=true
# AUTH0_DOMAIN=your-domain.auth0.com
# AUTH0_CLIENT_ID=your_client_id
# AUTH0_CLIENT_SECRET=your_client_secret
EOF

    log_success "Environment file created: .env"
    log_warn "Please review and update the configuration as needed"
}

# Setup directories
setup_directories() {
    log_info "Creating directories..."

    mkdir -p "$PROJECT_ROOT/data"
    mkdir -p "$PROJECT_ROOT/logs"
    mkdir -p "$PROJECT_ROOT/backups"
    mkdir -p "$PROJECT_ROOT/tmp"

    log_success "Directories created"
}

# Pull and build images
build_images() {
    log_info "Building Docker images..."

    cd "$PROJECT_ROOT"

    docker-compose -f docker/docker-compose.yml pull
    docker-compose -f docker/docker-compose.yml build

    log_success "Images built"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."

    cd "$PROJECT_ROOT"

    # Start just the database
    docker-compose -f docker/docker-compose.yml up -d db redis

    # Wait for database
    log_info "Waiting for database to be ready..."
    sleep 10

    # Run migrations
    docker-compose -f docker/docker-compose.yml run --rm api alembic upgrade head || {
        log_warn "Migrations may have failed, continuing anyway..."
    }

    log_success "Migrations complete"
}

# Start services
start_services() {
    log_info "Starting services..."

    cd "$PROJECT_ROOT"
    docker-compose -f docker/docker-compose.yml up -d

    log_success "Services started"
}

# Wait for health
wait_for_health() {
    log_info "Waiting for services to be healthy..."

    local retries=30
    local count=0

    while [ $count -lt $retries ]; do
        if curl -sf http://localhost:8099/api/v1/health > /dev/null 2>&1; then
            log_success "All services are healthy!"
            return 0
        fi

        count=$((count + 1))
        echo -n "."
        sleep 2
    done

    echo ""
    log_error "Services did not become healthy in time"
    return 1
}

# Print success message
print_success() {
    echo ""
    echo "=========================================="
    echo -e "${GREEN}Setup Complete!${NC}"
    echo "=========================================="
    echo ""
    echo "Services are running:"
    echo "  API:      http://localhost:8099"
    echo "  Frontend: http://localhost:5199"
    echo "  API Docs: http://localhost:8099/docs"
    echo ""
    echo "Useful commands:"
    echo "  make logs       - View logs"
    echo "  make status     - Check status"
    echo "  make stop       - Stop services"
    echo "  make restart    - Restart services"
    echo ""
    echo "Next steps:"
    echo "  1. Open http://localhost:5199 in your browser"
    echo "  2. Configure your API keys in .env for live trading"
    echo "  3. Run 'make test' to verify everything works"
    echo ""
}

# Main setup
main() {
    echo "=========================================="
    echo "Agentic Trader Platform - Setup"
    echo "=========================================="
    echo ""

    check_prerequisites
    setup_environment
    setup_directories
    build_images
    run_migrations
    start_services

    if wait_for_health; then
        print_success
    else
        log_warn "Setup completed but health check failed"
        log_info "Check logs with: make logs"
    fi
}

# Run main
main "$@"
