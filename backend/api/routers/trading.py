"""
Trading API Routes

Thin router that delegates to TradingService for all market / portfolio / order
operations.  Paper trading endpoints are preserved exactly from the previous
implementation and remain self-contained.
"""

import logging
import os
import random
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_tenant_id, get_db
from backend.services.trading_service import get_trading_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trading", tags=["Trading"])


# ─── Shared response models ────────────────────────────────────────────────────


class Candle(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class Order(BaseModel):
    id: str
    symbol: str
    side: str  # buy / sell
    type: str  # market / limit
    quantity: float
    price: float | None
    status: str  # active / filled / cancelled
    created_at: datetime


class Asset(BaseModel):
    symbol: str
    name: str
    type: str
    price: float
    change_24h: float
    volume_24h: float
    exchange: str = ""


# ─── Paper trading log helpers (unchanged) ─────────────────────────────────────


def get_paper_trading_logs():
    """Get real paper trading logs if they exist."""
    log_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "paper_trading_session.log",
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
        if "BUY" in line or "SELL" in line:
            try:
                ts_start = line.find("[")
                ts_end = line.find("]", ts_start)
                timestamp = line[ts_start + 1 : ts_end] if ts_start >= 0 else "00:00:00"

                agent_start = line.find("[", ts_end + 1)
                agent_end = line.find("]", agent_start)
                agent = (
                    line[agent_start + 1 : agent_end].strip()
                    if agent_start >= 0
                    else "Unknown"
                )

                side = "buy" if "BUY" in line else "sell"

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


# ─── Market endpoints ──────────────────────────────────────────────────────────


@router.get("/candles/{symbol}")
async def get_candles(
    symbol: str,
    timeframe: str = Query("1h", description="Timeframe: 1m, 5m, 15m, 1h, 4h, 1d"),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """Get OHLCV candles for a symbol via TradingService."""
    service = get_trading_service()
    try:
        candles = await service.get_candles(db, tenant_id, symbol, timeframe, limit)
        result = []
        for c in candles:
            result.append(
                {
                    "timestamp": c.get("timestamp") or c.get("time"),
                    "open": float(c.get("open", 0)),
                    "high": float(c.get("high", 0)),
                    "low": float(c.get("low", 0)),
                    "close": float(c.get("close", 0)),
                    "volume": float(c.get("volume") or c.get("value", 0)),
                }
            )
        return result
    except Exception as e:
        logger.error(f"Error fetching candles for {symbol}: {e}")
        return []


@router.get("/markets")
async def get_markets(
    exchange_id: str | None = Query(None, description="Filter by exchange"),
    type: str | None = Query(None, description="Filter by type: crypto"),
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """Get available markets via TradingService (multi-exchange)."""
    service = get_trading_service()
    try:
        markets = await service.get_markets(db, tenant_id)
        if exchange_id:
            markets = [m for m in markets if m.get("exchange") == exchange_id]
        if type:
            markets = [m for m in markets if m.get("type", "crypto") == type]
        return markets
    except Exception as e:
        logger.error(f"Error fetching markets: {e}")
        return []


@router.get("/assets")
async def get_assets(
    exchange_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """Alias for /markets."""
    return await get_markets(exchange_id=exchange_id, db=db, tenant_id=tenant_id)


# ─── Portfolio endpoints ───────────────────────────────────────────────────────


@router.get("/portfolio")
async def get_portfolio(
    exchange_id: str | None = Query(None, description="Filter holdings by exchange"),
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """Get portfolio state via TradingService."""
    service = get_trading_service()
    try:
        portfolio = await service.get_portfolio(db, tenant_id)
        if exchange_id and isinstance(portfolio, dict):
            holdings = portfolio.get("holdings", [])
            portfolio["holdings"] = [
                h for h in holdings if h.get("exchange") == exchange_id
            ]
        return portfolio
    except Exception as e:
        logger.error(f"Error fetching portfolio: {e}")
        return {"total_value": 0.0, "holdings": [], "recent_orders": []}


@router.get("/history")
async def get_history(
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """Get trade history via TradingService."""
    service = get_trading_service()
    try:
        return await service.get_history(db, tenant_id)
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        return []


# ─── Order endpoints ───────────────────────────────────────────────────────────


@router.get("/orders/active")
async def get_active_orders(
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """Get active orders via TradingService."""
    service = get_trading_service()
    try:
        return await service.get_active_orders(db, tenant_id)
    except Exception as e:
        logger.error(f"Error fetching active orders: {e}")
        return []


@router.get("/orders")
async def get_all_orders(
    status: str | None = Query(
        None, description="Filter by status: active, filled, cancelled"
    ),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """Get order history via TradingService."""
    service = get_trading_service()
    try:
        orders = await service.get_order_history(db, tenant_id, limit)
        if status:
            orders = [o for o in orders if o.get("status") == status]
        return orders
    except Exception as e:
        logger.error(f"Error fetching orders: {e}")
        return []


@router.post("/orders")
async def create_order(
    order_request: dict,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """Place an order via TradingService."""
    service = get_trading_service()
    try:
        return await service.execute_order(db, tenant_id, order_request)
    except Exception as e:
        logger.error(f"Error placing order: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/orders/{order_id}")
async def cancel_order(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """Cancel an order via TradingService."""
    service = get_trading_service()
    try:
        result = await service.cancel_order(db, tenant_id, order_id)
        if result is None:
            raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling order {order_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ─── Best-price routing (placeholder — implemented in Sectie 5) ───────────────


@router.get("/best-price/{symbol}")
async def get_best_price(
    symbol: str,
    side: str = Query("buy", description="buy or sell"),
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    Compare prices for *symbol* across all connected exchanges.

    Returns a list sorted by best execution price (lowest ask for buy,
    highest bid for sell).  The recommended exchange is marked with
    ``"recommended": true``.
    """
    service = get_trading_service()
    try:
        return await service.get_best_price(db, tenant_id, symbol, side)
    except Exception as e:
        logger.error(f"Error in get_best_price for {symbol}: {e}")
        return []


# ─── Recent trades (unchanged) ────────────────────────────────────────────────


@router.get("/trades/recent")
async def get_recent_trades(limit: int = 20):
    """Get recent trades from paper trading logs."""
    trades = parse_paper_trades()
    return trades[-limit:]


# ============================================================================
# PAPER TRADING ENGINE — kept exactly from previous implementation
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
        raise HTTPException(status_code=500, detail=f"Failed to start: {str(e)}") from e


@router.post("/paper-trading/stop")
async def stop_paper_trading():
    """Stop paper trading."""
    global _paper_trading_engine

    if _paper_trading_engine is None:
        return {"status": "not_running", "message": "Paper trading is not active"}

    try:
        _paper_trading_engine.running = False
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
        raise HTTPException(status_code=500, detail=f"Failed to stop: {str(e)}") from e


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
        portfolio_value = _paper_trading_engine.initial_capital
        if _paper_trading_engine.data_agent:
            prices = await _paper_trading_engine.data_agent.get_all_prices()
            portfolio_value = await _paper_trading_engine._calculate_portfolio_value(prices)

        initial = _paper_trading_engine.initial_capital
        pnl = portfolio_value - initial
        pnl_pct = (pnl / initial * 100) if initial > 0 else 0

        duration = 0.0
        if _paper_trading_engine.start_time:
            duration = (
                datetime.now() - _paper_trading_engine.start_time
            ).total_seconds() / 3600

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
        }
    except Exception as e:
        logger.error(f"Error getting paper trading status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}") from e


@router.post("/paper-trading/inject-test-trades")
async def inject_test_trades(count: int = 5):
    """
    Inject synthetic test trades into paper trading.

    This bypasses all strategy conditions to test the full pipeline:
    portfolio tracking → WebSocket broadcast → frontend rendering
    """
    global _paper_trading_engine

    if _paper_trading_engine is None:
        raise HTTPException(status_code=400, detail="Paper trading not active. Start it first.")

    try:
        from backend.schemas.orders import OrderRequest, OrderSide, OrderType
        from backend.services.paper_trading_ws_broadcast import broadcast_trade

        pairs = [
            ("BTC/EUR", 40000, 45000),
            ("ETH/EUR", 2500, 3000),
            ("SOL/EUR", 150, 200),
            ("ADA/EUR", 0.5, 0.8),
            ("XRP/EUR", 0.5, 0.7),
            ("DOT/EUR", 10, 15),
            ("LINK/EUR", 15, 20),
            ("LTC/EUR", 70, 90),
        ]

        injected = 0

        for i in range(count):
            symbol, price_min, price_max = random.choice(pairs)

            if i < 2 or random.random() > 0.5:
                side = OrderSide.BUY
            else:
                side = OrderSide.SELL

            price = random.uniform(price_min, price_max)
            qty = random.uniform(0.01, 0.1)
            value = price * qty

            _paper_trading_engine.portfolio.market_prices[symbol] = price

            order = OrderRequest(
                symbol=symbol,
                side=side,
                qty=qty,
                order_type=OrderType.MARKET,
                client_order_id=uuid.uuid4(),
            )

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
        import traceback

        logger.error(f"Error injecting test trades: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to inject: {str(e)}") from e
