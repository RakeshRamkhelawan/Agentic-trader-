from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

# OrderResult is defined here for now, or could move to schemas.
# Keeping it here as it might be execution-specific result format.


@dataclass
class OrderResult:
    order_id: str
    client_order_id: str
    status: str
    filled_qty: float = 0.0
    remaining_qty: float = 0.0
    avg_price: float | None = None
    error_message: str | None = None
    raw_response: dict | None = None


class ExecutionInterface(ABC):
    @abstractmethod
    async def submit_order(self, order_request):
        pass

    @abstractmethod
    async def get_balance(self) -> dict[str, float]:
        pass

    @abstractmethod
    async def get_ticker(self, symbol: str) -> dict[str, float]:
        pass

    @abstractmethod
    async def cancel_all_orders(self):
        pass

    @abstractmethod
    async def get_tickers(self, symbols: list[str]) -> dict[str, dict[str, Any]]:
        pass

    @abstractmethod
    async def get_candles(
        self, symbol: str, timeframe: str = "1h", limit: int = 100
    ) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    async def get_order_status(self, order_id: str) -> "OrderResult":
        pass
