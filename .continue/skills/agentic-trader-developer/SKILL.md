---
name: agentic-trader-developer
description: Development guide for the Agentic Trader V18 platform. Use when working on Python/FastAPI backend, React frontend, MCP broker integration, VedAstro signals, or trading system features. Covers architecture, coding standards, security practices, and development workflows.
---

# Agentic Trader Developer Guide

Complete development guide for the Agentic Trader V18 platform.

## Quick Reference

| Component | Tech Stack | Location |
|-----------|-----------|----------|
| Backend API | Python 3.13 + FastAPI | `backend/api/` |
| AI Agents | Python + Pydantic | `backend/agents/` |
| MCP Broker | FastMCP | `backend/mcp_broker/` |
| VedAstro | Swiss Ephemeris | `backend/vedastro/` |
| Frontend | React 19 + Vite + Tailwind | `frontend/` |
| Database | PostgreSQL + ClickHouse | See references/db-schema.md |

## Development Setup

```bash
# 1. Environment
cp .env.example .env
# Edit .env with your credentials

# 2. Infrastructure
docker-compose up -d postgres redis clickhouse chromadb redpanda

# 3. Python dependencies
pip install -r requirements/base.txt
pip install -r requirements/dev.txt

# 4. Run migrations
alembic upgrade head

# 5. Start services
# Terminal 1: Backend
uvicorn backend.api.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm install && npm run dev
```

## Code Standards

### Python
- **Formatter**: Black (line length 88)
- **Linter**: Ruff
- **Type checker**: mypy (strict mode)
- **Security**: Bandit (run before committing)

```bash
# Format
black backend/
isort backend/

# Lint
ruff check backend/

# Type check
mypy backend/ --strict --ignore-missing-imports

# Security scan
python -m bandit -r backend/ --severity-level high --exclude backend/tests
```

### Critical Security Rules

1. **No MD5** - Use BLAKE2b for hashing (B324)
2. **Parameterized queries** - Never use f-strings with SQL user input (B608)
3. **Timeouts** - All requests calls must have timeout (B113)
4. **No hardcoded secrets** - Use environment variables (B105)

```python
# GOOD - Parameterized query
query = f"SELECT * FROM {table} WHERE id = %(id)s"  # table is internal
result = await client.execute(query, {"id": user_id})

# BAD - SQL injection risk
query = f"SELECT * FROM users WHERE id = '{user_id}'"

# GOOD - Timeout
requests.get(url, timeout=30)

# GOOD - Secure hash
import hashlib
hashlib.blake2b(data, digest_size=16).hexdigest()
```

## Architecture Patterns

### Adding a New Agent

```python
# backend/agents/my_agent.py
from backend.agents.base_agent import BaseAgent, AgentConfig
from backend.governance.agent_gatekeeper import AgentRole

class MyAgent(BaseAgent):
    """My specialized agent."""

    def __init__(self, config: AgentConfig):
        super().__init__(
            agent_name="my_agent",
            agent_role=AgentRole.STRATEGIST,
            **config
        )

    async def analyze(self, features: dict, context: dict) -> dict:
        # Implementation
        return {"action": "hold"}
```

### Adding MCP Tools

```python
# backend/mcp_broker/tools/my_tools.py
from backend.mcp_broker.resilience import circuit_breaker

@circuit_breaker(failure_threshold=5, timeout_seconds=30)
async def my_tool(param: str) -> dict:
    """Tool description."""
    return {"result": param}

# Register in server.py
@mcp.tool(name="my__tool")
async def my_tool_wrapper(param: str) -> dict:
    return await my_tool(param)
```

### API Endpoint Pattern

```python
# backend/api/my_module.py
from fastapi import APIRouter, Depends
from backend.core.auth.middleware import require_auth

router = APIRouter(prefix="/my-module", tags=["My Module"])

@router.get("/items")
async def get_items(user: dict = Depends(require_auth)):
    """Get items for authenticated user."""
    return {"items": []}

# Register in backend/api/main.py
from backend.api import my_module
app.include_router(my_module.router)
```

## Testing

### Test Organization
```
backend/tests/
├── unit/           # Isolated unit tests
├── integration/    # Integration tests
└── e2e/           # End-to-end tests
```

### Running Tests
```bash
# All tests
pytest backend/tests/ -v

# Unit only
pytest backend/tests/unit/ -v

# Specific test
pytest backend/tests/unit/test_sentiment_agent.py -v

# With coverage
pytest backend/tests/ --cov=backend --cov-report=html
```

### Security Testing
```bash
# Run before committing
python scripts/test_real_gaps.py
python -m bandit -r backend/ --severity-level high --exclude backend/tests
```

## VedAstro Integration

See `references/vedastro-patterns.md` for detailed VedAstro patterns.

Quick example:
```python
from backend.vedastro import EnhancedAstroOrchestrator

orchestrator = EnhancedAstroOrchestrator()
signal = await orchestrator.analyze_asset(symbol="BTC", current_price=45000)
```

## MCP Tool Development

See `references/mcp-tools-guide.md` for detailed MCP patterns.

Key principles:
1. Always use `@circuit_breaker` decorator
2. Add timeouts to external calls
3. Return structured dict responses
4. Handle errors gracefully

## Frontend Development

```bash
cd frontend

# Development
npm run dev

# Build
npm run build

# Lint
npm run lint
```

### Component Pattern
```typescript
// src/components/MyComponent.tsx
import { useState } from 'react';

export function MyComponent({ data }: { data: MyType }) {
  const [value, setValue] = useState('');

  return (
    <div className="p-4 bg-card rounded-lg">
      {/* Implementation */}
    </div>
  );
}
```

## Scripts Reference

| Script | Purpose | Usage |
|--------|---------|-------|
| `scripts/test_real_gaps.py` | Verify core integrations | Run before commits |
| `scripts/security_summary.py` | Security scan summary | Weekly |
| `scripts/analyze_bandit.py` | Bandit issue analysis | As needed |

See `scripts/` directory for all available scripts.

## Common Tasks

### Adding a New API Endpoint
1. Create file in `backend/api/`
2. Define router with prefix
3. Implement endpoint with auth
4. Register in `main.py`
5. Add tests

### Adding an MCP Tool
1. Define tool function in `backend/mcp_broker/tools/`
2. Add `@circuit_breaker` decorator
3. Register in `server.py`
4. Test with agent

### Database Migration
```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## SOC2 Security Controls

### CC6.1 - Logical Access Security
- All endpoints require authentication via JWT
- Role-based access control (RBAC) enforced
- API keys stored in environment variables, never in code

### CC6.2 - Access Removal
- Token expiration: 24 hours
- Automatic logout on password change
- Session invalidation endpoint available

### CC6.3 - Access Changes
- Audit logs for all permission changes
- Admin approval required for role changes
- Monthly access reviews

### CC6.6 - Encryption
- Data in transit: TLS 1.3
- Data at rest: AES-256
- Secrets: HashiCorp Vault

### CC7.2 - System Monitoring
- All trades logged with user ID and timestamp
- Failed login attempts tracked
- Security events sent to SIEM

### CC8.1 - Change Management
- All changes via pull request
- Required reviews: 2 approvers for production
- Automated tests must pass

## Security Checklist

Before committing:
- [ ] Bandit scan passes (no HIGH issues)
- [ ] No hardcoded secrets
- [ ] SQL queries are parameterized
- [ ] All requests have timeouts
- [ ] MD5 replaced with BLAKE2b
- [ ] No PII in logs
- [ ] Audit logging added for sensitive operations

## Troubleshooting

### Module Import Errors
```bash
# Ensure PYTHONPATH includes project root
$env:PYTHONPATH="$env:PYTHONPATH;C:\path\to\project"
```

### Database Connection Issues
```bash
# Check Docker
docker-compose ps
docker-compose restart postgres
```

### Test Failures
```bash
# Run tests in isolation
pytest backend/tests/unit/test_specific.py -v --tb=short
```

## References

- **Database Schema**: See `references/db-schema.md`
- **VedAstro Patterns**: See `references/vedastro-patterns.md`
- **MCP Tools Guide**: See `references/mcp-tools-guide.md`
- **Security Guide**: See `references/security-guide.md`
- **API Documentation**: See `references/api-docs.md`
- **SOC2 Controls**: See `references/soc2-controls.md`
