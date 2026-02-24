"""
Execution MCP Tools.

Paper trading en order execution.
"""

import logging
from datetime import datetime
from typing import Any

from mcp.server.fastmcp import Context

from backend.mcp_broker.resilience import circuit_breaker

logger = logging.getLogger(__name__)

# V17 Constants
COMMISSION_PCT = 0.0005  # 0.05%
SLIPPAGE_PCT = 0.001  # 0.1%
MAX_POSITION_EUR = 2000.0


@circuit_breaker(failure_threshold=5, timeout_seconds=15)
async def execution_execute_paper_trade(
    symbol: str,
    action: str,
    quantity: float,
    current_price: float,
    account_id: str,
    ctx: Context = None,
) -> dict[str, Any]:
    """
    Execute a paper trade.

    V17 Constraints:
    - Max €2,000 position size
    - 0.05% commission
    - 0.1% slippage

    Args:
        symbol: Asset symbol
        action: BUY or SELL
        quantity: Number of shares/contracts
        current_price: Current market price
        account_id: Account identifier
        ctx: MCP context

    Returns:
        Trade execution details
    """
    if ctx:
        ctx.info(f"Executing {action} {quantity} {symbol} for {account_id}")

    # Validate action
    action = action.upper()
    if action not in ["BUY", "SELL"]:
        raise ValueError(f"Invalid action: {action}. Must be BUY or SELL")

    # Validate quantity
    if quantity <= 0:
        raise ValueError(f"Invalid quantity: {quantity}. Must be positive")

    # Calculate execution price with slippage
    if action == "BUY":
        execution_price = current_price * (1 + SLIPPAGE_PCT)
    else:
        execution_price = current_price * (1 - SLIPPAGE_PCT)

    # Calculate gross value
    gross_value = quantity * execution_price

    # V17: Check max position size for BUY
    if action == "BUY" and gross_value > MAX_POSITION_EUR:
        error_msg = f"Position size €{gross_value:.2f} exceeds maximum of €{MAX_POSITION_EUR}"
        if ctx:
            ctx.error(error_msg)
        raise ValueError(error_msg)

    try:
        # Try to execute via paper exchange
        from backend.execution.paper_exchange import PaperExchange

        exchange = PaperExchange(account_id=account_id)

        order = await exchange.place_order(
            symbol=symbol,
            side=action.lower(),
            quantity=quantity,
            order_type="market",
            current_price=current_price,
        )

        if ctx:
            ctx.info(f"Trade executed: {order.id}")

        return {
            "order_id": order.id,
            "status": order.status,
            "symbol": symbol,
            "action": action,
            "quantity": quantity,
            "filled_price": order.filled_price,
            "gross_value": gross_value,
            "commission": order.commission,
            "net_value": gross_value - order.commission,
            "timestamp": order.timestamp.isoformat(),
            "account_id": account_id,
            "constraints_applied": ["max_2000_eur", "commission_0.05pct", "slippage_0.1pct"],
        }

    except Exception as e:
        logger.warning(f"Paper exchange failed: {e}, using mock execution")

        # Fallback: mock execution
        # Calculate commission
        commission = gross_value * COMMISSION_PCT
        net_value = gross_value - commission

        # Generate order ID
        order_id = f"paper_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{symbol}"

        if ctx:
            ctx.info(f"Mock trade executed: {order_id}")

        return {
            "order_id": order_id,
            "status": "FILLED",
            "symbol": symbol,
            "action": action,
            "quantity": quantity,
            "filled_price": execution_price,
            "gross_value": gross_value,
            "commission": commission,
            "net_value": net_value,
            "timestamp": datetime.utcnow().isoformat(),
            "account_id": account_id,
            "constraints_applied": ["max_2000_eur", "commission_0.05pct", "slippage_0.1pct"],
            "note": "Mock execution for testing",
        }


@circuit_breaker(failure_threshold=5, timeout_seconds=10)
async def execution_get_open_positions(account_id: str, ctx: Context = None) -> dict[str, Any]:
    """
    Get all open positions for an account.

    Args:
        account_id: Account identifier
        ctx: MCP context

    Returns:
        List of open positions
    """
    if ctx:
        ctx.info(f"Fetching open positions for {account_id}")

    try:
        from backend.execution.paper_exchange import PaperExchange

        exchange = PaperExchange(account_id=account_id)
        positions = await exchange.get_positions()

        return {
            "account_id": account_id,
            "positions": [
                {
                    "symbol": pos.symbol,
                    "quantity": pos.quantity,
                    "entry_price": pos.entry_price,
                    "current_price": pos.current_price,
                    "unrealized_pnl": pos.unrealized_pnl,
                    "unrealized_pnl_pct": pos.unrealized_pnl_pct,
                    "entry_date": (
                        pos.entry_date.isoformat()
                        if hasattr(pos.entry_date, "isoformat")
                        else str(pos.entry_date)
                    ),
                }
                for pos in positions
            ],
            "count": len(positions),
        }

    except Exception as e:
        logger.warning(f"Failed to get positions: {e}, using mock")

        return {
            "account_id": account_id,
            "positions": [],
            "count": 0,
            "note": "Mock data for testing",
        }


@circuit_breaker(failure_threshold=3, timeout_seconds=10)
async def execution_close_position(
    symbol: str, account_id: str, current_price: float, ctx: Context = None
) -> dict[str, Any]:
    """
    Close an open position.

    Args:
        symbol: Asset symbol
        account_id: Account identifier
        current_price: Current market price
        ctx: MCP context

    Returns:
        Close order details
    """
    if ctx:
        ctx.info(f"Closing position {symbol} for {account_id}")

    try:
        from backend.execution.paper_exchange import PaperExchange

        exchange = PaperExchange(account_id=account_id)

        # Get position
        position = await exchange.get_position(symbol)
        if not position:
            raise ValueError(f"No open position found for {symbol}")

        # Close position (sell if long, buy if short)
        action = "SELL" if position.quantity > 0 else "BUY"
        quantity = abs(position.quantity)

        order = await exchange.place_order(
            symbol=symbol,
            side="sell" if position.quantity > 0 else "buy",
            quantity=quantity,
            order_type="market",
            current_price=current_price,
        )

        if ctx:
            ctx.info(f"Position closed: {order.id}")

        return {
            "order_id": order.id,
            "status": order.status,
            "symbol": symbol,
            "action": action,
            "quantity": quantity,
            "filled_price": order.filled_price,
            "realized_pnl": position.unrealized_pnl,  # Approximation
            "timestamp": order.timestamp.isoformat(),
            "account_id": account_id,
        }

    except Exception as e:
        logger.error(f"Failed to close position: {e}")
        raise


@circuit_breaker(failure_threshold=5, timeout_seconds=10)
async def execution_get_trade_history(
    account_id: str, limit: int = 100, ctx: Context = None
) -> dict[str, Any]:
    """
    Get trade history for an account.

    Args:
        account_id: Account identifier
        limit: Maximum number of trades to return
        ctx: MCP context

    Returns:
        Trade history
    """
    if ctx:
        ctx.info(f"Fetching trade history for {account_id}")

    try:
        from backend.execution.paper_exchange import PaperExchange

        exchange = PaperExchange(account_id=account_id)
        trades = await exchange.get_trade_history(limit=limit)

        return {
            "account_id": account_id,
            "trades": [
                {
                    "order_id": trade.id,
                    "symbol": trade.symbol,
                    "action": trade.side.upper(),
                    "quantity": trade.quantity,
                    "price": trade.price,
                    "commission": trade.commission,
                    "timestamp": (
                        trade.timestamp.isoformat()
                        if hasattr(trade.timestamp, "isoformat")
                        else str(trade.timestamp)
                    ),
                    "pnl": getattr(trade, "pnl", 0.0),
                }
                for trade in trades
            ],
            "count": len(trades),
        }

    except Exception as e:
        logger.warning(f"Failed to get trade history: {e}, using mock")

        return {"account_id": account_id, "trades": [], "count": 0, "note": "Mock data for testing"}
