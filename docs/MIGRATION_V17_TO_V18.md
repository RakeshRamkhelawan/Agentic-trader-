# Migration Guide: V17 → V18 (MCP ToolBroker)

> **Agentic Trader Platform**  
> **Date**: February 22, 2026  
> **Status**: Production Ready

---

## Executive Summary

V18 transforms the Agentic Trader Platform from a static, hardcoded backtest loop to a dynamic, **MCP-enabled** trading architecture. All V17 financial constraints are preserved.

### Key Changes

| Aspect | V17 | V18 |
|--------|-----|-----|
| **Architecture** | Direct method calls | MCP tool calls via stdio/SSE |
| **Broker** | None (direct) | FastMCP server |
| **Resilience** | None | Circuit breakers + retry |
| **LLM Support** | Limited | Full orchestration |
| **Error Isolation** | None | Per-tool circuit breakers |

---

## What's New in V18

### 1. MCP ToolBroker Architecture

```
V17 Flow:
  BacktestEngine → ElementalAgentManagerV17 → Direct agent calls

V18 Flow:
  BacktestEngineV18 → MCPClient → FastMCP Server → Tool execution
```

### 2. New Components

```
backend/mcp_broker/
├── server.py                      # FastMCP server (16 tools)
├── client.py                      # MCP client wrapper
├── elemental_manager_v18.py       # V18 Elemental Manager
├── backtest_engine_v18.py         # V18 Backtest Engine
├── resilience/
│   ├── circuit_breaker.py         # Circuit breaker decorator
│   └── retry.py                   # Retry decorator
└── tools/
    ├── elemental_tools.py         # Fire/Earth/Water/Ether
    ├── vedastro_tools.py          # VedAstro tools
    ├── data_tools.py              # Data tools
    └── execution_tools.py         # Execution tools
```

### 3. API Endpoints

```
GET  /api/v1/mcp/tools             # List all MCP tools
GET  /api/v1/mcp/health            # Health check
GET  /api/v1/mcp/circuit-breakers  # Circuit breaker states
GET  /api/v1/mcp/stats             # MCP statistics
POST /api/v1/mcp/tools/{name}/execute  # Execute tool
POST /api/v1/mcp/backtest/run      # Run V18 backtest
```

---

## Migration Steps

### Step 1: Verify Dependencies

```bash
pip install mcp[cli] pydantic anyio
```

### Step 2: Update Imports

**Old (V17):**
```python
from backend.agents.elemental_agent_manager_v17 import VedAstroElementalAgentV17
```

**New (V18):**
```python
from backend.mcp_broker import ElementalAgentManagerV18, MCPClientWrapper
```

### Step 3: Replace Backtest Engine

**Old (V17):**
```python
from backend.execution.backtest_engine import BacktestEngine

engine = BacktestEngine(start_date, end_date)
```

**New (V18):**
```python
from backend.mcp_broker import BacktestEngineV18, BacktestConfig

config = BacktestConfig(
    start_date=start_date,
    end_date=end_date,
    symbols=["AAPL", "MSFT"],
    initial_cash=100000.0
)
engine = BacktestEngineV18(config)
await engine.initialize()
results = await engine.run_backtest()
```

### Step 4: Update Agent Calls

**Old (V17):**
```python
agent = VedAstroElementalAgentV17()
entry = await agent.evaluate_entry(symbol, price, date, portfolio)
```

**New (V18):**
```python
async with MCPClientWrapper() as client:
    manager = ElementalAgentManagerV18(client)
    await manager.initialize()
    
    entry = await manager.evaluate_entry(
        symbol=symbol,
        current_price=price,
        portfolio_value=portfolio,
        vedastro_score=75.0,
        dominant_planet="JUPITER",
        price_history=prices
    )
```

### Step 5: Update Configuration

**Old (V17):**
```python
MAX_POSITION_EUR = 2000.0  # In agent code
```

**New (V18):**
```python
from backend.mcp_broker.backtest_engine_v18 import BacktestConfig

config = BacktestConfig(
    max_position_eur=2000.0,  # Same constraint
    max_position_pct=0.02     # Same constraint
)
```

---

## Preserved Constraints (100%)

All V17 financial constraints are preserved in V18:

| Constraint | V17 Location | V18 Location | Status |
|------------|--------------|--------------|--------|
| €2,000 max position | `FireAgentV17.MAX_POSITION_EUR` | `elemental_tools.MAX_POSITION_EUR` | ✅ Preserved |
| 2% portfolio limit | `FireAgentV17.calculate_position_size()` | `elemental__fire_position_size` | ✅ Preserved |
| 60-day failsafe | `EarthAgentV17.MAX_HOLD_DAYS` | `elemental_tools.MAX_HOLD_DAYS` | ✅ Preserved |
| 3-loss rule | `EarthAgentV17.should_enter()` | `elemental__earth_entry_check` | ✅ Preserved |
| Trailing stop (+40% → -15%) | `EarthAgentV17.check_trailing_stop()` | `elemental__earth_exit_check` | ✅ Preserved |
| Commission (0.05%) | `VedAstroElementalAgentV17.COMMISSION_PCT` | `execution_tools.COMMISSION_PCT` | ✅ Preserved |
| Slippage (0.1%) | `VedAstroElementalAgentV17.SLIPPAGE_PCT` | `execution_tools.SLIPPAGE_PCT` | ✅ Preserved |

---

## Tool Mapping

| V17 Method | V18 MCP Tool | Parameters |
|------------|--------------|------------|
| `VedAstroElementalAgentV17.evaluate_entry()` | `vedastro__generate_signal` | `symbol`, `current_price` |
| `FireAgentV17.calculate_position_size()` | `elemental__fire_position_size` | `symbol`, `portfolio_value`, `vedastro_score`, `dominant_planet`, `price_history` |
| `EarthAgentV17.should_enter()` | `elemental__earth_entry_check` | `symbol`, `trade_history` |
| `EarthAgentV17.check_trailing_stop()` | `elemental__earth_exit_check` | `symbol`, `entry_date`, `current_date`, `entry_price`, `current_price`, `peak_price` |
| `WaterAgentV12.get_macro_signal()` | `elemental__water_regime_check` | `symbol`, `prices` |
| `Ether consensus` | `elemental__ether_consensus` | `fire_vote`, `earth_vote`, `water_vote`, `air_vote` |

---

## Testing Migration

### 1. Validate V17 Constraints

```bash
python scripts/validate_v17_constraints.py
```

Expected output:
```
[PASS] Position size respects €2,000 cap
[PASS] Position size respects 2% portfolio limit
[PASS] Entry allowed with winning history
[PASS] Entry BLOCKED with 3 consecutive losses
[PASS] Exit triggered after 65 days (60-day failsafe)
[PASS] Trailing stop active
[PASS] Commission and slippage applied correctly
```

### 2. Test MCP Server

```bash
python -m backend.mcp_broker.server
```

Expected output:
```
============================================================
Starting AgenticTraderBroker MCP Server
============================================================
Tools registered: 16
Available tools:
  - elemental__earth_entry_check
  - elemental__earth_exit_check
  - elemental__ether_consensus
  - elemental__fire_position_size
  - elemental__water_regime_check
  - vedastro__generate_signal
  ...
```

### 3. Test API Endpoints

```bash
# List tools
curl http://localhost:8000/api/v1/mcp/tools

# Health check
curl http://localhost:8000/api/v1/mcp/health

# Circuit breakers
curl http://localhost:8000/api/v1/mcp/circuit-breakers
```

---

## Rollback Plan

If issues occur, you can rollback to V17:

1. **Stop V18 MCP Server**
   ```bash
   # Kill MCP server process
   pkill -f "backend.mcp_broker.server"
   ```

2. **Revert to V17 Code**
   ```python
   # Change imports back to V17
   from backend.agents.elemental_agent_manager_v17 import VedAstroElementalAgentV17
   ```

3. **Verify V17 Still Works**
   ```bash
   python -c "from backend.agents.elemental_agent_manager_v17 import VedAstroElementalAgentV17; print('OK')"
   ```

---

## Benefits of Migration

### 1. Resilience
- **Before**: One failure crashes entire backtest
- **After**: Circuit breakers isolate failures per tool

### 2. LLM Orchestration
- **Before**: Hardcoded execution flow
- **After**: LLM can dynamically orchestrate tools

### 3. Error Isolation
- **Before**: Errors propagate through entire system
- **After**: Each tool is isolated with retry logic

### 4. Extensibility
- **Before**: Adding tools requires code changes
- **After**: New tools register via MCP protocol

### 5. Monitoring
- **Before**: Limited visibility
- **After**: Full circuit breaker and metrics visibility

---

## Troubleshooting

### Issue: MCP Server Won't Start

**Solution:**
```bash
# Check if port is in use
lsof -i :8000

# Kill existing process
pkill -f "backend.mcp_broker.server"

# Restart
python -m backend.mcp_broker.server
```

### Issue: Circuit Breaker Open

**Solution:**
```python
# Check circuit breaker state
from backend.mcp_broker.resilience import get_circuit_state

state = get_circuit_state("vedastro__generate_signal")
print(state)  # { "state": "open", "failure_count": 5 }

# Wait for reset (60 seconds default)
# Or restart MCP server
```

### Issue: Tool Call Timeout

**Solution:**
```python
# Increase timeout in client call
result = await client.call_tool(
    "vedastro__generate_signal",
    params,
    timeout=60.0  # Increase from default 30s
)
```

---

## Support

For migration support:
1. Check V17 constraints validation: `scripts/validate_v17_constraints.py`
2. Review API documentation: `/api/v1/mcp/docs`
3. Contact: development team

---

## Summary

V18 migration provides:
- ✅ **Same financial constraints** as V17
- ✅ **Better resilience** via circuit breakers
- ✅ **LLM orchestration** capabilities
- ✅ **Standard MCP protocol** compatibility
- ✅ **Improved monitoring** and observability

**Migration effort**: Low (mostly import changes)  
**Risk**: Low (V17 code preserved)  
**Benefit**: High (resilience + LLM support)

---

*Migration Guide Version: 1.0*  
*Last Updated: 2026-02-22*
