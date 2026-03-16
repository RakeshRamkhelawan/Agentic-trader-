# =============================================================================
# AGENTIC TRADER - MAKEFILE
# Convenient shortcuts for Docker operations
# =============================================================================

.PHONY: help start stop restart build logs clean reset test migrate dev prod format format-check lint security-check

# Default target
.DEFAULT_GOAL := help

# Colors
BLUE := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
NC := \033[0m

help: ## Show this help message
	@echo "$(BLUE)Agentic Trader Platform - Docker Commands$(NC)"
	@echo "=========================================="
	@echo ""
	@echo "$(GREEN)Development Commands:$(NC)"
	@echo "  make start     - Start all services"
	@echo "  make stop      - Stop all services"
	@echo "  make restart   - Restart services"
	@echo "  make build     - Build Docker images"
	@echo "  make logs      - View service logs"
	@echo "  make shell     - Open shell in backend"
	@echo "  make test      - Run tests"
	@echo "  make migrate   - Run database migrations"
	@echo ""
	@echo "$(GREEN)Service-Specific Commands:$(NC)"
	@echo "  make frontend  - Start only frontend"
	@echo "  make backend   - Start only backend + infra"
	@echo "  make ai        - Start AI/Federated services"
	@echo ""
	@echo "$(GREEN)Maintenance Commands:$(NC)"
	@echo "  make clean     - Clean up Docker resources"
	@echo "  make reset     - Reset all data (DESTRUCTIVE)"
	@echo "  make status    - Show service status"
	@echo ""
	@echo "$(YELLOW)Production Commands:$(NC)"
	@echo "  make prod      - Deploy to production"
	@echo "  make prod-stop - Stop production"
	@echo "  make backup    - Backup databases"
	@echo ""

# Development Commands
start: ## Start all services
	@./scripts/docker-dev.sh start

stop: ## Stop all services
	@./scripts/docker-dev.sh stop

restart: ## Restart services
	@./scripts/docker-dev.sh restart

build: ## Build Docker images
	@./scripts/docker-dev.sh build

logs: ## View service logs
	@./scripts/docker-dev.sh logs

shell: ## Open shell in backend container
	@./scripts/docker-dev.sh shell api-server

frontend: ## Start only frontend
	@./scripts/docker-dev.sh frontend

backend: ## Start only backend services
	@./scripts/docker-dev.sh backend

ai: ## Start AI/Federated Triad services
	@docker-compose up -d federated-triad

test: ## Run tests
	@./scripts/docker-dev.sh test

migrate: ## Run database migrations
	@./scripts/docker-dev.sh migrate

# Maintenance
clean: ## Clean up Docker resources
	@./scripts/docker-dev.sh clean

reset: ## Reset all data (DESTRUCTIVE)
	@./scripts/docker-dev.sh reset

status: ## Show service status
	@./scripts/docker-dev.sh status

# Production
prod: ## Deploy to production
	@./scripts/docker-prod.sh deploy

prod-stop: ## Stop production
	@./scripts/docker-prod.sh stop

prod-update: ## Rolling update production
	@./scripts/docker-prod.sh update

backup: ## Backup databases
	@./scripts/docker-prod.sh backup

# Utility
ps: ## Show running containers
	@docker-compose ps

images: ## Show Docker images
	@docker images | grep agentic || docker images

prune: ## Prune Docker system
	@docker system prune -f

volume-ls: ## List volumes
	@docker volume ls | grep agentic || docker volume ls

network-ls: ## List networks
	@docker network ls | grep agentic || docker network ls

# Code Quality Commands
format: ## Auto-format all Python files (black + isort)
	@echo "$(BLUE)Formatting Python code...$(NC)"
	@black backend/ --line-length=100
	@isort backend/ --profile=black --line-length=100
	@echo "$(GREEN)✓ Formatting complete$(NC)"

format-check: ## Check formatting without making changes
	@echo "$(BLUE)Checking Python formatting...$(NC)"
	@black backend/ --line-length=100 --check --diff
	@isort backend/ --profile=black --line-length=100 --check-only --diff
	@echo "$(GREEN)✓ Formatting check complete$(NC)"

lint: ## Run all linters (ruff, black check, isort check)
	@echo "$(BLUE)Running linters...$(NC)"
	@ruff check backend/ --fix --exit-non-zero-on-fix
	@black backend/ --line-length=100 --check --diff
	@isort backend/ --profile=black --line-length=100 --check-only --diff
	@echo "$(GREEN)✓ Linting complete$(NC)"

security-check: ## Run security scans (bandit + pip-audit)
	@echo "$(BLUE)Running security scans...$(NC)"
	@bandit -r backend/ --exclude backend/tests/ -f json -o bandit-report.json || true
	@pip-audit --requirement requirements/base.txt || true
	@echo "$(GREEN)✓ Security scan complete$(NC)"

quality-gate: ## Run all quality checks (format, lint, security)
	@echo "$(BLUE)Running full quality gate...$(NC)"
	@make format
	@make lint
	@make security-check
	@echo "$(GREEN)✓ All quality checks passed$(NC)"
