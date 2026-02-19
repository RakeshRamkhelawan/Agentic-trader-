"""
Trading API - Endpoints for market data, portfolio, and history.
"""

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.deps import get_current_tenant_id, get_current_user, get_db
from backend.services.trading_service import (TradingService,
                                              get_trading_service)

router = APIRouter(prefix="/api/v1/trading", tags=["trading"])


async def get_service() -> TradingService:
    return get_trading_service()


# ============================================================================
# Markets
# ============================================================================


@router.get("/markets")
async def get_markets(
    tenant_id: str = Depends(get_current_tenant_id),
    service: TradingService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    """Get available markets data."""
    return await service.get_markets(db, tenant_id)


# ============================================================================
# Candles
# ============================================================================


@router.get("/candles/{symbol:path}")
async def get_candles(
    symbol: str,
    timeframe: str = "1m",
    limit: int = 100,
    tenant_id: str = Depends(get_current_tenant_id),
    service: TradingService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    """Get OHLCV candles for a symbol."""
    return await service.get_candles(db, tenant_id, symbol, timeframe, limit)


# ============================================================================
# Portfolio
# ============================================================================


@router.get("/portfolio")
async def get_portfolio(
    tenant_id: str = Depends(get_current_tenant_id),
    service: TradingService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    """Get portfolio holdings and stats."""
    return await service.get_portfolio(db, tenant_id)


# ============================================================================
# History
# ============================================================================


@router.get("/history")
async def get_history(
    tenant_id: str = Depends(get_current_tenant_id),
    service: TradingService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    """Get trade history."""
    return await service.get_history(db, tenant_id)


# ============================================================================
# Orders
# ============================================================================


@router.post("/orders")
async def create_order(
    order: Dict[str, Any],
    tenant_id: str = Depends(get_current_tenant_id),
    service: TradingService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
    user: Dict = Depends(get_current_user),
):
    """
    Create and execute a new order.
    """
    # Simply pass payload to execute_order
    # execute_order will handle validation (RiskGuardian) and execution (Adapter)

    # We might want to construct a typed schema for 'order' later,
    # but for now Dict is flexible as per TradingService.execute_order expectation.
    return await service.execute_order(db, tenant_id, order, user_prefs=None)


@router.get("/orders/active")
async def get_active_orders(
    tenant_id: str = Depends(get_current_tenant_id),
    service: TradingService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all active orders (OPEN, PENDING, PARTIALLY_FILLED).
    """
    return await service.get_active_orders(db, tenant_id)


@router.delete("/orders/{order_id}")
async def cancel_order(
    order_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    service: TradingService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a specific open order by ID."""
    result = await service.cancel_order(db, tenant_id, order_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    if result.get("status") == "error":
        raise HTTPException(status_code=409, detail=result["message"])
    return result


@router.delete("/orders")
async def cancel_all_orders(
    tenant_id: str = Depends(get_current_tenant_id),
    service: TradingService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Emergency: Cancel all open orders for the tenant.
    """
    return await service.cancel_all_orders(db, tenant_id)


@router.get("/orders/history")
async def get_order_history(
    limit: int = 50,
    tenant_id: str = Depends(get_current_tenant_id),
    service: TradingService = Depends(get_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Get historical orders (FILLED, CANCELLED, etc).
    """
    return await service.get_order_history(db, tenant_id, limit)
