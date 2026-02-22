# Developer Onboarding Guide

> Complete guide for engineers joining the Agentic Trader Platform team

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Development Environment](#development-environment)
4. [Project Structure](#project-structure)
5. [Coding Standards](#coding-standards)
6. [Testing](#testing)
7. [Debugging](#debugging)
8. [Common Tasks](#common-tasks)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.13+ | Backend runtime |
| Node.js | 20+ | Frontend runtime |
| Docker | 24+ | Infrastructure |
| Docker Compose | 2+ | Local orchestration |
| Git | 2.40+ | Version control |
| VS Code | Latest | Recommended IDE |

### VS Code Extensions (Recommended)

```bash
# Install via VS Code extensions panel or:
code --install-extension ms-python.python
code --install-extension ms-python.black-formatter
code --install-extension charliermarsh.ruff
code --install-extension bradlc.vscode-tailwindcss
code --install-extension esbenp.prettier-vscode
```

---

## Quick Start

### 1. Clone Repository

```bash
git clone <repository-url>
cd agentic_trader_platform
git config --local core.autocrlf false  # Windows only
```

### 2. Environment Setup

```bash
# Copy environment templates
cp .env.example .env
cp frontend/.env.example frontend/.env

# Edit with your values
# Required for backend:
# - DATABASE_URL
# - REDIS_URL
# - AUTH0_DOMAIN, AUTH0_CLIENT_ID, AUTH0_AUDIENCE
# - DEEPSEEK_API_KEY

# Required for frontend:
# - VITE_AUTH0_DOMAIN, VITE_AUTH0_CLIENT_ID
# - VITE_API_URL, VITE_WS_URL
```

### 3. Start Infrastructure

```bash
# Start databases and cache
docker-compose up -d postgres redis clickhouse chromadb

# Verify all services are running
docker-compose ps
```

### 4. Install Dependencies

```bash
# Backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements/base.txt
pip install -r requirements/dev.txt

# Frontend
cd frontend
npm install
```

### 5. Database Setup

```bash
# Run migrations
alembic upgrade head

# Seed initial data (optional)
python scripts/seed_data.py
```

### 6. Start Development Servers

```bash
# Terminal 1: Backend
cd backend
uvicorn api.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev

# Terminal 3: MCP Server (optional)
cd backend
python -m mcp_server.server
```

### 7. Verify Installation

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Frontend
curl http://localhost:5173

# WebSocket test
wscat -c ws://localhost:8000/ws
```

**You're ready!** Open http://localhost:5173 in your browser.

---

## Development Environment

### IDE Configuration

#### VS Code Settings

```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.ruff": "explicit"
  },
  "typescript.tsdk": "frontend/node_modules/typescript/lib",
  "tailwindCSS.includeLanguages": {
    "typescript": "javascript",
    "typescriptreact": "javascript"
  }
}
```

#### PyCharm Users

1. Set Python interpreter to `venv/bin/python`
2. Enable Black formatter (Preferences > Tools > Black)
3. Configure TypeScript (frontend/tsconfig.json)

### Git Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes, commit with conventional commits
git commit -m "feat: add new trading strategy"

# Push and create PR
git push origin feature/your-feature-name
```

**Commit Message Format:**
```
<type>(<scope>): <subject>

<body>

<footer>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Example: `feat(trading): add stop-loss order type`

---

## Project Structure

```
agentic_trader_platform/
│
├── backend/                    # Python backend
│   ├── api/                    # FastAPI routes
│   │   ├── routers/            # API endpoint definitions
│   │   ├── websocket_*.py      # WebSocket handling
│   │   └── main.py             # FastAPI app
│   │
│   ├── services/               # Business logic
│   │   ├── trading_service.py
│   │   ├── backtest_service.py
│   │   └── consensus/          # VedAstro, Elemental
│   │
│   ├── core/                   # Shared infrastructure
│   │   ├── config/             # Settings management
│   │   ├── database/           # SQLAlchemy models
│   │   ├── cache/              # Redis client
│   │   └── telemetry/          # Monitoring
│   │
│   ├── adapters/               # External integrations
│   │   ├── bitvavo_client.py
│   │   └── deepseek_client.py
│   │
│   ├── security/               # Auth & security
│   │   ├── jwt_handler.py
│   │   └── rls.py              # Row-level security
│   │
│   ├── mcp_server/             # AI tool server
│   │   ├── server.py
│   │   └── tools/
│   │
│   └── tests/                  # Test suite
│       ├── unit/
│       └── integration/
│
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── hooks/              # Custom hooks
│   │   ├── services/           # API clients
│   │   ├── store/              # Zustand state
│   │   └── types/              # TypeScript types
│   │
│   └── tests/
│
├── infrastructure/             # DevOps
│   ├── docker/
│   ├── k8s/
│   └── prometheus/
│
├── docs/                       # Documentation
│   ├── architecture/
│   ├── adr/                    # Decision records
│   └── engineering/
│
├── scripts/                    # Utility scripts
├── requirements/               # Python dependencies
└── docker-compose.yml          # Local infrastructure
```

### Key Files for Engineers

| File | Purpose |
|------|---------|
| `backend/api/main.py` | FastAPI application entry |
| `backend/core/config/settings.py` | Configuration |
| `frontend/src/main.tsx` | React entry point |
| `docker-compose.yml` | Local services |
| `pyproject.toml` | Python project config |

---

## Coding Standards

### Python

#### Style Guide
- **Formatter**: Black (line length 88)
- **Linter**: Ruff
- **Type Hints**: Required for all functions
- **Docstrings**: Google style

```python
from typing import Optional, Dict, Any
from decimal import Decimal

async def execute_trade(
    symbol: str,
    side: str,
    amount: Decimal,
    order_type: str = "market",
    price: Optional[Decimal] = None
) -> Dict[str, Any]:
    """
    Execute a trade order.

    Args:
        symbol: Trading pair (e.g., "BTC-EUR")
        side: "buy" or "sell"
        amount: Order quantity
        order_type: Order type (market, limit, stop)
        price: Limit price (required for limit orders)

    Returns:
        dict: Order details including order_id and status

    Raises:
        RiskViolationError: If order exceeds risk limits
        ExchangeError: If exchange execution fails
    """
    # Implementation
```

#### Imports (isort)
```python
# Standard library
import asyncio
from typing import Optional

# Third party
from fastapi import FastAPI
from sqlalchemy import select

# Local
from backend.core.config import settings
from backend.services.trading import TradingService
```

### TypeScript/React

#### Style Guide
- **Linter**: ESLint
- **Formatter**: Prettier
- **Types**: Strict TypeScript

```typescript
// frontend/src/components/TradeButton.tsx
import { useState, useCallback } from 'react';

interface TradeButtonProps {
  symbol: string;
  side: 'buy' | 'sell';
  onTrade: (amount: number) => Promise<void>;
  disabled?: boolean;
}

export function TradeButton({
  symbol,
  side,
  onTrade,
  disabled = false
}: TradeButtonProps) {
  const [isLoading, setIsLoading] = useState(false);

  const handleClick = useCallback(async () => {
    setIsLoading(true);
    try {
      await onTrade(0.1); // Default amount
    } finally {
      setIsLoading(false);
    }
  }, [onTrade]);

  return (
    <button
      onClick={handleClick}
      disabled={disabled || isLoading}
      className={`btn ${side === 'buy' ? 'btn-green' : 'btn-red'}`}
    >
      {isLoading ? 'Processing...' : `${side.toUpperCase()} ${symbol}`}
    </button>
  );
}
```

---

## Testing

### Running Tests

```bash
# All tests
pytest backend/tests/ -v

# Unit tests only
pytest backend/tests/unit/ -v

# Specific test file
pytest backend/tests/unit/test_trading_service.py -v

# With coverage
pytest backend/tests/ --cov=backend --cov-report=html

# Frontend tests
cd frontend
npm test

# E2E tests
npm run test:e2e
```

### Writing Tests

#### Python Unit Test
```python
# backend/tests/unit/test_trading_service.py
import pytest
from unittest.mock import Mock, AsyncMock

@pytest.mark.asyncio
async def test_create_order_success():
    # Arrange
    mock_db = Mock()
    mock_risk = Mock()
    mock_risk.check_order = AsyncMock(return_value=RiskCheck(approved=True))
    mock_exchange = Mock()
    mock_exchange.place_order = AsyncMock(return_value={
        'orderId': 'test-123',
        'status': 'filled'
    })

    service = TradingService(mock_db, mock_risk, mock_exchange)

    # Act
    order = await service.create_order(
        tenant_id='tenant-1',
        account_id='account-1',
        symbol='BTC-EUR',
        side='buy',
        amount=Decimal('0.1')
    )

    # Assert
    assert order.id == 'test-123'
    assert order.status == 'filled'
    mock_exchange.place_order.assert_called_once()
```

#### React Component Test
```typescript
// frontend/src/components/__tests__/TradeButton.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { TradeButton } from '../TradeButton';

describe('TradeButton', () => {
  it('calls onTrade when clicked', async () => {
    const mockTrade = jest.fn().mockResolvedValue(undefined);

    render(
      <TradeButton
        symbol="BTC-EUR"
        side="buy"
        onTrade={mockTrade}
      />
    );

    fireEvent.click(screen.getByText('BUY BTC-EUR'));

    expect(mockTrade).toHaveBeenCalledWith(0.1);
  });
});
```

---

## Debugging

### Backend Debugging

#### VS Code Launch Configuration
```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "debugpy",
      "request": "launch",
      "module": "uvicorn",
      "args": ["backend.api.main:app", "--reload", "--port", "8000"],
      "jinja": true,
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    }
  ]
}
```

#### Common Debug Commands
```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use ipdb for better experience
import ipdb; ipdb.set_trace()

# FastAPI auto-reload logs
uvicorn backend.api.main:app --reload --log-level debug
```

### Frontend Debugging

```bash
# Start with source maps
npm run dev -- --sourcemap

# Debug MCP server
DEBUG=mcp:* python -m backend.mcp_server.server
```

### Database Debugging

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U trader -d trading_db

# Check Redis
docker-compose exec redis redis-cli
> KEYS *
> GET session:xxx

# Check ClickHouse
docker-compose exec clickhouse clickhouse-client
SELECT * FROM trades LIMIT 10;
```

---

## Common Tasks

### Adding a New API Endpoint

```python
# 1. Create router file
# backend/api/routers/portfolio.py
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])

@router.get("/")
async def get_portfolio(user: User = Depends(get_current_user)):
    return {"portfolio": []}

# 2. Register in main.py
from backend.api.routers import portfolio
app.include_router(portfolio.router, prefix="/api/v1")

# 3. Test
curl http://localhost:8000/api/v1/portfolio/
```

### Adding a Database Migration

```bash
# Create migration
alembic revision --autogenerate -m "Add positions table"

# Review generated file
# backend/alembic/versions/xxx_add_positions_table.py

# Apply migration
alembic upgrade head

# Rollback (if needed)
alembic downgrade -1
```

### Adding an MCP Tool

```python
# backend/mcp_server/tools/new_tool.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("agentic-trader")

@mcp.tool()
async def analyze_portfolio(portfolio_id: str) -> dict:
    """Analyze portfolio performance."""
    # Implementation
    return {"analysis": "..."}
```

---

## Troubleshooting

### Common Issues

#### "ModuleNotFoundError: No module named 'backend'"
```bash
# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or run from project root
cd /path/to/agentic_trader_platform
python -m backend.api.main
```

#### "Database connection refused"
```bash
# Start infrastructure
docker-compose up -d postgres redis

# Check status
docker-compose ps

# View logs
docker-compose logs postgres
```

#### "CORS error in browser"
```bash
# Check .env has correct frontend URL
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Restart backend after changing .env
```

#### "WebSocket connection failed"
```bash
# Verify backend is running
curl http://localhost:8000/health

# Check WebSocket stats
curl http://localhost:8000/ws/stats

# Test with wscat
npx wscat -c ws://localhost:8000/ws
```

### Getting Help

1. **Check documentation**: `/docs` directory
2. **Search code**: Use VS Code global search (Ctrl+Shift+F)
3. **Ask team**: Post in #engineering Slack channel
4. **Check logs**: `docker-compose logs -f`

---

## Next Steps

After completing onboarding:

1. Read [Architecture Decision Records](../../adr/)
2. Review [C4 Architecture Documentation](../c4/)
3. Pick up a "good first issue" from GitHub
4. Schedule architecture walkthrough with tech lead

---

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [C4 Model](https://c4model.com/)
- [Project Wiki](../../)

**Welcome to the team!** 🚀
