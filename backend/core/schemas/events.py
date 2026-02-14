"""
Event schemas for the EventBus system.

Defines payload structures for events emitted during the OODA loop.
These events enable decoupling between agents and observers.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime, UTC

from .ooda_types import TradeProposal, ExecutionOutcome


class MarketTickEvent(BaseModel):
    """Event emitted when new market data arrives."""

    symbol: str = Field(..., description="Trading pair symbol")
    price: float = Field(..., gt=0, description="Current price")
    volume: float = Field(..., ge=0, description="Volume")
    timestamp: float = Field(default_factory=lambda: datetime.now(UTC).timestamp())


class NewsEvent(BaseModel):
    """Event for news/sentiment updates."""

    source: str = Field(..., description="News source")
    headline: str = Field(..., description="News headline")
    sentiment: float = Field(
        ..., ge=-1.0, le=1.0, description="Sentiment score [-1, 1]"
    )
    symbols: list[str] = Field(
        default_factory=list, description="Related trading symbols"
    )
    timestamp: float = Field(default_factory=lambda: datetime.now(UTC).timestamp())


class TradeProposalEvent(BaseModel):
    """
    Event for notifying about trade proposals (Notify-Only mode).

    Emitted when TRADING_MODE is set to 'notify_only', allowing
    human operators to review and approve trades.
    """

    proposal: TradeProposal = Field(..., description="The trade proposal")
    trace_id: str = Field(..., description="Audit trace ID")
    orientation_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence from Orient phase"
    )
    timestamp: float = Field(default_factory=lambda: datetime.now(UTC).timestamp())


class TradeExecutedEvent(BaseModel):
    """Event emitted after a trade is executed."""

    proposal: TradeProposal = Field(..., description="Original proposal")
    outcome: ExecutionOutcome = Field(..., description="Execution result")
    trace_id: str = Field(..., description="Audit trace ID")
    timestamp: float = Field(default_factory=lambda: datetime.now(UTC).timestamp())


class RiskAlertEvent(BaseModel):
    """Event for risk threshold violations."""

    severity: str = Field(
        ..., pattern="^(low|medium|high|critical)$", description="Alert severity"
    )
    message: str = Field(..., description="Alert message")
    symbol: Optional[str] = Field(None, description="Related symbol")
    metric: str = Field(..., description="Risk metric that triggered alert")
    current_value: float = Field(..., description="Current metric value")
    threshold: float = Field(..., description="Threshold that was breached")
    timestamp: float = Field(default_factory=lambda: datetime.now(UTC).timestamp())


class SystemHealthEvent(BaseModel):
    """Event for system health monitoring."""

    component: str = Field(..., description="Component name")
    status: str = Field(
        ..., pattern="^(healthy|degraded|down)$", description="Health status"
    )
    metrics: Dict[str, Any] = Field(
        default_factory=dict, description="Health metrics (latency, error_rate, etc.)"
    )
    message: Optional[str] = Field(None, description="Status message")
    timestamp: float = Field(default_factory=lambda: datetime.now(UTC).timestamp())
