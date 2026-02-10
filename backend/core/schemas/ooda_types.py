"""
OODA Loop Type Definitions

Defines immutable Pydantic models for the Observe-Orient-Decide-Act cycle.
These types ensure type safety and validation across the multi-agent system.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, List, Optional
from datetime import datetime, UTC
from enum import Enum


class MarketRegime(str, Enum):
    """Current market regime classification."""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    VOLATILE = "volatile"
    UNKNOWN = "unknown"


class RiskDecision(str, Enum):
    """Risk management decision on trade proposal."""
    APPROVE = "approve"
    REJECT = "reject"
    REDUCE_SIZE = "reduce_size"


class Observation(BaseModel):
    """
    Raw market observation from the DataScout agent.
    
    This is the 'Observe' phase output - a snapshot of market state
    at a specific point in time.
    """
    model_config = ConfigDict(frozen=True)
    
    symbol: str = Field(..., description="Trading pair symbol (e.g., 'BTC/USDT')")
    price: float = Field(..., gt=0, description="Current market price")
    volume: float = Field(..., ge=0, description="Trading volume")
    orderbook: Dict[str, Any] = Field(
        default_factory=dict,
        description="Orderbook snapshot with bids/asks"
    )
    funding_rate: Optional[float] = Field(
        None,
        description="Funding rate for perpetual futures"
    )
    social_sentiment: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="Aggregated social sentiment score [-1, 1]"
    )
    timestamp: float = Field(
        default_factory=lambda: datetime.now(UTC).timestamp(),
        description="Unix timestamp of observation"
    )
    raw_ticker: Dict[str, Any] = Field(
        default_factory=dict,
        description="Raw ticker data from exchange"
    )


class Orientation(BaseModel):
    """
    Enriched context after analysis and RAG retrieval.
    
    This is the 'Orient' phase output - combines technical analysis,
    core cognitive sentiment, and historical knowledge.
    """
    model_config = ConfigDict(frozen=True)
    
    symbol: str = Field(..., description="Trading pair symbol")
    regime: MarketRegime = Field(..., description="Detected market regime")
    indicators: Dict[str, float] = Field(
        default_factory=dict,
        description="Technical indicators (RSI, MACD, Bollinger, etc.)"
    )
    core_sentiment: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score from SystemIdentity (Ahamkara core)"
    )
    rag_context: List[str] = Field(
        default_factory=list,
        description="Relevant historical scenarios from VectorMemory"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall orientation confidence"
    )
    timestamp: float = Field(
        default_factory=lambda: datetime.now(UTC).timestamp()
    )


class TradeProposal(BaseModel):
    """
    Trading decision proposal from the Trader agent.
    
    This is the initial 'Decide' phase output, subject to risk approval.
    """
    model_config = ConfigDict(frozen=True)
    
    trade_id: str = Field(
        default_factory=lambda: f"trade-{int(datetime.now(UTC).timestamp() * 1000)}",
        description="Unique trade identifier"
    )
    symbol: str = Field(..., description="Trading pair symbol")
    side: str = Field(..., pattern="^(buy|sell)$", description="Order side")
    size: float = Field(..., gt=0, description="Position size")
    entry_price: Optional[float] = Field(
        None,
        gt=0,
        description="Target entry price (None for market orders)"
    )
    stop_loss: float = Field(..., gt=0, description="Stop loss price")
    take_profit: float = Field(..., gt=0, description="Take profit price")
    leverage: Optional[float] = Field(
        None,
        gt=0,
        description="Leverage multiplier (None for spot trading)"
    )
    time_in_force: str = Field(
        default="GTC",
        description="Time in force (GTC, IOC, FOK)"
    )
    rationale: str = Field(
        ...,
        min_length=10,
        description="Human-readable reasoning for the trade"
    )
    strategy_id: str = Field(
        ...,
        description="Strategy identifier for audit trail"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for this trade proposal"
    )
    timestamp: float = Field(
        default_factory=lambda: datetime.now(UTC).timestamp()
    )


class RiskAssessment(BaseModel):
    """
    Risk evaluation of a trade proposal.
    
    Output from RiskManager agent - validates against portfolio policies.
    """
    model_config = ConfigDict(frozen=True)
    
    trade_id: str = Field(..., description="ID of evaluated trade proposal")
    decision: RiskDecision = Field(..., description="Risk decision (approve/reject/reduce)")
    rationale: str = Field(
        ...,
        min_length=5,
        description="Explanation of decision"
    )
    risk_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall risk score [0=safe, 1=dangerous]"
    )
    win_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Estimated win probability"
    )
    modified_size: Optional[float] = Field(
        None,
        gt=0,
        description="Risk-adjusted position size (if decision=REDUCESIZE)"
    )
    timestamp: float = Field(
        default_factory=lambda: datetime.now(UTC).timestamp()
    )


class ExecutionPlan(BaseModel):
    """
    Final execution parameters for the Hot Path.
    
    This is the output after FundManager allocation - ready for execution.
    """
    model_config = ConfigDict(frozen=True)
    
    symbol: str = Field(..., description="Trading pair symbol")
    side: str = Field(..., pattern="^(buy|sell)$", description="Order side")
    quantity: float = Field(..., gt=0, description="Final allocated quantity")
    order_type: str = Field(
        default="LIMIT",
        description="Order type (LIMIT, MARKET, STOP_LIMIT)"
    )
    price: Optional[float] = Field(
        None,
        gt=0,
        description="Limit price (None for market orders)"
    )
    expected_price: float = Field(
        ...,
        gt=0,
        description="Expected fill price for slippage calculation"
    )
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional exchange-specific parameters"
    )
    trace_id: str = Field(
        ...,
        description="Unique trace ID for audit logging"
    )
    timestamp: float = Field(
        default_factory=lambda: datetime.now(UTC).timestamp()
    )


class ExecutionOutcome(BaseModel):
    """
    Result of trade execution on the exchange.
    
    This is the 'Act' phase output - feedback from the real world.
    """
    model_config = ConfigDict(frozen=True)
    
    success: bool = Field(..., description="Whether execution succeeded")
    trace_id: Optional[str] = Field(
        None,
        description="Trace ID from ExecutionPlan"
    )
    order_id: Optional[str] = Field(
        None,
        description="Exchange order ID (if successful)"
    )
    filled_qty: float = Field(
        default=0.0,
        ge=0.0,
        description="Quantity filled"
    )
    avg_price: float = Field(
        default=0.0,
        ge=0.0,
        description="Average fill price"
    )
    fee: float = Field(
        default=0.0,
        ge=0.0,
        description="Trading fee paid"
    )
    error: Optional[str] = Field(
        None,
        description="Error message (if failed)"
    )
    execution_latency_ms: Optional[float] = Field(
        None,
        ge=0.0,
        description="Execution latency in milliseconds"
    )
    timestamp: float = Field(
        default_factory=lambda: datetime.now(UTC).timestamp()
    )


class PortfolioState(BaseModel):
    """
    Current portfolio state voor FundManager.
    """
    model_config = ConfigDict(frozen=True)
    
    total_equity: float = Field(..., gt=0, description="Total account equity")
    available_capital: float = Field(..., ge=0, description="Available capital for trading")
    total_exposure_pct: float = Field(..., ge=0, le=1.0, description="Total exposure as % of equity")
    num_open_positions: int = Field(..., ge=0, description="Number of open positions")
    timestamp: float = Field(
        default_factory=lambda: datetime.now(UTC).timestamp()
    )


class CapitalAllocation(BaseModel):
    """
    Capital allocation decision from FundManager.
    """
    model_config = ConfigDict(frozen=True)
    
    position_size_usd: float = Field(..., ge=0, description="Position size in USD")
    position_fraction: float = Field(..., ge=0, le=1.0, description="Position as % of equity")
    kelly_fraction: float = Field(..., ge=0, description="Kelly Criterion optimal fraction")
    approved: bool = Field(..., description="Whether allocation approved")
    reasoning: str = Field(..., min_length=10, description="Allocation reasoning")
    timestamp: float = Field(
        default_factory=lambda: datetime.now(UTC).timestamp()
    )


class ResearchHypothesis(BaseModel):
    """
    Research hypothesis from Bull/Bear researchers.
    """
    model_config = ConfigDict(frozen=True)
    
    stance: str = Field(..., pattern="^(bullish|bearish)$", description="Bullish or bearish stance")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in hypothesis")
    arguments: List[str] = Field(..., min_length=1, description="List of arguments")
    contrarian_score: float = Field(..., ge=0.0, le=1.0, description="How contrarian vs analyst")
    generated_at: float = Field(
        default_factory=lambda: datetime.now(UTC).timestamp()
    )


class Order(BaseModel):
    """
    Exchange order voor HotPathEngine.
    """
    model_config = ConfigDict(frozen=False)  # Mutable for status updates
    
    order_id: str = Field(
        default_factory=lambda: f"order-{int(datetime.now(UTC).timestamp() * 1000)}",
        description="Unique order identifier"
    )
    symbol: str = Field(..., description="Trading pair")
    side: str = Field(..., pattern="^(buy|sell)$", description="Order side")
    order_type: str = Field(..., pattern="^(market|limit)$", description="Order type")
    quantity: float = Field(..., gt=0, description="Order quantity")
    price: Optional[float] = Field(None, gt=0, description="Limit price (None for market)")
    status: str = Field(
        default="pending",
        pattern="^(pending|filled|cancelled|rejected)$",
        description="Order status"
    )
    filled_quantity: float = Field(default=0.0, ge=0, description="Filled quantity")
    avg_fill_price: Optional[float] = Field(None, description="Average fill price")
    created_at: float = Field(
        default_factory=lambda: datetime.now(UTC).timestamp()
    )
