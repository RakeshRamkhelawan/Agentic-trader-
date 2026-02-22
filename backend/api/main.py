import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api import analytics_api  # Added new APIs
from backend.api import (agents_api, approval_api, backtest_api, federated_api,
                         kyc_api, monitoring_api, navagraha_api, ooda_api,
                         prediction_api, trading_api, user_settings_api)
# Routers
from backend.api.auth_api import router as auth_router
from backend.api.websocket_endpoints import router as ws_router
from backend.api.websocket_manager import ws_manager
from backend.api.paper_trading_ws_simple import router as paper_trading_ws_router
from backend.api import paper_trading_api
from backend.api import health as health_api
from backend.core.auth.jwt_validator import JWTValidator
# Auth Middleware
from backend.core.auth.middleware import AuthMiddleware
from backend.core.config.settings import settings
from backend.core.navagraha.service import NavagrahaService
from backend.core.system_identity import SystemIdentity
from backend.core.telemetry.logging_config import configure_logging
from backend.observability.metrics import (PrometheusMiddleware,
                                           metrics_endpoint)
from backend.schemas.agent_messages import AgentMessage
from backend.services.cognitive_orchestrator import CognitiveOrchestrator

# Services

# ... (JWT setup)

# Configure structured logging
configure_logging()
logger = structlog.get_logger("API")


# ... (Market Data Publisher)
# Background Task: Market Data Publisher
# Bridges the gap between TradingService (Revolut) and WebSocketManager (Frontend)
async def market_data_publisher():
    """
    Periodically fetches market data from Revolut (via TradingService)
    and broadcasts it to connected WebSocket clients.
    """
    logger.info("Starting Market Data Publisher...")
    from backend.core.cache_layer import get_cache

    cache = get_cache()

    while True:
        try:
            # 1. Get all markets from cache (populated by sync task)
            # We check multiple possible keys to be robust
            markets = await cache.get("markets:revolut") or await cache.get(
                "markets:kraken"
            )

            if markets:
                # Limit initial broadcast frequency for many symbols
                for market in markets[:30]:  # Broadcast top 30 frequently
                    symbol = market.get("symbol", "").replace("-", "/")
                    if not symbol:
                        continue

                    # In a real app, we'd fetch fresh prices here or from a stream
                    # For demo 'wow', we can simulate small price movements if ticker stagnant
                    price = market.get("price", 0.0)

                    # Broadcast to WebSocket
                    await ws_manager.broadcast_to_channel(
                        f"ticker.{market['symbol']}",
                        {
                            "type": "update",
                            "data": {
                                "symbol": market["symbol"],
                                "price": price,
                                "change": market.get("change", 0.0),
                                "volume": market.get("volume", "0"),
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            },
                        },
                    )
            else:
                logger.debug(
                    "Market Data Publisher: Cache empty, waiting for sync task..."
                )

        except Exception as e:
            logger.error(f"Market Data Publisher Error: {e}")

        await asyncio.sleep(2)  # Broadcast cycle every 2s


async def system_state_publisher(app: FastAPI):
    """
    Periodically fetches and broadcasts System State (Navagraha, OODA)
    to connected WebSocket clients.
    """
    logger.info("Starting System State Publisher...")
    while True:
        try:
            # 1. Navagraha Update
            if hasattr(app.state, "navagraha_service") and app.state.navagraha_service:
                # Use default location (Delhi) or configure system default
                state = await app.state.navagraha_service.get_current_state(
                    28.61, 77.20
                )
                await ws_manager.broadcast_navagraha_update(
                    state.model_dump(mode="json")
                )

            # 2. OODA/System Identity Update
            if hasattr(app.state, "system_identity") and app.state.system_identity:
                stats = app.state.system_identity.get_system_statistics()
                # Create a simplified OODA update payload
                ooda_update = {
                    "phase": "ORIENT",  # TODO: Get dynamic phase
                    "cycle_id": f"cycle_{stats['system_state']['total_experiences']}",
                    "coherence": stats["system_state"]["coherence"],
                    "confidence": stats["system_state"]["confidence"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                await ws_manager.broadcast_ooda_update(ooda_update)

        except Exception as e:
            logger.error(f"System State Publisher Error: {e}")

        await asyncio.sleep(5)  # Update every 5 seconds


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("API Server Starting...")

    # Initialize Backend Services
    try:
        # 1. Navagraha Service
        app.state.navagraha_service = NavagrahaService()
        logger.info("Navagraha Service Initialized")

        # 2. System Identity (OODA)
        app.state.system_identity = SystemIdentity()
        await app.state.system_identity.initialize()
        logger.info("System Identity Initialized")

        # 3. Cognitive Orchestrator
        # We initialize it here to be accessible via API
        # Note: In a microservices setup, this might be a remote RPC client.
        app.state.orchestrator = CognitiveOrchestrator(
            agent_registry=None,  # Use default
            usage_tracker=None,  # Optional
            audit_logger=None,  # Optional
        )
        logger.info("Cognitive Orchestrator Initialized")

        # Initialize LLM Gateway for intelligent routing
        try:
            from backend.llm.gateway import get_llm_gateway
            app.state.llm_gateway = await get_llm_gateway()
            logger.info("LLM Gateway initialized")
        except Exception as e:
            logger.error(f"Failed to initialize LLM Gateway: {e}")
            app.state.llm_gateway = None

        # Start NewsAgent and SentimentAgent
        if "news_v1" in app.state.orchestrator.agents:
            try:
                await app.state.orchestrator.agents["news_v1"].start()
                logger.info("NewsAgent started")
            except Exception as e:
                logger.error(f"Failed to start NewsAgent: {e}")
                
        if "sentiment_v1" in app.state.orchestrator.agents:
            try:
                await app.state.orchestrator.agents["sentiment_v1"].start()
                logger.info("SentimentAgent started")
            except Exception as e:
                logger.error(f"Failed to start SentimentAgent: {e}")

        # Start Orchestrator Background Tasks (if any)
        # e.g., consumer_task = asyncio.create_task(app.state.orchestrator.start_market_consumer())

    except Exception as e:
        logger.error(f"Failed to initialize backend services: {e}", exc_info=True)
        # We define them as None to avoid AttributeErrors, but app might be unstable
        app.state.navagraha_service = None
        app.state.system_identity = None
        app.state.orchestrator = None

    # 4. Start Market Data Sync Service (for real-time prices)
    from backend.services.market_data_sync import (start_market_sync,
                                                   stop_market_sync)

    await start_market_sync()
    logger.info("Market Data Sync Service STARTED")

    # Re-enabled: Background Publisher now uses SessionManager.system_admin_session()
    market_task = asyncio.create_task(market_data_publisher())
    system_task = asyncio.create_task(
        system_state_publisher(app)
    )  # Start System Publisher
    logger.info("Background Publishers STARTED")

    # Start NewsAgent periodic fetch
    async def news_fetcher():
        """Fetch news every 60 seconds for major coins."""
        while True:
            try:
                if app.state.orchestrator and "news_v1" in app.state.orchestrator.agents:
                    await app.state.orchestrator.handle_message(
                        AgentMessage(
                            source="system",
                            target="news_v1",
                            type="FETCH_NEWS_REQUEST",
                            payload={"coins": ["BTC", "ETH", "SOL"]},
                        )
                    )
            except Exception as e:
                logger.error(f"News fetcher error: {e}")
            await asyncio.sleep(60)

    news_task = asyncio.create_task(news_fetcher())
    logger.info("News Fetcher STARTED")

    yield

    # Shutdown
    logger.info("API Server Shutting Down...")
    news_task.cancel()
    try:
        await news_task
    except asyncio.CancelledError:
        pass

    # Shutdown
    logger.info("API Server Shutting Down...")
    await stop_market_sync()
    market_task.cancel()
    system_task.cancel()
    try:
        await market_task
        await system_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="Agentic Trader API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DOCS_ENABLED else None,
    redoc_url="/redoc" if settings.DOCS_ENABLED else None,
)

# Prometheus Middleware (add before AuthMiddleware)
app.add_middleware(PrometheusMiddleware)


# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers[
        "Strict-Transport-Security"
    ] = "max-age=31536000; includeSubDomains"
    response.headers[
        "Content-Security-Policy"
    ] = "default-src 'self'; frame-ancestors 'none';"
    return response


# ============================================================================
# CORS Helper Function (must be defined before exception handler)
# ============================================================================


def parse_allowed_origins(origins):
    """Parse ALLOWED_ORIGINS from settings, handling JSON string format."""
    import json

    if isinstance(origins, str):
        try:
            # Try to parse as JSON list
            parsed = json.loads(origins)
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, ValueError):
            # Not valid JSON, treat as single origin
            return [origins]
    elif isinstance(origins, (list, tuple)):
        return list(origins)
    # Fallback to default
    return ["http://localhost:3000"]


# Global Exception Handler (Sanitization)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch-all exception handler to prevent stack traces in production.
    In development (ENV != production), allows FastAPI's default handler (with debug info).
    
    IMPORTANT: Adds CORS headers to error responses to prevent CORS errors in browser
    when the error occurs before the CORS middleware can add headers.
    """
    # Get origin from request for CORS header
    origin = request.headers.get("origin")
    allowed_origins = parse_allowed_origins(settings.ALLOWED_ORIGINS)
    
    # Build CORS headers
    cors_headers = {}
    if origin and origin in allowed_origins:
        cors_headers["Access-Control-Allow-Origin"] = origin
        cors_headers["Access-Control-Allow-Credentials"] = "true"
    elif "*" in allowed_origins:
        cors_headers["Access-Control-Allow-Origin"] = "*"
    
    if settings.ENV == "production":
        logger.error(f"Global Exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error. Please contact support."},
            headers=cors_headers,
        )
    
    # Development mode: return detailed error with CORS headers
    import traceback
    error_detail = {
        "detail": str(exc),
        "type": type(exc).__name__,
        "traceback": traceback.format_exc().split("\n") if settings.DEBUG else None,
    }
    return JSONResponse(
        status_code=500,
        content=error_detail,
        headers=cors_headers,
    )


# ============================================================================
# AUTH MIDDLEWARE - JWT Token Validation
# ============================================================================

# Extend public paths for our API
AuthMiddleware.PUBLIC_PATHS = {
    "/",
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/api/v1/auth/token",
    "/api/v1/auth/register",
    "/api/v1/auth/login",
    "/api/v1/auth/callback",
    "/api/v1/auth/callback",
    "/ws",
    "/metrics",
    "/api/v1/health",
    "/api/v1/prediction/*",
    # Dashboard Data (Allow Public for Demo/Dev Mode)
    "/api/v1/navagraha/current-state",
    "/api/v1/agents/status",
    "/api/v1/agents/chat",
    "/api/v1/agents/run-cycle",
    "/api/v1/agents/trades",
    "/api/v1/federated/state",
    "/api/v1/federated/cycle",
    "/api/v1/ooda/current-cycle",
    "/api/v1/monitoring/health",
    "/api/v1/monitoring/soul-context",
    "/api/v1/monitoring/karma-summary",
    # Trading Data (Allow Public for Demo/Dev Mode)
    "/api/v1/trading/markets",
    "/api/v1/trading/candles/*",
    # Paper Trading (Allow Public for Demo/Dev Mode)
    "/api/v1/paper-trading/status",
    "/api/v1/paper-trading/ws-url",
    "/api/v1/paper-trading/start",
    "/api/v1/paper-trading/stop",
}

# Use JWTValidator with Auth0 config
jwks_url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
token_validator = JWTValidator(
    jwks_url=jwks_url,
    issuer=settings.AUTH0_ISSUER,
    audience=settings.AUTH0_API_AUDIENCE,
    algorithms=[settings.AUTH0_ALGORITHM],
)

# Add AuthMiddleware BEFORE CORS
# (middleware order: last added = first executed, so CORS must be added last to be outermost)
app.add_middleware(AuthMiddleware, jwt_validator=token_validator)

# ============================================================================
# CORS MIDDLEWARE - Must be added LAST to be the OUTERMOST middleware
# This ensures CORS headers are added to ALL responses, including errors
# ============================================================================


# CORS must be the outermost middleware to handle CORS preflight and
# add headers to error responses from inner middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=parse_allowed_origins(settings.ALLOWED_ORIGINS),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(kyc_api.router, prefix="/api/v1/kyc", tags=["kyc"])
app.include_router(trading_api.router)  # Prefix defined in router
app.include_router(
    user_settings_api.router, prefix="/api/v1/settings", tags=["settings"]
)
app.include_router(approval_api.router, prefix="/api/v1/approvals", tags=["approvals"])
app.include_router(analytics_api.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(backtest_api.router, prefix="/api/v1/backtest", tags=["backtesting"])
app.include_router(prediction_api.router, prefix="/api/v1", tags=["prediction"])
app.include_router(ws_router)  # /ws endpoint
app.include_router(paper_trading_ws_router)  # /ws/paper-trading endpoint
app.include_router(paper_trading_api.router)  # Paper trading API

# New Dashboard APIs
app.include_router(navagraha_api.router, prefix="/api/v1/navagraha", tags=["navagraha"])
app.include_router(agents_api.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(federated_api.router, prefix="/api/v1/federated", tags=["federated"])
app.include_router(ooda_api.router, prefix="/api/v1/ooda", tags=["ooda"])
app.include_router(
    monitoring_api.router, prefix="/api/v1/monitoring", tags=["monitoring"]
)

# Health API (Enterprise Resiliency)
app.include_router(health_api.router)

# Metrics Endpoint
app.add_route("/metrics", metrics_endpoint)
