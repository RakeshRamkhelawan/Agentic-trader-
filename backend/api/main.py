
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone

# Routers
from backend.api.auth_api import router as auth_router
from backend.api import trading_api
from backend.api import user_settings_api
from backend.api import approval_api
from backend.api.websocket_endpoints import router as ws_router
from backend.api import analytics_api

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


# Background Task: Market Data Publisher
# Bridges the gap between TradingService (Revolut) and WebSocketManager (Frontend)
async def market_data_publisher():
    """
    Periodically fetches market data from Revolut (via TradingService)
    and broadcasts it to connected WebSocket clients.
    """
    logger.info("Starting Market Data Publisher...")
    trading_service = get_trading_service()
    from backend.core.cache_layer import get_cache
    cache = get_cache()
    
    while True:
        try:
            # 1. Get all markets from cache (populated by sync task)
            # We check multiple possible keys to be robust
            markets = await cache.get("markets:revolut") or await cache.get("markets:kraken")
            
            if markets:
                # Limit initial broadcast frequency for many symbols
                for market in markets[:30]: # Broadcast top 30 frequently
                    symbol = market.get("symbol", "").replace("-", "/")
                    if not symbol: continue
                    
                    # In a real app, we'd fetch fresh prices here or from a stream
                    # For demo 'wow', we can simulate small price movements if ticker stagnant
                    price = market.get("price", 0.0)
                    
                    # Broadcast to WebSocket
                    await ws_manager.broadcast_to_channel(
                        f"ticker.{market['symbol']}",
                        {
                            "type": "update",
                            "data": {
                                "symbol": market['symbol'],
                                "price": price,
                                "change": market.get("change", 0.0),
                                "volume": market.get("volume", "0"),
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            }
                        }
                    )
            else:
                logger.debug("Market Data Publisher: Cache empty, waiting for sync task...")
                
        except Exception as e:
            logger.error(f"Market Data Publisher Error: {e}")
            
        await asyncio.sleep(2) # Broadcast cycle every 2s

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("API Server Starting...")
    
    # Re-enabled: Background Publisher now uses SessionManager.system_admin_session()
    task = asyncio.create_task(market_data_publisher())
    logger.info("Market Data Publisher STARTED")
    
    yield
    
    # Shutdown
    logger.info("API Server Shutting Down...")
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="Agentic Trader API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
# Frontend runs on 3000, API on 8001
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    "/ws",
}

# Use JWTValidator with Auth0 config
jwks_url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
token_validator = JWTValidator(
    jwks_url=jwks_url,
    issuer=settings.AUTH0_ISSUER,
    audience=settings.AUTH0_API_AUDIENCE,
    algorithms=[settings.AUTH0_ALGORITHM]
)

# Add AuthMiddleware AFTER CORS (middleware order: last added = first executed)
app.add_middleware(AuthMiddleware, jwt_validator=token_validator)

# Mount Routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(trading_api.router) # Prefix defined in router
app.include_router(user_settings_api.router, prefix="/api/v1/settings", tags=["settings"])
app.include_router(approval_api.router, prefix="/api/v1/approvals", tags=["approvals"])
app.include_router(analytics_api.router, prefix="/api/v1/analytics", tags=["analytics"]) # Added analytics_api router
app.include_router(ws_router) # /ws endpoint

@app.get("/health")
def health_check():
    return {"status": "ok"}
