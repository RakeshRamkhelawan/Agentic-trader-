"""
Analysis Router
Provides endpoints for running and managing analyses.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, status, Query

from src.api.schemas.analysis import (
    AnalysisRequest,
    AnalysisResult,
    AnalysisListResponse,
    AnalysisType,
    AnalysisStatus,
    MarketSummary,
)
from src.api.services.analysis_service import AnalysisService
from src.api.services.ingestion_service import IngestionService
from src.db.duckdb_manager import DuckDBManager

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory storage for demo (replace with Redis/DB in production)
_analyses: dict[str, AnalysisResult] = {}

# Service instances
_db_manager: Optional[DuckDBManager] = None
_analysis_service: Optional[AnalysisService] = None
_ingestion_service: Optional[IngestionService] = None


def initialize_services(data_dir: str = "/app/data"):
    """Initialize services on startup."""
    global _db_manager, _analysis_service, _ingestion_service

    try:
        _db_manager = DuckDBManager(data_dir=data_dir)
        _analysis_service = AnalysisService(db_manager=_db_manager)
        _ingestion_service = IngestionService()
        logger.info("Analysis services initialized")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise


@router.post(
    "/analysis/run",
    response_model=AnalysisResult,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Run Analysis",
    description="Trigger an analysis job (async)",
)
async def run_analysis(
    request: AnalysisRequest, background_tasks: BackgroundTasks
) -> AnalysisResult:
    """
    Trigger an analysis job.

    Analysis runs asynchronously in the background.
    Poll GET /analysis/{id} for status and results.

    Args:
        request: Analysis configuration
        background_tasks: FastAPI background tasks

    Returns:
        AnalysisResult with job ID and queued status
    """
    analysis_id = f"analysis_{uuid.uuid4().hex[:12]}"

    result = AnalysisResult(
        analysis_id=analysis_id,
        analysis_type=request.analysis_type,
        status=AnalysisStatus.QUEUED,
        created_at=datetime.now(timezone.utc),
        completed_at=None,
        result=None,
        error=None,
        metadata={
            "market": request.market,
            "category": request.category,
            "parameters": request.parameters,
        },
    )

    _analyses[analysis_id] = result

    # Queue background task
    background_tasks.add_task(_execute_analysis, analysis_id, request)

    return result


@router.get(
    "/analysis/{analysis_id}",
    response_model=AnalysisResult,
    summary="Get Analysis Status",
    description="Get status and results of an analysis",
)
async def get_analysis(analysis_id: str) -> AnalysisResult:
    """
    Get analysis status and results.

    Args:
        analysis_id: Unique analysis ID

    Returns:
        AnalysisResult with current status

    Raises:
        HTTPException 404 if analysis not found
    """
    if analysis_id not in _analyses:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis {analysis_id} not found",
        )

    return _analyses[analysis_id]


@router.get(
    "/analysis",
    response_model=AnalysisListResponse,
    summary="List Analyses",
    description="List recent analyses",
)
async def list_analyses(
    status_filter: Optional[AnalysisStatus] = Query(None, alias="status"),
    limit: int = Query(10, ge=1, le=50),
) -> AnalysisListResponse:
    """
    List recent analyses.

    Args:
        status_filter: Filter by status
        limit: Maximum results

    Returns:
        List of recent analyses
    """
    analyses = list(_analyses.values())

    if status_filter:
        analyses = [a for a in analyses if a.status == status_filter]

    # Sort by created_at descending
    analyses.sort(key=lambda x: x.created_at, reverse=True)
    analyses = analyses[:limit]

    return AnalysisListResponse(analyses=analyses, total=len(analyses))


@router.get(
    "/markets/summary",
    response_model=MarketSummary,
    summary="Get Market Summary",
    description="Get summary statistics for a prediction market",
)
async def get_market_summary(
    market: str = Query("kalshi", description="Market source")
) -> MarketSummary:
    """
    Get market summary statistics.

    Args:
        market: Market source (kalshi/polymarket)

    Returns:
        MarketSummary with statistics
    """
    # TODO: Replace with actual data from analysis engine
    return MarketSummary(
        market=market,
        total_markets=1250,
        active_markets=487,
        total_volume_24h=15_420_000.50,
        categories=["crypto", "politics", "economics", "finance", "sports"],
        last_updated=datetime.now(timezone.utc),
    )


async def _execute_analysis(analysis_id: str, request: AnalysisRequest):
    """Execute analysis in background with real analysis engines."""
    if analysis_id not in _analyses:
        return

    # Update status to running
    _analyses[analysis_id].status = AnalysisStatus.RUNNING
    logger.info(
        f"Starting analysis {analysis_id} for {request.market}/{request.category}"
    )

    try:
        # Fetch market data
        logger.info(f"Fetching data from {request.market}")
        trades_df, metadata = await _ingestion_service.fetch_market_data(
            market=request.market,
            symbol=request.parameters.get("symbol", "DEFAULT"),
            category=request.category,
            limit=request.parameters.get("limit", 1000),
        )

        # Check if data fetch was successful
        if len(trades_df) == 0:
            _analyses[analysis_id].status = AnalysisStatus.COMPLETED
            _analyses[analysis_id].completed_at = datetime.now(timezone.utc)
            _analyses[analysis_id].result = {
                "status": "insufficient_data",
                "metadata": metadata,
                "message": f"No trades available for {request.parameters.get('symbol', 'DEFAULT')}",
            }
            logger.warning(f"No trades found for analysis {analysis_id}")
            return

        # Run analysis pipeline
        logger.info(f"Running analysis on {len(trades_df)} trades")
        analysis_result = _analysis_service.analyze_market(
            market=request.market,
            symbol=request.parameters.get("symbol", "DEFAULT"),
            trades_df=trades_df,
            category=request.category,
        )

        # Prepare final result
        result = {
            "analysis_type": request.analysis_type.value,
            "market": request.market,
            "category": request.category,
            "status": analysis_result.get("status"),
            "timestamp": analysis_result.get("timestamp"),
            "metadata": metadata,
            "spread_metrics": analysis_result.get("spread_metrics"),
            "volume_metrics": analysis_result.get("volume_metrics"),
            "statistical_tests": analysis_result.get("statistical_tests"),
            "signals": analysis_result.get("signals", []),
            "signal_count": len(analysis_result.get("signals", [])),
            "high_confidence_signals": len(
                [
                    s
                    for s in analysis_result.get("signals", [])
                    if s.get("confidence", 0) >= 70
                ]
            ),
        }

        _analyses[analysis_id].status = AnalysisStatus.COMPLETED
        _analyses[analysis_id].completed_at = datetime.now(timezone.utc)
        _analyses[analysis_id].result = result

        logger.info(
            f"Analysis {analysis_id} completed with {result['signal_count']} signals"
        )

    except Exception as e:
        logger.error(f"Analysis {analysis_id} failed: {e}", exc_info=True)
        _analyses[analysis_id].status = AnalysisStatus.FAILED
        _analyses[analysis_id].error = str(e)
        _analyses[analysis_id].completed_at = datetime.now(timezone.utc)
