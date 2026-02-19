#!/bin/bash
# =============================================================================
# PRODUCTION DEPLOYMENT VALIDATION SCRIPT
# Validates .env.prod and docker-compose.prod.yml before deployment
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env.prod"

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

# -----------------------------------------------------------------------------
# CHECK 1: .env.prod file exists
# -----------------------------------------------------------------------------
check_env_file() {
    log_info "Checking .env.prod file..."
    
    if [ ! -f "$ENV_FILE" ]; then
        log_error ".env.prod file not found!"
        log_info "Copy .env.prod.example to .env.prod and configure it:"
        log_info "  cp .env.prod.example .env.prod"
        exit 1
    fi
    
    log_success ".env.prod file exists"
}

# -----------------------------------------------------------------------------
# CHECK 2: Required variables are set
# -----------------------------------------------------------------------------
check_required_vars() {
    log_info "Checking required environment variables..."
    
    local required_vars=(
        "DB_PASSWORD"
        "CLICKHOUSE_PASSWORD"
        "GRAFANA_ADMIN_PASSWORD"
        "JWT_SECRET_KEY"
    )
    
    local missing=0
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" "$ENV_FILE" || grep -q "^${var}=CHANGE_ME" "$ENV_FILE"; then
            log_error "Missing or not configured: $var"
            missing=1
        fi
    done
    
    if [ $missing -eq 1 ]; then
        log_error "Some required variables are not configured!"
        exit 1
    fi
    
    log_success "All required variables are configured"
}

# -----------------------------------------------------------------------------
# CHECK 3: No default/weak passwords
# -----------------------------------------------------------------------------
check_password_strength() {
    log_info "Checking password strength..."
    
    local weak_patterns=("password" "123" "admin" "test" "change_me" "default")
    local weak_found=0
    
    for pattern in "${weak_patterns[@]}"; do
        if grep -qi "$pattern" "$ENV_FILE"; then
            log_warning "Potential weak password detected containing: $pattern"
            weak_found=1
        fi
    done
    
    if [ $weak_found -eq 1 ]; then
        log_warning "Consider using stronger passwords"
    else
        log_success "No obvious weak passwords detected"
    fi
}

# -----------------------------------------------------------------------------
# CHECK 4: Docker Compose syntax validation
# -----------------------------------------------------------------------------
check_compose_syntax() {
    log_info "Validating Docker Compose syntax..."
    
    if ! docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" config > /dev/null 2>&1; then
        log_error "Docker Compose syntax validation failed!"
        log_info "Run the following to see details:"
        log_info "  docker compose -f $COMPOSE_FILE --env-file $ENV_FILE config"
        exit 1
    fi
    
    log_success "Docker Compose syntax is valid"
}

# -----------------------------------------------------------------------------
# CHECK 5: Environment variable substitution
# -----------------------------------------------------------------------------
check_env_substitution() {
    log_info "Checking environment variable substitution..."
    
    # Export env vars for docker compose to use
    export $(grep -v '^#' "$ENV_FILE" | xargs) 2>/dev/null || true
    
    if ! docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" config > /dev/null 2>&1; then
        log_error "Environment variable substitution failed!"
        log_info "Check that all referenced variables are defined in $ENV_FILE"
        exit 1
    fi
    
    log_success "Environment variable substitution successful"
}

# -----------------------------------------------------------------------------
# CHECK 6: No localhost in production URLs (where inappropriate)
# -----------------------------------------------------------------------------
check_no_localhost() {
    log_info "Checking for localhost references in production config..."
    
    local localhost_vars=$(grep -E "(DATABASE_URL|REDIS_URL|KAFKA).*localhost" "$ENV_FILE" || true)
    
    if [ -n "$localhost_vars" ]; then
        log_warning "Found localhost references in infrastructure URLs:"
        echo "$localhost_vars"
        log_warning "In Docker Compose, use service names (postgres, redis, redpanda) instead of localhost"
    else
        log_success "No localhost references in infrastructure URLs"
    fi
}

# -----------------------------------------------------------------------------
# CHECK 7: ENV=production
# -----------------------------------------------------------------------------
check_production_env() {
    log_info "Checking ENV setting..."
    
    if grep -q 'ENV=production' "$ENV_FILE"; then
        log_success "ENV is set to production"
    else
        log_warning "ENV is not set to production"
        log_info "Add to $ENV_FILE: ENV=production"
    fi
}

# -----------------------------------------------------------------------------
# CHECK 8: DEBUG=False
# -----------------------------------------------------------------------------
check_debug_disabled() {
    log_info "Checking DEBUG setting..."
    
    if grep -q 'DEBUG=False' "$ENV_FILE"; then
        log_success "DEBUG is disabled"
    else
        log_warning "DEBUG may be enabled in production"
        log_info "Add to $ENV_FILE: DEBUG=False"
    fi
}

# -----------------------------------------------------------------------------
# CHECK 9: .env.prod is in .gitignore
# -----------------------------------------------------------------------------
check_gitignore() {
    log_info "Checking .gitignore..."
    
    if grep -q ".env.prod" .gitignore; then
        log_success ".env.prod is in .gitignore"
    else
        log_error ".env.prod is NOT in .gitignore!"
        log_info "Add the following to .gitignore:"
        log_info "  .env.prod"
        exit 1
    fi
}

# -----------------------------------------------------------------------------
# CHECK 10: Required files exist
# -----------------------------------------------------------------------------
check_required_files() {
    log_info "Checking required files..."
    
    local required_files=(
        "infrastructure/docker/Dockerfile.backend"
        "infrastructure/docker/Dockerfile.frontend.prod"
    )
    
    local missing=0
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            log_error "Required file not found: $file"
            missing=1
        fi
    done
    
    if [ $missing -eq 1 ]; then
        exit 1
    fi
    
    log_success "All required files exist"
}

# -----------------------------------------------------------------------------
# PRINT CONFIGURATION SUMMARY
# -----------------------------------------------------------------------------
print_summary() {
    echo ""
    echo "========================================"
    echo "  PRODUCTION CONFIGURATION SUMMARY"
    echo "========================================"
    echo ""
    
    # Count services
    local service_count=$(docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" config --services | wc -l)
    echo "Services to deploy: $service_count"
    
    # Show images
    echo ""
    echo "Images:"
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" config | grep "image:" | sed 's/.*image: /  - /'
    
    # Show exposed ports
    echo ""
    echo "Exposed ports:"
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" config | grep -A1 "published:" | grep -v "^--$" | sed 'N;s/\n/ /' | sed 's/.*published: \([^ ]*\).*/  - \1/'
    
    echo ""
    echo "========================================"
}

# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------
main() {
    echo "========================================"
    echo "  PRODUCTION DEPLOYMENT VALIDATION"
    echo "========================================"
    echo ""
    
    check_env_file
    check_required_vars
    check_password_strength
    check_gitignore
    check_compose_syntax
    check_env_substitution
    check_no_localhost
    check_production_env
    check_debug_disabled
    check_required_files
    
    echo ""
    log_success "All validation checks passed!"
    echo ""
    
    print_summary
    
    echo ""
    echo "To deploy, run:"
    echo "  docker compose -f $COMPOSE_FILE --env-file $ENV_FILE up -d"
    echo ""
}

main "$@"
