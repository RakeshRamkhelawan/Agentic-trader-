"""
API Endpoints for MCP ToolBroker monitoring and control.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from backend.core.auth.middleware import require_auth
from backend.mcp_broker.resilience import get_circuit_state
from backend.mcp_broker.server import mcp

router = APIRouter(prefix="/v1/mcp", tags=["MCP ToolBroker"])


@router.get("/tools")
async def list_mcp_tools(user: dict = Depends(require_auth)) -> dict[str, Any]:
    """
    List all available MCP tools.

    Returns:
        List of registered tools with their schemas
    """
    try:
        tool_manager = mcp._tool_manager
        tools = tool_manager._tools

        tool_list = []
        for name, tool in tools.items():
            tool_list.append(
                {
                    "name": name,
                    "description": getattr(tool, "description", "No description"),
                }
            )

        return {"tools": tool_list, "count": len(tool_list)}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tools: {str(e)}",
        )


@router.get("/health")
async def mcp_health_check(user: dict = Depends(require_auth)) -> dict[str, Any]:
    """
    Check MCP ToolBroker health status.

    Returns:
        Health status and circuit breaker states
    """
    try:
        # Get circuit breaker states
        tools = [
            "vedastro_generate_signal",
            "elemental_fire_position_size",
            "elemental_earth_entry_check",
            "elemental_earth_exit_check",
            "elemental_water_regime_check",
            "elemental_ether_consensus",
        ]

        circuit_states = {}
        for tool in tools:
            state = get_circuit_state(tool)
            if state:
                circuit_states[tool] = state
            else:
                circuit_states[tool] = {"state": "closed"}

        all_healthy = all(s.get("state") == "closed" for s in circuit_states.values())

        return {
            "status": "healthy" if all_healthy else "degraded",
            "server_name": "AgenticTraderBroker",
            "version": "1.0.0",
            "circuit_breaker_states": circuit_states,
            "tool_count": len(mcp._tool_manager._tools),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}",
        )


@router.get("/circuit-breakers")
async def get_circuit_breaker_states(
    user: dict = Depends(require_auth),
) -> dict[str, Any]:
    """
    Get detailed circuit breaker states.

    Returns:
        Circuit breaker states for all tools
    """
    try:
        from backend.mcp_broker.resilience.circuit_breaker import CircuitBreaker

        states = {}
        for name, breaker in CircuitBreaker._instances.items():
            states[name] = breaker.get_state()

        return {"circuit_breakers": states, "count": len(states)}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get circuit breaker states: {str(e)}",
        )


@router.post("/tools/{tool_name}/execute")
async def execute_mcp_tool(
    tool_name: str, params: dict[str, Any], user: dict = Depends(require_auth)
) -> dict[str, Any]:
    """
    Execute an MCP tool directly via HTTP.

    Args:
        tool_name: Name of the tool to execute
        params: Tool parameters

    Returns:
        Tool execution result
    """
    try:
        # Check if tool exists
        tool_manager = mcp._tool_manager
        if tool_name not in tool_manager._tools:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool '{tool_name}' not found",
            )

        # Execute tool
        result = await mcp.call_tool(tool_name, params)

        # Parse result
        if result.content and len(result.content) > 0:
            content = result.content[0]
            if hasattr(content, "text"):
                import json

                try:
                    return json.loads(content.text)
                except json.JSONDecodeError:
                    return {"result": content.text}

        return {"success": True}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tool execution failed: {str(e)}",
        )


@router.get("/stats")
async def get_mcp_stats(user: dict = Depends(require_auth)) -> dict[str, Any]:
    """
    Get MCP ToolBroker statistics.

    Returns:
        Usage statistics and metrics
    """
    try:
        tool_manager = mcp._tool_manager
        tools = tool_manager._tools

        return {
            "total_tools": len(tools),
            "tool_categories": {
                "vedastro": len([t for t in tools if t.startswith("vedastro")]),
                "elemental": len([t for t in tools if t.startswith("elemental")]),
                "data": len([t for t in tools if t.startswith("data")]),
                "execution": len([t for t in tools if t.startswith("execution")]),
                "system": len([t for t in tools if t.startswith("system")]),
            },
            "server_version": "1.0.0",
            "protocol": "MCP",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}",
        )


@router.post("/backtest/run")
async def run_backtest_v18_endpoint(
    symbols: list[str],
    start_date: str,
    end_date: str,
    initial_cash: float = 100000.0,
    user: dict = Depends(require_auth),
) -> dict[str, Any]:
    """
    Run a backtest using MCP tools.

    Args:
        symbols: List of symbols to trade
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
        initial_cash: Initial cash

    Returns:
        Backtest results
    """
    try:
        from datetime import datetime

        from backend.mcp_broker import run_backtest_v18

        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)

        results = await run_backtest_v18(
            symbols=symbols, start_date=start, end_date=end, initial_cash=initial_cash
        )

        return results

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Backtest failed: {str(e)}",
        )
