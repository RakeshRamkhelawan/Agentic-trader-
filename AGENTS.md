# AGENTS.md - Agentic Trader Platform

> **Guide for AI Coding Agents**
> This document provides essential information for AI agents working on the Agentic Trader Platform. It covers the project architecture, development workflow, testing strategies, and conventions specific to this codebase.

> **⚠️ CRITICAL: Before any network/port configuration task, read [PORT_ALLOCATION_SSOT.md](PORT_ALLOCATION_SSOT.md)**

---

## Table of Contents

1. [⚠️ Mandatory Reading (CRITICAL)](#-mandatory-reading-critical)
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

## ⚠️ Mandatory Reading (CRITICAL)

### Before Starting Any Task

**YOU MUST READ these documents FIRST:**

| Priority | Document | When Required |
|----------|----------|---------------|
| 🔴 **CRITICAL** | [PORT_ALLOCATION_README.md](PORT_ALLOCATION_README.md) | Gateway naar poortallocatie docs |
| 🔴 **CRITICAL** | [PORT_ALLOCATION_SSOT.md](PORT_ALLOCATION_SSOT.md) | Enige bron van waarheid voor poorten |
| 🟡 HIGH | [AGENTS.md](AGENTS.md) (this file) | Alle taken |

### Port/Nework Tasks - Required Checklist

For any task involving:
- Docker Compose configuration
- Environment variables (.env)
- Port mappings
- Service URLs
- Infrastructure setup

**YOU MUST:**
1. Read `PORT_ALLOCATION_SSOT.md` completely
2. Follow the port allocation table exactly
3. Use only allowed ports (8000, 8001, 5432, 6379, 5000, 5001, 6000, 6001, 8100, 9000, 9090, 3000, 3080)
4. **NEVER** use forbidden ports (8123, 9092, 9644 for host mapping)
5. Add the verification checklist to your PR

### Quick Port Reference

```
Core:      API=8000, MCP=8001, Postgres=5432, Redis=6379
Extended:  ClickHouse=5000/5001, Redpanda=6000/6001, ChromaDB=8100
Monitoring: Grafana=9000, Prometheus=9090
Frontend:  Dev=3000, Prod=3080
```

**Full details:** [PORT_ALLOCATION_SSOT.md](PORT_ALLOCATION_SSOT.md)

---

## Project Overview

The **Agentic Trader Platform** is a production-grade AI-powered trading system built with enterprise-grade architecture. It features a multi-agent cognitive system with ReAct reasoning pattern, advanced risk management (VaR, stress testing, Kelly criterion), and real-time trade execution.

### Key Characteristics

- **Language**: English (all code comments, documentation)
- **Status**: Phases A-E Complete, 734+ tests passing
- **Architecture**: Modular, pluggable, multi-tenant SaaS
- **Philosophy**: Vedic/Consciousness-inspired cognitive architecture (Samkhya philosophy)

### Core Features

- **AI Agents**: Multi-agent system with specialized roles (research, macro, valuation, risk)
- **Risk Management**: VaR calculations, stress testing, Kelly criterion optimization
- **Execution**: Smart order routing, shadow portfolios, multi-exchange support
- **Infrastructure**: ClickHouse analytics, Redis event bus, Kafka messaging
- **Observability**: OpenTelemetry tracing, Prometheus metrics, structured logging

---

## Architecture

### Layered Architecture (Samkhya-Inspired)

```
┌──────────────────────────────────────────────────────────────┐
│  PHASE E: Analytics & Business Layer                         │
│  (VaR, Stress Testing, Kelly, Multi-Tenant API Gateway)     │
├──────────────────────────────────────────────────────────────┤
│  PHASE D: Enterprise Operations & Monitoring                 │
│  (OpenTelemetry, Prometheus, Docker, CI/CD)                 │
├──────────────────────────────────────────────────────────────┤
│  PHASE P: Conscious Core │ PHASE C: Cognition & AI          │
│  (Guna Balance, Intent)  │ (ChromaDB, Memory, RAG)          │
├──────────────────────────────────────────────────────────────┤
│  PHASE B: Execution & Risk Management                        │
│  (Smart Routing, Orders, Risk Governor, Backtesting)        │
├──────────────────────────────────────────────────────────────┤
│  PHASE A: Foundation & Data Infrastructure                   │
│  (ClickHouse, Redis, Kafka, Feature Store, Market Data)     │
└──────────────────────────────────────────────────────────────┘
```

### Multi-Frequency Consciousness Architecture

The platform implements a three-layer consciousness model:

1. **Layer 1: Eternal Soul** (`EternalSoulService`) - Cosmic constraints, ~1 minute frequency
2. **Layer 2: Cognitive Mind** (`CognitiveMindService`) - Decision making, 50-200ms frequency
3. **Layer 3: Reflex Body** (`ReflexExecutor`) - Order execution, <10ms frequency

### Pluggable Architecture

All major infrastructure components use adapter patterns:
- **LLM Provider**: DeepSeek (default), OpenAI, Gemini, Ollama, or custom
- **Database**: PostgreSQL (primary), ClickHouse (analytics)
- **Message Broker**: Kafka/Redpanda (default), RabbitMQ compatible
- **Exchange/Broker**: Bitvavo, Revolut, or custom adapter
- **Vector DB**: ChromaDB (default), Pinecone/Weaviate compatible

---

## Technology Stack

### Backend

| Component | Technology | Version |
|-----------|------------|---------|
| Language | Python | 3.13+ |
| Web Framework | FastAPI | 0.104+ |
| Data Validation | Pydantic | v2 |
| Settings | pydantic-settings | latest |
| Async DB | asyncpg + SQLAlchemy | latest |
| Testing | pytest | 8.4+ |

### Frontend

| Component | Technology | Version |
|-----------|------------|---------|
| Framework | React | 19.2.0 |
| Language | TypeScript | 5.9+ |
| Build Tool | Vite | 7.2+ |
| Styling | Tailwind CSS | 3.4+ |
| UI Components | Radix UI | latest |
| State Management | Zustand | 5.0+ |
| Forms | React Hook Form + Zod | latest |

### Infrastructure

| Component | Technology |
|-----------|------------|
| Containerization | Docker & Docker Compose |
| Database | PostgreSQL 15 + TimescaleDB |
| Analytics DB | ClickHouse 24.3 |
| Cache/Event Bus | Redis 7.2 |
| Vector DB | ChromaDB 0.5 |
| Message Broker | Redpanda (Kafka-compatible) |
| Monitoring | Prometheus + Grafana |
| Tracing | OpenTelemetry |
| CI/CD | GitHub Actions |

---

## Project Structure

```
agentic_trader_platform/
│
├── backend/                          # Python backend (549+ modules)
│   ├── agents/                       # AI agent implementations
│   │   ├── base_agent.py            # Abstract base with ReAct pattern
│   │   ├── sentiment_agent.py        # Sentiment analysis
│   │   └── ...
│   ├── api/                          # FastAPI endpoints
│   │   ├── main.py                  # Main app entry
│   │   ├── gateway.py               # API gateway
│   │   └── ...
│   ├── core/                         # Core cognitive system
│   │   ├── config/settings.py       # Central configuration
│   │   ├── telemetry/               # Metrics, tracing, logging
│   │   ├── security/                # Auth, encryption, audit
│   │   └── ...
│   ├── execution/                    # Trading execution layer
│   ├── events/                       # Event bus (Redis Streams)
│   ├── llm/                          # LLM provider interface
│   ├── risk/                         # Risk management (VaR, Kelly)
│   ├── services/                     # High-level services
│   ├── storage/                      # Database clients
│   └── tests/                        # Test suite
│       ├── unit/                     # Unit tests
│       ├── integration/              # Integration tests
│       └── e2e/                      # End-to-end tests
│
├── frontend/                         # React frontend
│   ├── src/                         # Source code
│   ├── package.json                 # NPM dependencies
│   └── vite.config.ts               # Vite configuration
│
├── infrastructure/                   # Infrastructure as Code
│   ├── docker/                      # Dockerfiles
│   └── prometheus/                  # Monitoring configs
│
├── docs/                            # Documentation
│   ├── architecture/                # Architecture docs
│   ├── phases/                      # Phase completion reports
│   └── ...
│
├── requirements/                    # Python requirements
│   ├── base.txt                     # Production deps
│   ├── dev.txt                      # Development deps
│   └── test.txt                     # Testing deps
│
├── docker-compose.yml               # Full stack orchestration
├── pytest.ini                      # Test configuration
├── Makefile                        # Development shortcuts
└── .env.example                    # Environment template
```

---

## Development Setup

### Prerequisites

- **Python**: 3.13.7+ (with timezone.utc support)
- **Node.js**: 18+ (for frontend)
- **Docker**: 24.0+ & Docker Compose 2.0+
- **Git**: For version control

### Quick Start

```bash
# 1. Clone repository
git clone <repository-url>
cd agentic_trader_platform_1734

# 2. Set up environment
cp .env.example .env
# Edit .env with your configuration

# 3. Start infrastructure
docker-compose up -d postgres redis clickhouse chromadb redpanda

# 4. Install Python dependencies
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements/base.txt
pip install -r requirements/dev.txt

# 5. Run migrations
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
# Database
DATABASE_URL=postgresql+asyncpg://trader:trading_secure@localhost:5432/trading_db
CLICKHOUSE_HOST=localhost
REDIS_URL=redis://localhost:6379/0

# LLM Provider (choose one)
LLM_PROVIDER=deepseek  # or openai, gemini, ollama
DEEPSEEK_API_KEY=your_key

# Trading
TRADING_MODE=paper  # paper, live, backtest

# Security
JWT_SECRET_KEY=your-secret-key
SECRET_KEY=your-super-secret-key
```

---

## Build and Test Commands

### Using Make (Recommended)

```bash
# Development
make start       # Start all services
make stop        # Stop all services
make restart     # Restart services
make logs        # View service logs
make shell       # Open shell in backend container

# Testing
make test        # Run all tests
make migrate     # Run database migrations

# Maintenance
make clean       # Clean up Docker resources
make status      # Show service status
```

### Using Docker Compose Directly

```bash
# Start all services
docker-compose up -d

# Start specific services
docker-compose up -d api-server frontend postgres redis

# View logs
docker-compose logs -f api-server

# Rebuild
docker-compose build --no-cache
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
```

### Frontend Commands

```bash
cd frontend

# Development
npm run dev

# Build
npm run build

# Lint
npm run lint
```

---

## Code Style Guidelines

### Python

- **Formatter**: Black (line length 88)
- **Import Sorting**: isort
- **Linter**: Ruff
- **Type Checker**: mypy (strict mode)

```bash
# Format code
black backend/
isort backend/

# Lint
ruff check backend/

# Type check
mypy backend/ --strict --ignore-missing-imports

# Security scan
bandit -r backend/ --exclude backend/tests
```

### Code Patterns

```python
# Use type hints
from typing import Optional, Dict, List, Any

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
```

### Frontend (TypeScript/React)

- **Linter**: ESLint
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

---

## Testing Strategy

### Test Organization

```
backend/tests/
├── unit/                    # Unit tests (isolated)
│   ├── test_*.py           # Test files
│   ├── core/               # Core module tests
│   ├── cognition/          # AI agent tests
│   └── ...
├── integration/            # Integration tests
│   └── test_*.py
├── e2e/                    # End-to-end tests
│   └── test_*.py
└── conftest.py             # Shared fixtures
```

### Running Tests

```bash
# All tests
pytest backend/tests/ -v

# Unit tests only
pytest backend/tests/unit/ -v

# Specific test file
pytest backend/tests/unit/test_sentiment_agent.py -v

# Specific test class
pytest backend/tests/unit/test_phase_e_enterprise.py::TestVaRCalculator -v

# With coverage
pytest backend/tests/ --cov=backend --cov-report=html

# Integration tests
pytest backend/tests/integration/ -v --timeout=300
```

### Test Configuration

Configured in `pytest.ini`:

```ini
[pytest]
pythonpath = .
testpaths = backend/tests
asyncio_mode = auto
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    asyncio: marks tests as async
    integration: marks tests as integration tests
    unit: marks tests as unit tests
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
```

### Key Test Metrics

- **Total Tests**: 734+ (unit + integration)
- **Pass Rate**: 100%
- **Coverage**: 95%+ (critical modules)
- **Execution Time**: ~53 seconds (unit)

---

## Security Considerations

### Authentication

- **Method**: JWT tokens (RS256 signing)
- **Token Lifetime**: 24 hours (configurable)
- **Multi-tenant**: Row-level security via `account_id`

### Security Checklist

- [ ] No hardcoded secrets in code
- [ ] Use environment variables for sensitive data
- [ ] Validate all inputs with Pydantic models
- [ ] Use parameterized queries (prevent SQL injection)
- [ ] Implement rate limiting (60 req/min default)
- [ ] Audit log all operations
- [ ] Encrypt connections (TLS 1.3)

### Security Tools

```bash
# Code scanning
bandit -r backend/ -f json -o bandit-report.json

# Dependency scanning
safety check

# Run in CI/CD
# See .github/workflows/security.yml
```

### Compliance

- **OWASP 2024**: 95/100 score
- **MiFID II**: Audit trails, 7-year retention
- **GDPR**: Data retention, privacy controls
- **SOX 404**: Financial audit logging

---

## Common Patterns

### Adding a New API Endpoint

```python
# backend/api/my_module.py
from fastapi import APIRouter, Depends
from backend.core.auth.middleware import require_auth

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
from backend.agents.base_agent import BaseAgent, AgentConfig

class MyAgent(BaseAgent):
    """My specialized agent."""

    def __init__(self, config: AgentConfig):
        super().__init__(config)

    async def think(self, observation: dict) -> dict:
        """Process observation and return decision."""
        # Implementation
        return {"action": "hold"}
```

### Database Operations

```python
from backend.core.database import get_db_session

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

event_bus = EventBus()
await event_bus.publish(
    stream="trading.events",
    event={
        "type": "order_executed",
        "data": order_data,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
)
```

---

## Troubleshooting

### Common Issues

#### "Duplicated timeseries in CollectorRegistry"

```bash
# Solution: Run tests in isolation
pytest backend/tests/unit/ -v

# Or clear registry
from backend.core.telemetry.metrics import PrometheusMetrics
PrometheusMetrics.clear_registry()
```

#### "ClickHouse Connection Refused"

```bash
# Check Docker status
docker-compose ps

# Restart ClickHouse
docker-compose restart clickhouse

# Verify connection
docker exec clickhouse clickhouse-client --query "SELECT 1"
```

#### "Redis Connection Error"

```bash
# Check Redis
docker-compose ps | findstr redis
docker exec redis redis-cli ping
# Expected: PONG
```

#### Module Import Errors

```bash
# Ensure PYTHONPATH includes project root
set PYTHONPATH=%PYTHONPATH%;C:\path\to\agentic_trader_platform

# Or install in dev mode
pip install -e .
```

### Debugging

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Or via environment
set LOG_LEVEL=DEBUG

# Trace API requests
curl -v http://localhost:8000/health
```

### Database Debugging

```bash
# ClickHouse queries
docker exec clickhouse clickhouse-client --query "SHOW TABLES;"
docker exec clickhouse clickhouse-client --query "SELECT COUNT(*) FROM trades;"

# Redis
docker exec -it redis redis-cli
> KEYS *
> GET key_name
```

---

## CI/CD Pipeline

### GitHub Actions Workflows

1. **ci-cd.yml**: Main pipeline
   - Code quality (Black, isort, Ruff, mypy)
   - Unit tests with coverage
   - Integration tests
   - Docker build & push
   - E2E tests
   - Security scanning

2. **security.yml**: Security scanning
   - Dependency check
   - CodeQL analysis
   - Weekly schedule

### Pipeline Stages

```
Code Quality → Unit Tests → Integration Tests → Docker Build → E2E Tests → Deploy
```

### Deployment Environments

- **Staging**: Auto-deploy on `develop` branch
- **Production**: Manual approval on `main` branch

---

## Additional Resources

### Documentation

- `README.md`: Main project documentation
- `docs/ARCHITECTURE_DOCUMENTATION.md`: Detailed architecture
- `docs/phases/`: Phase completion reports
- `KANBAN_TASKS.md`: Project roadmap

### External References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic v2](https://docs.pydantic.dev/latest/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [React Documentation](https://react.dev/)
- [Tailwind CSS](https://tailwindcss.com/)

---

## Build Findings & Lessons Learned

> **Critical insights from the v1.0.0 security hardening and reliability improvements**

### Security Fixes Applied (v1.0.0)

The following 18 critical security issues were resolved. **Always verify these patterns are not reintroduced:**

| Issue | Location | Fix Applied | Verification |
|-------|----------|-------------|--------------|
| SQL Injection (3 locations) | `backend/core/context.py` | Parameterized queries with `bindparams` | Use `text("...").bindparams()` pattern |
| JWT Hardcoded Secrets | `backend/auth/jwt_handler.py` | Environment variable validation | `JWT_SECRET_KEY` must be set or `ValueError` raised |
| Authentication Bypass Paths | Multiple API modules | Removed hardcoded bypass tokens | Search for `# DEBUG` or `skip_auth` patterns |
| Pickle RCE | `backend/cache/redis_cache.py` | JSON serialization | `json.dumps()` instead of `pickle.dumps()` |
| LLM Prompt Injection | LLM provider modules | Input sanitization | Verify `sanitize_input()` calls on user data |
| Hardcoded API Keys | Exchange adapters | Vault/AWS Secrets Manager | No secrets in `.env.example` |
| Insecure Deserialization | Event bus | Schema validation | Pydantic models for all event data |

**Security Testing Commands:**
```bash
# Run before any PR
bandit -r backend/ -f json -o bandit-report.json
# Must show: 0 high/critical issues

# Check for new SQL injection patterns
grep -r "f\".*SELECT" backend/ --include="*.py" | grep -v "bindparams"

# Verify no hardcoded secrets
grep -r "sk-\|secret.*=.*[^${}]\|password.*=.*\"" backend/ --include="*.py"
```

### Reliability Fixes Applied (v1.0.0)

| Issue | Component | Fix | Pattern to Maintain |
|-------|-----------|-----|---------------------|
| Missing VaR Check | `backend/risk/risk_orchestrator.py` | Added `portfolio_var_pct` validation | Always check `max_daily_var_pct` limit |
| Kelly Formula Edge Cases | `backend/risk/kelly_criterion.py` | Added win_rate/payoff validation | Validate inputs before calculation |
| Circuit Breaker Unit Mismatch | `backend/governance/circuit_breaker.py` | Compare % to % (not € to %) | Document units in variable names |
| Event Bus Non-Atomic Ops | `backend/events/event_bus.py` | Redis pipeline for retry+ack | Use `pipe.execute()` for multi-key ops |
| Non-Deterministic Slippage | Backtest engine | Fixed random seed | Set `random.seed()` in tests |

### Pre-commit Configuration (Fixed)

**Issue**: YAML syntax error in `.pre-commit-config.yaml` (line 165) - `check-sql-injection` hook had malformed `entry` field.

**Resolution**: Fixed multiline string syntax using proper YAML `|` operator.

**Always run before committing:**
```bash
pre-commit run --all-files
# Fix any failures before git push
```

### Git Workflow Best Practices

**From v1.0.0 release:**
1. **Feature branches**: Use `feature/description` or `fix/description` naming
2. **Merge strategy**: Use `--no-ff` for release merges to preserve history
3. **Tagging**: Always tag releases with annotated tags
   ```bash
   git tag -a vX.Y.Z -m "Release notes"
   ```
4. **Cleanup**: Delete merged feature branches to prevent confusion

### Docker Build Requirements

**Multi-stage build must include:**
```dockerfile
# Non-root user (security requirement)
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser

# No secrets in layers
# Use build args or runtime env vars only
```

**Verify build:**
```bash
docker build -t agentic-trader:test .
docker run --rm agentic-trader:test id  # Should show appuser, not root
```

### Test Coverage Requirements

**Minimum thresholds (enforced in CI):**
- Unit tests: 85% line coverage
- Critical modules (risk, auth, execution): 95% coverage
- Integration tests: All happy paths + error scenarios

**Coverage check:**
```bash
pytest backend/tests/ --cov=backend --cov-report=term-missing
# Fail if coverage < 85%
```

### Port Allocation Enforcement

**CRITICAL**: The project uses a strict port allocation scheme. **Never** hardcode ports without checking:

```python
# CORRECT - Use centralized config
from backend.core.config.settings import Settings
port = Settings().API_PORT  # 8000

# INCORRECT - Hardcoded port
port = 8000  # Will fail if changed
```

**Forbidden ports for host mapping:** 8123, 9092, 9644 (used internally by ClickHouse/Redpanda)

### Environment Variable Validation

**New requirement (v1.0.0)**: All required env vars must be validated at startup:

```python
# Pattern to follow (from backend/auth/jwt_handler.py)
def __init__(self, secret_key: str | None = None):
    self.secret_key = secret_key or os.getenv("JWT_SECRET_KEY")
    if not self.secret_key:
        raise ValueError("JWT_SECRET_KEY environment variable is required")
```

### Documentation Updates

**When modifying code, update:**
1. `CHANGELOG.md` - Add entry under `## [Unreleased]`
2. `docs/` - Update relevant runbook if behavior changes
3. `AGENTS.md` - Update this file if patterns/conventions change
4. Tests - Update or add tests for new behavior

---

## Contact

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Email**: support@agentictrader.com

---

*Last Updated: March 1, 2026*
*Platform Version: 1.0.0*
*Status: PRODUCTION READY*
*Build: Security Hardening & Reliability Release*
