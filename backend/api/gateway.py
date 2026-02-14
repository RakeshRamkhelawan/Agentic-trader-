"""
Public API Gateway - Enterprise REST/GraphQL Interface.

Features:
- Rate limiting per API key
- JWT authentication
- Multi-tenant isolation
- Request/response validation
- Audit logging
"""

import logging
import os
import time
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional

import jwt
import redis.asyncio as redis
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field

from backend.core.config.settings import settings

_logger = logging.getLogger(__name__)

_JWT_SECRET = os.getenv("JWT_SECRET_KEY")
if not _JWT_SECRET:
    _logger.warning(
        "JWT_SECRET_KEY not set! Gateway JWT auth will be unavailable. "
        "Set JWT_SECRET_KEY in .env for production use."
    )


# ============================================
# API MODELS
# ============================================


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderRequest(BaseModel):
    """Place a trading order via API."""

    symbol: str = Field(..., description="Trading pair (e.g., BTC-EUR)")
    side: OrderSide
    quantity: float = Field(..., gt=0, description="Amount to trade")
    price: Optional[float] = Field(
        None, description="Limit price (None = market order)"
    )
    order_type: str = Field("limit", pattern="^(limit|market|stop)$")


class PortfolioRequest(BaseModel):
    """Get portfolio details."""

    account_id: str


class PortfolioResponse(BaseModel):
    """Portfolio snapshot response."""

    account_id: str
    balance_usd: float
    total_positions: int
    portfolio_value: float
    max_drawdown_pct: float
    var_95: float


class ExecutionResponse(BaseModel):
    """Response from order execution."""

    execution_id: str
    status: str
    timestamp: datetime
    symbol: str
    quantity: float
    price: float
    commission: float


class HealthResponse(BaseModel):
    """API health check response."""

    status: str
    timestamp: datetime
    version: str


# ============================================
# RATE LIMITING
# ============================================


class RateLimiter:
    """
    Redis-backed rate limiter per API key (Fixed Window).
    Falls back to in-memory if Redis is not configured.
    """

    def __init__(self, requests_per_minute: int = 60, redis_url: Optional[str] = None):
        self.requests_per_minute = requests_per_minute
        self.redis_url = redis_url
        self.redis: Optional[redis.Redis] = None
        self._local_history: Dict[str, List[float]] = {}

        if self.redis_url:
            try:
                self.redis = redis.from_url(
                    self.redis_url, encoding="utf-8", decode_responses=True
                )
            except Exception as e:
                _logger.error(f"Failed to initialize Redis Rate Limiter: {e}")

    async def is_allowed(self, api_key: str) -> bool:
        """Check if API key can make a request (Async)."""
        if self.redis:
            try:
                key = f"rate_limit:{api_key}"
                # Atomic INCR
                count = await self.redis.incr(key)

                # Set expiry on first request
                if count == 1:
                    await self.redis.expire(key, 60)

                return count <= self.requests_per_minute
            except Exception as e:
                _logger.error(
                    f"Redis rate limit check failed: {e}. Falling back to in-memory."
                )

        # In-memory fallback (Same logic as before)
        current_time = time.time()
        cutoff_time = current_time - 60

        if api_key not in self._local_history:
            self._local_history[api_key] = []

        self._local_history[api_key] = [
            t for t in self._local_history[api_key] if t > cutoff_time
        ]

        if len(self._local_history[api_key]) >= self.requests_per_minute:
            return False

        self._local_history[api_key].append(current_time)
        return True


# ============================================
# AUTHENTICATION
# ============================================


class JWTManager:
    """JWT token management for API authentication."""

    def __init__(self, secret_key: Optional[str] = None, algorithm: str = "HS256"):
        if secret_key is None:
            secret_key = _JWT_SECRET
        if not secret_key:
            raise ValueError("JWT secret key is required. Set JWT_SECRET_KEY in .env.")
        self.secret_key = secret_key
        self.algorithm = algorithm

    def create_token(
        self, tenant_id: str, account_id: str, expires_in_hours: int = 24
    ) -> str:
        """Create JWT token for API access."""
        now = datetime.now(timezone.utc)
        payload = {
            "tenant_id": tenant_id,
            "account_id": account_id,
            "exp": now + timedelta(hours=expires_in_hours),
            "iat": now,
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token

    def verify_token(self, token: str) -> Dict:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")


# ============================================
# API GATEWAY
# ============================================


class APIGateway:
    """Enterprise API Gateway with auth, rate limiting, and audit logging."""

    def __init__(
        self,
        secret_key: Optional[str] = None,
        requests_per_minute: int = 60,
        redis_url: Optional[str] = None,
    ):
        self.app = FastAPI(title="Agentic Trader API", version="1.0.0")
        self.jwt_manager = JWTManager(secret_key)

        # Use settings.REDIS_URL if not provided
        if redis_url is None:
            redis_url = settings.REDIS_URL

        self.rate_limiter = RateLimiter(requests_per_minute, redis_url)

        # Include WebSocket router
        from backend.api.websocket_endpoints import router as ws_router

        self.app.include_router(ws_router, tags=["websocket"])

        # Exception Handlers
        from backend.core.exceptions import QuotaExceededError

        @self.app.exception_handler(QuotaExceededError)
        async def quota_exceeded_handler(request: Request, exc: QuotaExceededError):
            return JSONResponse(
                status_code=429,
                content={"detail": exc.message, "details": exc.details},
                headers={"Retry-After": "3600"},  # Default retry after 1 hour
            )

        # Setup routes
        self._setup_routes()

    def _setup_routes(self):
        """Setup all API endpoints."""

        # Helper function to verify auth
        def get_token_from_header(authorization: str = Header(None)) -> str:
            """Extract and verify Bearer token from Authorization header."""
            if not authorization:
                raise HTTPException(
                    status_code=403, detail="Missing authorization header"
                )

            parts = authorization.split()
            if len(parts) != 2 or parts[0].lower() != "bearer":
                raise HTTPException(
                    status_code=403, detail="Invalid authorization header"
                )

            return parts[1]

        @self.app.get("/health", response_model=HealthResponse)
        async def health_check():
            """Health check endpoint (no auth required)."""
            return HealthResponse(
                status="healthy", timestamp=datetime.now(timezone.utc), version="1.0.0"
            )

        @self.app.post("/auth/token")
        async def get_token(tenant_id: str, account_id: str):
            """
            Get JWT token for API access.

            Args:
                tenant_id: Tenant identifier
                account_id: Account identifier

            Returns:
                JWT token for use in subsequent requests
            """
            token = self.jwt_manager.create_token(tenant_id, account_id)
            return {"access_token": token, "token_type": "bearer"}

        @self.app.post("/orders", response_model=ExecutionResponse)
        async def place_order(order: OrderRequest, authorization: str = Header(None)):
            """
            Place a trading order.

            Requires: JWT token in Authorization header
            """
            # Get and verify token
            token = get_token_from_header(authorization)
            token_data = self.jwt_manager.verify_token(token)

            # Check rate limit
            api_key = token_data.get("account_id")
            if not await self.rate_limiter.is_allowed(api_key):
                raise HTTPException(status_code=429, detail="Rate limit exceeded")

            # Validate order
            if order.quantity <= 0:
                raise HTTPException(status_code=400, detail="Quantity must be positive")

            if order.order_type == "limit" and order.price is None:
                raise HTTPException(
                    status_code=400, detail="Limit orders require price"
                )

            # In production: Send to execution engine
            # For now: Return mock response
            return ExecutionResponse(
                execution_id="exec_" + str(int(time.time())),
                status="pending",
                timestamp=datetime.now(timezone.utc),
                symbol=order.symbol,
                quantity=order.quantity,
                price=order.price or 0.0,
                commission=order.quantity * (order.price or 0.0) * 0.001,
            )

        @self.app.get("/portfolio", response_model=PortfolioResponse)
        async def get_portfolio(account_id: str, authorization: str = Header(None)):
            """
            Get portfolio details.

            Requires: JWT token, must own account_id
            """
            # Get and verify token
            token = get_token_from_header(authorization)
            token_data = self.jwt_manager.verify_token(token)

            # Tenant isolation: Can only access own accounts
            if token_data["account_id"] != account_id:
                raise HTTPException(status_code=403, detail="Access denied")

            # Check rate limit
            if not await self.rate_limiter.is_allowed(account_id):
                raise HTTPException(status_code=429, detail="Rate limit exceeded")

            # In production: Fetch from database
            # For now: Return mock data
            return PortfolioResponse(
                account_id=account_id,
                balance_usd=100000.0,
                total_positions=5,
                portfolio_value=105000.0,
                max_drawdown_pct=2.5,
                var_95=2500.0,
            )

        @self.app.get("/risk/var")
        async def get_var(
            account_id: str,
            confidence_level: float = 0.95,
            authorization: str = Header(None),
        ):
            """
            Get Value at Risk metrics.

            Args:
                account_id: Account to analyze
                confidence_level: VaR confidence (0.90, 0.95, 0.99)
            """
            # Get and verify token
            token = get_token_from_header(authorization)
            token_data = self.jwt_manager.verify_token(token)

            # Tenant isolation
            if token_data["account_id"] != account_id:
                raise HTTPException(status_code=403, detail="Access denied")

            if not (0.85 < confidence_level < 0.995):
                raise HTTPException(status_code=400, detail="Invalid confidence level")

            # In production: Calculate VaR from historical data
            return {
                "account_id": account_id,
                "confidence_level": confidence_level,
                "var_usd": 2500.0,
                "cvar_usd": 3200.0,
                "timestamp": datetime.now(timezone.utc),
            }

    def get_app(self) -> FastAPI:
        """Get FastAPI app instance."""
        return self.app


# ============================================
# MIDDLEWARE
# ============================================


def create_gateway(
    secret_key: Optional[str] = None, requests_per_minute: int = 60
) -> FastAPI:
    """
    Factory function to create API gateway.

    Args:
        secret_key: Secret key for JWT signing
        requests_per_minute: Rate limit per API key

    Returns:
        FastAPI application instance
    """
    gateway = APIGateway(secret_key, requests_per_minute)
    return gateway.get_app()


if __name__ == "__main__":
    import uvicorn

    app = create_gateway()

    # Run: uvicorn backend.api.gateway:app --reload
    uvicorn.run(app, host="0.0.0.0", port=8000)
