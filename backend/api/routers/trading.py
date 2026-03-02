"""
Trading API Routes - REAL Implementation

Endpoints for trading operations, portfolio, orders, and market data.
Uses REAL data from:
- Bitvavo exchange for market data
- ShadowPortfolioManager for portfolio state
- Real order history from trading services
"""

import logging
import os
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trading", tags=["Trading"])


# Models
class Candle(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class Portfolio(BaseModel):
    total_value: float
    cash: float
    positions: list[dict]
    pnl: float
    pnl_percent: float


class Order(BaseModel):
    id: str
    symbol: str
    side: str  # buy/sell
    type: str  # market/limit
    quantity: float
    price: float | None
    status: str  # active/filled/cancelled
    created_at: datetime


class Asset(BaseModel):
    symbol: str
    name: str
    type: str
    price: float
    change_24h: float
    volume_24h: float


# Real Portfolio Manager (Shadow Portfolio for paper trading)
_real_portfolio = None


def get_real_portfolio():
    """Get or create real shadow portfolio."""
    global _real_portfolio
    if _real_portfolio is None:
        try:
            from backend.execution.shadow_portfolio import ShadowPortfolioManager

            _real_portfolio = ShadowPortfolioManager(initial_cash=10000.0)
            logger.info("✅ Real ShadowPortfolioManager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize portfolio: {e}")
            _real_portfolio = None
    return _real_portfolio


# Bitvavo adapter (lazy import to handle missing ccxt)
_bitvavo_adapter = None


async def get_bitvavo_adapter():
    """Get or initialize Bitvavo adapter (if ccxt is available)."""
    global _bitvavo_adapter
    if _bitvavo_adapter is not None:
        return _bitvavo_adapter

    try:
        from backend.execution.bitvavo_adapter import BitvavoAdapter

        _bitvavo_adapter = BitvavoAdapter()
        await _bitvavo_adapter.initialize()
        return _bitvavo_adapter
    except ImportError as e:
        logger.warning(f"Bitvavo adapter not available: {e}")
        return None
    except Exception as e:
        logger.error(f"Error initializing Bitvavo: {e}")
        return None


def get_paper_trading_logs():
    """Get real paper trading logs if they exist."""
    log_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "paper_trading_session.log"
    )
    if os.path.exists(log_file):
        try:
            with open(log_file) as f:
                return f.readlines()
        except Exception as e:
            logger.error(f"Error reading paper trading logs: {e}")
    return []


def parse_paper_trades():
    """Parse real trades from paper trading logs."""
    logs = get_paper_trading_logs()
    trades = []

    for line in logs:
        # Parse trade lines like: [HH:MM:SS] [Agent] BUY 0.1 BTC-EUR @ EUR 50000 = EUR 5000
        if "BUY" in line or "SELL" in line:
            try:
                # Extract timestamp
                ts_start = line.find("[")
                ts_end = line.find("]", ts_start)
                timestamp = line[ts_start + 1 : ts_end] if ts_start >= 0 else "00:00:00"

                # Extract agent
                agent_start = line.find("[", ts_end + 1)
                agent_end = line.find("]", agent_start)
                agent = line[agent_start + 1 : agent_end].strip() if agent_start >= 0 else "Unknown"

                # Determine side
                side = "buy" if "BUY" in line else "sell"

                # Try to extract qty, symbol, price
                # Format: BUY 0.1 BTC-EUR @ EUR 50000 = EUR 5000
                parts = line.split()
                for i, part in enumerate(parts):
                    if part in ["BUY", "SELL"] and i + 2 < len(parts):
                        try:
                            qty = float(parts[i + 1])
                            symbol = parts[i + 2]
                            if "-EUR" in symbol and i + 5 < len(parts):
                                price = float(parts[i + 5].replace(",", ""))
                                trades.append(
                                    {
                                        "timestamp": f"2026-02-23T{timestamp}",
                                        "symbol": symbol,
                                        "side": side,
                                        "qty": qty,
                                        "price": price,
                                        "value": qty * price,
                                        "agent": agent,
                                        "exchange": "Bitvavo",
                                    }
                                )
                                break
                        except (ValueError, IndexError):
                            continue
            except Exception as e:
                logger.debug(f"Failed to parse trade line: {e}")
                continue

    return trades


@router.get("/candles/{symbol}", response_model=list[Candle])
async def get_candles(
    symbol: str,
    timeframe: str = Query("1h", description="Timeframe: 1m, 5m, 15m, 1h, 4h, 1d"),
    limit: int = Query(100, ge=1, le=1000),
):
    """Get REAL OHLCV candles for a symbol from Bitvavo."""
    bitvavo_symbol = symbol.replace("-", "/")

    timeframe_map = {
        "1m": "1m",
        "5m": "5m",
        "15m": "15m",
        "1h": "1h",
        "4h": "4h",
        "1d": "1d",
        "1w": "1w",
    }
    bitvavo_timeframe = timeframe_map.get(timeframe, "1h")

    try:
        adapter = await get_bitvavo_adapter()
        if adapter and adapter.exchange:
            ohlcv = await adapter.fetch_ohlcv(bitvavo_symbol, bitvavo_timeframe, limit)
            if ohlcv:
                candles = []
                for data in ohlcv:
                    candles.append(
                        Candle(
                            timestamp=datetime.fromtimestamp(data[0] / 1000),
                            open=float(data[1]),
                            high=float(data[2]),
                            low=float(data[3]),
                            close=float(data[4]),
                            volume=float(data[5]),
                        )
                    )
                logger.info(f"✅ Fetched {len(candles)} REAL candles for {symbol}")
                return candles
    except Exception as e:
        logger.error(f"Error fetching candles: {e}")

    logger.warning(f"❌ Failed to get real candles for {symbol}")
    return []


@router.get("/portfolio", response_model=Portfolio)
async def get_portfolio():
    """Get REAL portfolio state from ShadowPortfolioManager."""
    try:
        portfolio = get_real_portfolio()
        if portfolio:
            # Get current prices for valuation
            adapter = await get_bitvavo_adapter()
            positions_value = 0.0
            positions_list = []

            for symbol, pos in portfolio.positions.items():
                current_price = pos.get("entry_price", 0)

                # Try to get real current price
                if adapter and adapter.exchange:
                    try:
                        ticker = await adapter.fetch_ticker(symbol.replace("-", "/"))
                        if ticker:
                            current_price = float(ticker.get("last", current_price))
                    except Exception:
                        pass

                qty = pos.get("quantity", 0)
                value = qty * current_price
                positions_value += value

                positions_list.append(
                    {
                        "symbol": symbol,
                        "quantity": qty,
                        "avg_price": pos.get("entry_price", current_price),
                        "current_price": current_price,
                        "value": value,
                    }
                )

            cash = portfolio.cash_balance
            total_value = cash + positions_value
            initial_capital = portfolio.initial_cash
            pnl = total_value - initial_capital
            pnl_percent = (pnl / initial_capital * 100) if initial_capital > 0 else 0

            logger.info(f"✅ REAL Portfolio: €{total_value:,.2f} (PnL: {pnl_percent:+.2f}%)")
            return Portfolio(
                total_value=total_value,
                cash=cash,
                positions=positions_list,
                pnl=pnl,
                pnl_percent=pnl_percent,
            )
    except Exception as e:
        logger.error(f"Error getting real portfolio: {e}")

    # Return empty portfolio if nothing exists
    logger.warning("❌ No real portfolio available, returning empty")
    return Portfolio(total_value=10000.0, cash=10000.0, positions=[], pnl=0.0, pnl_percent=0.0)


@router.get("/orders/active", response_model=list[Order])
async def get_active_orders():
    """Get REAL active orders from paper trading."""
    try:
        portfolio = get_real_portfolio()
        if portfolio and hasattr(portfolio, "active_orders"):
            orders = []
            for order_id, order in portfolio.active_orders.items():
                orders.append(
                    Order(
                        id=str(order_id),
                        symbol=order.get("symbol", ""),
                        side=order.get("side", "buy"),
                        type=order.get("order_type", "market"),
                        quantity=order.get("qty", 0),
                        price=order.get("price"),
                        status="active",
                        created_at=datetime.now(),
                    )
                )
            return orders
    except Exception as e:
        logger.error(f"Error getting active orders: {e}")

    return []


@router.get("/orders", response_model=list[Order])
async def get_all_orders(
    status: str | None = Query(None, description="Filter by status: active, filled, cancelled")
):
    """Get REAL orders from paper trading logs."""
    try:
        trades = parse_paper_trades()
        orders = []

        for trade in trades:
            orders.append(
                Order(
                    id=f"trade-{trade['timestamp']}",
                    symbol=trade["symbol"],
                    side=trade["side"],
                    type="market",
                    quantity=trade["qty"],
                    price=trade["price"],
                    status="filled",
                    created_at=datetime.fromisoformat(trade["timestamp"]),
                )
            )

        if status:
            orders = [o for o in orders if o.status == status]

        return orders
    except Exception as e:
        logger.error(f"Error parsing orders: {e}")

    return []


@router.get("/markets", response_model=list[Asset])
async def get_markets(
    type: str | None = Query(None, description="Filter by type: crypto, stock, forex")
):
    """Get REAL markets/assets from Bitvavo."""
    try:
        adapter = await get_bitvavo_adapter()
        if adapter and adapter.exchange:
            tickers = await adapter.exchange.fetch_tickers()
            assets = []

            for symbol, ticker in tickers.items():
                if symbol.endswith("/EUR"):
                    base_symbol = symbol.replace("/", "-")
                    last_price = ticker.get("last")
                    percentage = ticker.get("percentage")
                    quote_volume = ticker.get("quoteVolume")

                    assets.append(
                        Asset(
                            symbol=base_symbol,
                            name=symbol.split("/")[0],
                            type="crypto",
                            price=float(last_price) if last_price else 0.0,
                            change_24h=float(percentage) if percentage else 0.0,
                            volume_24h=float(quote_volume) if quote_volume else 0.0,
                        )
                    )

            if assets:
                logger.info(f"✅ Fetched {len(assets)} REAL markets from Bitvavo")
                if type:
                    assets = [a for a in assets if a.type == type]
                return assets
    except Exception as e:
        logger.error(f"Error fetching markets: {e}")

    logger.warning("❌ Failed to get real markets")
    return []


@router.get("/assets", response_model=list[Asset])
async def get_assets():
    """Alias for /markets - Get available assets."""
    return await get_markets()


@router.get("/trades/recent")
async def get_recent_trades(limit: int = 20):
    """Get REAL recent trades from paper trading logs."""
    trades = parse_paper_trades()
    return trades[-limit:]


# ============================================================================
# PAPER TRADING ENGINE - REAL-TIME TRADING WITH AGENTS
# ============================================================================

_paper_trading_engine = None


class PaperTradingStatus(BaseModel):
    is_running: bool
    start_time: datetime | None
    duration_hours: float
    initial_capital: float
    current_value: float
    pnl: float
    pnl_percent: float
    total_trades: int
    agents_active: int


@router.post("/paper-trading/start")
async def start_paper_trading(initial_capital: float = 10000.0, duration_hours: int = 8):
    """Start REAL paper trading with all agents."""
    global _paper_trading_engine

    if _paper_trading_engine is not None:
        return {"status": "already_running", "message": "Paper trading is already active"}

    try:
        from backend.services.real_paper_trading_v18_direct import RealPaperTradingV18

        _paper_trading_engine = RealPaperTradingV18(initial_capital=initial_capital)
        await _paper_trading_engine.initialize()

        # Start trading in background
        import asyncio

        asyncio.create_task(_paper_trading_engine.run(duration_hours=duration_hours))

        logger.info(f"✅ Paper trading STARTED with €{initial_capital:,.2f} for {duration_hours}h")

        return {
            "status": "started",
            "initial_capital": initial_capital,
            "duration_hours": duration_hours,
            "engine": "V18_MCP_VedAstro",
            "symbols": len(_paper_trading_engine.all_symbols),
        }
    except Exception as e:
        import traceback

        logger.error(f"Failed to start paper trading: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        _paper_trading_engine = None
        raise HTTPException(status_code=500, detail=f"Failed to start: {str(e)}")


@router.post("/paper-trading/stop")
async def stop_paper_trading():
    """Stop paper trading."""
    global _paper_trading_engine

    if _paper_trading_engine is None:
        return {"status": "not_running", "message": "Paper trading is not active"}

    try:
        _paper_trading_engine.running = False

        # Get final stats
        state = _paper_trading_engine.state

        logger.info(f"✅ Paper trading STOPPED. Total trades: {state.total_trades}")

        await _paper_trading_engine.close()
        _paper_trading_engine = None

        return {
            "status": "stopped",
            "total_trades": state.total_trades,
            "total_pnl": state.total_pnl,
            "open_positions": len(state.open_positions),
        }
    except Exception as e:
        logger.error(f"Error stopping paper trading: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop: {str(e)}")


@router.get("/paper-trading/status")
async def get_paper_trading_status():
    """Get REAL paper trading status."""
    global _paper_trading_engine

    if _paper_trading_engine is None:
        return {
            "is_running": False,
            "message": "Paper trading not active. Use POST /paper-trading/start to begin.",
        }

    try:
        # Calculate current portfolio value
        portfolio_value = _paper_trading_engine.initial_capital
        if _paper_trading_engine.data_agent:
            prices = await _paper_trading_engine.data_agent.get_all_prices()
            portfolio_value = await _paper_trading_engine._calculate_portfolio_value(prices)

        initial = _paper_trading_engine.initial_capital
        pnl = portfolio_value - initial
        pnl_pct = (pnl / initial * 100) if initial > 0 else 0

        # Calculate duration
        duration = 0.0
        if _paper_trading_engine.start_time:
            duration = (datetime.now() - _paper_trading_engine.start_time).total_seconds() / 3600

        # Get trades from state
        trades = (
            _paper_trading_engine.state.trades
            if hasattr(_paper_trading_engine.state, "trades")
            else []
        )

        # Get logs
        logs = get_paper_trading_logs()

        # Build stats
        buy_trades = len([t for t in trades if t.get("side") == "buy"])
        sell_trades = len([t for t in trades if t.get("side") == "sell"])
        avg_trade_value = sum([t.get("value", 0) for t in trades]) / len(trades) if trades else 0

        # Calculate uptime
        uptime_seconds = 0
        if _paper_trading_engine.start_time:
            uptime_seconds = (datetime.now() - _paper_trading_engine.start_time).total_seconds()

        return {
            "is_running": _paper_trading_engine.running,
            "start_time": (
                _paper_trading_engine.start_time.isoformat()
                if _paper_trading_engine.start_time
                else None
            ),
            "duration_hours": round(duration, 2),
            "initial_capital": initial,
            "current_value": round(portfolio_value, 2),
            "pnl": round(pnl, 2),
            "pnl_percent": round(pnl_pct, 2),
            "total_trades": _paper_trading_engine.state.total_trades,
            "open_positions": len(_paper_trading_engine.state.open_positions),
            "engine": "V18_MCP_VedAstro",
            "symbols_monitored": len(_paper_trading_engine.all_symbols),
            # Additional data for frontend
            "trades": trades,
            "logs": logs[-100:] if logs else [],  # Last 100 log lines
            "stats": {
                "total_trades": _paper_trading_engine.state.total_trades,
                "buy_trades": buy_trades,
                "sell_trades": sell_trades,
                "avg_trade_value": round(avg_trade_value, 2),
                "uptime_seconds": int(uptime_seconds),
            },
            "portfolio": {
                "cash": _paper_trading_engine.state.cash,
                "total_value": round(portfolio_value, 2),
                "pnl": round(pnl, 2),
                "positions": _paper_trading_engine.state.open_positions,
            },
        }
    except Exception as e:
        logger.error(f"Error getting paper trading status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.post("/paper-trading/inject-test-trades")
async def inject_test_trades(count: int = 5):
    """
    Inject synthetic test trades into paper trading.

    This bypasses all strategy conditions to test the full pipeline:
    portfolio tracking → WebSocket broadcast → frontend rendering

    Args:
        count: Number of test trades to inject (default: 5)

    Returns:
        dict: Number of trades injected
    """
    global _paper_trading_engine

    if _paper_trading_engine is None:
        raise HTTPException(status_code=400, detail="Paper trading not active. Start it first.")

    try:
        import random
        import uuid
        from datetime import datetime

        from backend.schemas.orders import OrderRequest, OrderSide, OrderType
        from backend.services.paper_trading_ws_broadcast import broadcast_trade

        # Common trading pairs with realistic price ranges
        pairs = [
            ("BTC/EUR", 40000, 45000),  # Bitcoin ~€40-45k
            ("ETH/EUR", 2500, 3000),  # Ethereum ~€2.5-3k
            ("SOL/EUR", 150, 200),  # Solana ~€150-200
            ("ADA/EUR", 0.5, 0.8),  # Cardano ~€0.5-0.8
            ("XRP/EUR", 0.5, 0.7),  # XRP ~€0.5-0.7
            ("DOT/EUR", 10, 15),  # Polkadot ~€10-15
            ("LINK/EUR", 15, 20),  # Chainlink ~€15-20
            ("LTC/EUR", 70, 90),  # Litecoin ~€70-90
        ]

        injected = 0

        for i in range(count):
            symbol, price_min, price_max = random.choice(pairs)

            # Alternate BUY/SELL, but first 2 must be BUY to build positions
            if i < 2 or random.random() > 0.5:
                side = OrderSide.BUY
            else:
                side = OrderSide.SELL

            # Realistic price and small qty to stay within €10k budget
            price = random.uniform(price_min, price_max)
            qty = random.uniform(0.01, 0.1)  # Small qty
            value = price * qty

            # Set market price in portfolio manager (required for order to succeed)
            _paper_trading_engine.portfolio.market_prices[symbol] = price

            # Create and submit order
            order = OrderRequest(
                symbol=symbol,
                side=side,
                qty=qty,
                order_type=OrderType.MARKET,
                client_order_id=uuid.uuid4(),
            )

            # Submit to portfolio
            result = await _paper_trading_engine.portfolio.submit_order(order)
            logger.info(
                f"[TEST TRADE] Order: {side.value} {qty} {symbol} @ €{price:.2f} = €{value:.2f}"
            )
            logger.info(
                f"[TEST TRADE] Result: {result.status.value if hasattr(result, 'status') else 'unknown'}"
            )
            if hasattr(result, "error_message") and result.error_message:
                logger.warning(f"[TEST TRADE] Error: {result.error_message}")

            if result.status.value == "FILLED":
                trade = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "symbol": symbol,
                    "agent": "TEST_AGENT",
                    "strategy": "test_injection",
                    "side": side.value,
                    "qty": qty,
                    "price": price,
                    "value": value,
                    "reason": "Synthetic test trade",
                }

                # Update stats
                _paper_trading_engine.stats["total_trades"] += 1
                _paper_trading_engine.stats["symbols_traded"].add(symbol)
                _paper_trading_engine.stats["agent_trades"]["TEST_AGENT"] = (
                    _paper_trading_engine.stats["agent_trades"].get("TEST_AGENT", 0) + 1
                )
                _paper_trading_engine.stats["total_volume"] += value

                if side == OrderSide.BUY:
                    _paper_trading_engine.stats["buy_trades"] += 1
                else:
                    _paper_trading_engine.stats["sell_trades"] += 1

                # Broadcast
                await broadcast_trade(trade)
                injected += 1

                logger.info(f"[TEST TRADE] {side.value} {symbol} @ €{price:.2f}")

        logger.info(f"✅ Injected {injected} test trades")
        return {
            "status": "success",
            "injected": injected,
            "total_trades_now": _paper_trading_engine.stats["total_trades"],
        }

    except Exception as e:
        logger.error(f"Error injecting test trades: {e}")
        import traceback

        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to inject: {str(e)}")
