from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, AsyncGenerator
from dataclasses import dataclass, field

# GEBRUIK DE CENTRALE SCHEMAS
from backend.schemas.orders import OrderRequest, OrderSide, OrderType, OrderStatus
from backend.schemas.market_data import TickerUpdate, OrderBook, OrderUpdate

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
    """
    Abstract base class for exchange/broker execution adapters.
    
    Supports both REST (synchronous) and WebSocket (streaming) operations.
    """
    
    # ==================== REST METHODS ====================
    
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
    
    # ==================== WEBSOCKET STREAMING METHODS ====================
    
    @abstractmethod
    async def subscribe_ticker(self, symbol: str) -> AsyncGenerator[TickerUpdate, None]:
        """
        Stream real-time price ticker updates via WebSocket.
        
        Args:
            symbol: Trading pair (e.g., "BTC/EUR")
            
        Yields:
            TickerUpdate: Real-time bid/ask/last price updates
        """
        pass
    
    @abstractmethod
    async def subscribe_orderbook(self, symbol: str, depth: int = 10) -> AsyncGenerator[OrderBook, None]:
        """
        Stream order book snapshots via WebSocket.
        
        Args:
            symbol: Trading pair
            depth: Number of price levels (default: 10)
            
        Yields:
            OrderBook: Order book snapshot with bids/asks
        """
        pass
    
    @abstractmethod
    async def subscribe_orders(self) -> AsyncGenerator[OrderUpdate, None]:
        """
        Stream order status updates via WebSocket.
        
        Yields:
            OrderUpdate: Order execution/status updates
        """
        pass
    
    # ==================== CONNECTION MANAGEMENT ====================
    
    async def connect(self) -> None:
        """Establish WebSocket connections. Override in subclass if needed."""
        pass
    
    async def disconnect(self) -> None:
        """Close WebSocket connections. Override in subclass if needed."""
        pass