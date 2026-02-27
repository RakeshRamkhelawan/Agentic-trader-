# Agentic Trader Dev Skill

Developer productivity skill for the Agentic Trader Platform.

## Installation

Copy this directory to your skills location:

```bash
# For Continue
cp -r .continue/skills/agentic-trader-dev ~/.continue/skills/

# For Claude CLI
cp -r .continue/skills/agentic-trader-dev ~/.claude/skills/
```

## Capabilities

| Capability | Command Example |
|------------|-----------------|
| **Backtest Analysis** | "Run a 30-day backtest on BTC" |
| **Agent Scaffolding** | "Scaffold a new sentiment ReAct agent" |
| **FastAPI Routes** | "Generate FastAPI route for portfolio" |
| **Docker Diagnosis** | "Diagnose unhealthy api-server" |

## Usage Examples

### Backtest Workflow

```bash
# Run backtest menu
python run_backtest_menu.py

# Analyze latest results
python .continue/skills/agentic-trader-dev/scripts/backtest_analyzer.py --latest --symbols

# Compare last 3 runs
python .continue/skills/agentic-trader-dev/scripts/backtest_analyzer.py --compare 3
```

### Agent Creation

```bash
# Copy template
cp .continue/skills/agentic-trader-dev/templates/react_agent.py.template \
   backend/agents/my_agent.py

# Customize and implement
```

### FastAPI Route

```bash
# Copy template
cp .continue/skills/agentic-trader-dev/templates/fastapi_route.py.template \
   backend/api/my_module.py

# Register in main.py
```

### Docker Health

```bash
# Check all services
python .continue/skills/agentic-trader-dev/scripts/docker_health_check.py --all

# Fix issues automatically
python .continue/skills/agentic-trader-dev/scripts/docker_health_check.py --fix
```

## File Structure

```
agentic-trader-dev/
├── SKILL.md                      # Main skill documentation
├── README.md                     # This file
├── scripts/
│   ├── backtest_analyzer.py     # Analyze backtest results
│   └── docker_health_check.py   # Diagnose Docker issues
├── templates/
│   ├── react_agent.py.template  # New agent template
│   └── fastapi_route.py.template # FastAPI route template
└── references/
    ├── backtest_patterns.md     # Backtest analysis patterns
    ├── agent_patterns.md        # ReAct agent patterns
    ├── fastapi_patterns.md      # FastAPI + Redis patterns
    └── docker_troubleshooting.md # Docker troubleshooting
```

## Triggers

This skill activates on:

- "backtest", "run strategy", "compare runs"
- "scaffold agent", "new agent", "create agent"
- "FastAPI route", "new endpoint", "Redis event"
- "docker", "container", "health check", "unhealthy service"

## License

Part of the Agentic Trader Platform.
