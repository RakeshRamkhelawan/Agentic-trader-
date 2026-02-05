import uuid
from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, model_validator, ConfigDict

class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"

class OrderStatus(str, Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

class OrderRequest(BaseModel):
    """
    Standardized Order Request.
    Sent from Strategy -> Execution Gateway.
    """
    client_order_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    symbol: str
    qty: float = Field(gt=0, description="Quantity must be positive")
    side: OrderSide
    order_type: OrderType
    
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    
    strategy_id: str = "manual"
    timestamp: datetime = Field(default_factory=datetime.now)

    model_config = ConfigDict(frozen=True)

    @model_validator(mode='after')
    def check_limit_price(self) -> 'OrderRequest':
        if self.order_type == OrderType.LIMIT and self.limit_price is None:
            raise ValueError("Limit price is required for LIMIT orders")
        return self
