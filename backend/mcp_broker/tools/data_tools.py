"""
Data MCP Tools.

Market data en portfolio informatie.
"""

import logging
from typing import Any

from mcp.server.fastmcp import Context

from backend.mcp_broker.resilience import circuit_breaker, retry

logger = logging.getLogger(__name__)


@circuit_breaker(failure_threshold=10, timeout_seconds=30)
@retry(max_attempts=3, initial_delay_ms=200)
async def data_get_historical_prices(
    symbol: str, start_date: str, end_date: str, timeframe: str = "1d", ctx: Context = None
) -> dict[str, Any]:
    """
    Get historical price data.

    Args:
        symbol: Asset symbol
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
        timeframe: Data timeframe (1m, 5m, 1h, 1d)
        ctx: MCP context

    Returns:
        OHLCV data
    """
    if ctx:
        ctx.info(f"Fetching historical data for {symbol} from {start_date} to {end_date}")

    try:
        # Try to get from database first
        from backend.data.repository import MarketDataRepository

        repo = MarketDataRepository()
        data = await repo.get_ohlcv(
            symbol=symbol, start_date=start_date, end_date=end_date, timeframe=timeframe
        )

        if ctx:
            ctx.info(f"Retrieved {len(data)} candles for {symbol}")

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "start_date": start_date,
            "end_date": end_date,
            "data": [
                {
                    "timestamp": candle.timestamp.isoformat(),
                    "open": candle.open,
                    "high": candle.high,
                    "low": candle.low,
                    "close": candle.close,
                    "volume": candle.volume,
                }
                for candle in data
            ],
            "count": len(data),
        }

    except Exception as e:
        logger.warning(f"Failed to get data from repository: {e}, using fallback")

        # Fallback: generate mock data for testing
        # In production, this would fetch from external API
        if ctx:
            ctx.info(f"Using mock data for {symbol}")

        import random
        from datetime import datetime, timedelta

        base_price = 100.0
        mock_data = []

        start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        current = start

        while current <= end:
            # Random price movement
            change = (random.random() - 0.5) * 0.02
            open_price = base_price
            close_price = base_price * (1 + change)
            high_price = max(open_price, close_price) * (1 + random.random() * 0.01)
            low_price = min(open_price, close_price) * (1 - random.random() * 0.01)

            mock_data.append(
                {
                    "timestamp": current.isoformat(),
                    "open": round(open_price, 2),
                    "high": round(high_price, 2),
                    "low": round(low_price, 2),
                    "close": round(close_price, 2),
                    "volume": int(random.random() * 1000000),
                }
            )

            base_price = close_price
            current += timedelta(days=1)

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "start_date": start_date,
            "end_date": end_date,
            "data": mock_data,
            "count": len(mock_data),
            "note": "Mock data for testing",
        }


@circuit_breaker(failure_threshold=5, timeout_seconds=10)
async def data_get_portfolio_status(account_id: str, ctx: Context = None) -> dict[str, Any]:
    """
    Get current portfolio status.

    Args:
        account_id: Account identifier
        ctx: MCP context

    Returns:
        Portfolio summary
    """
    if ctx:
        ctx.info(f"Fetching portfolio status for {account_id}")

    try:
        # Try to get from database
        from backend.execution.paper_exchange import PaperExchange

        exchange = PaperExchange(account_id=account_id)
        portfolio = await exchange.get_portfolio()

        return {
            "account_id": account_id,
            "cash_eur": portfolio.cash,
            "total_value_eur": portfolio.total_value,
            "open_positions": [
                {
                    "symbol": pos.symbol,
                    "quantity": pos.quantity,
                    "entry_price": pos.entry_price,
                    "current_price": pos.current_price,
                    "unrealized_pnl": pos.unrealized_pnl,
                    "unrealized_pnl_pct": pos.unrealized_pnl_pct,
                }
                for pos in portfolio.positions
            ],
            "daily_pnl": portfolio.daily_pnl,
            "total_pnl": portfolio.total_pnl,
            "margin_used": portfolio.margin_used,
            "margin_available": portfolio.margin_available,
        }

    except Exception as e:
        logger.warning(f"Failed to get portfolio: {e}, using mock")

        # Fallback: mock portfolio
        return {
            "account_id": account_id,
            "cash_eur": 50000.0,
            "total_value_eur": 50000.0,
            "open_positions": [],
            "daily_pnl": 0.0,
            "total_pnl": 0.0,
            "note": "Mock portfolio for testing",
        }


@circuit_breaker(failure_threshold=5, timeout_seconds=10)
async def data_get_market_regime(symbol: str, ctx: Context = None) -> dict[str, Any]:
    """
    Get current market regime for a symbol.

    Args:
        symbol: Asset symbol
        ctx: MCP context

    Returns:
        Market regime assessment
    """
    if ctx:
        ctx.info(f"Fetching market regime for {symbol}")

    # This is a simplified implementation
    # In production, this would use more sophisticated analysis

    try:
        # Get recent price data
        from datetime import datetime, timedelta

        prices_result = await data_get_historical_prices(
            symbol=symbol,
            start_date=(datetime.utcnow() - timedelta(days=30)).isoformat(),
            end_date=datetime.utcnow().isoformat(),
            timeframe="1d",
            ctx=ctx,
        )

        prices = [candle["close"] for candle in prices_result["data"]]

        if len(prices) < 20:
            return {
                "symbol": symbol,
                "regime": "unknown",
                "trend": "neutral",
                "volatility": "unknown",
                "confidence": 0.0,
            }

        # Calculate trend
        sma_20 = sum(prices[-20:]) / 20
        current_price = prices[-1]
        trend = "bullish" if current_price > sma_20 else "bearish"

        # Calculate volatility
        returns = [(prices[i] - prices[i - 1]) / prices[i - 1] for i in range(1, len(prices))]
        volatility = sum(r**2 for r in returns) / len(returns) ** 0.5

        vol_label = "low"
        if volatility > 0.02:
            vol_label = "medium"
        if volatility > 0.04:
            vol_label = "high"

        return {
            "symbol": symbol,
            "regime": "trending" if abs(current_price - sma_20) / sma_20 > 0.05 else "ranging",
            "trend": trend,
            "volatility": vol_label,
            "volatility_value": volatility,
            "sma_20": sma_20,
            "current_price": current_price,
            "confidence": 0.7,
        }

    except Exception as e:
        logger.error(f"Failed to get market regime: {e}")
        return {
            "symbol": symbol,
            "regime": "unknown",
            "trend": "neutral",
            "volatility": "unknown",
            "error": str(e),
        }
