"""
MCP Client Wrapper for BacktestEngine.

Provides a synchronous-style interface for calling MCP tools
from within the backtest loop.
"""

import asyncio
import logging
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class MCPClientWrapper:
    """
    Wrapper for MCP client that provides synchronous-style interface.

    Usage:
        client = MCPClientWrapper()
        result = await client.call_tool("elemental__fire_position_size", {...})
    """

    def __init__(self, server_params: StdioServerParameters | None = None):
        """
        Initialize MCP client wrapper.

        Args:
            server_params: Optional custom server parameters.
                          If not provided, uses default local server.
        """
        if server_params is None:
            import sys
            from pathlib import Path

            project_root = Path(__file__).parent.parent.parent

            self.server_params = StdioServerParameters(
                command=sys.executable,
                args=["-m", "backend.mcp_broker.server"],
                env={"PYTHONPATH": str(project_root)},
            )
        else:
            self.server_params = server_params

        self._session: ClientSession | None = None
        self._stdio_context = None
        self._initialized = False

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def initialize(self):
        """Initialize connection to MCP server."""
        if self._initialized:
            return

        logger.info("Initializing MCP client connection...")

        self._stdio_context = stdio_client(self.server_params)
        read, write = await self._stdio_context.__aenter__()

        self._session = ClientSession(read, write)
        await self._session.initialize()

        self._initialized = True
        logger.info("MCP client connected successfully")

    async def close(self):
        """Close connection to MCP server."""
        if not self._initialized:
            return

        logger.info("Closing MCP client connection...")

        if self._stdio_context:
            await self._stdio_context.__aexit__(None, None, None)

        self._session = None
        self._initialized = False
        logger.info("MCP client disconnected")

    async def call_tool(
        self, tool_name: str, params: dict[str, Any], timeout: float = 30.0
    ) -> dict[str, Any]:
        """
        Call an MCP tool.

        Args:
            tool_name: Name of the tool (e.g., "elemental__fire_position_size")
            params: Tool parameters
            timeout: Timeout in seconds

        Returns:
            Tool result as dictionary
        """
        if not self._initialized:
            await self.initialize()

        try:
            result = await asyncio.wait_for(
                self._session.call_tool(tool_name, params), timeout=timeout
            )

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

        except TimeoutError:
            logger.error(f"Tool call timeout: {tool_name}")
            raise
        except Exception as e:
            logger.error(f"Tool call failed: {tool_name} - {e}")
            raise

    async def list_tools(self) -> list[str]:
        """List available tools."""
        if not self._initialized:
            await self.initialize()

        tools = await self._session.list_tools()
        return [tool.name for tool in tools.tools]

    async def health_check(self) -> dict[str, Any]:
        """Check system health."""
        return await self.call_tool("system__health_check", {})


class SynchronousMCPClient:
    """
    Synchronous wrapper for MCP client.

    This allows using MCP tools from synchronous code (like existing backtests).
    """

    def __init__(self):
        self._async_client: MCPClientWrapper | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    def connect(self):
        """Connect to MCP server (synchronous)."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        self._async_client = MCPClientWrapper()
        self._loop.run_until_complete(self._async_client.initialize())

        logger.info("Synchronous MCP client connected")

    def disconnect(self):
        """Disconnect from MCP server (synchronous)."""
        if self._async_client and self._loop:
            self._loop.run_until_complete(self._async_client.close())
            self._loop.close()
            logger.info("Synchronous MCP client disconnected")

    def call_tool(
        self, tool_name: str, params: dict[str, Any], timeout: float = 30.0
    ) -> dict[str, Any]:
        """
        Call an MCP tool (synchronous).

        Args:
            tool_name: Name of the tool
            params: Tool parameters
            timeout: Timeout in seconds

        Returns:
            Tool result
        """
        if not self._async_client:
            raise RuntimeError("Client not connected. Call connect() first.")

        return self._loop.run_until_complete(
            self._async_client.call_tool(tool_name, params, timeout)
        )

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


# Convenience functions for direct tool calls


async def get_elemental_consensus(
    fire_vote: float,
    earth_vote: float,
    water_vote: float,
    air_vote: float,
    client: MCPClientWrapper | None = None,
) -> dict[str, Any]:
    """Get elemental consensus decision."""
    params = {
        "fire_vote": fire_vote,
        "earth_vote": earth_vote,
        "water_vote": water_vote,
        "air_vote": air_vote,
    }

    if client:
        return await client.call_tool("elemental__ether_consensus", params)
    else:
        async with MCPClientWrapper() as c:
            return await c.call_tool("elemental__ether_consensus", params)


async def get_position_size(
    symbol: str,
    portfolio_value: float,
    vedastro_score: float,
    dominant_planet: str,
    price_history: list[float],
    client: MCPClientWrapper | None = None,
) -> dict[str, Any]:
    """Calculate position size using Fire element."""
    params = {
        "symbol": symbol,
        "portfolio_value": portfolio_value,
        "vedastro_score": vedastro_score,
        "dominant_planet": dominant_planet,
        "price_history": price_history,
    }

    if client:
        return await client.call_tool("elemental__fire_position_size", params)
    else:
        async with MCPClientWrapper() as c:
            return await c.call_tool("elemental__fire_position_size", params)


async def check_entry_allowed(
    symbol: str,
    trade_history: list[dict[str, Any]],
    client: MCPClientWrapper | None = None,
) -> bool:
    """Check if entry is allowed (Earth element)."""
    params = {"symbol": symbol, "trade_history": trade_history}

    if client:
        result = await client.call_tool("elemental__earth_entry_check", params)
    else:
        async with MCPClientWrapper() as c:
            result = await c.call_tool("elemental__earth_entry_check", params)

    return result.get("can_enter", False)


async def check_exit_needed(
    symbol: str,
    entry_date: str,
    current_date: str,
    entry_price: float,
    current_price: float,
    peak_price: float,
    client: MCPClientWrapper | None = None,
) -> dict[str, Any]:
    """Check if position should be exited."""
    params = {
        "symbol": symbol,
        "entry_date": entry_date,
        "current_date": current_date,
        "entry_price": entry_price,
        "current_price": current_price,
        "peak_price": peak_price,
    }

    if client:
        return await client.call_tool("elemental__earth_exit_check", params)
    else:
        async with MCPClientWrapper() as c:
            return await c.call_tool("elemental__earth_exit_check", params)


async def get_vedastro_signal(
    symbol: str, current_price: float, client: MCPClientWrapper | None = None
) -> dict[str, Any]:
    """Get VedAstro trading signal."""
    params = {"symbol": symbol, "current_price": current_price}

    if client:
        return await client.call_tool("vedastro__generate_signal", params)
    else:
        async with MCPClientWrapper() as c:
            return await c.call_tool("vedastro__generate_signal", params)


async def execute_paper_trade(
    symbol: str,
    action: str,
    quantity: float,
    current_price: float,
    account_id: str,
    client: MCPClientWrapper | None = None,
) -> dict[str, Any]:
    """Execute a paper trade."""
    params = {
        "symbol": symbol,
        "action": action,
        "quantity": quantity,
        "current_price": current_price,
        "account_id": account_id,
    }

    if client:
        return await client.call_tool("execution__execute_paper_trade", params)
    else:
        async with MCPClientWrapper() as c:
            return await c.call_tool("execution__execute_paper_trade", params)


# Global client instance for convenience
_global_client: MCPClientWrapper | None = None


async def get_client() -> MCPClientWrapper:
    """Get or create global MCP client instance."""
    global _global_client
    if _global_client is None:
        _global_client = MCPClientWrapper()
        await _global_client.initialize()
    return _global_client


async def close_global_client() -> None:
    """Close global client if open."""
    global _global_client
    if _global_client:
        await _global_client.close()
        _global_client = None
