# AGENTS.md - Agentic Trader Platform

> **Guide for AI Coding Agents**
> This document provides essential information for AI agents working on the Agentic Trader Platform. It covers the project architecture, development workflow, testing strategies, and conventions specific to this codebase.

---

## Table of Contents

1. [⚠️ Mandatory Code Quality Gates](#️-mandatory-code-quality-gates)
2. [Project Overview](#project-overview)
3. [Architecture](#architecture)
4. [Technology Stack](#technology-stack)
5. [Project Structure](#project-structure)
6. [Development Setup](#development-setup)
7. [Build and Test Commands](#build-and-test-commands)
8. [Code Style Guidelines](#code-style-guidelines)
9. [Testing Strategy](#testing-strategy)
10. [Security Considerations](#security-considerations)
11. [Common Patterns](#common-patterns)
12. [Troubleshooting](#troubleshooting)

---

## ⚠️ Mandatory Code Quality Gates

> **CRITICAL: Before ANY code is written or saved, ALL quality gates MUST pass.**

### Pre-Commit Quality Checklist

**EVERY AI agent MUST execute these checks before writing/saving code:**

| Priority | Check | Command | Must Pass |
|----------|-------|---------|-----------|
| 🔴 **CRITICAL** | Linting | `ruff check backend/` | ✅ Yes |
| 🔴 **CRITICAL** | Formatting | `black backend/ --line-length=100` | ✅ Yes |
| 🔴 **CRITICAL** | Import Sorting | `isort backend/ --profile=black` | ✅ Yes |
| 🟡 HIGH | Type Checking | `mypy backend/` | ✅ Yes |
| 🔴 **CRITICAL** | Security Scan | `bandit -r backend/` | ✅ Yes |
| 🟡 HIGH | Dependency Audit | `pip-audit` | ✅ Yes |

### Quick Commands

```bash
# Auto-format all code (RECOMMENDED - run this first)
make format

# Check formatting without changes
make format-check

# Run all linters
make lint

# Run security scans
make security-check

# Run full quality gate (format + lint + security)
make quality-gate
```

### Individual Tool Commands

```bash
# 1. Ruff - Fast Python linter
ruff check backend/ --fix --exit-non-zero-on-fix

# 2. Black - Code formatting
black backend/ --line-length=100

# 3. isort - Import sorting
isort backend/ --profile=black --line-length=100

# 4. mypy - Type checking
mypy backend/ --strict --ignore-missing-imports

# 5. Bandit - Security scanning
bandit -r backend/ --exclude backend/tests/

# 6. pip-audit - Dependency vulnerability scan
pip-audit --requirement requirements/base.txt
```

### Quality Gate Enforcement

**NEVER commit code that:**
- ❌ Fails ruff linting
- ❌ Is not formatted with black
- ❌ Has unsorted imports
- ❌ Contains security vulnerabilities (bandit)
- ❌ Uses dependencies with known CVEs (pip-audit)

**Always ensure:**
- ✅ All checks pass before `WriteFile` or `StrReplaceFile`
- ✅ Run `make format` before finalizing changes
- ✅ Run `make lint` to verify compliance
- ✅ Security scan shows no HIGH/CRITICAL issues

---

## Project Overview

The **Agentic Trader Platform** is a production-grade AI-powered trading system that combines modern financial technology with Vedic intelligence principles. Built with enterprise-grade architecture, it features a multi-agent cognitive system with ReAct reasoning patterns, advanced risk management, and real-time trade execution.

### Key Characteristics

- **Language**: English (all code comments, documentation)
- **Status**: Production Ready, 734+ tests passing, 88% code coverage
- **Architecture**: Modular, pluggable, multi-tenant SaaS
- **Philosophy**: Vedic/Consciousness-inspired cognitive architecture (Samkhya philosophy)
- **Security Score**: 88/100 (OWASP compliance)

### Core Features

- **AI Agents**: Multi-agent system with specialized roles (research, macro, valuation, risk)
- **Vedic Intelligence**: Navagraha (9 planets) astrology-based trading signals via `pyswisseph`
- **Risk Management**: VaR calculations, stress testing, Kelly criterion optimization
- **Execution**: Smart order routing, shadow portfolios, multi-exchange support (Bitvavo, Revolut)
- **Infrastructure**: ClickHouse analytics, Redis event bus, Kafka/Redpanda messaging, ChromaDB vector store
- **Observability**: OpenTelemetry tracing, Prometheus metrics, structured logging

---

## Architecture

### Layered Architecture (Samkhya-Inspired)

```
┌──────────────────────────────────────────────────────────────┐
│  LAYER 1: Eternal Soul (Cosmic Constraints)                  │
│  - Guna Balance, Intent, Universal Laws                      │
│  - Frequency: ~1 minute                                      │
├──────────────────────────────────────────────────────────────┤
│  LAYER 2: Cognitive Mind (Decision Making)                   │
│  - OODA Loop, Federated Triad Councils                       │
│  - Frequency: 50-200ms                                       │
├──────────────────────────────────────────────────────────────┤
│  LAYER 3: Reflex Body (Order Execution)                      │
│  - Smart order routing, <10ms latency                        │
│  - Frequency: <10ms                                          │
├──────────────────────────────────────────────────────────────┤
│  INFRASTRUCTURE LAYER                                        │
│  PostgreSQL • Redis • ClickHouse • ChromaDB • Redpanda       │
└──────────────────────────────────────────────────────────────┘
```

### Multi-Agent Hierarchy

```
Meta-Orchestrator (CEO)
    ├── Fund Manager Agent (Capital Allocation)
    ├── Portfolio Manager Agent (Asset Weights)
    ├── Risk Manager Agent (Circuit Breakers, VaR)
    │
    ├── Data Scout Agent (Market Data Ingestion)
    ├── Asset Discovery Agent (Anomaly Detection)
    │
    ├── Federated Triad Councils
    │   ├── Dynamic Guna Council (Trend vs Stability)
    │   ├── Mind Council (Psychology/Contrarian)
    │   └── Body Council (Liquidity/Execution)
    │
    ├── Elemental Swarm (Micro-Agents)
    │   ├── ElementalValuation
    │   ├── ElementalMacro
    │   └── ElementalRiskGuardian
    │
    └── Vedic Intelligence
        ├── VedastroSignalAgent (Planetary Cycles)
        └── Navagraha Calculations
```

### Pluggable Architecture

All major infrastructure components use adapter patterns:
- **LLM Provider**: DeepSeek (default), OpenAI, Gemini, Ollama, or custom
- **Database**: PostgreSQL 15 (primary), ClickHouse (analytics)
- **Message Broker**: Redpanda/Kafka (default), RabbitMQ compatible
- **Exchange/Broker**: Bitvavo, Revolut, or custom adapter via CCXT
- **Vector DB**: ChromaDB (default), Pinecone/Weaviate compatible

---

## Technology Stack

### Backend

| Component | Technology | Version |
|-----------|------------|---------|
| Language | Python | 3.13+ |
| Web Framework | FastAPI | 0.115.9 |
| Data Validation | Pydantic | v2 (2.12.5) |
| Settings | pydantic-settings | 2.12.0 |
| Async DB | asyncpg + SQLAlchemy | 2.0.25 |
| Migrations | Alembic | 1.13.1 |
| Cache | Redis | 7+ (redis-py 5.0.1) |
| Vector DB | ChromaDB | 0.5.0 |
| Message Broker | aiokafka | 0.13.0 (Redpanda compatible) |
| Analytics DB | ClickHouse | 24.3 (clickhouse-connect 0.10.0) |
| Trading | CCXT | 4.2.18 |
| Backtesting | Backtrader | 1.9.78.123 |
| ML | scikit-learn | 1.3.0 |
| Online ML | River | 0.23.0 |
| Vedic Astrology | pyswisseph | 2.10.3.2 |
| Auth | python-jose[cryptography] | 3.3.0 |
| HTTP Client | httpx | 0.28.1 |

### Frontend

| Component | Technology | Version |
|-----------|------------|---------|
| Framework | React | 19.2.0 |
| Language | TypeScript | 5.9.3 |
| Build Tool | Vite | 7.2.4 |
| Styling | Tailwind CSS | 3.4.19 |
| UI Components | Radix UI | Latest |
| State Management | Zustand | 5.0.11 |
| Forms | React Hook Form + Zod | 7.70.0 / 4.3.5 |
| Auth | @auth0/auth0-react | 2.15.0 |
| Charts | Recharts | 2.15.4 |
| Icons | lucide-react | 0.562.0 |

### Infrastructure

| Component | Technology | Ports |
|-----------|------------|-------|
| Containerization | Docker & Docker Compose | - |
| Database | PostgreSQL 15 + TimescaleDB | 5432 |
| Analytics DB | ClickHouse | 5000 (HTTP), 5001 (Native) |
| Cache/Event Bus | Redis 7.2 | 6379 |
| Vector DB | ChromaDB | 8100 |
| Message Broker | Redpanda (Kafka-compatible) | 6000, 6001 |
| Monitoring | Prometheus | 9090 |
| Dashboard | Grafana | 9000 |
| API Server | FastAPI/Uvicorn | 8000 |
| MCP Broker | Model Context Protocol | 8001 |
| Frontend Dev | Vite | 3000 |
| Frontend Prod | Nginx | 3080 |

---

## Project Structure

```
agentic_trader_platform/
│
├── backend/                          # Python backend (549+ modules)
│   ├── agents/                       # AI agent implementations (37+ agents)
│   │   ├── base_agent.py            # Abstract base with ReAct pattern
│   │   ├── meta_orchestrator.py     # CEO-level coordination
│   │   ├── elemental_*.py           # Elemental swarm agents
│   │   ├── sentiment_agent.py       # Sentiment analysis
│   │   └── vedastro_signal_agent.py # Vedic astrology signals
│   ├── api/                          # FastAPI endpoints
│   │   ├── main.py                  # Main app entry
│   │   ├── routers/                 # API route modules
│   │   └── websocket_endpoints.py   # Real-time WebSocket API
│   ├── core/                         # Core cognitive system
│   │   ├── config/settings.py       # Central configuration (Pydantic)
│   │   ├── conscious/               # Chitta memory, consciousness layers
│   │   ├── security/                # Auth, encryption, vault
│   │   └── telemetry/               # Metrics, tracing, logging
│   ├── councils/                     # Federated Triad Councils
│   ├── events/                       # Event bus (Redis Streams)
│   ├── exchange/                     # Exchange adapters (Bitvavo, Revolut)
│   ├── execution/                    # Trading execution layer
│   ├── governance/                   # Circuit breakers, gatekeepers
│   ├── llm/                          # LLM provider interface
│   ├── market_data/                  # Real-time market data
│   ├── mcp_broker/                   # Model Context Protocol broker
│   ├── migrations/                   # Alembic database migrations
│   ├── rag/                          # Retrieval Augmented Generation
│   ├── risk/                         # Risk management (VaR, Kelly)
│   ├── schemas/                      # Pydantic models
│   ├── services/                     # High-level services
│   ├── storage/                      # Database clients
│   ├── strategies/                   # Trading strategies
│   ├── tests/                        # Test suite
│   │   ├── unit/                     # Unit tests
│   │   ├── integration/              # Integration tests
│   │   ├── e2e/                      # End-to-end tests
│   │   └── conftest.py               # Pytest fixtures
│   └── vedastro/                     # Vedic astrology calculations
│
├── frontend/                         # React frontend
│   ├── src/
│   │   ├── components/              # React components
│   │   ├── pages/                   # Page components
│   │   ├── store/                   # Zustand state management
│   │   ├── hooks/                   # Custom React hooks
│   │   ├── lib/                     # Utility functions
│   │   └── types/                   # TypeScript type definitions
│   ├── package.json                 # NPM dependencies
│   └── vite.config.ts               # Vite configuration
│
├── docker/                          # Docker configurations
│   ├── docker-compose.yml           # Base compose
│   ├── docker-compose.prod.yml      # Production compose
│   └── Dockerfile                   # Multi-stage build
│
├── docs/                            # Documentation
│   ├── architecture/                # Architecture docs
│   ├── guides/                      # User guides
│   ├── operations/                  # Operations runbooks
│   ├── phases/                      # Phase completion reports
│   └── security/                    # Security documentation
│
├── infrastructure/                  # Infrastructure as Code
│   └── prometheus/                  # Monitoring configs
│
├── scripts/                         # Utility scripts
│   ├── docker-dev.sh                # Development Docker helper
│   └── docker-prod.sh               # Production deployment
│
├── requirements/                    # Python requirements
│   ├── base.txt                     # Production deps
│   ├── dev.txt                      # Development deps (includes test.txt)
│   └── test.txt                     # Testing deps
│
├── .github/workflows/               # CI/CD pipelines
│   ├── ci.yml                       # Main CI workflow
│   ├── cd.yml                       # Deployment workflow
│   └── release.yml                  # Release workflow
│
├── Dockerfile                       # Multi-stage Docker build
├── Makefile                         # Development shortcuts
├── alembic.ini                      # Database migration config
├── pytest.ini                      # Test configuration
├── ruff.toml                        # Ruff linter configuration
├── .pre-commit-config.yaml          # Pre-commit hooks
└── .env.example                     # Environment template
```

---

## Development Setup

### Prerequisites

- **Python**: 3.13+ (with timezone.utc support)
- **Node.js**: 18+ (for frontend)
- **Docker**: 24.0+ & Docker Compose 2.0+
- **Git**: For version control

### Quick Start

```bash
# 1. Clone repository
git clone <repository-url>
cd agentic_trader_platform

# 2. Set up environment
cp .env.example .env
# Edit .env with your configuration (see Environment Variables section)

# 3. Start infrastructure services
docker-compose -f docker/docker-compose.yml up -d postgres redis

# 4. Install Python dependencies
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements/base.txt
pip install -r requirements/dev.txt

# 5. Run database migrations
alembic upgrade head

# 6. Start backend
uvicorn backend.api.main:app --reload --port 8000

# 7. Start frontend (separate terminal)
cd frontend
npm install
npm run dev
```

### Environment Variables

Key variables in `.env`:

```env
# Core Application
API_PORT=8000
API_HOST=0.0.0.0
LOG_LEVEL=INFO

# Security (REQUIRED - No defaults!)
JWT_SECRET_KEY=your-secure-random-key-min-32-chars

# Database
DATABASE_URL=postgresql+asyncpg://trader:password@localhost:5432/trading_db

# Cache
REDIS_URL=redis://localhost:6379/0

# Analytics
CLICKHOUSE_HOST=localhost
CLICKHOUSE_HTTP_PORT=5000
CLICKHOUSE_NATIVE_PORT=5001

# LLM Provider (choose one)
LLM_PROVIDER=deepseek  # or openai, gemini, ollama
DEEPSEEK_API_KEY=your_key

# Trading Mode
TRADING_MODE=paper  # paper, live, backtest

# Auth0 (for production)
AUTH0_DOMAIN=your-domain.auth0.com
AUTH0_CLIENT_ID=your-client-id
AUTH0_CLIENT_SECRET=your-client-secret
AUTH_DISABLED=false  # NEVER true in production
```

---

## Build and Test Commands

### Using Make (Recommended)

```bash
# Development
make start       # Start all services via docker-dev.sh
make stop        # Stop all services
make restart     # Restart services
make logs        # View service logs
make shell       # Open shell in backend container
make test        # Run tests
make migrate     # Run database migrations
make status      # Show service status

# Code Quality (MANDATORY - see ⚠️ Mandatory Code Quality Gates)
make format      # Auto-format all Python files (black + isort)
make format-check # Check formatting without changes
make lint        # Run all linters
make security-check # Run security scans
make quality-gate # Run full quality gate

# Maintenance
make clean       # Clean up Docker resources
make reset       # Reset all data (DESTRUCTIVE)
```

### Using Docker Compose Directly

```bash
# Start all services
docker-compose -f docker/docker-compose.yml up -d

# Start specific services
docker-compose -f docker/docker-compose.yml up -d api-server postgres redis

# View logs
docker-compose -f docker/docker-compose.yml logs -f api-server

# Rebuild
docker-compose -f docker/docker-compose.yml build --no-cache
```

### Python Commands

```bash
# Run backend
uvicorn backend.api.main:app --reload --port 8000

# Run with metrics server
python backend/main.py

# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1

# Code Quality (MANDATORY - see ⚠️ Mandatory Code Quality Gates)
make format              # Auto-format all Python files
make format-check        # Check formatting without changes
make lint                # Run all linters
make security-check      # Run security scans
make quality-gate        # Run full quality gate

# Individual quality tools
ruff check backend/ --fix --exit-non-zero-on-fix
black backend/ --line-length=100
isort backend/ --profile=black --line-length=100
mypy backend/ --strict --ignore-missing-imports

# Security scans
bandit -r backend/ --exclude backend/tests -f json -o bandit-report.json
pip-audit --requirement requirements/base.txt
```

### Frontend Commands

```bash
cd frontend

# Development
npm run dev          # Start dev server on port 3000

# Build
npm run build        # Production build
npm run preview      # Preview production build

# Testing
npm run test         # Unit tests with Vitest
npm run test:e2e     # E2E tests with Playwright
npm run test:e2e:ui  # E2E tests with UI

# Linting
npm run lint         # ESLint check
```

### Testing Commands

```bash
# All tests with coverage (80% minimum)
pytest backend/tests/ -v --cov=backend --cov-report=term-missing --cov-fail-under=80

# Unit tests only
pytest backend/tests/unit/ -v

# Integration tests (requires DB/Redis)
pytest backend/tests/integration/ -v --timeout=300

# Specific test file
pytest backend/tests/unit/test_sentiment_agent.py -v

# Specific test class
pytest backend/tests/unit/test_phase_e_enterprise.py::TestVaRCalculator -v

# Run with markers
pytest backend/tests/ -m "unit" -v
pytest backend/tests/ -m "integration" -v
pytest backend/tests/ -m "not slow" -v
```

---

## Code Style Guidelines

### Python

> **⚠️ MANDATORY: All code MUST pass these checks before saving. See [Mandatory Code Quality Gates](#️-mandatory-code-quality-gates).**

- **Formatter**: Black (line length 100)
- **Import Sorting**: isort (black profile)
- **Linter**: Ruff (configured in `ruff.toml`)
- **Type Checker**: mypy (strict mode - 766 pre-existing errors, run in CI)
- **Security**: Bandit + pip-audit

```bash
# Quick format (RECOMMENDED)
make format

# Individual commands
black backend/ --line-length=100
isort backend/ --profile=black --line-length=100
ruff check backend/ --fix --exit-non-zero-on-fix
python -m mypy backend/ --strict --ignore-missing-imports

# Security scans
bandit -r backend/ --exclude backend/tests/
pip-audit --requirement requirements/base.txt
```

### Ruff Configuration (ruff.toml)

```toml
[lint]
ignore = ["E741", "E402", "E722", "F401", "F811", "F821", "F823"]
# E741: ambiguous variable names (math/ML code)
# E402: module-level import not at top
# E722: bare except (gradual migration)
# F401: unused imports (__init__.py re-exports)
# F811: redefinition of unused name
# F821: undefined name (dynamic imports)
# F823: undefined name in __all__
```

### Code Patterns

```python
# Use type hints
from typing import Optional, Dict, List, Any
from datetime import datetime, UTC

# Class structure
class MyClass:
    """One-line summary docstring."""

    def __init__(self, name: str) -> None:
        self.name = name

    async def async_method(self, param: str) -> Dict[str, Any]:
        """Multi-line docstring with full details."""
        return {"result": "value"}

# Exception handling
try:
    result = await some_async_operation()
except SpecificException as e:
    logger.error(f"Operation failed: {e}")
    raise CustomException("Context message") from e

# Memory-safe collections (prevents OOM)
from collections import deque
self.reasoning_history: deque[dict] = deque(maxlen=1000)
```

### Frontend (TypeScript/React)

- **Linter**: ESLint (configured in `eslint.config.js`)
- **Formatter**: Prettier (via ESLint)
- **Style Guide**: React Hooks + Functional Components

```bash
# Lint
cd frontend
npm run lint
```

### Naming Conventions

- **Files**: `snake_case.py` (backend), `PascalCase.tsx` (components)
- **Classes**: `PascalCase`
- **Functions/Variables**: `snake_case`
- **Constants**: `UPPER_CASE`
- **Private**: `_leading_underscore`
- **Type Variables**: `PascalCase` with descriptive names

---

## Testing Strategy

### Test Organization

```
backend/tests/
├── conftest.py             # Shared fixtures
├── unit/                   # Unit tests (isolated, no external deps)
│   ├── test_agents/
│   ├── test_core/
│   └── test_risk/
├── integration/            # Integration tests (needs DB/Redis)
│   ├── test_api/
│   └── test_events/
├── e2e/                    # End-to-end tests (full stack)
├── security/               # Security regression tests
├── load/                   # Performance/stress tests
└── quality/                # Code quality tests
```

### Test Configuration (pytest.ini)

```ini
[pytest]
pythonpath = .
testpaths = tests
asyncio_mode = auto
addopts =
    -v
    --tb=short
    --strict-markers
    --cov=backend
    --cov-report=term-missing
    --cov-fail-under=80

markers =
    asyncio: marks tests as async
    unit: Unit tests (no external dependencies)
    integration: Integration tests (may need DB/Redis)
    e2e: End-to-end tests (full stack)
    security: Security regression tests
    slow: Tests that take > 5s
```

### Writing Tests

```python
import pytest
from unittest.mock import Mock, AsyncMock

@pytest.mark.asyncio
async def test_my_feature():
    # Arrange
    mock_service = Mock()
    mock_service.fetch = AsyncMock(return_value={"data": "value"})

    # Act
    result = await my_function(mock_service)

    # Assert
    assert result == expected_value
    mock_service.fetch.assert_called_once()

@pytest.mark.integration
async def test_database_connection():
    # Requires running PostgreSQL
    async with get_db_session() as session:
        result = await session.execute(text("SELECT 1"))
        assert result.scalar() == 1
```

### Test Metrics

- **Total Tests**: 734+ (unit + integration)
- **Pass Rate**: 100%
- **Coverage**: 80% minimum (enforced in CI)
- **Execution Time**: ~53 seconds (unit)

---

## Security Considerations

### Authentication & Authorization

- **Method**: JWT tokens (RS256 signing)
- **Token Lifetime**: 24 hours (configurable)
- **Multi-tenant**: Row-level security via `account_id`
- **Provider**: Auth0 (production), disabled for local dev (never in prod)

### Security Checklist

- [ ] No hardcoded secrets in code
- [ ] Use environment variables for sensitive data
- [ ] Validate all inputs with Pydantic models
- [ ] Use parameterized queries (prevent SQL injection)
- [ ] Implement rate limiting (60 req/min default)
- [ ] Audit log all operations
- [ ] Encrypt connections (TLS 1.3)

### Security Tools

> **⚠️ MANDATORY: Security scans MUST pass before saving code. See [Mandatory Code Quality Gates](#️-mandatory-code-quality-gates).**

```bash
# Code scanning (MANDATORY)
bandit -r backend/ -f json -o bandit-report.json

# Dependency vulnerability scanning (MANDATORY)
pip-audit --requirement requirements/base.txt

# Alternative: safety check
safety check

# Container scanning (Trivy)
trivy image agentic-trader:latest

# Pre-commit hooks
pre-commit run --all-files
```

### Security Patterns

```python
# SQL Injection Prevention - ALWAYS use parameterized queries
from sqlalchemy import text, bindparams

# CORRECT
query = text("SELECT * FROM trades WHERE symbol = :symbol").bindparams(symbol=user_input)

# INCORRECT - NEVER DO THIS
query = f"SELECT * FROM trades WHERE symbol = '{user_input}'"  # SQL INJECTION RISK

# Input sanitization for LLM prompts
from backend.core.security.prompt_guard import PromptGuard
sanitized = PromptGuard.sanitize(user_input)

# Secrets management
from backend.core.config.settings import settings
api_key = settings.REVOLUT_API_KEY  # Loaded from Vault or env var
```

### Compliance

- **OWASP 2024**: 88/100 score
- **MiFID II**: Audit trails, 7-year retention
- **GDPR**: Data retention, privacy controls
- **SOX 404**: Financial audit logging

---

## Common Patterns

### Adding a New API Endpoint

```python
# backend/api/my_module.py
from fastapi import APIRouter, Depends
from backend.core.security.auth_middleware import require_auth

router = APIRouter(prefix="/my-module", tags=["My Module"])

@router.get("/items")
async def get_items(
    user: dict = Depends(require_auth)
):
    """Get items for authenticated user."""
    return {"items": []}

# Register in backend/api/main.py
from backend.api import my_module
app.include_router(my_module.router)
```

### Adding a New Agent

```python
# backend/agents/my_agent.py
from backend.agents.base_agent import BaseAgent
from backend.governance.agent_gatekeeper import AgentRole

class MyAgent(BaseAgent):
    """My specialized agent."""

    def __init__(self, config: dict):
        super().__init__(
            agent_name="my_agent",
            agent_role=AgentRole.STANDARD,
            # LLM and EventBus injected via BaseAgent
        )

    async def think(self, observation: dict) -> dict:
        """Process observation and return decision using ReAct pattern."""
        # 1. Reasoning
        reasoning = await self._reason_about(observation)

        # 2. Acting
        action = await self._decide_action(reasoning)

        return {
            "action": action,
            "reasoning": reasoning,
            "confidence": self._calculate_confidence()
        }
```

### Database Operations

```python
from backend.core.database import get_db_session
from sqlalchemy import select

async def get_user(user_id: str):
    async with get_db_session() as session:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
```

### Event Publishing

```python
from backend.events.event_bus import EventBus
from datetime import datetime, UTC

event_bus = EventBus()
await event_bus.publish(
    stream="trading.events",
    event={
        "type": "order_executed",
        "data": order_data,
        "timestamp": datetime.now(UTC).isoformat()
    }
)
```

### Configuration Access

```python
from backend.core.config.settings import settings

# Access configuration (loaded from .env)
database_url = settings.DATABASE_URL
jwt_secret = settings.JWT_SECRET_KEY
trading_mode = settings.TRADING_MODE
```

---

## Troubleshooting

### Common Issues

#### "Duplicated timeseries in CollectorRegistry"

```bash
# Solution: Run tests in isolation
pytest backend/tests/unit/ -v

# Or clear registry
from backend.observability.metrics import PrometheusMetrics
PrometheusMetrics.clear_registry()
```

#### "ClickHouse Connection Refused"

```bash
# Check Docker status
docker-compose -f docker/docker-compose.yml ps

# Restart ClickHouse
docker-compose -f docker/docker-compose.yml restart clickhouse

# Verify connection
docker exec clickhouse clickhouse-client --query "SELECT 1"
```

#### "Redis Connection Error"

```bash
# Check Redis
docker-compose -f docker/docker-compose.yml ps

# Test connection
docker exec redis redis-cli ping
# Expected: PONG
```

#### Module Import Errors

```bash
# Ensure PYTHONPATH includes project root
export PYTHONPATH="${PYTHONPATH}:$(pwd)"  # Linux/Mac
set PYTHONPATH=%PYTHONPATH%;C:\path\to\project  # Windows
```

### Debugging

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Or via environment
export LOG_LEVEL=DEBUG

# Trace API requests
curl -v http://localhost:8000/api/v1/health
```

### Database Debugging

```bash
# ClickHouse queries
docker exec clickhouse clickhouse-client --query "SHOW TABLES;"
docker exec clickhouse clickhouse-client --query "SELECT COUNT(*) FROM trades;"

# PostgreSQL
psql $DATABASE_URL -c "\dt"

# Redis
docker exec -it redis redis-cli
> KEYS *
> GET key_name
```

---

## CI/CD Pipeline

### GitHub Actions Workflows

1. **ci.yml**: Main pipeline
   - Quick validation (always runs)
   - Backend tests (on main/develop/PR)
   - Docker build test
   - Security scan (Bandit, Trivy)
   - Code quality (Black, Ruff)

2. **cd.yml**: Deployment workflow

3. **release.yml**: Release workflow

### Pipeline Stages

```
Quick Validation → Backend Tests → Docker Build → Security Scan → Code Quality → Deploy
```

### Pre-commit Hooks

```bash
# Install hooks
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files

# Hooks include:
# - Black formatting
# - Ruff linting
# - isort import sorting
# - Bandit security scan
# - JSON/YAML validation
# - Private key detection
```

---

## Additional Resources

### Documentation

| Document | Description |
|----------|-------------|
| `README.md` | Main project documentation |
| `docs/SECURITY_RUNBOOK.md` | Security practices |
| `docs/TESTING.md` | Testing strategy |
| `docs/INCIDENT_RESPONSE.md` | Incident handling |
| `PORT_ALLOCATION_SSOT.md` | Port allocation guide |
| `docs/guides/QUICK_START.md` | Detailed setup guide |
| `docs/operations/DOCKER.md` | Docker operations |

### External References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic v2](https://docs.pydantic.dev/latest/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [React Documentation](https://react.dev/)
- [Tailwind CSS](https://tailwindcss.com/)
- [CCXT Documentation](https://docs.ccxt.com/)

---

## Build Findings & Lessons Learned

### Critical Security Patterns

1. **JWT Secret**: Must be set via `JWT_SECRET_KEY` env var (min 32 chars)
2. **SQL Injection**: Always use parameterized queries with `bindparams()`
3. **Pickle Security**: Use JSON serialization instead of pickle
4. **LLM Prompt Injection**: Sanitize all user inputs before LLM calls

### Port Allocation Enforcement

**CRITICAL**: Never hardcode ports. Use centralized config:

```python
# CORRECT
from backend.core.config.settings import Settings
port = Settings().API_PORT  # 8000

# INCORRECT
port = 8000  # Will fail if changed
```

**Forbidden ports for host mapping:** 8123, 9092, 9644

### Environment Variable Validation

All required env vars must be validated at startup:

```python
def __init__(self, secret_key: str | None = None):
    self.secret_key = secret_key or os.getenv("JWT_SECRET_KEY")
    if not self.secret_key:
        raise ValueError("JWT_SECRET_KEY environment variable is required")
```

---

## Contact

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions

---

*Last Updated: March 16, 2026*
*Platform Version: 1.0.0*
*Status: PRODUCTION READY*
*Build: Security Hardening & Reliability Release*
