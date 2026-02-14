from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from backend.services.performance_analytics import (
    PerformanceAnalytics,
    PerformanceMetrics,
)
from backend.services.trading_service import get_trading_service, TradingService
from backend.api.deps import get_db, get_current_tenant_id
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

router = APIRouter(tags=["analytics"])


class PerformanceResponse(BaseModel):
    max_drawdown: float
    sharpe_ratio: float
    total_return: float
    win_rate: float
    trade_count: int


class CoherenceMetrics(BaseModel):
    L32: float
    L33: float
    L34: float
    L35: float
    L36: float


class AnalyticsMetrics(BaseModel):
    mahabhutas_coherence: CoherenceMetrics
    performance: PerformanceResponse


@router.get("/performance", response_model=PerformanceResponse)
async def get_performance_metrics(
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    trading_service: TradingService = Depends(get_trading_service),
):
    """
    Calculate performance metrics based on trade history.
    """
    # 1. Fetch History
    trades = await trading_service.get_history(db, tenant_id)

    # 2. Reconstruct Equity Curve from trades (Simplified for now)
    # In reality, we'd query a daily balance snapshot table.
    # Here we assume starting capital of 10,000 and apply trade PnL.
    current_equity = 10000.0
    equity_curve = [current_equity]

    formatted_trades = []

    for t in sorted(trades, key=lambda x: x["time"]):
        # Assuming trade dict has 'total' which is cost.
        # Mock data doesn't have PnL/Exit Price.
        # We need PnL to calculate performance.
        # For mock purposes, we'll assume a random PnL % if not present

        # Note: TradingService mock data has: price, amount, total, side.
        # It represents a single execution, not a closed trade with PnL.
        # This is a limitation of the current mock.
        # We will simulate PnL for the analytics test.

        pnl = t.get("pnl")
        if pnl is None:
            # Simulate PnL driven by side
            import random

            cost = t["total"]
            pnl = cost * (random.random() - 0.45) * 0.1  # Slight bias to positive

        current_equity += pnl
        equity_curve.append(current_equity)

        formatted_trades.append({"pnl": pnl})

    # 3. Calculate Metrics
    analytics = PerformanceAnalytics()
    metrics = analytics.calculate_metrics(equity_curve, formatted_trades)

    return PerformanceResponse(
        max_drawdown=metrics.max_drawdown,
        sharpe_ratio=metrics.sharpe_ratio,
        total_return=metrics.total_return,
        win_rate=metrics.win_rate,
        trade_count=metrics.trade_count,
    )


@router.get("/metrics", response_model=AnalyticsMetrics)
async def get_dashboard_metrics(
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
    trading_service: TradingService = Depends(get_trading_service),
):
    """
    Get aggregated dashboard metrics including Mahabhutas Coherence.
    """
    # Reuse performance logic (could be refactored to shared function)
    perf_response = await get_performance_metrics(db, tenant_id, trading_service)

    # Mock Coherence Data (In real scenarios, this would come from the Orchestrator or HealthCheck service)
    # Different values to test visualization
    import random

    return AnalyticsMetrics(
        mahabhutas_coherence=CoherenceMetrics(
            L32=0.95,  # High stability
            L33=0.88,
            L34=0.72,
            L35=0.65,  # Warning
            L36=0.45,  # Critical
        ),
        performance=perf_response,
    )
