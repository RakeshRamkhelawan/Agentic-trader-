
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime
import asyncio
import uuid
from dataclasses import dataclass, field

# We need definitions for OrderRequest and OrderResult.
# Assuming they exist in backend.schemas.trading or similar.
# For now defining placeholders or checking if they exist.
# I will inspect the codebase for existing Order schemas.

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