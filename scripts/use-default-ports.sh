#!/bin/bash
# =============================================================================
# RESTORE DEFAULT PORTS
# =============================================================================

echo "========================================"
echo "  RESTORING DEFAULT PORTS"
echo "========================================"
echo ""

# Check if backup exists
if [ -f docker-compose.override.yml.backup ]; then
    cp docker-compose.override.yml.backup docker-compose.override.yml
    rm docker-compose.override.yml.backup
    echo "Restored original port configuration."
else
    # Recreate default override
    cat > docker-compose.override.yml << 'EOF'
version: '3.8'

services:
  api-server:
    build:
      target: development
    volumes:
      - ./backend:/app/backend:cached
      - ./scripts:/app/scripts:cached
      - ./data:/app/data:cached
      - backend_venv:/opt/venv
    environment:
      - ENVIRONMENT=development
      - DEBUG=true
      - LOG_LEVEL=DEBUG
      - ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:5173","http://127.0.0.1:5173","http://frontend:5173"]
      - CORS_ORIGINS=["http://localhost:3000","http://localhost:5173","http://127.0.0.1:5173"]
    command: uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir /app/backend
    healthcheck:
      disable: false

  frontend:
    build:
      dockerfile: ../infrastructure/docker/Dockerfile.frontend
    environment:
      - NODE_ENV=development
      - VITE_API_URL=http://localhost:8000
      - VITE_WS_URL=ws://localhost:8000/ws
      - CHOKIDAR_USEPOLLING=true
    volumes:
      - ./frontend:/app:cached
      - frontend_node_modules:/app/node_modules
    command: sh -c "npm install && npm run dev -- --host 0.0.0.0 --port 5173"

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=trader
      - POSTGRES_PASSWORD=trading_secure
      - POSTGRES_DB=trading_db
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data
    healthcheck:
      disable: false

  clickhouse:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G

  redpanda:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G

  chromadb:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M

  redpanda-console:
    profiles:
      - monitoring
      
  grafana:
    profiles:
      - monitoring

volumes:
  backend_venv:
  frontend_node_modules:
  postgres_dev_data:
EOF
    echo "Created default port configuration."
fi

echo ""
echo "Default ports restored:"
echo ""
echo "  Service             Port"
echo "  ------------------------"
echo "  API Server          8000"
echo "  Frontend            5173"
echo "  PostgreSQL          5456"
echo "  Redis               6380"
echo "  ClickHouse HTTP     8124"
echo "  ChromaDB            8005"
echo "  Redpanda            9094"
echo "  Prometheus          9091"
echo "  Grafana             3100"
echo ""
echo "Run 'make start' to start with default ports."
