#!/bin/bash
# =============================================================================
# DEPLOYMENT SCRIPT - Agentic Trader Platform
# Supports: local, staging, production
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default values
ENVIRONMENT="${1:-local}"
ACTION="${2:-deploy}"
VERSION="${3:-latest}"

# Functions
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

# Show usage
usage() {
    echo "Usage: $0 [environment] [action] [version]"
    echo ""
    echo "Environments:"
    echo "  local       - Deploy locally with docker-compose"
    echo "  staging     - Deploy to staging server"
    echo "  production  - Deploy to production server"
    echo ""
    echo "Actions:"
    echo "  deploy      - Deploy the application (default)"
    echo "  rollback    - Rollback to previous version"
    echo "  stop        - Stop all services"
    echo "  logs        - View logs"
    echo "  status      - Check service status"
    echo ""
    echo "Examples:"
    echo "  $0 local deploy"
    echo "  $0 staging deploy abc123"
    echo "  $0 production rollback"
    echo "  $0 local logs"
}

# Local deployment
deploy_local() {
    log_info "Deploying locally..."

    cd "$PROJECT_ROOT"

    # Check if .env exists
    if [ ! -f .env ]; then
        log_warn ".env file not found, creating from example..."
        cp .env.example .env
        log_warn "Please update .env with your configuration!"
    fi

    # Build and start
    docker-compose -f docker/docker-compose.yml down
    docker-compose -f docker/docker-compose.yml up -d --build

    # Wait for health
    log_info "Waiting for services to be healthy..."
    sleep 10

    # Health check
    if curl -f http://localhost:8099/api/v1/health > /dev/null 2>&1; then
        log_success "Local deployment complete!"
        echo ""
        echo "Services:"
        echo "  API:      http://localhost:8099"
        echo "  Frontend: http://localhost:5199"
        echo "  Docs:     http://localhost:8099/docs"
    else
        log_error "Health check failed. Check logs with: docker-compose logs"
        exit 1
    fi
}

# Staging deployment
deploy_staging() {
    log_info "Deploying to STAGING..."

    # Check required secrets
    if [ -z "$STAGING_HOST" ] || [ -z "$STAGING_USER" ]; then
        log_error "STAGING_HOST and STAGING_USER must be set"
        exit 1
    fi

    # Trigger GitHub Action
    log_info "Triggering GitHub Actions workflow..."
    gh workflow run deploy.yml -f environment=staging -f version="$VERSION"

    log_success "Staging deployment triggered!"
    log_info "Check progress at: https://github.com/$(gh repo view --json nameWithOwner -q .nameWithOwner)/actions"
}

# Production deployment
deploy_production() {
    log_info "Deploying to PRODUCTION..."

    # Safety checks
    if [ "$VERSION" == "latest" ]; then
        log_error "Production requires specific version (git SHA)"
        exit 1
    fi

    # Confirm deployment
    echo ""
    log_warn "⚠️  PRODUCTION DEPLOYMENT"
    log_warn "Version: $VERSION"
    echo ""
    read -p "Are you sure? Type 'yes' to continue: " confirm

    if [ "$confirm" != "yes" ]; then
        log_info "Deployment cancelled"
        exit 0
    fi

    # Trigger GitHub Action
    log_info "Triggering production deployment..."
    gh workflow run deploy.yml -f environment=production -f version="$VERSION"

    log_success "Production deployment triggered!"
    log_info "This requires manual approval in GitHub Environments"
}

# Rollback
rollback() {
    log_info "Rolling back $ENVIRONMENT..."

    case $ENVIRONMENT in
        local)
            cd "$PROJECT_ROOT"
            docker-compose -f docker/docker-compose.yml down
            docker-compose -f docker/docker-compose.yml up -d
            log_success "Rollback complete"
            ;;
        staging|production)
            log_info "Rollback for $ENVIRONMENT must be done manually"
            log_info "SSH to server and run: docker-compose down && docker-compose up -d"
            ;;
    esac
}

# Stop services
stop_services() {
    log_info "Stopping services on $ENVIRONMENT..."

    case $ENVIRONMENT in
        local)
            cd "$PROJECT_ROOT"
            docker-compose -f docker/docker-compose.yml down
            log_success "Services stopped"
            ;;
        staging|production)
            log_info "Stopping remote services..."
            ssh "${STAGING_USER}@${STAGING_HOST}" "cd ~/agentic-trader && docker-compose down" || true
            log_success "Services stopped"
            ;;
    esac
}

# View logs
view_logs() {
    case $ENVIRONMENT in
        local)
            cd "$PROJECT_ROOT"
            docker-compose -f docker/docker-compose.yml logs -f
            ;;
        staging|production)
            ssh "${STAGING_USER}@${STAGING_HOST}" "cd ~/agentic-trader && docker-compose logs -f"
            ;;
    esac
}

# Check status
check_status() {
    case $ENVIRONMENT in
        local)
            cd "$PROJECT_ROOT"
            docker-compose -f docker/docker-compose.yml ps
            echo ""
            curl -s http://localhost:8099/api/v1/health | jq . || echo "API not responding"
            ;;
        staging|production)
            ssh "${STAGING_USER}@${STAGING_HOST}" "cd ~/agentic-trader && docker-compose ps"
            ;;
    esac
}

# Main
main() {
    echo "=========================================="
    echo "Agentic Trader - Deployment Script"
    echo "Environment: $ENVIRONMENT"
    echo "Action: $ACTION"
    echo "=========================================="
    echo ""

    case $ACTION in
        deploy)
            case $ENVIRONMENT in
                local) deploy_local ;;
                staging) deploy_staging ;;
                production) deploy_production ;;
                *) usage; exit 1 ;;
            esac
            ;;
        rollback)
            rollback
            ;;
        stop)
            stop_services
            ;;
        logs)
            view_logs
            ;;
        status)
            check_status
            ;;
        *)
            usage
            exit 1
            ;;
    esac
}

main "$@"
