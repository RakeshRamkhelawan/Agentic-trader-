#!/bin/bash
#
# Docker startup script for Agentic Trader Platform
#
# Usage:
#   ./scripts/docker-start.sh          # Start all services
#   ./scripts/docker-start.sh dev      # Start with hot reload
#   ./scripts/docker-start.sh prod     # Start production mode
#   ./scripts/docker-start.sh stop     # Stop all services
#   ./scripts/docker-start.sh logs     # View logs

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    print_status "Docker and Docker Compose are installed"
}

# Create necessary directories
setup_directories() {
    print_status "Creating necessary directories..."
    mkdir -p logs data cache redis_data nginx/logs nginx/ssl

    # Set permissions
    chmod 755 logs data cache redis_data

    print_status "Directories created"
}

# Start development mode
start_dev() {
    print_status "Starting in DEVELOPMENT mode with hot reload..."

    check_docker
    setup_directories

    # Copy .env.example if .env doesn't exist
    if [ ! -f .env ]; then
        print_warning ".env file not found, copying from .env.example"
        cp .env.example .env
    fi

    docker-compose up --build -d

    print_status "Services started!"
    echo ""
    echo "API Documentation: http://localhost:8000/docs"
    echo "Health Check:      http://localhost:8000/api/v1/health"
    echo "Redis:             redis://localhost:6379"
    echo ""
    echo "View logs: docker-compose logs -f api"
}

# Start production mode
start_prod() {
    print_status "Starting in PRODUCTION mode..."

    check_docker
    setup_directories

    # Check if .env exists
    if [ ! -f .env ]; then
        print_error ".env file not found! Please create it from .env.example"
        print_error "  cp .env.example .env"
        print_error "Then edit .env with your production settings"
        exit 1
    fi

    # Check for SECRET_KEY
    if ! grep -q "SECRET_KEY=your" .env && ! grep -q "^SECRET_KEY=" .env; then
        print_warning "SECRET_KEY not set in .env. Generating one..."
        SECRET_KEY=$(openssl rand -hex 32 2>/dev/null || head -c 64 /dev/urandom | xxd -p | tr -d '\n')
        echo "SECRET_KEY=$SECRET_KEY" >> .env
        print_status "Generated SECRET_KEY and added to .env"
    fi

    docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d

    print_status "Production services started!"
    echo ""
    echo "API:      https://your-domain.com"
    echo "Health:   https://your-domain.com/api/v1/health"
    echo ""
    echo "View logs: docker-compose logs -f api"
}

# Stop all services
stop_services() {
    print_status "Stopping all services..."
    docker-compose down
    print_status "Services stopped"
}

# View logs
view_logs() {
    docker-compose logs -f api
}

# Run database migrations (if needed)
run_migrations() {
    print_status "Running database migrations..."
    docker-compose exec api alembic upgrade head
}

# Main command handler
case "${1:-dev}" in
    dev|development)
        start_dev
        ;;
    prod|production)
        start_prod
        ;;
    stop|down)
        stop_services
        ;;
    logs)
        view_logs
        ;;
    migrate)
        run_migrations
        ;;
    restart)
        stop_services
        start_dev
        ;;
    build)
        print_status "Building Docker images..."
        docker-compose build
        ;;
    clean)
        print_status "Cleaning up Docker resources..."
        docker-compose down -v --remove-orphans
        docker system prune -f
        print_status "Cleanup complete"
        ;;
    *)
        echo "Usage: $0 {dev|prod|stop|logs|restart|build|clean|migrate}"
        echo ""
        echo "Commands:"
        echo "  dev       Start in development mode (default)"
        echo "  prod      Start in production mode"
        echo "  stop      Stop all services"
        echo "  logs      View API logs"
        echo "  restart   Restart services"
        echo "  build     Build Docker images"
        echo "  clean     Clean up Docker resources"
        echo "  migrate   Run database migrations"
        exit 1
        ;;
esac
