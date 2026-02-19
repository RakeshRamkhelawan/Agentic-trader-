#!/bin/bash
# =============================================================================
# AGENTIC TRADER - BACKEND ENTRYPOINT
# Handles database migrations and startup
# =============================================================================

set -e

echo "🚀 Starting Agentic Trader Backend..."

# Wait for database to be ready
echo "⏳ Waiting for PostgreSQL..."
while ! curl -f http://postgres:5432 > /dev/null 2>&1; do
    sleep 1
done
echo "✅ PostgreSQL is ready"

# Wait for Redis
echo "⏳ Waiting for Redis..."
while ! redis-cli -h redis ping > /dev/null 2>&1; do
    sleep 1
done
echo "✅ Redis is ready"

# Run database migrations
echo "🔄 Running database migrations..."
alembic upgrade head || echo "⚠️  Migration failed, continuing anyway..."

# Create directories if they don't exist
mkdir -p /app/data /app/logs

# Execute the main command
echo "✨ Starting server..."
exec "$@"
