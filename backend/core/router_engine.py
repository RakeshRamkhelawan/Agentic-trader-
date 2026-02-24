import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any

from backend.core.symbol_normalizer import SymbolNormalizer

logger = logging.getLogger(__name__)


@dataclass
class RoutingResult:
    """Standardized routing result containing the best price and execution path."""

    exchange_id: str
    symbol: str  # Canonical symbol
    price: float
    side: str
    timestamp: float
    order_book: dict[str, Any]
    normalized_symbol: str = ""

    def __post_init__(self):
        if not self.normalized_symbol:
            self.normalized_symbol = self.symbol


class RouterEngine:
    """
    Best-Price Routing Engine that aggregates order books from multiple brokers.
    """

    def __init__(self, brokers: list[Any], max_age_seconds: int = 30):
        self.brokers = brokers
        self.max_age_seconds = max_age_seconds

    async def get_best_route(self, symbol: str, side: str = "buy") -> RoutingResult | None:
        """
        Fetches order books from all brokers in parallel and returns the best execution path.
        """
        canonical_symbol = SymbolNormalizer.to_canonical(symbol)

        tasks = []
        for broker in self.brokers:
            # Normalize symbol for the specific exchange
            exchange_symbol = SymbolNormalizer.to_exchange(canonical_symbol, broker.exchange_id)
            tasks.append(self._fetch_broker_data(broker, exchange_symbol))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        best_result = None
        current_time_ms = time.time() * 1000

        for broker_data in results:
            if isinstance(broker_data, Exception) or broker_data is None:
                continue

            # Check data freshness
            ts = broker_data.get("timestamp")
            if ts is not None:
                try:
                    ts_val = float(ts)
                    if (current_time_ms - ts_val) > (self.max_age_seconds * 1000):
                        logger.warning(
                            f"Data from {broker_data['exchange_id']} is stale. TS: {ts_val}"
                        )
                        continue
                except (TypeError, ValueError):
                    continue

            order_book = broker_data.get("order_book")
            if not order_book:
                continue

            price = self._extract_price(order_book, side)
            if price is None:
                continue

            if best_result is None or self._is_better(price, best_result.price, side):
                best_result = RoutingResult(
                    exchange_id=broker_data["exchange_id"],
                    symbol=canonical_symbol,
                    price=price,
                    side=side,
                    timestamp=float(ts) / 1000 if ts else time.time(),
                    order_book=order_book,
                    normalized_symbol=canonical_symbol,
                )

        return best_result

    async def _fetch_broker_data(self, broker: Any, exchange_symbol: str) -> dict[str, Any] | None:
        """Wraps broker fetch call to include exchange metadata."""
        try:
            # Check if it's a coroutine or a normal function
            res = broker.fetch_order_book(exchange_symbol)
            if asyncio.iscoroutine(res):
                order_book = await res
            else:
                order_book = res

            return {
                "exchange_id": broker.exchange_id,
                "order_book": order_book,
                "timestamp": order_book.get("timestamp") if order_book else None,
            }
        except Exception as e:
            logger.error(f"Error fetching from {broker.exchange_id}: {e}")
            return None

    def _extract_price(self, order_book: dict[str, Any], side: str) -> float | None:
        """Extracts the best price (top of book) for the given side."""
        if side == "buy":
            asks = order_book.get("asks", [])
            return asks[0][0] if asks else None
        else:
            bids = order_book.get("bids", [])
            return bids[0][0] if bids else None

    def _is_better(self, new_price: float, current_best: float, side: str) -> bool:
        """Compares two prices to find the optimal one."""
        if side == "buy":
            return new_price < current_best
        return new_price > current_best
