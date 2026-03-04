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
from backend.mcp_broker.tools.competitions_tools import (
    competitions_enter_tournament,
    competitions_get_available_badges,
    competitions_get_badges,
    competitions_get_leaderboard,
    competitions_get_league_info,
    competitions_get_tournaments,
    competitions_register_competitor,
    competitions_search_strategies,
    competitions_share_strategy,
)
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
from backend.mcp_broker.tools.external_tools import (
    external__macro_indicators as ext_macro_indicators,
)
from backend.mcp_broker.tools.external_tools import (
    external__market_correlation as ext_market_correlation,
)
from backend.mcp_broker.tools.external_tools import external__market_news as ext_market_news
from backend.mcp_broker.tools.external_tools import (
    external__sentiment_analysis as ext_sentiment_analysis,
)
from backend.mcp_broker.tools.external_tools import (
    external__social_sentiment as ext_social_sentiment,
)
from backend.mcp_broker.tools.external_tools import (
    external__technical_indicators as ext_technical_indicators,
)
from backend.mcp_broker.tools.live_trading_tools import (
    live_trading_cancel_order,
    live_trading_get_order_status,
    live_trading_get_positions,
    live_trading_get_stats,
    live_trading_place_order,
    live_trading_validate_order,
)
from backend.mcp_broker.tools.monitoring_tools import (
    monitoring_acknowledge_alert,
    monitoring_export_data,
    monitoring_get_alerts,
    monitoring_get_health,
    monitoring_get_metrics,
    monitoring_get_performance_summary,
)
from backend.mcp_broker.tools.multi_exchange_tools import (
    multi_exchange_find_arbitrage,
    multi_exchange_get_best_price,
    multi_exchange_get_discrepancies,
    multi_exchange_get_price,
    multi_exchange_get_stats,
    smart_order_route,
)
from backend.mcp_broker.tools.revolut_x_tools import (
    revolutx_get_account_info,
    revolutx_get_active_orders,
    revolutx_get_orderbook,
    revolutx_get_symbols,
    revolutx_get_ticker,
    revolutx_place_order,
)
from backend.mcp_broker.tools.vedastro_tools import (
    vedastro_generate_signal,
    vedastro_get_dasha,
    vedastro_get_transits,
)
from backend.mcp_broker.tools.vedic_dasha_tools import (
    vedic_calculate_transits,
    vedic_calculate_vimshottari_dasha,
    vedic_get_nakshatra_analysis,
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


@mcp.tool()
async def vedic__calculate_vimshottari_dasha(
    birth_nakshatra: str,
    birth_nakshatra_pad: int,
    birth_date: str,
) -> dict[str, Any]:
    """
    Calculate Vimshottari Dasha planetary periods for birth chart analysis.

    Args:
        birth_nakshatra: Birth nakshatra (lunar mansion) name
        birth_nakshatra_pad: Pada (quarter) 1-4
        birth_date: Birth date (YYYY-MM-DD)

    Returns:
        Complete 120-year dasha cycle with current period
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

        def error(self, msg):
            logger.error(msg)

    ctx = MinimalContext()
    return await vedic_calculate_vimshottari_dasha(
        birth_nakshatra, birth_nakshatra_pad, birth_date, ctx
    )


@mcp.tool()
async def vedic__get_nakshatra_analysis(
    nakshatra: str,
    pada: int = 1,
) -> dict[str, Any]:
    """
    Get detailed analysis of a Nakshatra (lunar mansion).

    Args:
        nakshatra: Nakshatra name (e.g., "Ashwini", "Rohini")
        pada: Quarter (1-4), default 1

    Returns:
        Nakshatra characteristics and trading implications
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await vedic_get_nakshatra_analysis(nakshatra, pada, ctx)


@mcp.tool()
async def vedic__calculate_transits(
    date: str,
    symbols: list[str] | None = None,
) -> dict[str, Any]:
    """
    Calculate planetary transits (Gochara) for market timing.

    Args:
        date: Date for transit calculation (YYYY-MM-DD)
        symbols: List of asset symbols to analyze (optional)

    Returns:
        Transit analysis with market predictions
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await vedic_calculate_transits(date, symbols, ctx)


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
# EXTERNAL TOOLS (Third-party APIs)
# ============================================================================


@mcp.tool()
async def external__sentiment_analysis(
    symbol: str,
    source: str = "news",
) -> dict[str, Any]:
    """
    Analyze sentiment for a symbol.

    Args:
        symbol: Asset symbol (e.g., "BTC", "AAPL")
        source: "news", "social", or "combined"

    Returns:
        Sentiment score (-1.0 to 1.0) and confidence
    """
    return await ext_sentiment_analysis(symbol, source)


@mcp.tool()
async def external__social_sentiment(
    symbol: str,
    platforms: list[str] | None = None,
) -> dict[str, Any]:
    """
    Get social media sentiment for a symbol.

    Args:
        symbol: Asset symbol (e.g., "BTC", "AAPL")
        platforms: List of platforms (twitter, reddit, youtube)

    Returns:
        Social sentiment metrics
    """
    return await ext_social_sentiment(symbol, platforms)


@mcp.tool()
async def external__macro_indicators(
    indicator: str = "all",
) -> dict[str, Any]:
    """
    Get macro economic indicators.

    Args:
        indicator: "all", "inflation", "rates", "employment", "gdp"

    Returns:
        Macro economic data
    """
    return await ext_macro_indicators(indicator)


@mcp.tool()
async def external__market_news(
    symbol: str | None = None,
    category: str = "crypto",
    limit: int = 5,
) -> dict[str, Any]:
    """
    Get latest market news.

    Args:
        symbol: Optional symbol filter
        category: "crypto", "stocks", "forex", "macro"
        limit: Number of news items

    Returns:
        News articles with sentiment
    """
    return await ext_market_news(symbol, category, limit)


@mcp.tool()
async def external__technical_indicators(
    symbol: str,
    price_history: list[float],
    indicators: list[str] | None = None,
) -> dict[str, Any]:
    """
    Calculate technical indicators.

    Args:
        symbol: Asset symbol
        price_history: List of prices (oldest first)
        indicators: List of indicators (rsi, macd, sma, ema, bb)

    Returns:
        Technical indicator values
    """
    return await ext_technical_indicators(symbol, price_history, indicators)


@mcp.tool()
async def external__market_correlation(
    symbol: str,
    benchmark: str = "SPX",
    period: str = "1y",
) -> dict[str, Any]:
    """
    Calculate correlation with market benchmark.

    Args:
        symbol: Asset symbol
        benchmark: Benchmark index (SPX, BTC, etc.)
        period: Period for correlation

    Returns:
        Correlation metrics
    """
    return await ext_market_correlation(symbol, benchmark, period)


# ============================================================================
# REVOLUT X TOOLS (Live Trading)
# ============================================================================


@mcp.tool()
async def revolutx__get_ticker(symbol: str) -> dict[str, Any]:
    """
    Get real-time ticker data from Revolut X.

    Args:
        symbol: Trading pair (e.g., 'BTC-USD', 'ETH-USD')

    Returns:
        Ticker with last price, bid, ask, volume
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await revolutx_get_ticker(symbol, ctx)


@mcp.tool()
async def revolutx__get_orderbook(symbol: str, depth: int = 10) -> dict[str, Any]:
    """
    Get orderbook from Revolut X.

    Args:
        symbol: Trading pair (e.g., 'BTC-USD')
        depth: Number of price levels (default 10)

    Returns:
        Orderbook with bids and asks
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await revolutx_get_orderbook(symbol, depth, ctx)


@mcp.tool()
async def revolutx__get_symbols() -> dict[str, Any]:
    """
    Get list of available trading symbols from Revolut X.

    Returns:
        List of available trading pairs
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await revolutx_get_symbols(ctx)


@mcp.tool()
async def revolutx__place_order(
    symbol: str,
    side: str,
    quantity: float,
    order_type: str = "limit",
    price: float | None = None,
) -> dict[str, Any]:
    """
    Place a LIVE order on Revolut X (REAL MONEY).

    WARNING: This executes real trades on your Revolut X account!
    Make sure you have configured your API credentials correctly.

    Args:
        symbol: Trading pair (e.g., 'BTC-USD')
        side: 'buy' or 'sell'
        quantity: Order quantity in base currency
        order_type: 'market' or 'limit'
        price: Limit price (required for limit orders)

    Returns:
        Order details with ID and status
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await revolutx_place_order(symbol, side, quantity, order_type, price, ctx)


@mcp.tool()
async def revolutx__get_active_orders() -> dict[str, Any]:
    """
    Get active orders from Revolut X.

    Returns:
        List of active orders with their status
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await revolutx_get_active_orders(ctx)


@mcp.tool()
async def revolutx__get_account_info() -> dict[str, Any]:
    """
    Check Revolut X API connection status.

    Returns:
        Connection status and configuration info
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await revolutx_get_account_info(ctx)


# ============================================================================
# MULTI-EXCHANGE TOOLS (Price Aggregation & Smart Routing)
# ============================================================================


@mcp.tool()
async def multi_exchange__get_price(symbol: str) -> dict[str, Any]:
    """
    Get aggregated price from multiple exchanges (Bitvavo + Revolut X).

    Args:
        symbol: Base symbol (e.g., 'BTC', 'ETH', 'SOL')

    Returns:
        Aggregated price with best bid/ask across exchanges
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await multi_exchange_get_price(symbol, ctx)


@mcp.tool()
async def multi_exchange__get_best_price(symbol: str, side: str) -> dict[str, Any]:
    """
    Get best price for buying or selling across exchanges.

    Args:
        symbol: Base symbol (e.g., 'BTC')
        side: 'buy' or 'sell'

    Returns:
        Best price with exchange recommendation
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await multi_exchange_get_best_price(symbol, side, ctx)


@mcp.tool()
async def multi_exchange__find_arbitrage() -> dict[str, Any]:
    """
    Find arbitrage opportunities across exchanges.

    Scans Bitvavo and Revolut X for price discrepancies
    that could be profitable after fees.

    Returns:
        List of arbitrage opportunities with profit estimates
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await multi_exchange_find_arbitrage(ctx)


@mcp.tool()
async def multi_exchange__get_discrepancies(threshold_pct: float = 0.5) -> dict[str, Any]:
    """
    Find price discrepancies across exchanges.

    Args:
        threshold_pct: Minimum price difference to report (%)

    Returns:
        Symbols with significant price differences
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await multi_exchange_get_discrepancies(threshold_pct, ctx)


@mcp.tool()
async def smart_order__route(
    symbol: str,
    side: str,
    quantity: float,
    order_type: str = "market",
    price: float | None = None,
) -> dict[str, Any]:
    """
    Smart order routing - find best exchange for execution.

    Analyzes prices, liquidity, and fees across exchanges
    to recommend optimal execution venue.

    Args:
        symbol: Base symbol (e.g., 'BTC')
        side: 'buy' or 'sell'
        quantity: Order quantity
        order_type: 'market' or 'limit'
        price: Limit price (for limit orders)

    Returns:
        Routing recommendation with execution details
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await smart_order_route(symbol, side, quantity, order_type, price, ctx)


@mcp.tool()
async def multi_exchange__get_stats() -> dict[str, Any]:
    """
    Get multi-exchange aggregator statistics.

    Returns:
        Aggregator status, active exchanges, cache info
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await multi_exchange_get_stats(ctx)


# ============================================================================
# LIVE TRADING TOOLS (Real Money - Use with Caution)
# ============================================================================


@mcp.tool()
async def live_trading__place_order(
    symbol: str,
    side: str,
    quantity: float,
    order_type: str = "market",
    price: float | None = None,
    exchange: str | None = None,
) -> dict[str, Any]:
    """
    Place a LIVE order on an exchange (REAL MONEY).

    WARNING: This executes real trades with actual funds!
    Only use this if you have configured API credentials and understand trading risks.

    Args:
        symbol: Trading pair (e.g., 'BTC-EUR', 'BTC-USD')
        side: 'buy' or 'sell'
        quantity: Order quantity in base currency
        order_type: 'market' or 'limit'
        price: Limit price (required for limit orders)
        exchange: 'bitvavo', 'revolutx', or None for auto-selection

    Returns:
        Order details with execution confirmation
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await live_trading_place_order(symbol, side, quantity, order_type, price, exchange, ctx)


@mcp.tool()
async def live_trading__get_order_status(order_id: str) -> dict[str, Any]:
    """
    Get status of a live order.

    Args:
        order_id: Client order ID

    Returns:
        Current order status and fill details
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await live_trading_get_order_status(order_id, ctx)


@mcp.tool()
async def live_trading__cancel_order(order_id: str) -> dict[str, Any]:
    """
    Cancel an active live order.

    Args:
        order_id: Client order ID

    Returns:
        Cancellation confirmation
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await live_trading_cancel_order(order_id, ctx)


@mcp.tool()
async def live_trading__get_positions() -> dict[str, Any]:
    """
    Get all live positions across exchanges.

    Returns:
        Cross-exchange position summary
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await live_trading_get_positions(ctx)


@mcp.tool()
async def live_trading__validate_order(
    symbol: str,
    side: str,
    quantity: float,
    price: float | None = None,
) -> dict[str, Any]:
    """
    Validate an order without executing it.

    Checks risk limits and provides execution estimate without placing real order.

    Args:
        symbol: Trading pair
        side: 'buy' or 'sell'
        quantity: Order quantity
        price: Estimated price (optional)

    Returns:
        Validation result with risk assessment
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await live_trading_validate_order(symbol, side, quantity, price, ctx)


@mcp.tool()
async def live_trading__get_stats() -> dict[str, Any]:
    """
    Get live trading service statistics.

    Returns:
        Trading statistics and risk configuration
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await live_trading_get_stats(ctx)


# ============================================================================
# MONITORING & ALERTING TOOLS
# ============================================================================


@mcp.tool()
async def monitoring__get_metrics() -> dict[str, Any]:
    """
    Get current trading metrics summary.

    Returns:
        Metrics summary with Prometheus/Grafana links
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await monitoring_get_metrics(ctx)


@mcp.tool()
async def monitoring__get_alerts(severity: str | None = None) -> dict[str, Any]:
    """
    Get active alerts.

    Args:
        severity: Filter by severity (critical, warning, info)

    Returns:
        Active alerts with counts by severity
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await monitoring_get_alerts(severity, ctx)


@mcp.tool()
async def monitoring__acknowledge_alert(alert_id: str) -> dict[str, Any]:
    """
    Acknowledge an alert.

    Args:
        alert_id: Alert ID to acknowledge

    Returns:
        Acknowledgment result
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await monitoring_acknowledge_alert(alert_id, ctx)


@mcp.tool()
async def monitoring__get_health() -> dict[str, Any]:
    """
    Get comprehensive platform health status.

    Returns:
        Health status of all components
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await monitoring_get_health(ctx)


@mcp.tool()
async def monitoring__get_performance_summary() -> dict[str, Any]:
    """
    Get trading performance summary.

    Returns:
        Performance metrics and statistics
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await monitoring_get_performance_summary(ctx)


@mcp.tool()
async def monitoring__export_data(
    start_date: str,
    end_date: str,
    format: str = "json",
) -> dict[str, Any]:
    """
    Export trading data for analysis.

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        format: Export format (json, csv)

    Returns:
        Export result
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await monitoring_export_data(start_date, end_date, format, ctx)


# ============================================================================
# COMPETITIONS TOOLS
# ============================================================================


@mcp.tool()
async def competitions__register_competitor(
    name: str,
    email: str,
) -> dict[str, Any]:
    """
    Register a new competitor in the trading competitions.

    New competitors start in BRONZE league with 0 points.

    Args:
        name: Competitor display name
        email: Email address

    Returns:
        Registration result with competitor ID and league assignment
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await competitions_register_competitor(name, email, ctx)


@mcp.tool()
async def competitions__get_leaderboard(
    tier: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """
    Get competition leaderboard.

    View global rankings or filter by league tier:
    - bronze: 0-1,000 points
    - silver: 1,000-10,000 points
    - gold: 10,000-50,000 points
    - diamond: 50,000+ points

    Args:
        tier: League tier filter (optional)
        limit: Number of results (default 20)

    Returns:
        Ranked list of competitors
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await competitions_get_leaderboard(tier, limit, ctx)


@mcp.tool()
async def competitions__get_league_info() -> dict[str, Any]:
    """
    Get information about all competition leagues.

    Returns details about each tier including:
    - Point thresholds
    - Promotion requirements
    - Current member counts
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await competitions_get_league_info(ctx)


@mcp.tool()
async def competitions__get_tournaments(
    status: str = "active",
) -> dict[str, Any]:
    """
    Get available trading tournaments.

    Weekly tournaments start every Monday.
    Competitors start with 10,000 paper balance.
    Top 10 win points and badges.

    Args:
        status: Tournament status (active, upcoming)

    Returns:
        List of tournaments
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await competitions_get_tournaments(status, ctx)


@mcp.tool()
async def competitions__enter_tournament(
    competitor_id: str,
    tournament_id: str,
) -> dict[str, Any]:
    """
    Enter a competitor into a tournament.

    Requires:
    - Sufficient competition points for entry fee
    - Tournament must be in PENDING status
    - Competitor not already entered

    Args:
        competitor_id: Competitor UUID
        tournament_id: Tournament UUID

    Returns:
        Entry confirmation with starting balance
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await competitions_enter_tournament(competitor_id, tournament_id, ctx)


@mcp.tool()
async def competitions__share_strategy(
    competitor_id: str,
    name: str,
    description: str,
    code: str,
    language: str = "python",
    visibility: str = "public",
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """
    Share a trading strategy with the community.

    Strategies can be:
    - public: Visible to everyone
    - league_only: Visible to same-tier competitors
    - private: Only visible to author

    Args:
        competitor_id: Author competitor UUID
        name: Strategy name
        description: Strategy description
        code: Strategy implementation code
        language: Code language (python, javascript)
        visibility: Visibility level
        tags: List of tags for discovery

    Returns:
        Strategy sharing confirmation
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await competitions_share_strategy(
        competitor_id, name, description, code, language, visibility, tags, ctx
    )


@mcp.tool()
async def competitions__search_strategies(
    query: str | None = None,
    tags: list[str] | None = None,
    sort_by: str = "score",
    limit: int = 20,
) -> dict[str, Any]:
    """
    Search for shared trading strategies.

    Sort options:
    - score: Overall strategy score
    - likes: Most liked
    - newest: Recently added
    - downloads: Most downloaded

    Args:
        query: Search query (name/description)
        tags: Filter by tags
        sort_by: Sort method
        limit: Number of results

    Returns:
        Matching strategies
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await competitions_search_strategies(query, tags, sort_by, limit, ctx)


@mcp.tool()
async def competitions__get_badges(
    competitor_id: str,
) -> dict[str, Any]:
    """
    Get badges earned by a competitor.

    Returns all badges earned including:
    - Performance badges (Profitable Trader, Win Streak)
    - Competition badges (Champion, Podium Finish)
    - League badges (Bronze, Silver, Gold, Diamond)
    - Strategy badges (Strategy Creator, Viral Strategy)

    Args:
        competitor_id: Competitor UUID

    Returns:
        List of earned badges with timestamps
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await competitions_get_badges(competitor_id, ctx)


@mcp.tool()
async def competitions__get_available_badges() -> dict[str, Any]:
    """
    Get all available badges that can be earned.

    View all 15 badge types with their requirements:
    - Common badges: Easy to earn
    - Uncommon badges: Moderate difficulty
    - Rare badges: Challenging
    - Epic badges: Expert level
    - Legendary badges: Elite achievements

    Returns:
        Complete list of badges with requirements
    """

    class MinimalContext:
        def info(self, msg):
            logger.info(msg)

    ctx = MinimalContext()
    return await competitions_get_available_badges(ctx)


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
        "competitions_register_competitor",
        "competitions_get_leaderboard",
        "competitions_get_tournaments",
        "competitions_get_badges",
        "competitions_get_available_badges",
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
