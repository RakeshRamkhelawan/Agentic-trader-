# Agentic Trader Platform - AI Coding Agent Guide

This document provides essential information for AI coding agents working on the Agentic Trader Platform, an enterprise-grade AI-powered trading system.

---

## Project Overview

**Agentic Trader Platform** is a production-grade AI trading system featuring:

- **Multi-Agent Cognitive System**: ReAct reasoning pattern with specialized agents (Research, Risk, Macro, Valuation)
- **Advanced Risk Management**: VaR calculations, stress testing, Kelly criterion optimization 
- **Real-time Execution**: Smart order routing, shadow portfolios, multi-exchange support
- **Enterprise Infrastructure**: ClickHouse analytics, Redis event bus, Kafka/Redpanda messaging
- **Observability**: OpenTelemetry tracing, Prometheus metrics, structured logging
- **Security**: JWT authentication (Auth0), multi-tenant isolation, MiFID II compliance

**Status**: Phases A-E Complete | 734+ tests passing | 100% success rate

---

## Technology Stack

### Backend (Python 3.13+)
| Component | Technology | Purpose |
|-----------|------------|---------|
| API Framework | FastAPI 0.115+ | REST/WebSocket endpoints |
| Database ORM | SQLAlchemy 2.0+ | PostgreSQL with asyncpg |
| Migrations | Alembic | Database schema versioning |
| Analytics DB | ClickHouse | Time-series & OLAP data |
| Cache/Event Bus | Redis 7.2+ | Caching & pub/sub |
| Message Broker | Redpanda (Kafka-compatible) | Distributed messaging |
| Vector DB | ChromaDB | Semantic memory & RAG |
| LLM Interface | Pluggable Pattern | DeepSeek, Gemini, Ollama, OpenAI |
| Trading | CCXT 4.2+ | Multi-exchange integration |
| Testing | Pytest 8.4+ | Unit & integration tests |
| Observability | OpenTelemetry 1.24+ | Distributed tracing |
| Metrics | Prometheus Client | Performance monitoring |

### Frontend (Next.js 15)
| Component | Technology |
|-----------|------------|
| Framework | Next.js 15.1.6 + React 19 |
| Styling | Tailwind CSS 4.0 |
| State Management | Zustand + TanStack Query |
| UI Components | Radix UI |
| Charts | D3.js + Lightweight Charts |
| Auth | Auth0 React SDK |
| Testing | Vitest |

---

## Project Structure

```
agentic_trader_platform/
├── backend/                          # Python backend (493+ modules)
│   ├── agents/                       # AI agent implementations
│   │   ├── base_agent.py            # ReAct pattern base class
│   │   ├── sentiment_agent.py        # Sentiment analysis
│   │   ├── fund_manager_agent.py     # Portfolio management
│   │   └── researcher_agents.py      # Bull/Bear researchers
│   ├── api/                          # FastAPI REST & WebSocket
│   │   ├── main.py                   # Main API application
│   │   ├── gateway.py                # API gateway
│   │   ├── auth_api.py               # Authentication endpoints
│   │   ├── trading_api.py            # Trading endpoints
│   │   └── websocket_endpoints.py    # Real-time WebSocket
│   ├── core/                         # Core cognitive system
│   │   ├── agent_registry.py         # Agent lifecycle management
│   │   ├── memory_system.py          # Long-term memory
│   │   ├── guna_quantifier.py        # Behavioral state metrics
│   │   ├── auth/                     # JWT & RBAC
│   │   ├── telemetry/                # OpenTelemetry & metrics
│   │   └── config/settings.py        # Central configuration
│   ├── events/                       # Event streaming
│   │   ├── event_bus.py              # Redis Streams
│   │   ├── kafka_broker.py           # Kafka implementation
│   │   └── schemas.py                # Event data models
│   ├── execution/                    # Trading execution
│   │   ├── smart_order_router.py     # Intelligent routing
│   │   ├── shadow_portfolio.py       # Paper trading
│   │   ├── hot_path_engine.py        # Low-latency execution
│   │   └── exchange_adapter.py       # Broker abstraction
│   ├── llm/                          # LLM provider interface
│   │   ├── provider_interface.py     # Abstract base
│   │   ├── factory.py                # Dynamic provider selection
│   │   └── providers/                # Gemini, Ollama, DeepSeek
│   ├── risk/                         # Risk management
│   │   ├── var_calculator.py         # Historical VaR
│   │   ├── stress_tester.py          # Stress scenarios
│   │   └── kelly_criterion.py        # Position sizing
│   ├── services/                     # High-level services
│   │   ├── cognitive_orchestrator.py # Main orchestrator
│   │   ├── trading_service.py        # Trading operations
│   │   └── market_data_processor.py  # Data ingestion
│   ├── storage/                      # Data persistence
│   │   ├── clickhouse_client.py      # ClickHouse adapter
│   │   └── migrations/               # Alembic migrations
│   ├── tests/                        # Test suite
│   │   ├── unit/                     # 232+ unit tests
│   │   ├── integration/              # 20+ integration tests
│   │   └── conftest.py               # Test fixtures
│   └── main.py                       # Application entry point
├── frontend/                         # Next.js frontend
│   ├── src/
│   │   ├── app/                      # Next.js app router
│   │   ├── components/               # React components
│   │   ├── lib/                      # Utilities & API client
│   │   └── stores/                   # Zustand state stores
│   └── package.json
├── infrastructure/                   # Docker & deployment
│   ├── docker/Dockerfile             # Backend container
│   └── prometheus/prometheus.yml     # Metrics config
├── docs/                             # Documentation (114+ files)
├── requirements/                     # Python dependencies
│   ├── base.txt                      # Production deps
│   ├── dev.txt                       # Development tools
│   └── test.txt                      # Testing deps
├── docker-compose.yml                # Full dev environment
├── alembic.ini                       # Migration configuration
├── pytest.ini                        # Test configuration
└── Makefile                          # DevEx commands
```

---

## Build & Development Commands

### Backend Development

```bash
# Install dependencies
pip install -r requirements/base.txt
pip install -r requirements/dev.txt

# Run API server (development)
uvicorn backend.api.main:app --reload --port 8000

# Alternative: Start with main.py
python backend/main.py

# Database migrations
alembic upgrade head              # Apply migrations
alembic revision --autogenerate -m "description"  # Create migration
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev          # Start dev server (port 3000)
npm run build        # Production build
npm run test         # Run Vitest tests
```

### Docker (Full Stack)

```bash
# Start all services
make up              # or: docker compose up -d

# View logs
make logs            # All services
make logs-backend    # Backend only

# Stop services
make down            # or: docker compose down

# Rebuild
make build           # Rebuild images
```

### Makefile Commands

```bash
make install         # Install Python dependencies
make test            # Run all tests
make test-unit       # Unit tests only
make test-integration # Integration tests
make lint            # Run all linters
make format          # Auto-format code
make coverage        # Generate coverage report
make health          # Deep health check
make clean           # Clean cache/artifacts
```

---

## Testing Instructions

### Test Configuration
- **Framework**: Pytest 8.4+ with asyncio support
- **Location**: `backend/tests/`
- **Config**: `pytest.ini`

### Running Tests

```bash
# All tests
pytest backend/tests/ -v

# Unit tests only
pytest backend/tests/unit/ -v --cov=backend --cov-report=term-missing

# Integration tests
pytest backend/tests/integration/ -v --timeout=300

# Specific test file
pytest backend/tests/unit/test_phase_e_enterprise.py -v

# Specific test class
pytest backend/tests/unit/test_phase_e_enterprise.py::TestAPIGateway -v

# With coverage
pytest backend/tests/ --cov=backend --cov-report=html --cov-report=term
```

### Test Organization
- **Unit Tests**: `backend/tests/unit/` - Fast, isolated tests
- **Integration Tests**: `backend/tests/integration/` - Service interaction tests
- **E2E Tests**: `backend/tests/e2e/` - Full flow tests

### Key Test Fixtures (conftest.py)
- `async_client` - HTTPX async client for FastAPI
- `system_db` - Database session with system admin privileges
- `sample_observation`, `sample_proposal` - Domain test data
- `mock_data_source`, `mock_event_bus` - Mocked dependencies

---

## Code Style Guidelines

### Python

1. **Formatting**: Black (line length 88)
2. **Import Sorting**: isort (profile=black)
3. **Linting**: Ruff for fast checks
4. **Type Checking**: MyPy (strict mode)

```bash
# Format code
black backend/
isort backend/

# Lint
ruff check backend/
mypy backend/ --ignore-missing-imports
```

### Code Patterns

```python
# Type hints required
from typing import Optional, Dict, List, Any

class MyClass:
    """One-line docstring summary."""
    
    def __init__(self, name: str) -> None:
        self.name = name
    
    async def async_method(self, param: str) -> Dict[str, Any]:
        """Multi-line docstring with details."""
        return {"result": "value"}
```

### Pre-commit Hooks
Configured in `.pre-commit-config.yaml`:
- Black (formatting)
- isort (import sorting)
- Ruff (linting)
- MyPy (type checking)

```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

---

## Configuration & Environment

### Environment Variables (`.env`)

Key variables (see `.env.example` for full list):

```bash
# LLM Configuration
LLM_PROVIDER=deepseek              # deepseek, gemini, ollama, openai
LLM_API_KEY=your_api_key
DEEPSEEK_API_KEY=your_deepseek_key

# Database
DATABASE_URL=postgresql+asyncpg://trader:trading_secure@localhost:5456/trading_db

# Infrastructure
REDIS_URL=redis://localhost:6379
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8124
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
CHROMA_HOST=localhost
CHROMA_PORT=8005

# Auth (Auth0)
AUTH0_DOMAIN=agentictrader.eu.auth0.com
AUTH0_API_AUDIENCE=https://api.agentic-trader.com

# Trading
TRADING_MODE=paper                 # paper, live, backtest
REVOLUT_API_KEY=your_key
REVOLUT_PRIVATE_KEY_PATH=revolut_private.pem

# Security
JWT_SECRET_KEY=secure-random-string
```

### Settings Class
Central configuration in `backend/core/config/settings.py`:
- Pydantic Settings with env file support
- Vault integration (optional)
- Lazy loading for secrets

---

## Security Considerations

### Authentication & Authorization
- **Auth0 Integration**: JWT tokens with RS256 signing
- **RBAC**: Role-based access control in `backend/core/auth/rbac.py`
- **Public Paths**: Configured in `backend/api/main.py`

### Security Practices
1. **No Hardcoded Secrets**: Use environment variables or Vault
2. **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
3. **Input Validation**: Pydantic models for all inputs
4. **Audit Logging**: All operations logged to ClickHouse
5. **Row-Level Security**: PostgreSQL RLS for multi-tenancy

### Security Scanning
```bash
# Bandit (Python security)
bandit -r backend/ --exclude backend/tests

# Dependency check
# (Run via GitHub Actions or security workflow)
```

---

## Database & Migrations

### PostgreSQL (Primary DB)
- **Migrations**: Alembic in `backend/migrations/`
- **Models**: SQLAlchemy 2.0 with async support
- **Multi-tenancy**: Row-level security (RLS) enabled

### Migration Commands
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Downgrade
alembic downgrade -1

# View history
alembic history --verbose
```

### ClickHouse (Analytics)
- **Purpose**: Time-series data, audit logs, metrics
- **Client**: `backend/storage/clickhouse_client.py`
- **Schema**: SQL files in `backend/storage/migrations/`

---

## CI/CD Pipeline

GitHub Actions workflows in `.github/workflows/`:

### ci-cd.yml
1. **Code Quality**: Black, isort, Ruff, MyPy, Bandit
2. **Unit Tests**: 232+ tests with coverage
3. **Integration Tests**: 20+ tests with infrastructure services
4. **Docker Build**: Multi-stage builds for backend/frontend
5. **E2E Tests**: Full Docker Compose testing
6. **Security Scan**: Trivy vulnerability scanner
7. **Deploy**: Staging/Production (manual approval)

### security.yml
- Weekly dependency checks
- CodeQL analysis

---

## Troubleshooting

### Common Issues

**ModuleNotFoundError: No module named 'backend'**
```bash
# Set PYTHONPATH
$env:PYTHONPATH = "$env:PYTHONPATH;$(Get-Location)"
# or
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Prometheus Registry Duplicate Metrics**
```bash
# Already fixed in metrics.py with try/except
# Run tests in isolation if needed:
pytest backend/tests/unit/ -v
```

**Database Connection Issues**
```bash
# Check Docker services
docker compose ps

# Restart PostgreSQL
docker compose restart postgres

# Verify connection
pg_isready -h localhost -p 5456 -U trader
```

**Redis Connection Error**
```bash
# Check Redis
docker exec redis redis-cli ping

# Restart
docker compose restart redis
```

### Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or via environment
$env:LOG_LEVEL = "DEBUG"
```

---

## Development Conventions

### Branch Naming
```
feature/new-agent-type
bugfix/metrics-registry-issue
docs/update-readme
release/v1.0.0
```

### Commit Message Format
```
<type>(<component>): <short description>

<detailed explanation>

- Bullet point 1
- Bullet point 2

Closes #<issue-number>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Pull Request Checklist
- [ ] Tests passing: `pytest backend/tests/ -v`
- [ ] Code formatted: `black backend/ && isort backend/`
- [ ] Type checking: `mypy backend/ --strict`
- [ ] Linting: `ruff check backend/`
- [ ] Security: No hardcoded secrets
- [ ] Coverage: 80%+ for new code
- [ ] Documentation updated

---

## Key Documentation

- `README.md` - Main project documentation
- `docs/architecture/` - System architecture docs
- `docs/phases/` - Phase completion reports
- `docs/kanban/` - Project task tracking
- `OWASP_SECURITY_AUDIT_2024.md` - Security analysis

---

## Architecture Patterns

### Multi-Frequency Consciousness
- **Eternal Soul** (~1 min): Cosmic constraints, guna balance
- **Cognitive Mind** (50-200ms): Decision making, OODA loop
- **Reflex Body** (<10ms): Order execution, hot path

### Event-Driven Architecture
- **Event Bus**: Redis Streams for pub/sub
- **Message Broker**: Kafka/Redpanda for persistence
- **Schema**: Pydantic models in `backend/events/schemas.py`

### Pluggable Components
- **LLM Providers**: Interface in `backend/llm/`
- **Exchange Adapters**: Interface in `backend/execution/`
- **Databases**: Adapter pattern for ClickHouse/PostgreSQL

---

## Contact & Resources

- **Repository**: https://github.com/RakeshRamkhelawan/Agentic-trader-
- **Issues**: GitHub Issues
- **Documentation**: `docs/` directory

---

*Last Updated: February 17, 2026*
*Platform Version: 1.0.0*
*Status: Production Ready*
