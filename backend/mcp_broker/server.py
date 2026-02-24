"""
FastMCP Server - De ToolBroker.

Centrale MCP server die alle trading tools exposeert.
Gebruikt Anthropic's officiële MCP SDK.

⚠️  BELANGRIJK: Alles naar stderr loggen om JSON-RPC stream niet te corrumperen!
"""

import logging
import sys
from datetime import datetime
from typing import Any

from mcp.server.fastmcp import FastMCP

# CRUCIAL: Configure logging naar STDERR (nooit stdout!)
# stdout is gereserveerd voor MCP JSON-RPC communicatie
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,  # ALTIJD naar stderr voor MCP compatibiliteit
)
logger = logging.getLogger(__name__)

# Import tools
from backend.mcp_broker.resilience import get_circuit_state
from backend.mcp_broker.tools.data_tools import (
    data_get_historical_prices,
    data_get_market_regime,
    data_get_portfolio_status,
)
from backend.mcp_broker.tools.elemental_tools import (
    elemental_earth_entry_check,
    elemental_earth_exit_check,
    elemental_ether_consensus,
    elemental_fire_position_size,
    elemental_water_regime_check,
)
from backend.mcp_broker.tools.execution_tools import (
    execution_close_position,
    execution_execute_paper_trade,
    execution_get_open_positions,
    execution_get_trade_history,
)
from backend.mcp_broker.tools.vedastro_tools import (
    vedastro_generate_signal,
    vedastro_get_dasha,
    vedastro_get_transits,
)

# Initialize FastMCP server
mcp = FastMCP("AgenticTraderBroker")

# ============================================================================
# VEDASTRO TOOLS
# ============================================================================


@mcp.tool()
async def vedastro__generate_signal(
    symbol: str,
    current_price: float,
) -> dict[str, Any]:
    """
    Generate trading signal from astrological data.

    Args:
        symbol: Asset symbol (e.g., "AAPL", "BTC")
        current_price: Current market price

    Returns:
        Trading signal with confidence and astrological context
    """

    # Create a minimal context for logging
    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

        def error(self, msg):
            logger.error(msg)

        def warning(self, msg):
            logger.warning(msg)

    ctx = MinimalContext()
    return await vedastro_generate_signal(symbol, current_price, ctx)


@mcp.tool()
async def vedastro__get_dasha(symbol: str) -> dict[str, Any]:
    """
    Get current Dasha period for an asset.

    Args:
        symbol: Asset symbol

    Returns:
        Dasha information including Mahadasha, Antardasha
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

        def error(self, msg):
            logger.error(msg)

    ctx = MinimalContext()
    return await vedastro_get_dasha(symbol, ctx)


@mcp.tool()
async def vedastro__get_transits(symbol: str) -> dict[str, Any]:
    """
    Get current planetary transits.

    Args:
        symbol: Asset symbol

    Returns:
        Transit information
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

        def error(self, msg):
            logger.error(msg)

    ctx = MinimalContext()
    return await vedastro_get_transits(symbol, ctx)


# ============================================================================
# ELEMENTAL TOOLS
# ============================================================================


@mcp.tool()
async def elemental__fire_position_size(
    symbol: str,
    portfolio_value: float,
    vedastro_score: float,
    dominant_planet: str,
    price_history: list,
) -> dict[str, Any]:
    """
    Calculate position size using Fire element logic.

    Constraints:
    - Max €2,000 per position
    - Max 2% of portfolio

    Args:
        symbol: Asset symbol
        portfolio_value: Total portfolio value
        vedastro_score: VedAstro strength (0-100)
        dominant_planet: Dominant planet
        price_history: Recent prices for volatility

    Returns:
        Position sizing recommendation
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await elemental_fire_position_size(
        symbol, portfolio_value, vedastro_score, dominant_planet, price_history, ctx
    )


@mcp.tool()
async def elemental__earth_entry_check(
    symbol: str,
    trade_history: list,
) -> dict[str, Any]:
    """
    Check if entry is allowed (Earth element).

    Blocks entry after 3 consecutive losses.

    Args:
        symbol: Asset symbol
        trade_history: Recent trade history

    Returns:
        Entry permission
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await elemental_earth_entry_check(symbol, trade_history, ctx)


@mcp.tool()
async def elemental__earth_exit_check(
    symbol: str,
    entry_date: str,
    current_date: str,
    entry_price: float,
    current_price: float,
    peak_price: float,
) -> dict[str, Any]:
    """
    Check if position should be exited (Earth element).

    Constraints:
    - Max 60 days hold
    - Trailing stop: +40% peak → -15% drop

    Args:
        symbol: Asset symbol
        entry_date: Entry date (ISO format)
        current_date: Current date (ISO format)
        entry_price: Entry price
        current_price: Current price
        peak_price: Peak price since entry

    Returns:
        Exit recommendation
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await elemental_earth_exit_check(
        symbol, entry_date, current_date, entry_price, current_price, peak_price, ctx
    )


@mcp.tool()
async def elemental__water_regime_check(
    symbol: str,
    prices: list,
) -> dict[str, Any]:
    """
    Check macro regime and hedge signals (Water element).

    Args:
        symbol: Asset symbol
        prices: Price history (min 20 points)

    Returns:
        Regime assessment
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await elemental_water_regime_check(symbol, prices, ctx)


@mcp.tool()
async def elemental__ether_consensus(
    fire_vote: float,
    earth_vote: float,
    water_vote: float,
    air_vote: float,
) -> dict[str, Any]:
    """
    Synthesize elemental consensus.

    Args:
        fire_vote: Fire score (0-1)
        earth_vote: Earth score (0-1)
        water_vote: Water score (0-1)
        air_vote: Air score (0-1)

    Returns:
        Consensus decision (approved if harmony > 0.45)
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await elemental_ether_consensus(fire_vote, earth_vote, water_vote, air_vote, ctx)


# ============================================================================
# DATA TOOLS
# ============================================================================


@mcp.tool()
async def data__get_historical_prices(
    symbol: str,
    start_date: str,
    end_date: str,
    timeframe: str = "1d",
) -> dict[str, Any]:
    """
    Get historical price data.

    Args:
        symbol: Asset symbol
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
        timeframe: Data timeframe (1m, 5m, 1h, 1d)

    Returns:
        OHLCV data
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await data_get_historical_prices(symbol, start_date, end_date, timeframe, ctx)


@mcp.tool()
async def data__get_portfolio_status(
    account_id: str,
) -> dict[str, Any]:
    """
    Get current portfolio status.

    Args:
        account_id: Account identifier

    Returns:
        Portfolio summary
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await data_get_portfolio_status(account_id, ctx)


@mcp.tool()
async def data__get_market_regime(
    symbol: str,
) -> dict[str, Any]:
    """
    Get current market regime for a symbol.

    Args:
        symbol: Asset symbol

    Returns:
        Market regime assessment
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await data_get_market_regime(symbol, ctx)


# ============================================================================
# EXECUTION TOOLS
# ============================================================================


@mcp.tool()
async def execution__execute_paper_trade(
    symbol: str,
    action: str,
    quantity: float,
    current_price: float,
    account_id: str,
) -> dict[str, Any]:
    """
    Execute a paper trade.

    Constraints:
    - Max €2,000 position size
    - 0.05% commission
    - 0.1% slippage

    Args:
        symbol: Asset symbol
        action: BUY or SELL
        quantity: Number of shares
        current_price: Current market price
        account_id: Account identifier

    Returns:
        Trade execution details
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

        def error(self, msg):
            logger.error(msg)

    ctx = MinimalContext()
    return await execution_execute_paper_trade(
        symbol, action, quantity, current_price, account_id, ctx
    )


@mcp.tool()
async def execution__get_open_positions(
    account_id: str,
) -> dict[str, Any]:
    """
    Get all open positions for an account.

    Args:
        account_id: Account identifier

    Returns:
        List of open positions
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await execution_get_open_positions(account_id, ctx)


@mcp.tool()
async def execution__close_position(
    symbol: str,
    account_id: str,
    current_price: float,
) -> dict[str, Any]:
    """
    Close an open position.

    Args:
        symbol: Asset symbol
        account_id: Account identifier
        current_price: Current market price

    Returns:
        Close order details
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await execution_close_position(symbol, account_id, current_price, ctx)


@mcp.tool()
async def execution__get_trade_history(
    account_id: str,
    limit: int = 100,
) -> dict[str, Any]:
    """
    Get trade history for an account.

    Args:
        account_id: Account identifier
        limit: Maximum number of trades to return

    Returns:
        Trade history
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await execution_get_trade_history(account_id, limit, ctx)


# ============================================================================
# HEALTH & MONITORING
# ============================================================================


@mcp.tool()
async def system__health_check() -> dict[str, Any]:
    """
    Check system health and circuit breaker states.

    Returns:
        Health status of all components
    """
    tools = [
        "vedastro_generate_signal",
        "vedastro_get_dasha",
        "elemental_fire_position_size",
        "elemental_earth_entry_check",
        "elemental_water_regime_check",
        "elemental_ether_consensus",
    ]

    circuit_states = {}
    for tool in tools:
        state = get_circuit_state(tool)
        if state:
            circuit_states[tool] = state["state"]
        else:
            circuit_states[tool] = "closed"

    all_healthy = all(s == "closed" for s in circuit_states.values())

    return {
        "status": "healthy" if all_healthy else "degraded",
        "circuit_breaker_states": circuit_states,
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Starting AgenticTraderBroker MCP Server")
    logger.info("=" * 60)
    logger.info("Server Name: AgenticTraderBroker")
    logger.info("Transport: stdio")

    # Get registered tools
    tool_manager = mcp._tool_manager
    tools = tool_manager._tools

    logger.info(f"Tools registered: {len(tools)}")
    logger.info("")
    logger.info("Available tools:")
    for tool_name in sorted(tools.keys()):
        logger.info(f"  - {tool_name}")
    logger.info("=" * 60)

    # Run with stdio transport (for Claude Desktop, etc.)
    mcp.run(transport="stdio")
