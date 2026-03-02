"""
Live Trading MCP Tools.

Real trade execution with risk controls and confirmation.
"""

import logging
from typing import Any

from backend.mcp_broker.resilience import circuit_breaker

logger = logging.getLogger(__name__)


@circuit_breaker(failure_threshold=3, timeout_seconds=30)
async def live_trading_place_order(
    symbol: str,
    side: str,
    quantity: float,
    order_type: str = "market",
    price: float | None = None,
    exchange: str | None = None,
    ctx=None,
) -> dict[str, Any]:
    """
    Place a LIVE order on an exchange (REAL MONEY).

    WARNING: This executes real trades with actual funds!
    Make sure you have configured API credentials and understand the risks.

    Args:
        symbol: Trading pair (e.g., 'BTC-EUR', 'BTC-USD')
        side: 'buy' or 'sell'
        quantity: Order quantity in base currency
        order_type: 'market' or 'limit'
        price: Limit price (required for limit orders)
        exchange: 'bitvavo', 'revolutx', or 'auto' for best price
        ctx: MCP context

    Returns:
        Order details with confirmation
    """
    if ctx:
        ctx.info(f"[LIVE TRADE] {side.upper()} {quantity} {symbol} on {exchange or 'auto'}")

    try:
        from backend.execution.live_multi_exchange_trading import (
            get_live_trading_service,
        )

        # Validate inputs
        side_lower = side.lower()
        if side_lower not in ["buy", "sell"]:
            return {"success": False, "error": f"Invalid side: {side}. Must be 'buy' or 'sell'"}

        type_lower = order_type.lower()
        if type_lower not in ["market", "limit"]:
            return {"success": False, "error": f"Invalid order_type: {order_type}. Must be 'market' or 'limit'"}

        if type_lower == "limit" and price is None:
            return {"success": False, "error": "Price is required for limit orders"}

        if quantity <= 0:
            return {"success": False, "error": "Quantity must be positive"}

        # Get trading service
        trading = await get_live_trading_service()

        # Place order
        order = await trading.place_order(
            symbol=symbol,
            side=side_lower,
            quantity=quantity,
            order_type=type_lower,
            price=price,
            exchange=exchange,
        )

        # Build response
        response = {
            "success": order.status.value not in ["error", "rejected"],
            "order_id": order.order_id,
            "client_order_id": order.client_order_id,
            "exchange": order.exchange,
            "symbol": order.symbol,
            "side": order.side,
            "order_type": order.order_type,
            "quantity": order.quantity,
            "price": order.price,
            "status": order.status.value,
            "filled_quantity": order.filled_quantity,
            "avg_fill_price": order.avg_fill_price,
            "exchange_order_id": order.exchange_order_id,
            "created_at": order.created_at.isoformat(),
            "warning": "LIVE ORDER EXECUTED WITH REAL FUNDS",
        }

        if order.error_message:
            response["error"] = order.error_message

        if ctx:
            ctx.info(f"Order status: {order.status.value}")

        return response

    except Exception as e:
        logger.error(f"Live order placement failed: {e}")
        return {"success": False, "error": str(e), "warning": "ORDER MAY HAVE FAILED"}


@circuit_breaker(failure_threshold=5, timeout_seconds=10)
async def live_trading_get_order_status(order_id: str, ctx=None) -> dict[str, Any]:
    """
    Get status of a live order.

    Args:
        order_id: Client order ID
        ctx: MCP context

    Returns:
        Current order status
    """
    if ctx:
        ctx.info(f"Checking order status: {order_id}")

    try:
        from backend.execution.live_multi_exchange_trading import (
            get_live_trading_service,
        )

        trading = await get_live_trading_service()
        order = await trading.get_order_status(order_id)

        if not order:
            return {"success": False, "error": f"Order {order_id} not found"}

        return {
            "success": True,
            "order_id": order.order_id,
            "exchange": order.exchange,
            "symbol": order.symbol,
            "side": order.side,
            "status": order.status.value,
            "quantity": order.quantity,
            "filled_quantity": order.filled_quantity,
            "remaining_quantity": order.remaining_quantity,
            "fill_pct": order.fill_pct,
            "avg_fill_price": order.avg_fill_price,
            "is_complete": order.is_complete,
            "updated_at": order.updated_at.isoformat(),
        }

    except Exception as e:
        logger.error(f"Order status check failed: {e}")
        return {"success": False, "error": str(e)}


@circuit_breaker(failure_threshold=3, timeout_seconds=10)
async def live_trading_cancel_order(order_id: str, ctx=None) -> dict[str, Any]:
    """
    Cancel an active live order.

    Args:
        order_id: Client order ID
        ctx: MCP context

    Returns:
        Cancellation result
    """
    if ctx:
        ctx.info(f"Cancelling order: {order_id}")

    try:
        from backend.execution.live_multi_exchange_trading import (
            get_live_trading_service,
        )

        trading = await get_live_trading_service()
        success = await trading.cancel_order(order_id)

        if success:
            return {
                "success": True,
                "order_id": order_id,
                "status": "cancelled",
            }
        else:
            return {
                "success": False,
                "order_id": order_id,
                "error": "Cancellation failed or order not found",
            }

    except Exception as e:
        logger.error(f"Order cancellation failed: {e}")
        return {"success": False, "error": str(e)}


@circuit_breaker(failure_threshold=5, timeout_seconds=10)
async def live_trading_get_positions(ctx=None) -> dict[str, Any]:
    """
    Get all live positions across exchanges.

    Args:
        ctx: MCP context

    Returns:
        Cross-exchange positions
    """
    if ctx:
        ctx.info("Fetching live positions")

    try:
        from backend.execution.live_multi_exchange_trading import (
            get_live_trading_service,
        )

        trading = await get_live_trading_service()
        positions = await trading.get_positions()

        position_data = []
        for pos in positions:
            position_data.append({
                "symbol": pos.symbol,
                "total_quantity": pos.total_quantity,
                "avg_entry_price": pos.avg_entry_price,
                "total_unrealized_pnl": pos.total_unrealized_pnl,
                "total_realized_pnl": pos.total_realized_pnl,
                "exchanges": {
                    ex: {
                        "quantity": p.quantity,
                        "avg_entry": p.avg_entry_price,
                        "unrealized_pnl": p.unrealized_pnl,
                    }
                    for ex, p in pos.positions.items()
                },
            })

        return {
            "success": True,
            "positions": position_data,
            "count": len(positions),
        }

    except Exception as e:
        logger.error(f"Positions fetch failed: {e}")
        return {"success": False, "error": str(e)}


@circuit_breaker(failure_threshold=5, timeout_seconds=10)
async def live_trading_get_stats(ctx=None) -> dict[str, Any]:
    """
    Get live trading service statistics.

    Args:
        ctx: MCP context

    Returns:
        Trading statistics and status
    """
    try:
        from backend.execution.live_multi_exchange_trading import (
            get_live_trading_service,
        )

        trading = await get_live_trading_service()
        stats = trading.get_stats()

        return {
            "success": True,
            "stats": stats,
            "mode": "LIVE TRADING",
            "warning": "This service executes real trades with real funds",
        }

    except Exception as e:
        logger.error(f"Stats fetch failed: {e}")
        return {"success": False, "error": str(e)}


@circuit_breaker(failure_threshold=3, timeout_seconds=10)
async def live_trading_validate_order(
    symbol: str,
    side: str,
    quantity: float,
    price: float | None = None,
    ctx=None,
) -> dict[str, Any]:
    """
    Validate an order without executing it.

    Checks risk limits and estimates execution without placing real order.

    Args:
        symbol: Trading pair
        side: 'buy' or 'sell'
        quantity: Order quantity
        price: Estimated price (optional)
        ctx: MCP context

    Returns:
        Validation result with risk assessment
    """
    if ctx:
        ctx.info(f"Validating {side} order: {quantity} {symbol}")

    try:
        from backend.execution.live_multi_exchange_trading import (
            LiveMultiExchangeTrading,
        )

        # Create temporary trading instance for validation
        trading = LiveMultiExchangeTrading()

        # Estimate price if not provided
        if price is None:
            # Use smart routing to get best price
            from backend.mcp_broker.tools.multi_exchange_tools import (
                multi_exchange_get_best_price,
            )

            base = symbol.split("-")[0].split("/")[0]
            best_price = await multi_exchange_get_best_price(base, side)

            if best_price.get("success"):
                price = best_price["price"]
            else:
                price = 0.0

        order_value = quantity * price if price else 0.0

        # Check risk limits
        allowed, reason = trading._check_risk_limits(symbol, side, quantity, price or 0)

        return {
            "success": True,
            "valid": allowed,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "estimated_price": price,
            "order_value": order_value,
            "risk_check": "passed" if allowed else "failed",
            "risk_reason": reason if not allowed else None,
            "max_order_value": trading.max_order_value_eur,
            "can_execute": allowed,
        }

    except Exception as e:
        logger.error(f"Order validation failed: {e}")
        return {"success": False, "error": str(e)}
