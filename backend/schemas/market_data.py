from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class MarketTick(BaseModel):
    """
    Standardized Market Data Event.
    Represents a single trade or quote update.
    """
    symbol: str
    price: float = Field(gt=0, description="Price must be positive")
    volume: float = Field(ge=0, description="Volume cannot be negative")
    timestamp: datetime = Field(default_factory=datetime.now)
    source: str = "unknown"
    
    # Performance optimalisatie voor Pydantic V2
    model_config = ConfigDict(frozen=True) 
