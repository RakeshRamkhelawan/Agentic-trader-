"""
Paper Trading API Endpoints - V18 Integrated with WebSocket

DEZE VERSIE draait de V18 engine als background task binnen de API,
zodat het direct WebSocket berichten kan sturen voor real-time updates.
"""

import asyncio
import logging
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.core.config.settings import settings
from backend.services.paper_trading_ws_broadcast import (
    broadcast_agent_decision,
    broadcast_portfolio,
    broadcast_stats,
    broadcast_trade,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/paper-trading", tags=["paper-trading"])

# Global state
_trading_task: asyncio.Task | None = None
_trading_engine: object | None = None
_trading_logs: list = []
_trading_trades: list = []
_session_start_time: datetime | None = None


def get_paper_trading_engine():
    """Get the current paper trading engine instance (for federated triad integration)."""
    return _trading_engine


def is_paper_trading_active():
    """Check if paper trading is currently active."""
    return _trading_task is not None and not _trading_task.done()


# Import engine type for type hints
try:
    from backend.services.real_paper_trading_v18_direct import RealPaperTradingV18

    _trading_engine: RealPaperTradingV18 | None = None
except:
    pass


class StartSessionRequest(BaseModel):
    duration: int = 8
    capital: float = 10000.0
    mode: str = "paper"  # "paper" or "live" - live uses REAL Bitvavo orders


async def _run_trading_engine(duration_hours: int, capital: float, mode: str = "paper"):
    """Run V18 trading engine as background task with WebSocket broadcasts.

    Args:
        duration_hours: How long to run the trading session
        capital: Initial capital amount
        mode: "paper" for simulation, "live" for real Bitvavo orders
    """
    global _trading_logs, _trading_trades, _session_start_time, _trading_engine

    # Import here to avoid circular imports
    import sys
    from pathlib import Path

    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

    from backend.services.real_paper_trading_v18_direct import RealPaperTradingV18

    _session_start_time = datetime.now(UTC)
    _trading_logs = []
    _trading_trades = []

    mode_label = "LIVE" if mode == "live" else "PAPER"
    logger.info(
        f"[TRADING TASK] Starting V18 {mode_label} engine for {duration_hours}h with €{capital:,.2f}"
    )

    # Initialize engine with mode
    engine = RealPaperTradingV18(initial_capital=capital, mode=mode)
    _trading_engine = engine  # Store globally for status endpoint

    try:
        await engine.initialize()

        # Broadcast initial state
        await broadcast_portfolio(
            cash=capital, total_value=capital, pnl=0.0, pnl_pct=0.0, positions={}
        )
        await broadcast_stats(
            total_trades=0, symbols_traded=0, buy_sell_ratio="0/0", agent_performance={}
        )

        # Run trading cycles
        cycle_count = 0
        max_cycles = int((duration_hours * 3600) / 30)  # Every 30 seconds

        while cycle_count < max_cycles:
            try:
                # Run one cycle
                await engine._trading_cycle()
                cycle_count += 1

                # Broadcast state every 5 cycles
                if cycle_count % 5 == 0 and engine.state:
                    await broadcast_portfolio(
                        cash=engine.state.cash,
                        total_value=engine.state.total_value,
                        pnl=engine.state.total_pnl,
                        pnl_pct=engine.state.total_value / capital - 1,
                        positions=engine.state.open_positions,
                    )
                    await broadcast_stats(
                        total_trades=engine.state.total_trades,
                        symbols_traded=len(engine.state.open_positions),
                        buy_sell_ratio=f"{engine.state.total_trades}/0",
                        agent_performance={"V18_Elemental": {"trades": engine.state.total_trades}},
                    )

                # Wait 30 seconds between cycles
                await asyncio.sleep(30)

            except asyncio.CancelledError:
                logger.info("[TRADING TASK] Cancelled")
                break
            except Exception as e:
                logger.error(f"[TRADING TASK] Cycle error: {e}")
                await asyncio.sleep(30)  # Continue after error

        logger.info(f"[TRADING TASK] Completed {cycle_count} cycles")

    except Exception as e:
        logger.error(f"[TRADING TASK] Fatal error: {e}", exc_info=True)
    finally:
        await engine.close()
        logger.info("[TRADING TASK] Engine closed")


@router.get("/status")
async def get_status():
    """Get current paper trading session status with real data."""
    global _trading_task, _trading_engine, _trading_logs, _trading_trades, _session_start_time

    is_running = _trading_task is not None and not _trading_task.done()

    # Calculate session duration
    uptime_seconds = 0
    if _session_start_time and is_running:
        uptime_seconds = (datetime.now(UTC) - _session_start_time).total_seconds()

    # Get latest data from engine if running
    portfolio = None
    stats = None
    logs = []

    # Try to get logs from engine's analytics directory
    if is_running and _trading_engine:
        try:
            log_dir = Path("paper_trading_analytics")
            if log_dir.exists():
                jsonl_files = sorted(log_dir.glob("v18_analytics_*.jsonl"))
                if jsonl_files:
                    with open(jsonl_files[-1]) as f:
                        lines = f.readlines()
                        logs = lines[-30:]  # Last 30 lines
        except Exception as e:
            logger.debug(f"Could not read logs: {e}")

    # Get portfolio from engine state
    if _trading_engine and hasattr(_trading_engine, "state") and _trading_engine.state:
        state = _trading_engine.state
        portfolio = {
            "cash": state.cash,
            "total_value": state.total_value,
            "pnl": state.total_pnl,
            "positions": state.open_positions,
        }
        stats = {"total_trades": state.total_trades, "uptime_seconds": uptime_seconds}

    # Get mode from engine if available
    engine_mode = None
    if _trading_engine and hasattr(_trading_engine, "mode"):
        engine_mode = _trading_engine.mode

    return {
        "is_running": is_running,
        "trading_mode": settings.TRADING_MODE,
        "mode": engine_mode,  # "paper" or "live"
        "logs": logs if logs else _trading_logs[-30:] if _trading_logs else [],
        "trades": _trading_trades[-20:] if _trading_trades else [],
        "portfolio": portfolio,
        "stats": stats,
        "websocket_url": "/ws/paper-trading",
        "session_duration": uptime_seconds,
    }


@router.post("/start")
async def start_paper_trading(request: StartSessionRequest):
    """Start a new paper trading session with live WebSocket updates.

    Args:
        request: Session configuration including mode ("paper" or "live")
            - paper: Simulated trading (no real orders)
            - live: REAL Bitvavo orders with €5 position size

    Note:
        Live mode requires:
        - TRADING_MODE environment variable set to "live"
        - Valid Bitvavo API credentials configured
    """
    global _trading_task, _trading_engine

    # Validate mode
    if request.mode not in ["paper", "live"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode '{request.mode}'. Must be 'paper' or 'live'",
        )

    # Extra safety check for live mode
    if request.mode == "live" and settings.TRADING_MODE != "live":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot start live trading: TRADING_MODE is '{settings.TRADING_MODE}', must be 'live'. "
            "Set TRADING_MODE=live in your .env file to enable live trading.",
        )

    # Check if already running
    if _trading_task and not _trading_task.done():
        raise HTTPException(status_code=400, detail="Trading session already running")

    try:
        # Start engine as background task (same process = WebSocket access!)
        _trading_task = asyncio.create_task(
            _run_trading_engine(request.duration, request.capital, request.mode)
        )

        mode_label = "LIVE" if request.mode == "live" else "PAPER"
        logger.info(f"[API] {mode_label} trading task started for {request.duration}h")

        return {
            "status": "started",
            "mode": request.mode,
            "duration": request.duration,
            "capital": request.capital,
            "message": f"V18 {mode_label} trading started with €{request.capital:,.2f} for {request.duration} hours",
            "websocket": "/ws/paper-trading",
            "realtime": True,
            "warning": (
                "LIVE MODE: Real Bitvavo orders will be placed!" if request.mode == "live" else None
            ),
        }

    except Exception as e:
        logger.error(f"[API] Failed to start: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_paper_trading():
    """Stop the current paper trading session."""
    global _trading_task

    if not _trading_task or _trading_task.done():
        return {"status": "not_running", "message": "No active session"}

    try:
        _trading_task.cancel()
        try:
            await asyncio.wait_for(_trading_task, timeout=5.0)
        except asyncio.CancelledError:
            pass
        except TimeoutError:
            logger.warning("[API] Task didn't cancel in time")

        logger.info("[API] Paper trading stopped")
        return {"status": "stopped", "message": "Trading session stopped"}
    except Exception as e:
        logger.error(f"[API] Error stopping: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/ws-url")
async def get_websocket_url():
    """Get WebSocket URL."""
    return {
        "websocket_url": "/ws/paper-trading",
        "channels": ["paper_trading.live", "paper_trading.stats"],
    }


@router.get("/cognitive-insights")
async def get_cognitive_insights(limit: int = 20):
    """Get recent AI cognitive decision insights from the V18 engine.

    Returns the most recent decisions from the in-memory ring buffer,
    including RAG evidence, VedAstro votes, and regime context.
    """
    global _trading_engine

    if _trading_engine is None:
        return {"insights": [], "message": "Paper trading not active.", "engine_running": False}

    try:
        cognitive_logger = getattr(_trading_engine, "cognitive_logger", None)
        if cognitive_logger is None:
            return {
                "insights": [],
                "message": "Cognitive logger not initialized.",
                "engine_running": _trading_engine.running,
            }

        decisions = cognitive_logger.get_recent_decisions(limit=limit)
        return {
            "insights": decisions,
            "count": len(decisions),
            "engine_running": getattr(_trading_engine, "running", False),
        }
    except Exception as e:
        logger.error(f"Error fetching cognitive insights: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get insights: {str(e)}")


@router.get("/tuning-stats")
async def get_tuning_stats():
    """Get current adaptive weights and Thompson Sampling stats from the Evolutionary Tuner.

    Provides real-time insights into how the bot is optimizing its own
    agent weights (VedAstro, Earth, Fire, Water) per regime.
    """
    try:
        from backend.services.evolutionary_tuner import tuner

        # Get all stats from the bandits
        stats = {}
        for regime, bandit in tuner.bandits.items():
            stats[regime] = {
                "weights": tuner.current_weights.get(regime, {}),
                "bandit_stats": bandit.get_stats(),
                "avg_slippage": tuner.avg_slippage.get(regime, 0.0),
            }

        return {
            "regimes": stats,
            "last_update": datetime.now(UTC).isoformat() + "Z",
            "agents": tuner.agents,
        }
    except Exception as e:
        logger.error(f"Error fetching tuning stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get tuning stats: {str(e)}")


# Export broadcast functions for V18 engine to use
def get_broadcast_functions():
    """Return broadcast functions for external use."""
    return {
        "broadcast_trade": broadcast_trade,
        "broadcast_agent_decision": broadcast_agent_decision,
        "broadcast_portfolio": broadcast_portfolio,
        "broadcast_stats": broadcast_stats,
    }
