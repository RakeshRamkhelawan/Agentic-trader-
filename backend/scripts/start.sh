#!/bin/bash
set -e

echo "📦 Running Database Migrations..."
alembic upgrade head

echo "🌱 Seeding Default Users..."
python -m backend.scripts.seed_users

echo "🚀 Starting Application: $@"
exec "$@"
