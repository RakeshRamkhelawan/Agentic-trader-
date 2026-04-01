"""
Revolut X MCP Tools.

Real trading execution via Revolut X Crypto Exchange API.
"""

import logging
from typing import Any

from backend.mcp_broker.resilience import circuit_breaker

logger = logging.getLogger(__name__)


@circuit_breaker(failure_threshold=3, timeout_seconds=30)
async def revolutx_get_ticker(symbol: str, ctx=None) -> dict[str, Any]:
    """
    Get ticker data from Revolut X for a symbol.

    Args:
        symbol: Trading pair (e.g., 'BTC-USD', 'ETH-USD')
        ctx: MCP context

    Returns:
        Ticker data with last price, volume, bid, ask
    """
    if ctx:
        ctx.info(f"Fetching Revolut X ticker for {symbol}")

    try:
        from backend.integrations.revolut_x_client import RevolutXClient

        client = RevolutXClient()
        connected = await client.connect()

        if not connected:
            return {
                "success": False,
                "error": "Failed to connect to Revolut X API. Check credentials.",
            }

        ticker = await client.get_ticker(symbol)
        await client.disconnect()

        return {
            "success": True,
            "symbol": symbol,
            "last": ticker.get("last", 0.0),
            "bid": ticker.get("bid", 0.0),
            "ask": ticker.get("ask", 0.0),
            "volume_24h": ticker.get("volume", 0.0),
            "high_24h": ticker.get("high_24h", 0.0),
            "low_24h": ticker.get("low_24h", 0.0),
            "source": "revolut_x",
        }

    except Exception as e:
        logger.error(f"Revolut X ticker fetch failed: {e}")
        return {"success": False, "error": str(e)}


@circuit_breaker(failure_threshold=3, timeout_seconds=30)
async def revolutx_get_orderbook(symbol: str, depth: int = 10, ctx=None) -> dict[str, Any]:
    """
    Get orderbook from Revolut X for a symbol.

    Args:
        symbol: Trading pair (e.g., 'BTC-USD')
        depth: Number of levels per side (default 10)
        ctx: MCP context

    Returns:
        Orderbook with bids and asks
    """
    if ctx:
        ctx.info(f"Fetching Revolut X orderbook for {symbol}")

    try:
        from backend.integrations.revolut_x_client import RevolutXClient

        client = RevolutXClient()
        connected = await client.connect()

        if not connected:
            return {
                "success": False,
                "error": "Failed to connect to Revolut X API. Check credentials.",
            }

        orderbook = await client.get_orderbook(symbol, depth=depth)
        await client.disconnect()

        return {
            "success": True,
            "symbol": symbol,
            "bids": orderbook.get("bids", []),
            "asks": orderbook.get("asks", []),
            "timestamp": orderbook.get("timestamp"),
            "source": "revolut_x",
        }

    except Exception as e:
        logger.error(f"Revolut X orderbook fetch failed: {e}")
        return {"success": False, "error": str(e)}


@circuit_breaker(failure_threshold=3, timeout_seconds=30)
async def revolutx_get_symbols(ctx=None) -> dict[str, Any]:
    """
    Get list of available trading symbols from Revolut X.

    Args:
        ctx: MCP context

    Returns:
        List of available trading pairs
    """
    if ctx:
        ctx.info("Fetching Revolut X trading symbols")

    try:
        from backend.integrations.revolut_x_client import RevolutXClient

        client = RevolutXClient()
        # Note: symbols endpoint is public, no auth required
        connected = await client.connect()

        if not connected:
            # Try anyway - symbols endpoint might work without auth
            pass

        symbols = await client.get_symbols()
        await client.disconnect()

        return {
            "success": True,
            "symbols": symbols,
            "count": len(symbols),
            "source": "revolut_x",
        }

    except Exception as e:
        logger.error(f"Revolut X symbols fetch failed: {e}")
        return {"success": False, "error": str(e)}


@circuit_breaker(failure_threshold=3, timeout_seconds=30)
async def revolutx_place_order(
    symbol: str,
    side: str,
    quantity: float,
    order_type: str = "limit",
    price: float | None = None,
    ctx=None,
) -> dict[str, Any]:
    """
    Place an order on Revolut X (LIVE TRADING).

    WARNING: This executes real trades on your Revolut X account!

    Args:
        symbol: Trading pair (e.g., 'BTC-USD')
        side: 'buy' or 'sell'
        quantity: Order quantity in base currency
        order_type: 'market' or 'limit'
        price: Limit price (required for limit orders)
        ctx: MCP context

    Returns:
        Order details if successful
    """
    if ctx:
        ctx.info(
            f"[LIVE TRADE] Placing {order_type} {side} order on Revolut X: {quantity} {symbol}"
        )

    try:
        from backend.integrations.revolut_x_client import OrderSide, OrderType, RevolutXClient

        # Validate inputs
        side_lower = side.lower()
        if side_lower not in ["buy", "sell"]:
            return {
                "success": False,
                "error": f"Invalid side: {side}. Must be 'buy' or 'sell'",
            }

        type_lower = order_type.lower()
        if type_lower not in ["market", "limit"]:
            return {
                "success": False,
                "error": f"Invalid order_type: {order_type}. Must be 'market' or 'limit'",
            }

        if type_lower == "limit" and price is None:
            return {"success": False, "error": "Price is required for limit orders"}

        client = RevolutXClient()
        connected = await client.connect()

        if not connected:
            return {
                "success": False,
                "error": "Failed to connect to Revolut X API. Check credentials.",
            }

        # Map to Revolut types
        rev_side = OrderSide.BUY if side_lower == "buy" else OrderSide.SELL
        rev_type = OrderType.LIMIT if type_lower == "limit" else OrderType.MARKET

        # Place order
        order = await client.place_order(
            symbol=symbol,
            side=rev_side,
            quantity=str(quantity),
            price=str(price) if price else None,
            order_type=rev_type,
            execution_instructions=["post_only"] if type_lower == "limit" else None,
        )

        await client.disconnect()

        if order:
            return {
                "success": True,
                "order_id": order.id,
                "client_order_id": order.client_order_id,
                "symbol": order.symbol,
                "side": order.side,
                "type": order.type,
                "quantity": order.quantity,
                "price": order.price,
                "status": order.status,
                "warning": "LIVE ORDER PLACED ON REVOLUT X",
            }
        else:
            return {"success": False, "error": "Order placement failed"}

    except Exception as e:
        logger.error(f"Revolut X order placement failed: {e}")
        return {"success": False, "error": str(e)}


@circuit_breaker(failure_threshold=3, timeout_seconds=30)
async def revolutx_get_active_orders(ctx=None) -> dict[str, Any]:
    """
    Get active orders from Revolut X.

    Args:
        ctx: MCP context

    Returns:
        List of active orders
    """
    if ctx:
        ctx.info("Fetching Revolut X active orders")

    try:
        from backend.integrations.revolut_x_client import RevolutXClient

        client = RevolutXClient()
        connected = await client.connect()

        if not connected:
            return {
                "success": False,
                "error": "Failed to connect to Revolut X API. Check credentials.",
            }

        orders = await client.get_active_orders()
        await client.disconnect()

        return {
            "success": True,
            "orders": [
                {
                    "id": o.id,
                    "symbol": o.symbol,
                    "side": o.side,
                    "type": o.type,
                    "quantity": o.quantity,
                    "filled_quantity": o.filled_quantity,
                    "price": o.price,
                    "status": o.status,
                }
                for o in orders
            ],
            "count": len(orders),
            "source": "revolut_x",
        }

    except Exception as e:
        logger.error(f"Revolut X active orders fetch failed: {e}")
        return {"success": False, "error": str(e)}


@circuit_breaker(failure_threshold=3, timeout_seconds=30)
async def revolutx_cancel_order(order_id: str, ctx=None) -> dict[str, Any]:
    """
    Cancel an active order on Revolut X.

    Args:
        order_id: Revolut X order ID
        ctx: MCP context

    Returns:
        Cancellation result
    """
    if ctx:
        ctx.info(f"Cancelling Revolut X order: {order_id}")

    try:
        from backend.integrations.revolut_x_client import RevolutXClient

        client = RevolutXClient()
        connected = await client.connect()

        if not connected:
            return {
                "success": False,
                "error": "Failed to connect to Revolut X API. Check credentials.",
            }

        success = await client.cancel_order(order_id)
        await client.disconnect()

        if success:
            return {
                "success": True,
                "order_id": order_id,
                "status": "cancelled",
                "source": "revolut_x",
            }
        else:
            return {
                "success": False,
                "order_id": order_id,
                "error": "Cancellation failed",
            }

    except Exception as e:
        logger.error(f"Revolut X order cancellation failed: {e}")
        return {"success": False, "error": str(e)}


@circuit_breaker(failure_threshold=3, timeout_seconds=30)
async def revolutx_get_account_info(ctx=None) -> dict[str, Any]:
    """
    Get Revolut X account connection status.

    Args:
        ctx: MCP context

    Returns:
        Account connection status
    """
    if ctx:
        ctx.info("Checking Revolut X account status")

    try:
        import os

        from backend.integrations.revolut_x_client import RevolutXClient

        api_key = os.getenv("REVOLUT_API_KEY")
        key_path = os.getenv("REVOLUT_PRIVATE_KEY_PATH")

        client = RevolutXClient()
        connected = await client.connect()
        await client.disconnect()

        return {
            "success": True,
            "connected": connected,
            "api_key_configured": bool(api_key),
            "private_key_configured": bool(key_path),
            "api_key_preview": api_key[:10] + "..." if api_key else None,
        }

    except Exception as e:
        logger.error(f"Revolut X account check failed: {e}")
        return {
            "success": False,
            "connected": False,
            "error": str(e),
        }
