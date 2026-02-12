
import asyncio
import logging
from contextlib import asynccontextmanager
from unittest.mock import MagicMock
from fastapi import FastAPI, Depends, Request

from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone

# Routers
from backend.api.auth_api import router as auth_router
from backend.api import trading_api
from backend.api import user_settings_api
from backend.api import approval_api
from backend.api.websocket_endpoints import router as ws_router
from backend.api import analytics_api
from backend.api import backtest_api
from backend.observability.metrics import PrometheusMiddleware, metrics_endpoint

# Services
from backend.services.trading_service import get_trading_service
from backend.api.websocket_manager import ws_manager
from backend.api.deps import get_db

# Auth Middleware
from backend.core.auth.middleware import AuthMiddleware
from backend.core.auth.models import TokenPayload
from backend.core.auth.jwt_validator import JWTValidator
from backend.core.config.settings import settings

# JWT validation
try:
    from jose import jwt, JWTError
    JOSE_AVAILABLE = True
except ImportError:
    JOSE_AVAILABLE = False
    jwt = None
    JWTError = Exception

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("API")

# SimpleTokenValidator removed - using Auth0 JWTValidator exclusively



# Background Task: Redis Subscriber (Replaces legacy publisher)

# Background Task: Redis Subscriber (Replaces legacy publisher)
from backend.market_data.sinks.redis_subscriber import RedisSubscriber
# Market Data Components
from backend.market_data.pipeline import MarketDataPipeline
from backend.market_data.providers.bybit_provider import BybitProvider
from backend.market_data.providers.kraken_provider import KrakenProvider
from backend.market_data.sinks.redis_publisher import RedisPublisher
from backend.market_data.sinks.clickhouse_writer import ClickHouseWriter
from backend.storage.clickhouse_init import get_clickhouse_client, init_clickhouse
import redis.asyncio as redis

# Global Pipeline
market_data_pipeline = None

def initialize_market_data() -> MarketDataPipeline:
    """
    Initialize the Market Data Pipeline with Providers and Sinks.
    """
    pipeline = MarketDataPipeline()
    
    # 0. Normalizer
    from backend.market_data.normalizer import StandardNormalizer
    symbol_map = {
        ("bybit_public", "BTCUSDT"): "BTC/USDT",
        ("bybit_public", "ETHUSDT"): "ETH/USDT",
        ("kraken_public", "XBT/USD"): "BTC/USD",
        ("kraken_public", "ETH/USD"): "ETH/USD",
    }
    normalizer = StandardNormalizer(symbol_map)
    pipeline.set_normalizer(normalizer)

    # 1. Redis Publisher (Sink)
    try:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=False)
        redis_publisher = RedisPublisher(redis_client, stream_key="market_events")
        pipeline.add_sink(redis_publisher)
        logger.info("Added RedisPublisher sink")
    except Exception as e:
        logger.error(f"Failed to initialize RedisPublisher: {e}")

    # 2. ClickHouse Writer (Sink)
    # Initialize SignalBridge
    from backend.services.signal_bridge import SignalBridge
    signal_bridge = SignalBridge()
    signal_bridge.set_ws_manager(ws_manager)

    # The following lines related to CognitiveOrchestrator and its dependencies
    # (clickhouse_client, market_writer, message_writer) are not defined in the current context.
    # This block is being inserted as per the user's instruction, but it might require
    # additional context or definitions to be fully functional.
    # For now, it's commented out to avoid syntax errors, assuming the user will
    # provide the necessary definitions later or this is a placeholder.
    # orchestrator = CognitiveOrchestrator(
    #     clickhouse_client=clickhouse_client,
    #     market_writer=market_writer,
    #     message_writer=message_writer,
    #     signal_bridge=signal_bridge # NIEUW
    # )
    if init_clickhouse():
        try:
            ch_client = get_clickhouse_client()
            if ch_client:
                ch_writer = ClickHouseWriter(ch_client, table="market_events")
                pipeline.add_sink(ch_writer)
                logger.info("Added ClickHouseWriter sink")
        except Exception as e:
             logger.error(f"Failed to initialize ClickHouseWriter: {e}")
    else:
        logger.warning("ClickHouse initialization failed - Skipping ClickHouseWriter")

    # 3. Providers
    # Bybit (Public)
    try:
        bybit = BybitProvider(name="bybit_public", symbols=["BTCUSDT", "ETHUSDT"])
        pipeline.add_provider(bybit)
        logger.info("Added BybitProvider")
    except Exception as e:
        logger.error(f"Failed to add BybitProvider: {e}")
        
    # Kraken (Public)
    try:
        kraken = KrakenProvider(name="kraken_public", symbols=["XBT/USD", "ETH/USD"])
        pipeline.add_provider(kraken)
        logger.info("Added KrakenProvider")
    except Exception as e:
        logger.error(f"Failed to add KrakenProvider: {e}")

    return pipeline

async def start_redis_subscriber():
    """Start the Redis Subscriber to bridge Redis Stream -> WebSocket."""
    import redis.asyncio as redis
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=False)
    subscriber = RedisSubscriber(redis_client, ws_manager, "market_events")
    await subscriber.run()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("API Server Starting...")
    
    # Initialize Market Data Pipeline (Producer)
    global market_data_pipeline
    market_data_pipeline = initialize_market_data()
    pipeline_task = asyncio.create_task(market_data_pipeline.start())
    logger.info("Market Data Pipeline STARTED")

    # Initialize Redis Subscriber (Consumer -> WebSocket)
    subscriber_task = asyncio.create_task(start_redis_subscriber())
    logger.info("Redis Subscriber STARTED")
    
    yield
    
    # Shutdown
    logger.info("API Server Shutting Down...")
    
    if market_data_pipeline:
        logger.info("Stopping Market Data Pipeline...")
        await market_data_pipeline.stop()
        pipeline_task.cancel()
        
    subscriber_task.cancel()
    try:
        await pipeline_task
        await subscriber_task
    except asyncio.CancelledError:
        pass

# ... (Auth Middleware etc)



    # End of lifespan


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
    docs_url="/docs" if settings.DOCS_ENABLED else None,
    redoc_url="/redoc" if settings.DOCS_ENABLED else None,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus Metrics
app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics", metrics_endpoint)

# Auth Middleware
app.add_middleware(AuthMiddleware)

# Include Routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(trading_api.router, prefix="/api/v1/trading", tags=["trading"])
app.include_router(user_settings_api.router, prefix="/api/v1/settings", tags=["settings"])
app.include_router(approval_api.router, prefix="/api/v1/approval", tags=["approval"])
# app.include_router(analytics_api.router, prefix="/api/v1/analytics", tags=["analytics"]) # Check if exists
# app.include_router(backtest_api.router, prefix="/api/v1/backtest", tags=["backtest"]) # Check if exists
app.include_router(ws_router, prefix="/api/v1/ws", tags=["websocket"])



@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/v1/health/market-data")
async def market_data_health():
    """Report Market Data Pipeline health."""
    if not market_data_pipeline:
        return JSONResponse(status_code=503, content={"status": "initializing"})
    
    return {
        "status": "ok",
        "queue_size": market_data_pipeline.raw_queue.qsize(),
        "providers": [
            {
                "name": p.name, 
                "connected": getattr(p, "connected", False) # internal state
            } for p in market_data_pipeline.providers
        ]
    }
