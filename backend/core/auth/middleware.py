"""
Auth Middleware - JWT validation and tenant context injection for FastAPI.

Provides:
- Bearer token extraction
- JWT validation via JWTValidator
- Tenant context injection per-request
"""

import logging
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.core.auth.context import clear_context, set_current_tenant, set_current_user
from backend.core.auth.models import TokenPayload

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for JWT authentication and tenant context.

    Flow:
    1. Extract Bearer token from Authorization header
    2. Validate JWT using JWTValidator
    3. Set tenant and user context for the request
    4. Clear context after response
    """

    # Paths that don't require authentication
    PUBLIC_PATHS = {
        "/",
        "/health",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/auth/login",
        "/auth/callback",
    }

    def __init__(self, app, jwt_validator=None):
        """
        Initialize AuthMiddleware.

        Args:
            app: ASGI application
            jwt_validator: Optional JWTValidator instance
        """
        super().__init__(app)
        self._jwt_validator = jwt_validator

    async def dispatch(self, request: Request, call_next: Callable):
        """Process request with authentication."""
        # Skip auth for public paths and OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS" or self._is_public_path(request.url.path):
            return await call_next(request)

        # Extract token
        token = self._extract_token(request)
        if not token:
            logger.debug(f"Missing token for protected path: {request.url.path}")
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing authorization token"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Validate token and set context
        try:
            if self._jwt_validator:
                payload = await self._jwt_validator.validate_token(token)
            else:
                # Development mode - create dummy payload
                payload = self._create_dev_payload(token)

            set_current_tenant(payload.tenant_id)
            set_current_user(payload.sub)

            # Store payload in request state for handlers
            request.state.token_payload = payload
            request.state.user_id = payload.sub
            request.state.tenant_id = payload.tenant_id
            request.state.roles = payload.roles
            logger.debug(
                f"Successfully authenticated user {payload.sub} for tenant {payload.tenant_id}"
            )

        except Exception as e:
            logger.error(f"Token validation failed for {request.url.path}: {e}")
            return JSONResponse(
                status_code=401,
                content={"detail": str(e)},
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Process request
        try:
            response = await call_next(request)
            return response
        finally:
            # Clear context after request
            clear_context()

    def _is_public_path(self, path: str) -> bool:
        """Check if path is public (no auth required).

        Handles exact matches, prefix matches (with *), and normalizes
        paths with/without trailing slashes.
        """
        # Normalize path: remove trailing slash (except for root "/")
        normalized_path = path if path == "/" else path.rstrip("/")

        # Check exact match (with original and normalized path)
        if path in self.PUBLIC_PATHS:
            return True
        if normalized_path in self.PUBLIC_PATHS:
            return True

        # Prefix match (paths ending with *)
        for public_path in self.PUBLIC_PATHS:
            if public_path.endswith("*"):
                prefix = public_path[:-1]  # Remove the *
                if path.startswith(prefix):
                    return True
                # Also check normalized path
                if normalized_path.startswith(prefix.rstrip("/")):
                    return True

        # Prefix match for API docs
        if path.startswith("/docs") or path.startswith("/redoc"):
            return True

        return False

    def _extract_token(self, request: Request) -> str | None:
        """Extract Bearer token from Authorization header."""
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:]
        return None

    def _create_dev_payload(self, token: str) -> TokenPayload:
        """Create development payload (for testing without real JWT).

        WARNING: This is only allowed in development mode with explicit env var set.
        """
        import os

        if os.getenv("DEVELOPMENT_MODE") != "true":
            raise ValueError(
                "Dev auth payload only available in development mode. "
                "Set DEVELOPMENT_MODE=true explicitly to enable."
            )
        return TokenPayload(
            sub="dev-user-001",
            tenant_id="dev-tenant-001",
            roles=["viewer"],
            exp=9999999999,
        )
