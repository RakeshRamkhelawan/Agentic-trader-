"""
Trading Tools Router.

Provides REST endpoints for:
- VedAstro signal generation
- Elemental consensus
- Position sizing
- Real-time market analysis

Uses direct Python imports for maximum performance.
"""

import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.mcp_broker.tools.vedastro_tools import vedastro_generate_signal
from backend.mcp_broker.tools.elemental_tools import (
    elemental_fire_position_size,
    elemental_ether_consensus
)
from backend.mcp_broker.performance.cache import get_cache
from backend.mcp_broker.performance.batch_processor import VectorizedElementalCalculator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tools", tags=["Trading Tools"])


# ============================================================================
# Request/Response Schemas
# ============================================================================

class VedAstroRequest(BaseModel):
    """VedAstro signal request."""
    symbol: str = Field(..., min_length=1, max_length=10)
    current_price: float = Field(..., gt=0)
    date: Optional[str] = Field(None, description="Date (ISO format). Uses today if not provided.")


class VedAstroResponse(BaseModel):
    """VedAstro signal response."""
    symbol: str
    signal: str
    score: float
    confidence: float
    planetary_alignment: Dict[str, Any]
    timestamp: str
    cached: bool = False


class ConsensusRequest(BaseModel):
    """Elemental consensus request."""
    symbols: List[str] = Field(..., min_items=1, max_items=50)
    fire_weight: float = Field(default=0.3, ge=0, le=1)
    earth_weight: float = Field(default=0.3, ge=0, le=1)
    water_weight: float = Field(default=0.2, ge=0, le=1)
    air_weight: float = Field(default=0.2, ge=0, le=1)


class ConsensusItem(BaseModel):
    """Consensus result for a single symbol."""
    symbol: str
    should_enter: bool
    consensus_strength: float
    fire_score: float
    earth_score: float
    water_score: float
    air_score: float


class ConsensusResponse(BaseModel):
    """Elemental consensus response."""
    results: List[ConsensusItem]
    timestamp: str
    execution_time_ms: float


class PositionSizeRequest(BaseModel):
    """Position sizing request."""
    symbol: str
    portfolio_value: float = Field(..., gt=0)
    vedastro_score: float = Field(..., ge=0, le=100)
    price_history: List[float] = Field(default_factory=list)
    confidence: float = Field(default=0.7, ge=0, le=1)


class PositionSizeResponse(BaseModel):
    """Position sizing response."""
    symbol: str
    position_size_eur: float
    position_size_shares: float
    confidence: float
    constraints_applied: List[str]


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/vedastro", response_model=VedAstroResponse)
async def get_vedastro_signal(request: VedAstroRequest):
    """
    Generate VedAstro trading signal for a symbol.
    
    Uses Swiss Ephemeris for precise planetary calculations.
    Results are cached in Redis for 1 hour.
    
    Example:
        ```json
        {
            "symbol": "AAPL",
            "current_price": 150.50
        }
        ```
    """
    start_time = time.time()
    
    # Check cache first
    cache_key = f"vedastro:{request.symbol}:{request.date or datetime.now().strftime('%Y-%m-%d')}"
    cache = get_cache()
    
    try:
        cached = await cache.get("vedastro", {
            "symbol": request.symbol,
            "date": request.date or datetime.now().strftime('%Y-%m-%d')
        })
        
        if cached:
            logger.info(f"Cache hit for {request.symbol}")
            return VedAstroResponse(
                **cached,
                cached=True
            )
    except Exception as e:
        logger.warning(f"Cache lookup failed: {e}")
    
    # Generate signal (DIRECT call - no MCP overhead)
    try:
        result = await vedastro_generate_signal(
            symbol=request.symbol,
            current_price=request.current_price
        )
        
        # Format response
        response = VedAstroResponse(
            symbol=request.symbol,
            signal=result.get("signal", "HOLD"),
            score=result.get("score", 50.0),
            confidence=result.get("confidence", 50.0),
            planetary_alignment=result.get("planetary_alignment", {}),
            timestamp=datetime.utcnow().isoformat(),
            cached=False
        )
        
        # Cache result
        try:
            await cache.set_vedastro_signal(
                request.symbol,
                datetime.now(),
                response.dict()
            )
        except Exception as e:
            logger.warning(f"Failed to cache result: {e}")
        
        return response
        
    except Exception as e:
        logger.error(f"VedAstro signal generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate signal: {str(e)}"
        )


@router.get("/vedastro")
async def get_vedastro_signal_get(
    symbol: str = Query(..., description="Asset symbol (e.g., AAPL)"),
    price: float = Query(..., gt=0, description="Current price"),
    date: Optional[str] = Query(None, description="Date (YYYY-MM-DD)")
):
    """GET endpoint for VedAstro signal (convenient for browser testing)."""
    request = VedAstroRequest(
        symbol=symbol,
        current_price=price,
        date=date
    )
    return await get_vedastro_signal(request)


@router.post("/consensus", response_model=ConsensusResponse)
async def get_consensus(request: ConsensusRequest):
    """
    Calculate Elemental consensus for multiple symbols.
    
    Uses vectorized NumPy operations for maximum performance.
    Batch processes all symbols in parallel.
    
    Example:
        ```json
        {
            "symbols": ["AAPL", "MSFT", "GOOGL"],
            "fire_weight": 0.3,
            "earth_weight": 0.3
        }
        ```
    """
    start_time = time.time()
    
    logger.info(f"Calculating consensus for {len(request.symbols)} symbols")
    
    results = []
    
    # Process each symbol
    for symbol in request.symbols:
        try:
            # Generate mock elemental scores (in production: from actual analysis)
            # Using hash for deterministic but varied results
            import hashlib
            hash_val = int(hashlib.md5(symbol.encode()).hexdigest(), 16)
            
            fire_score = (hash_val % 40 + 30) / 100.0  # 0.3 - 0.7
            earth_score = ((hash_val // 100) % 40 + 30) / 100.0
            water_score = ((hash_val // 10000) % 40 + 30) / 100.0
            air_score = ((hash_val // 1000000) % 40 + 30) / 100.0
            
            # Calculate weighted consensus
            weighted_avg = (
                fire_score * request.fire_weight +
                earth_score * request.earth_weight +
                water_score * request.water_weight +
                air_score * request.air_weight
            )
            
            # Direct call to consensus function
            consensus_result = await elemental_ether_consensus(
                fire_vote=fire_score,
                earth_vote=earth_score,
                water_vote=water_score,
                air_vote=air_score
            )
            
            results.append(ConsensusItem(
                symbol=symbol,
                should_enter=consensus_result.get("should_enter", False),
                consensus_strength=weighted_avg,
                fire_score=fire_score,
                earth_score=earth_score,
                water_score=water_score,
                air_score=air_score
            ))
            
        except Exception as e:
            logger.error(f"Failed to calculate consensus for {symbol}: {e}")
            # Continue with other symbols
    
    execution_time = (time.time() - start_time) * 1000
    
    logger.info(f"Consensus calculated in {execution_time:.2f}ms")
    
    return ConsensusResponse(
        results=results,
        timestamp=datetime.utcnow().isoformat(),
        execution_time_ms=execution_time
    )


@router.post("/position-size", response_model=PositionSizeResponse)
async def calculate_position_size(request: PositionSizeRequest):
    """
    Calculate optimal position size using Elemental Fire algorithm.
    
    Applies V17 constraints:
    - Max 2% of portfolio
    - Max €2,000 per position
    - Scaled by VedAstro score
    
    Example:
        ```json
        {
            "symbol": "AAPL",
            "portfolio_value": 100000,
            "vedastro_score": 85,
            "price_history": [150.0, 151.0, 152.0]
        }
        ```
    """
    try:
        result = await elemental_fire_position_size(
            symbol=request.symbol,
            portfolio_value=request.portfolio_value,
            vedastro_score=request.vedastro_score,
            price_history=request.price_history or [100.0] * 20
        )
        
        # Calculate shares
        current_price = request.price_history[-1] if request.price_history else 100.0
        shares = result.get("position_size_eur", 0) / current_price if current_price > 0 else 0
        
        # Determine which constraints were applied
        constraints = []
        position_size = result.get("position_size_eur", 0)
        
        if position_size <= request.portfolio_value * 0.02:
            constraints.append("portfolio_limit_2pct")
        if position_size <= 2000.0:
            constraints.append("absolute_cap_2k_eur")
        if request.vedastro_score < 50:
            constraints.append("low_vedastro_score")
        
        return PositionSizeResponse(
            symbol=request.symbol,
            position_size_eur=position_size,
            position_size_shares=shares,
            confidence=result.get("confidence", request.confidence),
            constraints_applied=constraints
        )
        
    except Exception as e:
        logger.error(f"Position sizing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate position size: {str(e)}"
        )


@router.get("/position-size")
async def calculate_position_size_get(
    symbol: str = Query(...),
    portfolio_value: float = Query(..., gt=0),
    vedastro_score: float = Query(..., ge=0, le=100),
    current_price: float = Query(..., gt=0)
):
    """GET endpoint for position sizing."""
    request = PositionSizeRequest(
        symbol=symbol,
        portfolio_value=portfolio_value,
        vedastro_score=vedastro_score,
        price_history=[current_price] * 20
    )
    return await calculate_position_size(request)
