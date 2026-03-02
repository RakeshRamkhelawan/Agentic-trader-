# MCP Tools Guide - Agentic Trader

Guide for developing MCP tools in the Agentic Trader platform.

## Overview

The MCP (Model Context Protocol) Broker exposes trading tools to AI agents via a standardized protocol.

**Location:** `backend/mcp_broker/`
**Server:** `backend/mcp_broker/server.py`
**Tools:** `backend/mcp_broker/tools/`

## Available Tools

### VedAstro Tools
```python
vedastro__generate_signal(symbol, current_price)
vedastro__get_dasha(symbol)
vedastro__get_transits(symbol)
```

### Elemental Tools
```python
elemental__fire_position_size(...)
elemental__earth_entry_check(...)
elemental__earth_exit_check(...)
elemental__water_regime_check(...)
elemental__ether_consensus(...)
```

### Execution Tools
```python
execution__execute_paper_trade(...)
execution__get_open_positions()
execution__get_trade_history()
execution__close_position(...)
```

### Data Tools
```python
data__get_historical_prices(...)
data__get_portfolio_status()
data__get_market_regime()
```

## Creating a New Tool

### 1. Define the Tool Function

```python
# backend/mcp_broker/tools/my_tools.py
import logging
from typing import Any

from backend.mcp_broker.resilience import circuit_breaker, retry

logger = logging.getLogger(__name__)

@circuit_breaker(failure_threshold=5, timeout_seconds=30)
@retry(max_attempts=3)
async def my_tool(
    symbol: str,
    param: float,
    ctx=None
) -> dict[str, Any]:
    """
    Brief description of what the tool does.

    Args:
        symbol: Asset symbol (e.g., "BTC", "AAPL")
        param: Description of parameter
        ctx: MCP context for logging

    Returns:
        Dictionary with results
    """
    if ctx:
        ctx.info(f"Processing {symbol} with param={param}")

    try:
        # Implementation
        result = await _internal_logic(symbol, param)

        return {
            "success": True,
            "result": result,
            "symbol": symbol,
        }
    except Exception as e:
        logger.error(f"My tool failed: {e}")
        return {
            "success": False,
            "error": str(e),
        }
```

### 2. Register in Server

```python
# backend/mcp_broker/server.py
from backend.mcp_broker.tools.my_tools import my_tool

@mcp.tool(name="my__tool")
async def my_tool_wrapper(
    symbol: str,
    param: float,
    ctx: Context = None
) -> dict:
    """Wrapper for my tool."""
    return await my_tool(symbol, param, ctx)
```

### 3. Use from Agent

```python
# In an AgentWithTools subclass
async def analyze(self, features, context):
    result = await self.call_tool(
        "my__tool",
        {"symbol": "BTC", "param": 0.5}
    )

    if result.get("success"):
        return {"action": "buy", "confidence": result["result"]}
    else:
        return {"action": "hold", "error": result.get("error")}
```

## Tool Patterns

### Circuit Breaker Pattern

Always use for external calls:

```python
@circuit_breaker(
    failure_threshold=5,      # Open after 5 failures
    timeout_seconds=30,       # Reset after 30 seconds
)
async def external_api_call(...):
    ...
```

### Retry Pattern

For transient failures:

```python
@retry(
    max_attempts=3,
    exceptions=(TimeoutError, ConnectionError),
)
async def flaky_operation(...):
    ...
```

### Combined Pattern

```python
@circuit_breaker(failure_threshold=5, timeout_seconds=30)
@retry(max_attempts=3)
async def robust_external_call(...):
    """Both retry and circuit breaker."""
    ...
```

## Error Handling

Always return structured responses:

```python
# Success
return {
    "success": True,
    "result": data,
    "metadata": {...}
}

# Failure
return {
    "success": False,
    "error": "Human readable error",
    "error_code": "ERROR_CODE"
}
```

## Testing Tools

```python
# Test the tool function directly
async def test_my_tool():
    result = await my_tool("BTC", 0.5)
    assert result["success"]
    assert "result" in result

# Test via MCP client
async def test_mcp_tool():
    from backend.mcp_broker.client import ToolBrokerClient

    client = ToolBrokerClient()
    result = await client.call_tool("my__tool", {
        "symbol": "BTC",
        "param": 0.5
    })
```

## Tool Registry

Tools are automatically registered in the MCP server. The naming convention is:

```
<category>__<tool_name>

Examples:
- vedastro__generate_signal
- elemental__fire_position_size
- execution__execute_paper_trade
```

## SOC2 Audit Logging

All tool calls must be logged for SOC2 compliance:

```python
@circuit_breaker(failure_threshold=5, timeout_seconds=30)
async def audited_tool(symbol: str, ctx=None) -> dict:
    """Tool with audit logging."""
    start_time = time.time()

    try:
        result = await _process(symbol)

        # Audit log
        logger.info(f"TOOL_CALL: {symbol}, success=True, duration={time.time()-start_time}")

        return {"success": True, "result": result}
    except Exception as e:
        # Audit log failure
        logger.error(f"TOOL_CALL: {symbol}, success=False, error={e}")
        return {"success": False, "error": str(e)}
```

## Best Practices

1. **Always use circuit breaker** for external calls
2. **Always add timeouts** to network requests
3. **Return structured responses** (success/error dict)
4. **Log with ctx.info()** for debugging
5. **Handle exceptions gracefully** - never crash the server
6. **Validate inputs** using Pydantic models
7. **Document parameters** in docstrings
8. **Add audit logging** for SOC2 compliance

## Common Pitfalls

### Bad
```python
async def bad_tool(symbol):
    result = requests.get(f"https://api.com/{symbol}")  # No timeout
    return result.json()  # No error handling
```

### Good
```python
@circuit_breaker(failure_threshold=5, timeout_seconds=30)
async def good_tool(symbol: str, ctx=None) -> dict:
    try:
        result = requests.get(
            f"https://api.com/{symbol}",
            timeout=30  # Always timeout
        )
        result.raise_for_status()
        return {"success": True, "result": result.json()}
    except Exception as e:
        logger.error(f"Tool failed: {e}")
        return {"success": False, "error": str(e)}
```
