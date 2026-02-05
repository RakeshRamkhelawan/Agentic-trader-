from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

# GEBRUIK DE CENTRALE SCHEMAS
from backend.schemas.orders import OrderRequest, OrderSide, OrderType, OrderStatus

@dataclass
class OrderResult:
    order_id: str
    client_order_id: str
    status: OrderStatus
    filled_qty: float = 0.0
    remaining_qty: float = 0.0
    avg_price: Optional[float] = None
    error_message: Optional[str] = None
    raw_response: Dict[str, Any] = field(default_factory=dict)

class ExecutionInterface(ABC):
    @abstractmethod
    async def submit_order(self, order: OrderRequest) -> OrderResult:
        """Verstuur een order."""
        pass

    @abstractmethod
    async def get_order_status(self, order_id: str) -> OrderResult:
        """Check de status van een specifieke order."""
        pass

    @abstractmethod
    async def get_balance(self) -> Dict[str, float]:
        """Haal je actuele saldo op."""
        pass

    @abstractmethod
    async def get_ticker(self, symbol: str) -> Dict[str, float]:
        """Haal de huidige marktprijs op."""
        pass
    
    @abstractmethod
    async def cancel_all_orders(self):
        """Panic button."""
        pass