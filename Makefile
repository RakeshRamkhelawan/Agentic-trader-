.PHONY: help install up down logs test lint format clean build health status restart shell db-shell redis-cli

COMPOSE_FILE := docker-compose.yml
COMPOSE_CMD := docker compose -f $(COMPOSE_FILE)
PYTHON := python
BACKEND_SERVICE := backend
BACKEND_DIR := backend

help:
	@echo "Samkhya Yoga Agentic Trader - DevEx Commands"
	@echo ""
	@echo "Environment Management:"
	@echo "  make install          Install Python dependencies locally"
	@echo "  make up              Start all services in detached mode"
	@echo "  make down            Stop and remove all containers"
	@echo "  make restart         Restart all services"
	@echo "  make build           Rebuild Docker images"
	@echo ""
	@echo "Development:"
	@echo "  make logs            Tail logs from all services"
	@echo "  make logs-backend    Tail logs from backend only"
	@echo "  make logs-redis      Tail logs from Redis"
	@echo "  make shell           Open shell in backend container"
	@echo "  make db-shell        Open PostgreSQL shell"
	@echo "  make redis-cli       Open Redis CLI"
	@echo ""
	@echo "Testing & Quality:"
	@echo "  make test            Run all tests"
	@echo "  make test-unit       Run unit tests only"
	@echo "  make test-integration Run integration tests only"
	@echo "  make test-e2e        Run end-to-end tests"
	@echo "  make lint            Run linters (black, isort, ruff, mypy)"
	@echo "  make format          Auto-format code with black and isort"
	@echo "  make coverage        Generate test coverage report"
	@echo ""
	@echo "Health & Monitoring:"
	@echo "  make health          Run deep health check"
	@echo "  make status          Show service status"
	@echo "  make verify-infra    Verify infrastructure connectivity"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean           Remove Python cache and test artifacts"
	@echo "  make clean-docker    Remove all containers, volumes, and images"
	@echo "  make clean-all       Clean everything (Python + Docker)"

install:
	@echo "Installing Python dependencies..."
	$(PYTHON) -m pip install --upgrade pip
	@if exist requirements\base.txt pip install -r requirements\base.txt
	@if exist requirements\dev.txt pip install -r requirements\dev.txt
	@if exist requirements\test.txt pip install -r requirements\test.txt
	@echo "Dependencies installed successfully"

up:
	@echo "Starting all services..."
	$(COMPOSE_CMD) up -d
	@echo "Waiting for services to be healthy..."
	@timeout /t 15 /nobreak >nul
	@$(MAKE) status

down:
	@echo "Stopping all services..."
	$(COMPOSE_CMD) down

restart:
	@echo "Restarting all services..."
	$(COMPOSE_CMD) restart
	@timeout /t 10 /nobreak >nul
	@$(MAKE) status

build:
	@echo "Building Docker images..."
	$(COMPOSE_CMD) build --parallel
	@echo "Build completed successfully"

logs:
	@echo "Tailing logs from all services (Ctrl+C to stop)..."
	$(COMPOSE_CMD) logs -f --tail=100

logs-backend:
	@echo "Tailing backend logs..."
	$(COMPOSE_CMD) logs -f --tail=100 $(BACKEND_SERVICE)

logs-redis:
	@echo "Tailing Redis logs..."
	$(COMPOSE_CMD) logs -f --tail=100 redis

logs-postgres:
	@echo "Tailing PostgreSQL logs..."
	$(COMPOSE_CMD) logs -f --tail=100 postgres

shell:
	@echo "Opening shell in backend container..."
	$(COMPOSE_CMD) exec $(BACKEND_SERVICE) /bin/bash

db-shell:
	@echo "Opening PostgreSQL shell..."
	$(COMPOSE_CMD) exec postgres psql -U trader -d trading_db

redis-cli:
	@echo "Opening Redis CLI..."
	$(COMPOSE_CMD) exec redis redis-cli

test:
	@echo "Running all tests..."
	$(PYTHON) -m pytest $(BACKEND_DIR)/tests/ -v --maxfail=5

test-unit:
	@echo "Running unit tests..."
	$(PYTHON) -m pytest $(BACKEND_DIR)/tests/unit/ -v --cov=$(BACKEND_DIR) --cov-report=term-missing

test-integration:
	@echo "Running integration tests..."
	$(PYTHON) -m pytest $(BACKEND_DIR)/tests/integration/ -v --timeout=300

test-e2e:
	@echo "Running end-to-end tests..."
	$(COMPOSE_CMD) exec -T $(BACKEND_SERVICE) python -m pytest backend/tests/e2e/ -v

coverage:
	@echo "Generating coverage report..."
	$(PYTHON) -m pytest $(BACKEND_DIR)/tests/ --cov=$(BACKEND_DIR) --cov-report=html --cov-report=term
	@echo "Coverage report generated in htmlcov/index.html"

lint:
	@echo "Running linters..."
	@echo "→ Black (formatting check)..."
	black --check $(BACKEND_DIR)/
	@echo "→ Isort (import check)..."
	isort --check-only $(BACKEND_DIR)/
	@echo "→ Ruff (linting)..."
	ruff check $(BACKEND_DIR)/
	@echo "→ MyPy (type checking)..."
	mypy $(BACKEND_DIR)/ --ignore-missing-imports
	@echo "All linters passed!"

format:
	@echo "Auto-formatting code..."
	black $(BACKEND_DIR)/
	isort $(BACKEND_DIR)/
	@echo "Code formatted successfully"

health:
	@echo "Running deep health check..."
	$(PYTHON) -m backend.scripts.ops.health_check

status:
	@echo "Service Status:"
	@$(COMPOSE_CMD) ps

verify-infra:
	@echo "Verifying infrastructure connectivity..."
	$(PYTHON) -m backend.scripts.ops.health_check --verbose

clean:
	@echo "Cleaning Python cache and test artifacts..."
	@if exist $(BACKEND_DIR)\__pycache__ rd /s /q $(BACKEND_DIR)\__pycache__
	@if exist .pytest_cache rd /s /q .pytest_cache
	@if exist .coverage del .coverage
	@if exist htmlcov rd /s /q htmlcov
	@if exist .mypy_cache rd /s /q .mypy_cache
	@if exist .ruff_cache rd /s /q .ruff_cache
	@for /r %i in (*.pyc) do @del "%i"
	@for /r %i in (*.pyo) do @del "%i"
	@echo "Cleanup completed"

clean-docker:
	@echo "Removing Docker containers and volumes..."
	$(COMPOSE_CMD) down -v --remove-orphans
	@echo "Docker cleanup completed"

clean-all: clean clean-docker
	@echo "Full cleanup completed"

ps:
	@$(COMPOSE_CMD) ps -a

top:
	@$(COMPOSE_CMD) top