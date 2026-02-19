#!/bin/bash
# =============================================================================
# SWITCH TO ALTERNATIVE PORTS
# Run this when default ports are occupied
# =============================================================================

echo "========================================"
echo "  SWITCHING TO ALTERNATIVE PORTS"
echo "========================================"
echo ""

# Backup original
cp docker-compose.override.yml docker-compose.override.yml.backup

# Copy alternative ports file
cp docker-compose.override.alt.yml docker-compose.override.yml 2>/dev/null || cat > docker-compose.override.yml << 'EOF'
version: '3.8'

services:
  api-server:
    build:
      target: development
    ports:
      - "9000:8000"
    environment:
      - ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:5173","http://localhost:6173","http://127.0.0.1:6173"]
      - CORS_ORIGINS=["http://localhost:3000","http://localhost:5173","http://localhost:6173"]

  frontend:
    ports:
      - "6173:5173"
    environment:
      - VITE_API_URL=http://localhost:9000
      - VITE_WS_URL=ws://localhost:9000/ws

  postgres:
    ports:
      - "6456:5432"

  redis:
    ports:
      - "7380:6379"

  clickhouse:
    ports:
      - "9124:8123"

  chromadb:
    ports:
      - "9005:8000"

  redpanda:
    ports:
      - "10094:9092"

  redpanda-console:
    ports:
      - "9081:8080"

  prometheus:
    ports:
      - "10091:9090"

  grafana:
    ports:
      - "4100:3000"

  federated-triad:
    ports:
      - "10001:8001"
EOF

echo "Alternative ports configured:"
echo ""
echo "  Service             Old Port    New Port"
echo "  -----------------------------------------"
echo "  API Server          8000    →   9000"
echo "  Frontend            5173    →   6173"
echo "  PostgreSQL          5456    →   6456"
echo "  Redis               6380    →   7380"
echo "  ClickHouse HTTP     8124    →   9124"
echo "  ChromaDB            8005    →   9005"
echo "  Redpanda            9094    →   10094"
echo "  Redpanda Console    8081    →   9081"
echo "  Prometheus          9091    →   10091"
echo "  Grafana             3100    →   4100"
echo "  Federated Triad     8001    →   10001"
echo ""
echo "Access your application at:"
echo "  Frontend: http://localhost:6173"
echo "  API:      http://localhost:9000"
echo "  API Docs: http://localhost:9000/docs"
echo ""
echo "Run 'make start' to start with alternative ports."
