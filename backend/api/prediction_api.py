"""
Prediction Market API - Proxy endpoints.

Provides access to prediction market intelligence through the main API.
Routes all requests to the prediction-intelligence container.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.services.prediction_market_client import (
    get_prediction_client,
    PredictionSignal,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/prediction", tags=["prediction"])


# ============================================================================
# REQUEST/RESPONSE SCHEMAS
# ============================================================================


class SignalResponse(BaseModel):
    """Single signal response."""

    id: str
    market: str
    category: str
    signal_type: str
    confidence: float
    symbol: Optional[str] = None
    indicators: Dict[str, float]
    timestamp: str
    metadata: Dict[str, Any]


class SignalsResponse(BaseModel):
    """Response for signals list endpoint."""

    signals: List[SignalResponse]
    total: int
    source: str = "prediction-intelligence"


class AnalysisRequest(BaseModel):
    """Request to run analysis."""

    analysis_type: str = Field(
        ...,
        description="Type of analysis: maker_taker, volume_trends, statistical_tests",
    )
    market: str = Field("kalshi", description="Target market: kalshi or polymarket")
    category: Optional[str] = Field(None, description="Optional category filter")


class AnalysisResponse(BaseModel):
    """Response from analysis endpoint."""

    job_id: Optional[str] = None
    status: str
    message: Optional[str] = None


class AnalysisStatusResponse(BaseModel):
    """Analysis job status."""

    job_id: str
    status: str
    progress: Optional[float] = None
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class MarketSummaryResponse(BaseModel):
    """Market summary statistics."""

    market: str
    total_volume: float
    total_trades: int
    active_contracts: int
    timestamp: str


class ServiceStatusResponse(BaseModel):
    """Prediction service status."""

    enabled: bool
    healthy: bool
    circuit_state: str
    base_url: str
    timestamp: str


# ============================================================================
# SIGNAL ENDPOINTS
# ============================================================================


@router.get(
    "/signals",
    response_model=SignalsResponse,
    summary="Get Prediction Market Signals",
    description="Fetch market signals from prediction-intelligence service",
)
async def get_prediction_signals(
    market: Optional[str] = Query(
        None, description="Filter by market: kalshi, polymarket"
    ),
    category: Optional[str] = Query(
        None, description="Filter by category: crypto, politics, etc"
    ),
    signal_type: Optional[str] = Query(
        None, description="Filter by signal type: bullish, bearish, neutral"
    ),
    min_confidence: float = Query(
        0.0, ge=0.0, le=1.0, description="Minimum confidence threshold"
    ),
    symbol: Optional[str] = Query(
        None, description="Filter by trading symbol: BTC, ETH, etc"
    ),
    limit: int = Query(10, ge=1, le=100, description="Max results"),
) -> SignalsResponse:
    """
    Get market intelligence signals.

    Proxies to the prediction-intelligence container and returns
    signals for consumption by trading agents.

    **Query Parameters:**
    - market: Optional market filter
    - category: Optional category filter
    - signal_type: Optional signal type filter
    - min_confidence: Minimum confidence threshold (0.0-1.0)
    - symbol: Optional trading symbol filter
    - limit: Maximum number of signals (1-100)

    **Returns:**
    - List of signals matching filters
    - Total count of signals
    - Source indicator
    """
    client = get_prediction_client()

    if not client.enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prediction market service is disabled",
        )

    try:
        signals = await client.get_signals(
            market=market,
            category=category,
            signal_type=signal_type,
            min_confidence=min_confidence,
            symbol=symbol,
            limit=limit,
        )

        # Convert PredictionSignal objects to response format
        signal_responses = [
            SignalResponse(
                id=s.id,
                market=s.market,
                category=s.category,
                signal_type=s.signal_type,
                confidence=s.confidence,
                symbol=s.symbol,
                indicators=s.indicators,
                timestamp=s.timestamp.isoformat(),
                metadata=s.metadata,
            )
            for s in signals
        ]

        return SignalsResponse(signals=signal_responses, total=len(signal_responses))

    except Exception as e:
        logger.error(f"Error fetching signals: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error fetching signals: {str(e)}",
        )


@router.get(
    "/signals/{signal_id}",
    response_model=SignalResponse,
    summary="Get Signal by ID",
    description="Fetch a specific signal by its ID",
)
async def get_prediction_signal(signal_id: str) -> SignalResponse:
    """
    Get a specific signal by ID.

    **Path Parameters:**
    - signal_id: The unique signal ID

    **Returns:**
    - Signal details

    **Errors:**
    - 404: Signal not found
    - 503: Service unavailable
    """
    client = get_prediction_client()

    if not client.enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prediction market service is disabled",
        )

    try:
        signal = await client.get_signal_by_id(signal_id)

        if not signal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Signal {signal_id} not found",
            )

        return SignalResponse(
            id=signal.id,
            market=signal.market,
            category=signal.category,
            signal_type=signal.signal_type,
            confidence=signal.confidence,
            symbol=signal.symbol,
            indicators=signal.indicators,
            timestamp=signal.timestamp.isoformat(),
            metadata=signal.metadata,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching signal {signal_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error fetching signal: {str(e)}",
        )


# ============================================================================
# ANALYSIS ENDPOINTS
# ============================================================================


@router.post(
    "/analysis",
    response_model=AnalysisResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Run Analysis Job",
    description="Trigger an analysis job on the prediction service",
)
async def run_prediction_analysis(request: AnalysisRequest) -> AnalysisResponse:
    """
    Trigger an analysis job.

    Starts an async analysis job on the prediction-intelligence service.

    **Request Body:**
    - analysis_type: Type of analysis to run
    - market: Target market for analysis
    - category: Optional category filter

    **Returns:**
    - 202 Accepted: Job queued successfully
    - job_id: ID to track analysis progress

    **Errors:**
    - 503: Service unavailable
    """
    client = get_prediction_client()

    if not client.enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prediction market service is disabled",
        )

    try:
        result = await client.run_analysis(
            analysis_type=request.analysis_type,
            market=request.market,
            category=request.category,
        )

        return AnalysisResponse(
            job_id=result.get("job_id"),
            status=result.get("status", "queued"),
            message=result.get("message"),
        )

    except Exception as e:
        logger.error(f"Error running analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error running analysis: {str(e)}",
        )


@router.get(
    "/analysis/{analysis_id}",
    response_model=AnalysisStatusResponse,
    summary="Get Analysis Status",
    description="Get status of an analysis job",
)
async def get_analysis_status(analysis_id: str) -> AnalysisStatusResponse:
    """
    Get status of an analysis job.

    **Path Parameters:**
    - analysis_id: The analysis job ID

    **Returns:**
    - Job status: queued, running, completed, failed
    - Progress percentage (if available)
    - Results (if completed)

    **Errors:**
    - 404: Analysis job not found
    - 503: Service unavailable
    """
    client = get_prediction_client()

    if not client.enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prediction market service is disabled",
        )

    try:
        result = await client.get_analysis_status(analysis_id)

        if result.get("status") == "error" and "error" in result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get("error", "Analysis not found"),
            )

        return AnalysisStatusResponse(
            job_id=analysis_id,
            status=result.get("status", "unknown"),
            progress=result.get("progress"),
            results=result.get("results"),
            error=result.get("error"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis status: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error getting analysis status: {str(e)}",
        )


# ============================================================================
# MARKET DATA ENDPOINTS
# ============================================================================


@router.get(
    "/markets/summary",
    response_model=MarketSummaryResponse,
    summary="Get Market Summary",
    description="Get summary statistics for a prediction market",
)
async def get_market_summary(
    market: str = Query("kalshi", description="Target market: kalshi or polymarket")
) -> MarketSummaryResponse:
    """
    Get market summary statistics.

    **Query Parameters:**
    - market: Market to summarize (kalshi, polymarket)

    **Returns:**
    - Market overview statistics
    - Total volume and trade count
    - Active contracts

    **Errors:**
    - 503: Service unavailable
    """
    client = get_prediction_client()

    if not client.enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Prediction market service is disabled",
        )

    try:
        result = await client.get_market_summary(market)

        return MarketSummaryResponse(
            market=result.get("market", market),
            total_volume=result.get("total_volume", 0.0),
            total_trades=result.get("total_trades", 0),
            active_contracts=result.get("active_contracts", 0),
            timestamp=result.get("timestamp", ""),
        )

    except Exception as e:
        logger.error(f"Error getting market summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error getting market summary: {str(e)}",
        )


# ============================================================================
# HEALTH/STATUS ENDPOINTS
# ============================================================================


@router.get(
    "/health",
    response_model=ServiceStatusResponse,
    summary="Get Service Status",
    description="Get prediction service connectivity and health status",
)
async def get_service_status() -> ServiceStatusResponse:
    """
    Get prediction service status.

    Checks the health of the prediction-intelligence container
    and reports circuit breaker state.

    **Returns:**
    - enabled: Service is enabled in configuration
    - healthy: Service responded to health check
    - circuit_state: Circuit breaker state (closed/open/half-open)
    - base_url: Service URL
    - timestamp: Status check timestamp
    """
    client = get_prediction_client()

    try:
        health = await client.health_check()
        is_healthy = health.get("status") == "healthy"
    except Exception as e:
        logger.warning(f"Health check failed: {e}")
        is_healthy = False

    from datetime import datetime, UTC

    return ServiceStatusResponse(
        enabled=client.enabled,
        healthy=is_healthy,
        circuit_state=client._circuit_state.value,
        base_url=client.base_url,
        timestamp=datetime.now(UTC).isoformat(),
    )
