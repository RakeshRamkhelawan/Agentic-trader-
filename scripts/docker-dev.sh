#!/bin/bash
# =============================================================================
# DOCKER DEVELOPMENT HELPER SCRIPT
# Usage: ./scripts/docker-dev.sh [command]
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if ports are in use
check_ports() {
    local ports=(8000 8001 5173 5456 6380 8124 8005 9094)
    local in_use=0
    
    for port in "${ports[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 || \
           netstat -tuln 2>/dev/null | grep -q ":$port " || \
           ss -tuln 2>/dev/null | grep -q ":$port " ; then
            ((in_use++))
        fi
    done
    
    echo $in_use
}

# Get frontend port from docker-compose.override.yml
get_frontend_port() {
    grep -A2 "frontend:" docker-compose.override.yml | grep "^.*5173" | sed 's/.*- "\([0-9]*\):5173".*/\1/' || echo "5173"
}

# Get API port from docker-compose.override.yml
get_api_port() {
    grep -A5 "api-server:" docker-compose.override.yml | grep "^.*8000" | head -1 | sed 's/.*- "\([0-9]*\):8000".*/\1/' || echo "8000"
}

# Get other ports
get_redpanda_port() {
    grep -A2 "redpanda-console:" docker-compose.override.yml | grep "^.*8080" | sed 's/.*- "\([0-9]*\):8080".*/\1/' || echo "8081"
}

get_prometheus_port() {
    grep -A2 "prometheus:" docker-compose.override.yml | grep "^.*9090" | sed 's/.*- "\([0-9]*\):9090".*/\1/' || echo "9091"
}

get_grafana_port() {
    grep -A2 "grafana:" docker-compose.override.yml | grep "^.*3000" | sed 's/.*- "\([0-9]*\):3000".*/\1/' || echo "3100"
}

# Commands
cmd_start() {
    log_info "Starting development environment..."
    
    # Check for port conflicts
    local conflicts=$(check_ports)
    if [ "$conflicts" -gt 0 ] && [ -f "docker-compose.override.yml.backup" ]; then
        log_warning "$conflicts ports are in use. Using alternative port configuration."
        log_info "To use default ports, run: bash scripts/use-default-ports.sh"
    fi
    
    docker-compose up -d
    
    # Get actual ports being used
    local frontend_port=$(get_frontend_port)
    local api_port=$(get_api_port)
    local redpanda_port=$(get_redpanda_port)
    local prometheus_port=$(get_prometheus_port)
    local grafana_port=$(get_grafana_port)
    
    log_success "Services started!"
    echo ""
    echo "📊 Services available at:"
    echo "  • Frontend: http://localhost:$frontend_port"
    echo "  • API: http://localhost:$api_port"
    echo "  • API Docs: http://localhost:$api_port/docs"
    echo "  • Redpanda Console: http://localhost:$redpanda_port"
    echo "  • Prometheus: http://localhost:$prometheus_port"
    echo "  • Grafana: http://localhost:$grafana_port"
}

cmd_stop() {
    log_info "Stopping development environment..."
    docker-compose down
    log_success "Services stopped!"
}

cmd_restart() {
    log_info "Restarting services..."
    docker-compose restart
    log_success "Services restarted!"
}

cmd_build() {
    log_info "Building Docker images..."
    docker-compose build --no-cache
    log_success "Build complete!"
}

cmd_logs() {
    log_info "Showing logs (Ctrl+C to exit)..."
    docker-compose logs -f
}

cmd_shell() {
    SERVICE=${1:-api-server}
    log_info "Opening shell in $SERVICE..."
    docker-compose exec $SERVICE /bin/bash
}

cmd_clean() {
    log_warning "This will remove all containers, volumes, and networks!"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Cleaning up..."
        docker-compose down -v --remove-orphans
        docker system prune -f
        log_success "Cleanup complete!"
    else
        log_info "Cancelled"
    fi
}

cmd_reset() {
    log_warning "This will RESET all databases and data!"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Resetting environment..."
        docker-compose down -v
        docker volume rm $(docker volume ls -q | grep agentic) 2>/dev/null || true
        cmd_start
        log_success "Environment reset!"
    else
        log_info "Cancelled"
    fi
}

cmd_status() {
    log_info "Service status:"
    docker-compose ps
}

cmd_test() {
    log_info "Running tests in container..."
    docker-compose exec api-server pytest backend/tests/ -v
}

cmd_migrate() {
    log_info "Running database migrations..."
    docker-compose exec api-server alembic upgrade head
    log_success "Migrations complete!"
}

cmd_frontend() {
    log_info "Starting frontend only..."
    docker-compose up -d frontend
    local frontend_port=$(get_frontend_port)
    log_success "Frontend started at http://localhost:$frontend_port"
}

cmd_backend() {
    log_info "Starting backend only..."
    docker-compose up -d api-server postgres redis clickhouse chromadb
    local api_port=$(get_api_port)
    log_success "Backend started at http://localhost:$api_port"
}

# Port configuration commands
cmd_alt_ports() {
    log_info "Switching to alternative ports..."
    if command -v powershell >/dev/null 2>&1; then
        powershell -ExecutionPolicy Bypass -File scripts\switch-ports.ps1 -Mode alt
    else
        bash scripts/use-alt-ports.sh
    fi
}

cmd_default_ports() {
    log_info "Switching to default ports..."
    if command -v powershell >/dev/null 2>&1; then
        powershell -ExecutionPolicy Bypass -File scripts\switch-ports.ps1 -Mode default
    else
        bash scripts/use-default-ports.sh
    fi
}

cmd_check_ports() {
    if command -v powershell >/dev/null 2>&1; then
        powershell -ExecutionPolicy Bypass -File scripts\switch-ports.ps1 -Mode check
    else
        bash scripts/use-alt-ports.sh check
    fi
}

# Main
case "${1:-start}" in
    start)
        cmd_start
        ;;
    stop)
        cmd_stop
        ;;
    restart)
        cmd_restart
        ;;
    build)
        cmd_build
        ;;
    logs)
        cmd_logs
        ;;
    shell)
        cmd_shell $2
        ;;
    clean)
        cmd_clean
        ;;
    reset)
        cmd_reset
        ;;
    status)
        cmd_status
        ;;
    test)
        cmd_test
        ;;
    migrate)
        cmd_migrate
        ;;
    frontend)
        cmd_frontend
        ;;
    backend)
        cmd_backend
        ;;
    alt-ports)
        cmd_alt_ports
        ;;
    default-ports)
        cmd_default_ports
        ;;
    check-ports)
        cmd_check_ports
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|build|logs|shell|clean|reset|status|test|migrate|frontend|backend|alt-ports|default-ports|check-ports}"
        echo ""
        echo "Commands:"
        echo "  start          - Start all services (default)"
        echo "  stop           - Stop all services"
        echo "  restart        - Restart services"
        echo "  build          - Rebuild Docker images"
        echo "  logs           - View service logs"
        echo "  shell          - Open shell in a service (default: api-server)"
        echo "  clean          - Remove containers and prune"
        echo "  reset          - Reset all data and restart"
        echo "  status         - Show service status"
        echo "  test           - Run tests"
        echo "  migrate        - Run database migrations"
        echo "  frontend       - Start only frontend"
        echo "  backend        - Start only backend services"
        echo "  alt-ports      - Switch to alternative ports"
        echo "  default-ports  - Switch to default ports"
        echo "  check-ports    - Check port availability"
        exit 1
        ;;
esac
