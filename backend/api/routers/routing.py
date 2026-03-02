import logging
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from backend.core.router_engine import RouterEngine
from backend.core.symbol_normalizer import SymbolNormalizer
from backend.observability.metrics import api_metrics

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/routing", tags=["Routing"])


# Mock brokers for validation (as per Task 4.1: validate with 2 exchanges first)
class MockBroker:
    def __init__(self, exchange_id: str, spreads: dict[str, float]):
        self.exchange_id = exchange_id
        self.spreads = spreads  # base price offset

    async def fetch_order_book(self, symbol: str) -> dict[str, Any]:
        base_price = 50000.0
        offset = self.spreads.get(symbol, 0.0)

        return {
            "timestamp": int(time.time() * 1000),
            "asks": [[base_price + offset, 1.0]],
            "bids": [[base_price + offset - 10, 1.0]],
        }


# Dependency to get RouterEngine
def get_router_engine():
    broker1 = MockBroker("bitvavo", {"BTC/EUR": 5.0})
    broker2 = MockBroker("revolut", {"BTC-EUR": 2.0})  # Better price
    return RouterEngine(brokers=[broker1, broker2])


class QuoteResponse(BaseModel):
    best_exchange: str
    symbol: str
    price: float
    side: str
    display_symbol: str


@router.get("/best-price", response_model=QuoteResponse)
async def get_best_price(
    symbol: str = Query(..., description="Symbol in any format (BTC/EUR, BTC-EUR, BTCEUR)"),
    side: str = Query("buy", pattern="^(buy|sell)$"),
    engine: RouterEngine = Depends(get_router_engine),
):
    """
    Finds the best price for a symbol across multiple exchanges.
    Performs normalization on input and output.
    Tracks performance metrics per exchange.
    """
    start_time = time.time()
    try:
        # 1. Normalize input to canonical
        canonical_symbol = SymbolNormalizer.to_canonical(symbol)

        # 2. Query Router Engine
        result = await engine.get_best_route(canonical_symbol, side)

        if not result:
            api_metrics.routing_errors_total.labels(exchange_id="none", error_type="no_route").inc()
            raise HTTPException(status_code=404, detail="No routes found for symbol")

        # TRACK METRICS per exchange
        latency = time.time() - start_time
        api_metrics.routing_request_latency.labels(exchange_id=result.exchange_id).observe(latency)
        api_metrics.routing_requests_total.labels(
            exchange_id=result.exchange_id, status="success"
        ).inc()

        # 3. Return normalized response
        return QuoteResponse(
            best_exchange=result.exchange_id,
            symbol=result.symbol,
            price=result.price,
            side=result.side,
            display_symbol=SymbolNormalizer.to_display(result.symbol),
        )
    except ValueError as e:
        api_metrics.routing_errors_total.labels(exchange_id="none", error_type="bad_request").inc()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Routing error: {e}")
        api_metrics.routing_errors_total.labels(
            exchange_id="unknown", error_type="internal_error"
        ).inc()
        raise HTTPException(status_code=500, detail="Internal routing error")
