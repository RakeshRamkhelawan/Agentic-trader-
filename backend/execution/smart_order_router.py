from typing import Dict, List, Any
from backend.execution.broker_interface import ExecutionInterface
from backend.schemas.orders import OrderRequest

class NoRouteFoundError(Exception):
    """Raised when no adapter is available for the given symbol."""
    pass

class SmartOrderRouter:
    """
    Routes orders to the best execution venue based on symbol support.
    """
    
    def __init__(self):
        self.adapters: Dict[str, ExecutionInterface] = {}
        self.symbol_map: Dict[str, str] = {} # symbol -> adapter_name

    def register_adapter(self, name: str, adapter: ExecutionInterface, supported_symbols: List[str]):
        """
        Register a broker adapter and its supported symbols.
        """
        self.adapters[name] = adapter
        for symbol in supported_symbols:
            self.symbol_map[symbol] = name

    async def route_and_execute(self, order: OrderRequest) -> Any:
        """
        Find best adapter and execute order.
        """
        adapter_name = self.symbol_map.get(order.symbol)
        
        if not adapter_name:
            raise NoRouteFoundError(f"No execution adapter found for symbol: {order.symbol}")
            
        adapter = self.adapters[adapter_name]
        return await adapter.submit_order(order)
