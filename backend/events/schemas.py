"""
Event Schemas for Event-Driven Architecture.

Pydantic models for type-safe event passing between agents.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class EventBase(BaseModel):
    """Base event schema with common fields."""

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MarketTick(EventBase):
    """Market tick event from exchange."""

    symbol: str = Field(..., description="Trading pair symbol (e.g., BTC/USD)")
    price: float = Field(..., gt=0, description="Current market price")
    volume: float = Field(..., ge=0, description="Trading volume")

    @field_validator("price")
    @classmethod
    def validate_positive_price(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Price must be positive")
        return v


class AgentThought(EventBase):
    """Agent reasoning and analysis event."""

    agent_name: str = Field(..., description="Name of the agent")
    reasoning: str = Field(..., description="Natural language explanation")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")
    data: Dict[str, Any] = Field(
        default_factory=dict, description="Additional structured data"
    )

    @field_validator("confidence")
    @classmethod
    def validate_confidence_range(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("Confidence must be between 0 and 1")
        return v


class TradeProposal(EventBase):
    """Trade proposal event from strategy agents."""

    agent_name: str = Field(..., description="Agent proposing the trade")
    symbol: str = Field(..., description="Trading pair")
    action: Literal["buy", "sell", "hold"] = Field(..., description="Trade action")
    quantity: float = Field(..., gt=0, description="Amount to trade")
    target_price: Optional[float] = Field(None, description="Target entry price")
    stop_loss: Optional[float] = Field(None, description="Stop loss price")
    take_profit: Optional[float] = Field(None, description="Take profit price")
    rationale: str = Field(..., description="Reasoning for the trade")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence 0-1")

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        allowed = {"buy", "sell", "hold"}
        if v not in allowed:
            raise ValueError(f"Action must be one of {allowed}")
        return v
