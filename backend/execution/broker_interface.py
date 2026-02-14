import asyncio
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from backend.schemas.orders import OrderRequest, OrderSide, OrderType

# OrderResult is defined here for now, or could move to schemas.
# Keeping it here as it might be execution-specific result format.


@dataclass
class OrderResult:
    order_id: str
    client_order_id: str
    status: str
    filled_qty: float = 0.0
    remaining_qty: float = 0.0
    avg_price: Optional[float] = None
    error_message: Optional[str] = None
    raw_response: Optional[Dict] = None


class ExecutionInterface(ABC):
    @abstractmethod
    async def submit_order(self, order_request):
        pass

    @abstractmethod
    async def get_balance(self) -> Dict[str, float]:
        pass

    @abstractmethod
    async def get_ticker(self, symbol: str) -> Dict[str, float]:
        pass

    @abstractmethod
    async def cancel_all_orders(self):
        pass
