#!/bin/bash
set -e

echo "Running Database Migrations..."
cd /app
alembic upgrade head || echo "Migrations already up to date or skipped"

echo "Seeding Default Users..."
python -m backend.scripts.seed_users

echo "Starting Application: $@"
exec "$@"
