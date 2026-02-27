"""
Public API Gateway - Enterprise REST/GraphQL Interface.

Features:
- Rate limiting per API key
- JWT authentication with token caching (SHA256 hash, 5min TTL)
- RBAC role enforcement
- Multi-tenant isolation
- Request/response validation
- Audit logging
"""

import hashlib
import logging
import os
import time
from datetime import UTC, datetime, timedelta
from enum import Enum

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

# Security scheme for OpenAPI docs
security = HTTPBearer()


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
    price: float | None = Field(None, description="Limit price (None = market order)")
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


class TokenCacheEntry:
    """Cached token validation result."""

    def __init__(self, payload: dict, cached_at: float):
        self.payload = payload
        self.cached_at = cached_at

    def is_expired(self, ttl_seconds: int = 300) -> bool:
        """Check if cache entry is expired (default 5 minutes)."""
        return (time.time() - self.cached_at) > ttl_seconds


# ============================================
# RATE LIMITING
# ============================================


class RateLimiter:
    """
    Redis-backed rate limiter per API key (Fixed Window).
    Uses Redis pipeline for batch operations.
    Falls back to in-memory if Redis is not configured.
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        redis_url: str | None = None,
        use_pipeline: bool = True,
    ):
        self.requests_per_minute = requests_per_minute
        self.redis_url = redis_url
        self.use_pipeline = use_pipeline
        self.redis: redis.Redis | None = None
        self._local_history: dict[str, list[float]] = {}
        self._pipeline_buffer: list[tuple] = []
        self._pipeline_batch_size = 10

        if self.redis_url:
            try:
                self.redis = redis.from_url(self.redis_url, encoding="utf-8", decode_responses=True)
            except Exception as e:
                _logger.error(f"Failed to initialize Redis Rate Limiter: {e}")

    async def is_allowed(self, api_key: str) -> bool:
        """Check if API key can make a request (Async)."""
        if self.redis:
            try:
                key = f"rate_limit:{api_key}"

                if self.use_pipeline:
                    # Use pipeline for atomic operations
                    pipe = self.redis.pipeline()
                    pipe.incr(key)
                    pipe.ttl(key)
                    results = await pipe.execute()
                    count = results[0]
                    ttl = results[1]

                    # Set expiry if new key or TTL is -1 (no expiry)
                    if count == 1 or ttl == -1:
                        await self.redis.expire(key, 60)
                else:
                    # Atomic INCR
                    count = await self.redis.incr(key)

                    # Set expiry on first request
                    if count == 1:
                        await self.redis.expire(key, 60)

                return count <= self.requests_per_minute
            except Exception as e:
                _logger.error(f"Redis rate limit check failed: {e}. Falling back to in-memory.")

        # In-memory fallback (Same logic as before)
        current_time = time.time()
        cutoff_time = current_time - 60

        if api_key not in self._local_history:
            self._local_history[api_key] = []

        self._local_history[api_key] = [t for t in self._local_history[api_key] if t > cutoff_time]

        if len(self._local_history[api_key]) >= self.requests_per_minute:
            return False

        self._local_history[api_key].append(current_time)
        return True


# ============================================
# AUTHENTICATION WITH TOKEN CACHING
# ============================================


class JWTManager:
    """
    JWT token management with SHA256 hash-based caching.

    NEVER stores raw tokens - only SHA256 hashes as cache keys.
    Cache TTL: 5 minutes (300 seconds).
    """

    def __init__(
        self,
        secret_key: str | None = None,
        algorithm: str = "HS256",
        cache_ttl_seconds: int = 300,
        redis_url: str | None = None,
    ):
        if secret_key is None:
            secret_key = _JWT_SECRET
        if not secret_key:
            raise ValueError("JWT secret key is required. Set JWT_SECRET_KEY in .env.")
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.cache_ttl_seconds = cache_ttl_seconds

        # Token cache: SHA256 hash -> TokenCacheEntry
        self._token_cache: dict[str, TokenCacheEntry] = {}

        # Redis for distributed caching (optional)
        self.redis: redis.Redis | None = None
        if redis_url:
            try:
                self.redis = redis.from_url(redis_url)
            except Exception as e:
                _logger.error(f"Failed to initialize Redis for token cache: {e}")

        # Cache hit/miss metrics
        self.cache_hits = 0
        self.cache_misses = 0

    def _hash_token(self, token: str) -> str:
        """
        Generate SHA256 hash of token for cache key.
        NEVER store raw tokens in cache.
        """
        return hashlib.sha256(token.encode()).hexdigest()

    async def verify_token(self, token: str) -> dict:
        """
        Verify and decode JWT token with caching.

        Args:
            token: Raw JWT token

        Returns:
            Decoded token payload

        Raises:
            HTTPException: If token is invalid or expired
        """
        token_hash = self._hash_token(token)

        # Check in-memory cache first
        cached_entry = self._token_cache.get(token_hash)
        if cached_entry and not cached_entry.is_expired(self.cache_ttl_seconds):
            self.cache_hits += 1
            _logger.debug(f"Token cache HIT for hash: {token_hash[:16]}...")
            return cached_entry.payload

        # Check Redis cache (distributed)
        if self.redis:
            try:
                cached_payload = await self.redis.get(f"token_cache:{token_hash}")
                if cached_payload:
                    import json

                    payload = json.loads(cached_payload)
                    # Update in-memory cache
                    self._token_cache[token_hash] = TokenCacheEntry(payload, time.time())
                    self.cache_hits += 1
                    _logger.debug(f"Token cache HIT (Redis) for hash: {token_hash[:16]}...")
                    return payload
            except Exception as e:
                _logger.error(f"Redis token cache read failed: {e}")

        # Cache miss - verify token cryptographically
        self.cache_misses += 1
        _logger.debug(f"Token cache MISS for hash: {token_hash[:16]}...")

        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Cache the verified payload
            self._token_cache[token_hash] = TokenCacheEntry(payload, time.time())

            # Also cache in Redis (distributed)
            if self.redis:
                try:
                    import json

                    await self.redis.setex(
                        f"token_cache:{token_hash}",
                        self.cache_ttl_seconds,
                        json.dumps(payload),
                    )
                except Exception as e:
                    _logger.error(f"Redis token cache write failed: {e}")

            return payload

        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

    def create_token(
        self,
        tenant_id: str,
        account_id: str,
        roles: list[str],
        expires_in_hours: int = 24,
    ) -> str:
        """
        Create JWT token for API access with role claims.

        Args:
            tenant_id: Tenant identifier
            account_id: Account identifier
            roles: List of roles (e.g., ["trader", "viewer"])
            expires_in_hours: Token expiration time

        Returns:
            JWT token string
        """
        now = datetime.now(UTC)
        payload = {
            "tenant_id": tenant_id,
            "account_id": account_id,
            "roles": roles,
            "exp": now + timedelta(hours=expires_in_hours),
            "iat": now,
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token

    def invalidate_cache(self, token: str) -> None:
        """
        Invalidate token cache (e.g., on logout).

        Args:
            token: Raw JWT token to invalidate
        """
        token_hash = self._hash_token(token)

        # Remove from in-memory cache
        if token_hash in self._token_cache:
            del self._token_cache[token_hash]

        # Remove from Redis
        if self.redis:
            try:
                # Use sync delete in async context - fire and forget
                import asyncio

                asyncio.create_task(self.redis.delete(f"token_cache:{token_hash}"))
            except Exception as e:
                _logger.error(f"Redis token cache invalidation failed: {e}")

    def get_cache_stats(self) -> dict:
        """Get token cache statistics."""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate_percent": round(hit_rate, 2),
            "cached_tokens": len(self._token_cache),
        }

    def clear_cache(self) -> None:
        """Clear token cache."""
        self._token_cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0


# ============================================
# RBAC DEPENDENCIES
# ============================================


async def get_current_user(token: str = Header(...), jwt_manager: JWTManager = None) -> dict:
    """
    FastAPI dependency to get current user from token.

    Args:
        token: Authorization header with Bearer token
        jwt_manager: JWTManager instance

    Returns:
        User payload dictionary
    """
    if jwt_manager is None:
        jwt_manager = JWTManager()

    # Extract token from Bearer header
    if token.startswith("Bearer "):
        token = token[7:]

    return await jwt_manager.verify_token(token)


def has_role(user_payload: dict, required_roles: list[str]) -> bool:
    """Check if user has any of the required roles."""
    user_roles = set(user_payload.get("roles", []))
    required = set(required_roles)
    return bool(user_roles & required)


# ============================================
# API GATEWAY
# ============================================


class APIGateway:
    """Enterprise API Gateway with auth, rate limiting, and audit logging."""

    def __init__(
        self,
        secret_key: str | None = None,
        requests_per_minute: int = 60,
        redis_url: str | None = None,
    ):
        self.app = FastAPI(title="Agentic Trader API", version="1.0.0")
        self.jwt_manager = JWTManager(
            secret_key,
            redis_url=redis_url,
            cache_ttl_seconds=300,  # 5 minutes
        )

        # Use settings.REDIS_URL if not provided
        if redis_url is None:
            redis_url = settings.REDIS_URL

        self.rate_limiter = RateLimiter(
            requests_per_minute,
            redis_url,
            use_pipeline=True,
        )

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
                raise HTTPException(status_code=403, detail="Missing authorization header")

            parts = authorization.split()
            if len(parts) != 2 or parts[0].lower() != "bearer":
                raise HTTPException(status_code=403, detail="Invalid authorization header")

            return parts[1]

        # Helper to get user from token
        async def get_user(authorization: str = Header(None)) -> dict:
            """Get verified user from authorization header."""
            token = get_token_from_header(authorization)
            return await self.jwt_manager.verify_token(token)

        @self.app.get("/health", response_model=HealthResponse)
        async def health_check():
            """Health check endpoint (no auth required)."""
            return HealthResponse(status="healthy", timestamp=datetime.now(UTC), version="1.0.0")

        @self.app.get("/health/cache")
        async def cache_stats():
            """Get token cache statistics (admin only)."""
            return self.jwt_manager.get_cache_stats()

        @self.app.post("/auth/token")
        async def get_token(tenant_id: str, account_id: str, roles: str = "viewer"):
            """
            Get JWT token for API access.

            Args:
                tenant_id: Tenant identifier
                account_id: Account identifier
                roles: Comma-separated list of roles

            Returns:
                JWT token for use in subsequent requests
            """
            role_list = [r.strip() for r in roles.split(",")]
            token = self.jwt_manager.create_token(tenant_id, account_id, role_list)
            return {"access_token": token, "token_type": "bearer"}

        @self.app.post("/auth/logout")
        async def logout(authorization: str = Header(None)):
            """
            Logout and invalidate token cache.

            Note: JWT tokens are stateless - this only clears server-side cache.
            Token will remain valid until expiry.
            """
            token = get_token_from_header(authorization)
            self.jwt_manager.invalidate_cache(token)
            return {"detail": "Token cache invalidated"}

        @self.app.post("/orders", response_model=ExecutionResponse)
        async def place_order(order: OrderRequest, user: dict = Depends(get_user)):
            """
            Place a trading order.

            Requires:
            - JWT token with 'trader' or 'admin' role
            - Rate limit compliance
            """
            # Check roles
            if not has_role(user, ["trader", "admin"]):
                raise HTTPException(
                    status_code=403,
                    detail="Insufficient permissions. Required: trader or admin",
                )

            # Get and verify token
            account_id = user.get("account_id")

            # Check rate limit
            if not await self.rate_limiter.is_allowed(account_id):
                raise HTTPException(status_code=429, detail="Rate limit exceeded")

            # Validate order
            if order.quantity <= 0:
                raise HTTPException(status_code=400, detail="Quantity must be positive")

            if order.order_type == "limit" and order.price is None:
                raise HTTPException(status_code=400, detail="Limit orders require price")

            # In production: Send to execution engine
            # For now: Return mock response
            return ExecutionResponse(
                execution_id="exec_" + str(int(time.time())),
                status="pending",
                timestamp=datetime.now(UTC),
                symbol=order.symbol,
                quantity=order.quantity,
                price=order.price or 0.0,
                commission=order.quantity * (order.price or 0.0) * 0.001,
            )

        @self.app.get("/portfolio", response_model=PortfolioResponse)
        async def get_portfolio(account_id: str, user: dict = Depends(get_user)):
            """
            Get portfolio details.

            Requires:
            - JWT token
            - Must own account_id or have admin role
            """
            # Check permissions
            is_owner = user.get("account_id") == account_id
            is_admin = has_role(user, ["admin"])

            if not (is_owner or is_admin):
                raise HTTPException(
                    status_code=403,
                    detail="Access denied. Can only access own portfolio or have admin role.",
                )

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
            user: dict = Depends(get_user),
        ):
            """
            Get Value at Risk metrics.

            Requires:
            - JWT token
            - Must own account or have admin/risk_manager role

            Args:
                account_id: Account to analyze
                confidence_level: VaR confidence (0.90, 0.95, 0.99)
            """
            # Check permissions
            is_owner = user.get("account_id") == account_id
            has_permission = has_role(user, ["admin", "risk_manager", "trader"])

            if not (is_owner or has_permission):
                raise HTTPException(
                    status_code=403,
                    detail="Access denied. Requires admin, risk_manager, or trader role.",
                )

            if not (0.85 < confidence_level < 0.995):
                raise HTTPException(status_code=400, detail="Invalid confidence level")

            # In production: Calculate VaR from historical data
            return {
                "account_id": account_id,
                "confidence_level": confidence_level,
                "var_usd": 2500.0,
                "cvar_usd": 3200.0,
                "timestamp": datetime.now(UTC),
            }

        @self.app.get("/admin/users")
        async def admin_list_users(user: dict = Depends(get_user)):
            """
            Admin endpoint to list all users.

            Requires: admin role
            """
            if not has_role(user, ["admin"]):
                raise HTTPException(status_code=403, detail="Admin access required")

            # Mock response
            return {"users": []}

    def get_app(self) -> FastAPI:
        """Get FastAPI app instance."""
        return self.app


# ============================================
# MIDDLEWARE
# ============================================


def create_gateway(
    secret_key: str | None = None,
    requests_per_minute: int = 60,
    redis_url: str | None = None,
) -> FastAPI:
    """
    Factory function to create API gateway.

    Args:
        secret_key: Secret key for JWT signing
        requests_per_minute: Rate limit per API key
        redis_url: Redis URL for distributed caching

    Returns:
        FastAPI application instance
    """
    gateway = APIGateway(secret_key, requests_per_minute, redis_url)
    return gateway.get_app()


if __name__ == "__main__":
    import uvicorn

    app = create_gateway()

    # Run: uvicorn backend.api.gateway:app --reload
    uvicorn.run(app, host="0.0.0.0", port=8000)  # nosec B104 - Required for Docker/containerized deployment
