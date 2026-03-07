#!/bin/bash
# =============================================================================
# Run Database Migrations
# =============================================================================

set -e

echo "🔄 Running database migrations..."

# Change to project root
cd "$(dirname "$0")/.."

# Run migrations using alembic
python -m alembic upgrade head

echo "✅ Migrations complete!"
