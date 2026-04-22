"""
Backtest Router.

Provides endpoints for:
- Running backtests
- Getting backtest results
- Batch backtest operations
"""

import logging
import time
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.mcp_broker.backtest_engine_v18_optimized import run_optimized_backtest
from backend.mcp_broker.backtest_engine_v18_ultra import run_ultra_backtest
from backend.mcp_broker.performance.cache import get_cache

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/backtest", tags=["Backtest"])


# ============================================================================
# Request/Response Schemas
# ============================================================================


class BacktestRequest(BaseModel):
    """Backtest execution request."""

    symbols: list[str] = Field(
        ..., min_items=1, max_items=100, description="List of symbols to backtest"
    )
    start_date: str = Field(..., description="Start date (ISO format: YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (ISO format: YYYY-MM-DD)")
    initial_capital: float = Field(default=100000.0, gt=0, description="Initial capital in EUR")
    enable_parallel: bool = Field(default=True, description="Enable parallel processing")
    max_workers: int = Field(default=4, ge=1, le=16, description="Number of parallel workers")
    use_cache: bool = Field(default=True, description="Use Redis caching")


class BacktestTrade(BaseModel):
    """Individual trade record."""

    date: str
    symbol: str
    action: str
    quantity: float
    price: float
    size: float
    pnl: float | None = None


class BacktestResponse(BaseModel):
    """Backtest execution response."""

    status: str
    backtest_id: str
    request: BacktestRequest
    results: dict[str, Any]
    performance: dict[str, Any]
    execution_time_seconds: float


class BatchBacktestRequest(BaseModel):
    """Batch backtest request for multiple configurations."""

    configs: list[BacktestRequest] = Field(..., max_length=10)


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/run", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest):
    """
    Execute a backtest with the specified parameters.

    Uses direct Python imports for maximum performance (NumPy + Redis).

    Example:
        ```json
        {
            "symbols": ["AAPL", "MSFT", "GOOGL"],
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "initial_capital": 100000
        }
        ```

    Returns:
        Complete backtest results with performance metrics
    """
    start_time = time.time()
    backtest_id = f"bt_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"

    logger.info(f"Starting backtest {backtest_id}")
    logger.info(f"  Symbols: {request.symbols}")
    logger.info(f"  Date range: {request.start_date} to {request.end_date}")

    try:
        # Parse dates
        start = datetime.fromisoformat(request.start_date)
        end = datetime.fromisoformat(request.end_date)

        if start >= end:
            raise HTTPException(status_code=400, detail="start_date must be before end_date")

        # Choose engine based on symbol count
        if len(request.symbols) > 10 and request.enable_parallel:
            logger.info("Using Ultra backtest engine (parallel)")
            results = await run_ultra_backtest(
                symbols=request.symbols,
                start_date=start,
                end_date=end,
                initial_capital=request.initial_capital,
                enable_parallel=True,
                max_workers=request.max_workers,
            )
        else:
            logger.info("Using Optimized backtest engine")
            results = await run_optimized_backtest(
                symbols=request.symbols,
                start_date=start,
                end_date=end,
                initial_capital=request.initial_capital,
                enable_parallel=request.enable_parallel,
                max_workers=request.max_workers,
            )

        execution_time = time.time() - start_time

        logger.info(f"Backtest {backtest_id} completed in {execution_time:.2f}s")

        return BacktestResponse(
            status="completed",
            backtest_id=backtest_id,
            request=request,
            results=results.get("trades", []),
            performance=results.get("performance", {}),
            execution_time_seconds=execution_time,
        )

    except ValueError as e:
        logger.error(f"Invalid request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Backtest failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Backtest execution failed: {str(e)}")


@router.post("/batch")
async def run_batch_backtest(request: BatchBacktestRequest):
    """
    Run multiple backtest configurations in parallel.

    Useful for parameter optimization or comparing strategies.
    """
    import asyncio

    logger.info(f"Starting batch backtest with {len(request.configs)} configs")

    async def run_single(config: BacktestRequest):
        try:
            result = await run_backtest(config)
            return {"status": "success", "result": result}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    # Run all configs in parallel
    tasks = [run_single(config) for config in request.configs]
    results = await asyncio.gather(*tasks)

    successful = sum(1 for r in results if r["status"] == "success")

    return {
        "batch_id": f"batch_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}",
        "total": len(request.configs),
        "successful": successful,
        "failed": len(request.configs) - successful,
        "results": results,
    }


@router.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics."""
    try:
        cache = get_cache()
        stats = await cache.get_stats()
        return {"status": "success", "stats": stats}
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return {"status": "error", "error": str(e)}


@router.post("/cache/clear")
async def clear_cache():
    """Clear the cache."""
    try:
        cache = get_cache()
        await cache.clear()
        return {"status": "success", "message": "Cache cleared"}
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))
