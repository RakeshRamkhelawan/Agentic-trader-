---
name: agentic-trader-dev
description: Developer productivity skill for the Agentic Trader Platform - a Python/FastAPI trading system with ReAct agents, Redis Streams, and VedAstro integration. Use when working with backtests, creating ReAct agents, generating FastAPI routes with Redis events, or diagnosing Docker/infrastructure issues. Triggers include "backtest", "run strategy", "scaffold agent", "new agent", "FastAPI route", "Redis event", "docker", "container", "health check", "unhealthy service".
---

# Agentic Trader Dev Skill

Developer productivity workflows for the Agentic Trader Platform.

## Capabilities

This skill supports four high-leverage workflows:

1. **Backtest scaffolding & analysis** - Run backtests and analyze results
2. **ReAct agent scaffolding** - Create new trading agents with proper patterns
3. **FastAPI route + event generation** - Generate endpoints and Redis Streams handlers
4. **Docker/service health diagnosis** - Diagnose and fix infrastructure issues

## Quick Reference

| Workflow | Trigger | Key File |
|----------|---------|----------|
| Backtest | "run 30-day backtest on BTC" | `scripts/backtest_analyzer.py` |
| Agent | "scaffold sentiment agent" | `templates/react_agent.py.template` |
| FastAPI | "generate route for orders" | `templates/fastapi_route.py.template` |
| Docker | "diagnose unhealthy api-server" | `scripts/docker_health_check.py` |

## Workflow 1: Backtest Analysis

### Run a Backtest

```bash
# Quick 30-day backtest
python run_agent_backtest.py --days 30

# Via Docker
docker exec api-server python run_agent_backtest.py --days 30

# Use the interactive menu
python run_backtest_menu.py
```

### Analyze Results

Use the analysis script to compare runs:

```bash
python .continue/skills/agentic-trader-dev/scripts/backtest_analyzer.py --latest
python .continue/skills/agentic-trader-dev/scripts/backtest_analyzer.py --compare 2
```

### Common Patterns

- Elemental backtest results: `elemental_backtest_*_harmony.csv`
- Trade logs: `elemental_backtest_*_trades.csv`
- Full results: `backtest_v*_full_*.json`

## Workflow 2: ReAct Agent Scaffolding

### Create a New Agent

1. Use the template to scaffold:

```bash
# Copy and customize the template
cp .continue/skills/agentic-trader-dev/templates/react_agent.py.template backend/agents/my_agent.py
```

2. Update the agent class name and implement the `analyze()` method
3. Follow the ReAct pattern: Observation → Thought → Action

### Agent Structure

```python
class MyAgent(BaseAgent):
    """My specialized trading agent."""
    
    async def analyze(self, features, context) -> dict:
        # 1. Reasoning (ReAct pattern)
        thought = await self._reason_about(features, context)
        
        # 2. Action
        action = self._decide_action(thought)
        
        # 3. Publish thought to event bus
        await self.publish_thought(thought.reasoning, thought.confidence, action)
        
        return action
```

### Key Conventions

- Inherit from `BaseAgent` (see `backend/agents/base_agent.py`)
- Use `self.ask_llm()` for LLM reasoning
- Publish thoughts via `self.publish_thought()`
- Set `agent_role` for security (UNTRUSTED, STANDARD, PRIVILEGED)

## Workflow 3: FastAPI Route + Event Pattern

### Generate a New Route

Use the template to scaffold:

```bash
cp .continue/skills/agentic-trader-dev/templates/fastapi_route.py.template backend/api/my_module.py
```

### Key Patterns

**Route with Auth:**
```python
@router.post("/orders")
async def create_order(
    order: OrderRequest,
    user: dict = Depends(require_auth)
):
    """Create a new order."""
    pass
```

**Redis Event Publisher:**
```python
from backend.events.event_bus import EventBus

event_bus = EventBus()
await event_bus.publish("trading.events", {
    "type": "order_executed",
    "data": order_data,
    "timestamp": datetime.now(UTC).isoformat()
})
```

**Register Route:**

Add to `backend/api/main.py`:
```python
from backend.api import my_module
app.include_router(my_module.router)
```

## Workflow 4: Docker Health Diagnosis

### Check Service Status

```bash
# Run the health check script
python .continue/skills/agentic-trader-dev/scripts/docker_health_check.py

# Or manual check
docker compose ps
docker compose logs -f api-server
```

### Common Fixes

**api-server unhealthy (curl not found):**
```bash
docker compose build --no-cache api-server
docker compose up -d --build api-server
```

**Port conflicts:**
```bash
# Check what's using port 8000
netstat -ano | findstr :8000
# Or modify ports in docker-compose.yml
```

**Database connection issues:**
```bash
# Check PostgreSQL
docker exec agentic_trader_db pg_isready

# Check Redis
docker exec agentic_trader_redis redis-cli ping
```

## Project Context

### Architecture

- **Phase A**: Data (ClickHouse, Redis, Kafka)
- **Phase B**: Execution (Orders, Risk, Backtesting)
- **Phase C**: Cognition (ChromaDB, Memory, RAG)
- **Phase D**: Operations (OpenTelemetry, Docker)
- **Phase E**: Analytics (VaR, Kelly, Multi-tenant)

### Key Files

| Purpose | Path |
|---------|------|
| Base Agent | `backend/agents/base_agent.py` |
| Event Bus | `backend/events/event_bus.py` |
| Main API | `backend/api/main.py` |
| Backtest Menu | `run_backtest_menu.py` |
| Docker Compose | `docker-compose.yml` |
| Health Diagnosis | `HEALTH_CHECK_DIAGNOSIS.md` |
| Agent Guide | `AGENTS.md` |

### Testing

```bash
# Run all tests
pytest backend/tests/ -v

# Specific test
pytest backend/tests/unit/test_sentiment_agent.py -v

# With coverage
pytest backend/tests/ --cov=backend --cov-report=html
```

## Reference Files

For detailed patterns, see:
- `references/backtest_patterns.md` - Backtest result analysis patterns
- `references/agent_patterns.md` - ReAct agent implementation details
- `references/fastapi_patterns.md` - FastAPI + Redis event patterns
- `references/docker_troubleshooting.md` - Common Docker issues
