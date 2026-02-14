"""
Analysis schemas for Prediction Market Intelligence API.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field


class AnalysisType(str, Enum):
    """Available analysis types."""
    MAKER_TAKER = "maker_taker"
    VOLUME_TRENDS = "volume_trends"
    STATISTICAL_TESTS = "statistical_tests"
    CATEGORY_PERFORMANCE = "category_performance"


class AnalysisStatus(str, Enum):
    """Analysis job status."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisRequest(BaseModel):
    """Request to run an analysis."""
    analysis_type: AnalysisType = Field(..., description="Type of analysis to run")
    market: str = Field("kalshi", description="Target market (kalshi/polymarket)")
    category: Optional[str] = Field(None, description="Filter by category")
    start_date: Optional[datetime] = Field(None, description="Analysis start date")
    end_date: Optional[datetime] = Field(None, description="Analysis end date")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Analysis parameters")


class AnalysisResult(BaseModel):
    """Result of a completed analysis."""
    analysis_id: str = Field(..., description="Unique analysis ID")
    analysis_type: AnalysisType = Field(..., description="Type of analysis")
    status: AnalysisStatus = Field(..., description="Analysis status")
    created_at: datetime = Field(..., description="When analysis was created")
    completed_at: Optional[datetime] = Field(None, description="When analysis completed")
    result: Optional[Dict[str, Any]] = Field(None, description="Analysis results")
    error: Optional[str] = Field(None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AnalysisListResponse(BaseModel):
    """Response for listing analyses."""
    analyses: List[AnalysisResult]
    total: int


class MarketSummary(BaseModel):
    """Summary statistics for a prediction market."""
    market: str = Field(..., description="Market source")
    total_markets: int = Field(..., description="Total number of markets")
    active_markets: int = Field(..., description="Currently active markets")
    total_volume_24h: float = Field(..., description="24h trading volume")
    categories: List[str] = Field(..., description="Available categories")
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last data update")
