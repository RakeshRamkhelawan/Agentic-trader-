#!/bin/bash
# =============================================================================
# DOCKER PRODUCTION DEPLOYMENT SCRIPT
# Usage: ./scripts/docker-prod.sh [command]
# =============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Load environment variables
if [ -f .env.prod ]; then
    export $(cat .env.prod | grep -v '^#' | xargs)
fi

cmd_deploy() {
    log_info "Deploying to production..."
    
    # Build images
    log_info "Building production images..."
    docker-compose -f docker-compose.prod.yml build
    
    # Deploy
    log_info "Starting production services..."
    docker-compose -f docker-compose.prod.yml up -d
    
    log_success "Production deployment complete!"
}

cmd_stop() {
    log_info "Stopping production services..."
    docker-compose -f docker-compose.prod.yml down
    log_success "Production services stopped!"
}

cmd_update() {
    log_info "Updating production deployment..."
    
    # Pull latest images
    docker-compose -f docker-compose.prod.yml pull
    
    # Rolling update
    docker-compose -f docker-compose.prod.yml up -d --no-deps --scale api-server=2 api-server
    docker-compose -f docker-compose.prod.yml up -d --no-deps --scale api-server=1 api-server
    
    log_success "Update complete!"
}

cmd_backup() {
    BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p $BACKUP_DIR
    
    log_info "Creating backup at $BACKUP_DIR..."
    
    # Backup PostgreSQL
    docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U trader trading_db > $BACKUP_DIR/postgres.sql
    
    # Backup Redis
    docker-compose -f docker-compose.prod.yml exec -T redis redis-cli BGSAVE
    docker cp $(docker-compose -f docker-compose.prod.yml ps -q redis):/data/dump.rdb $BACKUP_DIR/redis.rdb
    
    # Backup ClickHouse
    docker-compose -f docker-compose.prod.yml exec -T clickhouse clickhouse-client --query="BACKUP DATABASE trading_db TO File('/tmp/backup.zip')"
    docker cp $(docker-compose -f docker-compose.prod.yml ps -q clickhouse):/tmp/backup.zip $BACKUP_DIR/clickhouse.zip
    
    log_success "Backup complete: $BACKUP_DIR"
}

cmd_restore() {
    BACKUP_DIR=$1
    
    if [ -z "$BACKUP_DIR" ]; then
        log_error "Please specify backup directory: ./scripts/docker-prod.sh restore <backup-dir>"
        exit 1
    fi
    
    log_warning "This will RESTORE database from $BACKUP_DIR"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Restoring from backup..."
        
        # Restore PostgreSQL
        docker-compose -f docker-compose.prod.yml exec -T postgres psql -U trader trading_db < $BACKUP_DIR/postgres.sql
        
        log_success "Restore complete!"
    fi
}

cmd_logs() {
    docker-compose -f docker-compose.prod.yml logs -f
}

cmd_status() {
    docker-compose -f docker-compose.prod.yml ps
}

cmd_health() {
    log_info "Checking service health..."
    
    # Check API health
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log_success "API is healthy"
    else
        log_error "API is not responding"
    fi
    
    # Check frontend
    if curl -f http://localhost > /dev/null 2>&1; then
        log_success "Frontend is healthy"
    else
        log_error "Frontend is not responding"
    fi
}

# Main
case "${1:-deploy}" in
    deploy)
        cmd_deploy
        ;;
    stop)
        cmd_stop
        ;;
    update)
        cmd_update
        ;;
    backup)
        cmd_backup
        ;;
    restore)
        cmd_restore $2
        ;;
    logs)
        cmd_logs
        ;;
    status)
        cmd_status
        ;;
    health)
        cmd_health
        ;;
    *)
        echo "Usage: $0 {deploy|stop|update|backup|restore|logs|status|health}"
        echo ""
        echo "Commands:"
        echo "  deploy    - Deploy to production"
        echo "  stop      - Stop production services"
        echo "  update    - Rolling update of services"
        echo "  backup    - Backup all databases"
        echo "  restore   - Restore from backup"
        echo "  logs      - View production logs"
        echo "  status    - Show service status"
        echo "  health    - Check service health"
        exit 1
        ;;
esac
