"""
HTTP Server for MCP ToolBroker.

Provides HTTP endpoints for agents to call tools via the ToolBroker.
This allows easy integration with the existing FastAPI-based architecture.
"""

import json
import logging
import sys
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# Import MCP server
from backend.mcp_broker.server import mcp


# ============================================================================
# Pydantic Models
# ============================================================================

class ToolCallRequest(BaseModel):
    """Request model for tool calls."""
    tool_name: str = Field(..., description="Name of the tool to call")
    params: dict[str, Any] = Field(default_factory=dict, description="Tool parameters")
    timeout: float = Field(default=30.0, description="Timeout in seconds")


class ToolCallResponse(BaseModel):
    """Response model for tool calls."""
    success: bool
    result: dict[str, Any] | None = None
    error: str | None = None
    execution_time_ms: float | None = None


class ToolInfo(BaseModel):
    """Tool information."""
    name: str
    description: str
    parameters: dict[str, Any]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    server_name: str
    version: str
    tools_available: int


# ============================================================================
# FastAPI App
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("MCP HTTP Server starting...")
    yield
    logger.info("MCP HTTP Server shutting down...")


app = FastAPI(
    title="MCP ToolBroker HTTP API",
    description="HTTP interface for MCP Tool execution",
    version="1.0.0",
    lifespan=lifespan,
)


# ============================================================================
# Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    tools = list(mcp._tool_manager._tools.keys())
    return HealthResponse(
        status="healthy",
        server_name="AgenticTraderBroker",
        version="1.0.0",
        tools_available=len(tools),
    )


@app.get("/tools")
async def list_tools():
    """List all available tools."""
    tools = []
    for name, tool in mcp._tool_manager._tools.items():
        tools.append({
            "name": name,
            "description": getattr(tool, "description", "No description"),
        })
    return {"tools": tools, "count": len(tools)}


@app.post("/tools/call", response_model=ToolCallResponse)
async def call_tool(request: ToolCallRequest):
    """
    Call an MCP tool via HTTP.
    
    This endpoint allows agents to call tools via HTTP instead of MCP protocol.
    """
    import time
    
    start_time = time.time()
    
    try:
        # Get the tool
        tool = mcp._tool_manager._tools.get(request.tool_name)
        if not tool:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool '{request.tool_name}' not found"
            )
        
        # Call the tool
        logger.info(f"Calling tool: {request.tool_name}")
        
        # The tool is an async function, call it with params
        result = await tool(**request.params)
        
        execution_time = (time.time() - start_time) * 1000
        
        return ToolCallResponse(
            success=True,
            result=result if isinstance(result, dict) else {"result": result},
            execution_time_ms=execution_time,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Tool call failed: {e}")
        return ToolCallResponse(
            success=False,
            error=str(e),
            execution_time_ms=(time.time() - start_time) * 1000,
        )


@app.post("/tools/call/{tool_name}", response_model=ToolCallResponse)
async def call_tool_by_path(tool_name: str, params: dict[str, Any] = None):
    """
    Call a tool by path.
    
    Example: POST /tools/call/vedastro__generate_signal
    """
    if params is None:
        params = {}
    
    request = ToolCallRequest(tool_name=tool_name, params=params)
    return await call_tool(request)


@app.get("/tools/{tool_name}")
async def get_tool_info(tool_name: str):
    """Get detailed information about a tool."""
    tool = mcp._tool_manager._tools.get(tool_name)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_name}' not found"
        )
    
    # Extract parameter info from the function signature
    import inspect
    sig = inspect.signature(tool)
    params = {}
    for param_name, param in sig.parameters.items():
        if param_name == "ctx":
            continue
        params[param_name] = {
            "default": str(param.default) if param.default is not inspect.Parameter.empty else None,
            "annotation": str(param.annotation) if param.annotation is not inspect.Parameter.empty else "Any",
        }
    
    return {
        "name": tool_name,
        "description": getattr(tool, "description", "No description"),
        "parameters": params,
    }


# ============================================================================
# Convenience Endpoints for Common Operations
# ============================================================================

@app.post("/vedastro/signal")
async def vedastro_signal(symbol: str, current_price: float):
    """Get VedAstro signal for a symbol."""
    request = ToolCallRequest(
        tool_name="vedastro__generate_signal",
        params={"symbol": symbol, "current_price": current_price}
    )
    return await call_tool(request)


@app.post("/elemental/consensus")
async def elemental_consensus(
    fire_vote: float,
    earth_vote: float,
    water_vote: float,
    air_vote: float,
):
    """Get elemental consensus."""
    request = ToolCallRequest(
        tool_name="elemental__ether_consensus",
        params={
            "fire_vote": fire_vote,
            "earth_vote": earth_vote,
            "water_vote": water_vote,
            "air_vote": air_vote,
        }
    )
    return await call_tool(request)


@app.post("/elemental/position-size")
async def position_size(
    symbol: str,
    portfolio_value: float,
    vedastro_score: float,
    dominant_planet: str,
    price_history: list[float],
):
    """Calculate position size."""
    request = ToolCallRequest(
        tool_name="elemental__fire_position_size",
        params={
            "symbol": symbol,
            "portfolio_value": portfolio_value,
            "vedastro_score": vedastro_score,
            "dominant_planet": dominant_planet,
            "price_history": price_history,
        }
    )
    return await call_tool(request)


if __name__ == "__main__":
    import uvicorn
    
    host = "0.0.0.0"  # nosec B104 - Required for Docker/containerized deployment
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
    
    logger.info(f"Starting MCP HTTP Server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
