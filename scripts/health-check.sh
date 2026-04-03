#!/bin/bash
# =============================================================================
# HEALTH CHECK SCRIPT - Agentic Trader Platform
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
API_URL="${API_URL:-http://localhost:8099}"
WS_URL="${WS_URL:-ws://localhost:8099}"
TIMEOUT=10

# Functions
log_info() {
    echo -e "${BLUE}[CHECK]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

# Check API health
check_api() {
    log_info "Checking API health..."

    if curl -sf --max-time $TIMEOUT "$API_URL/api/v1/health" > /dev/null 2>&1; then
        log_success "API is healthy"
        return 0
    else
        log_error "API is not responding"
        return 1
    fi
}

# Check API docs
check_docs() {
    log_info "Checking API documentation..."

    if curl -sf --max-time $TIMEOUT "$API_URL/docs" > /dev/null 2>&1; then
        log_success "API docs available at $API_URL/docs"
        return 0
    else
        log_warn "API docs not accessible"
        return 1
    fi
}

# Check WebSocket
check_websocket() {
    log_info "Checking WebSocket..."

    if command -v websocat > /dev/null 2>&1; then
        if timeout 5 websocat "$WS_URL/ws/paper-trading" -1 - < /dev/null > /dev/null 2>&1; then
            log_success "WebSocket is accepting connections"
            return 0
        fi
    fi

    log_warn "WebSocket check skipped (websocat not installed)"
    return 1
}

# Check database
check_database() {
    log_info "Checking database connection..."

    # Try to get database status from API
    local db_status=$(curl -sf --max-time $TIMEOUT "$API_URL/api/v1/health" 2>/dev/null | grep -o '"database":"[^"]*"' | cut -d'"' -f4)

    if [ "$db_status" == "connected" ]; then
        log_success "Database is connected"
        return 0
    else
        log_warn "Database status: ${db_status:-unknown}"
        return 1
    fi
}

# Check Redis
check_redis() {
    log_info "Checking Redis connection..."

    # Check if we can connect via docker
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        log_success "Redis is responding"
        return 0
    else
        log_warn "Redis check failed"
        return 1
    fi
}

# Check frontend
check_frontend() {
    log_info "Checking frontend..."

    local FRONTEND_URL="${FRONTEND_URL:-http://localhost:5199}"

    if curl -sf --max-time $TIMEOUT "$FRONTEND_URL" > /dev/null 2>&1; then
        log_success "Frontend is accessible"
        return 0
    else
        log_warn "Frontend not accessible at $FRONTEND_URL"
        return 1
    fi
}

# Check Docker containers
check_containers() {
    log_info "Checking Docker containers..."

    local failed=0

    for container in agentic_trader_api agentic_trader_frontend agentic_trader_db agentic_trader_redis; do
        if docker ps --format "{{.Names}}" | grep -q "^${container}$"; then
            local status=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "unknown")
            if [ "$status" == "healthy" ]; then
                log_success "$container is healthy"
            else
                log_warn "$container status: $status"
                failed=1
            fi
        else
            log_error "$container is not running"
            failed=1
        fi
    done

    return $failed
}

# Main health check
main() {
    echo "=========================================="
    echo "Agentic Trader - Health Check"
    echo "=========================================="
    echo ""

    local failed=0

    # Run all checks
    check_api || failed=1
    check_docs || true  # Don't fail on docs
    check_database || true
    check_redis || true
    check_websocket || true  # Don't fail if websocat not installed
    check_frontend || true
    check_containers || failed=1

    echo ""
    echo "=========================================="

    if [ $failed -eq 0 ]; then
        echo -e "${GREEN}✓ All critical checks passed!${NC}"
        exit 0
    else
        echo -e "${RED}✗ Some checks failed${NC}"
        echo ""
        echo "Troubleshooting:"
        echo "  - Check logs: make logs"
        echo "  - Restart: make restart"
        echo "  - Reset: make reset"
        exit 1
    fi
}

# Show detailed status
status() {
    echo "=========================================="
    echo "Agentic Trader - Detailed Status"
    echo "=========================================="
    echo ""

    echo "Docker Containers:"
    echo "------------------"
    docker-compose ps

    echo ""
    echo "API Health:"
    echo "-----------"
    curl -s "$API_URL/api/v1/health" 2>/dev/null | jq . || echo "API not responding"

    echo ""
    echo "Resource Usage:"
    echo "---------------"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
}

# Handle arguments
case "${1:-check}" in
    check)
        main
        ;;
    status)
        status
        ;;
    watch)
        while true; do
            clear
            status
            sleep 5
        done
        ;;
    *)
        echo "Usage: $0 [check|status|watch]"
        exit 1
        ;;
esac
