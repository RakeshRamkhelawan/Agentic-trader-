"""
Multi-Exchange MCP Tools.

Price aggregation, arbitrage detection, and smart order routing.
"""

import logging
from typing import Any

from backend.mcp_broker.resilience import circuit_breaker

logger = logging.getLogger(__name__)


@circuit_breaker(failure_threshold=5, timeout_seconds=30)
async def multi_exchange_get_price(symbol: str, ctx=None) -> dict[str, Any]:
    """
    Get aggregated price from multiple exchanges.

    Args:
        symbol: Base symbol (e.g., 'BTC', 'ETH')
        ctx: MCP context

    Returns:
        Aggregated price data from all exchanges
    """
    if ctx:
        ctx.info(f"Fetching multi-exchange price for {symbol}")

    try:
        from backend.execution.multi_exchange_aggregator import (
            get_multi_exchange_aggregator,
        )

        aggregator = await get_multi_exchange_aggregator()
        agg_price = await aggregator.get_aggregated_price(symbol)

        if not agg_price:
            return {
                "success": False,
                "error": f"No price data available for {symbol}",
            }

        # Build exchange prices dict
        exchange_prices = {}
        for ex, price in agg_price.prices.items():
            exchange_prices[ex] = {
                "bid": price.bid,
                "ask": price.ask,
                "last": price.last,
                "spread_pct": round(price.spread_pct, 4),
                "latency_ms": round(price.latency_ms, 2),
                "fresh": price.is_fresh(),
            }

        best_bid = agg_price.best_bid
        best_ask = agg_price.best_ask

        return {
            "success": True,
            "symbol": symbol,
            "vwap": round(agg_price.vwap, 2),
            "best_bid": {"exchange": best_bid[0], "price": best_bid[1]} if best_bid else None,
            "best_ask": {"exchange": best_ask[0], "price": best_ask[1]} if best_ask else None,
            "price_discrepancy_pct": round(agg_price.price_discrepancy_pct, 4),
            "exchanges": exchange_prices,
            "aggregated_at": agg_price.aggregated_at.isoformat(),
        }

    except Exception as e:
        logger.error(f"Multi-exchange price fetch failed: {e}")
        return {"success": False, "error": str(e)}


@circuit_breaker(failure_threshold=5, timeout_seconds=30)
async def multi_exchange_get_best_price(symbol: str, side: str, ctx=None) -> dict[str, Any]:
    """
    Get best price for buying or selling across exchanges.

    Args:
        symbol: Base symbol (e.g., 'BTC')
        side: 'buy' or 'sell'
        ctx: MCP context

    Returns:
        Best price with exchange recommendation
    """
    if ctx:
        ctx.info(f"Finding best {side} price for {symbol}")

    try:
        from backend.execution.multi_exchange_aggregator import (
            get_multi_exchange_aggregator,
        )

        aggregator = await get_multi_exchange_aggregator()
        best = await aggregator.get_best_price(symbol, side)

        if not best:
            return {
                "success": False,
                "error": f"No price data available for {symbol}",
            }

        return {
            "success": True,
            "symbol": symbol,
            "side": side,
            "recommended_exchange": best["exchange"],
            "price": best["price"],
            "action": f"{side} on {best['exchange']}",
        }

    except Exception as e:
        logger.error(f"Best price fetch failed: {e}")
        return {"success": False, "error": str(e)}


@circuit_breaker(failure_threshold=3, timeout_seconds=30)
async def multi_exchange_find_arbitrage(ctx=None) -> dict[str, Any]:
    """
    Find arbitrage opportunities across exchanges.

    Args:
        ctx: MCP context

    Returns:
        List of arbitrage opportunities
    """
    if ctx:
        ctx.info("Scanning for arbitrage opportunities")

    try:
        from backend.execution.multi_exchange_aggregator import (
            get_multi_exchange_aggregator,
        )

        aggregator = await get_multi_exchange_aggregator()
        opportunities = await aggregator.get_arbitrage_opportunities()

        if ctx:
            ctx.info(f"Found {len(opportunities)} arbitrage opportunities")

        return {
            "success": True,
            "opportunities": opportunities,
            "count": len(opportunities),
            "note": "Profitable after fees if profit_pct > 0.2%",
        }

    except Exception as e:
        logger.error(f"Arbitrage scan failed: {e}")
        return {"success": False, "error": str(e)}


@circuit_breaker(failure_threshold=3, timeout_seconds=30)
async def multi_exchange_get_discrepancies(threshold_pct: float = 0.5, ctx=None) -> dict[str, Any]:
    """
    Find price discrepancies across exchanges.

    Args:
        threshold_pct: Minimum discrepancy to report (%)
        ctx: MCP context

    Returns:
        List of price discrepancies
    """
    if ctx:
        ctx.info(f"Scanning for price discrepancies above {threshold_pct}%")

    try:
        from backend.execution.multi_exchange_aggregator import (
            get_multi_exchange_aggregator,
        )

        aggregator = await get_multi_exchange_aggregator()
        discrepancies = await aggregator.get_price_discrepancies(threshold_pct)

        if ctx:
            ctx.info(f"Found {len(discrepancies)} discrepancies")

        return {
            "success": True,
            "discrepancies": discrepancies,
            "count": len(discrepancies),
            "threshold_pct": threshold_pct,
        }

    except Exception as e:
        logger.error(f"Discrepancy scan failed: {e}")
        return {"success": False, "error": str(e)}


@circuit_breaker(failure_threshold=5, timeout_seconds=30)
async def smart_order_route(
    symbol: str,
    side: str,
    quantity: float,
    order_type: str = "market",
    price: float | None = None,
    ctx=None,
) -> dict[str, Any]:
    """
    Smart order routing - find best exchange for execution.

    Args:
        symbol: Base symbol (e.g., 'BTC')
        side: 'buy' or 'sell'
        quantity: Order quantity
        order_type: 'market' or 'limit'
        price: Limit price (for limit orders)
        ctx: MCP context

    Returns:
        Routing recommendation with expected execution details
    """
    if ctx:
        ctx.info(f"Routing {side} order for {quantity} {symbol}")

    try:
        from backend.execution.multi_exchange_aggregator import (
            get_multi_exchange_aggregator,
        )

        aggregator = await get_multi_exchange_aggregator()
        agg_price = await aggregator.get_aggregated_price(symbol)

        if not agg_price:
            return {
                "success": False,
                "error": f"No price data available for {symbol}",
            }

        # Get best price
        best = await aggregator.get_best_price(symbol, side)
        if not best:
            return {
                "success": False,
                "error": f"Could not determine best price for {symbol}",
            }

        # Calculate expected value
        expected_price = best["price"]
        expected_value = quantity * expected_price

        # Estimate fees (approximate)
        fee_pct = 0.0025  # 0.25% maker/taker average
        estimated_fee = expected_value * fee_pct
        net_value = expected_value - estimated_fee

        # Build recommendation
        recommendation = {
            "success": True,
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "order_type": order_type,
            "recommended_exchange": best["exchange"],
            "expected_price": expected_price,
            "expected_value": round(expected_value, 2),
            "estimated_fee": round(estimated_fee, 2),
            "net_value": round(net_value, 2),
            "alternative_exchanges": [
                ex for ex in agg_price.prices.keys()
                if ex != best["exchange"]
            ],
            "price_comparison": {
                ex: {
                    "bid": p.bid,
                    "ask": p.ask,
                    "spread_pct": round(p.spread_pct, 4),
                }
                for ex, p in agg_price.prices.items()
            },
        }

        if ctx:
            ctx.info(f"Recommended: {best['exchange']} at {expected_price}")

        return recommendation

    except Exception as e:
        logger.error(f"Smart order routing failed: {e}")
        return {"success": False, "error": str(e)}


@circuit_breaker(failure_threshold=3, timeout_seconds=10)
async def multi_exchange_get_stats(ctx=None) -> dict[str, Any]:
    """
    Get multi-exchange aggregator statistics.

    Args:
        ctx: MCP context

    Returns:
        Aggregator status and statistics
    """
    try:
        from backend.execution.multi_exchange_aggregator import (
            get_multi_exchange_aggregator,
        )

        aggregator = await get_multi_exchange_aggregator()
        stats = aggregator.get_stats()

        return {
            "success": True,
            "stats": stats,
        }

    except Exception as e:
        logger.error(f"Stats fetch failed: {e}")
        return {"success": False, "error": str(e)}
