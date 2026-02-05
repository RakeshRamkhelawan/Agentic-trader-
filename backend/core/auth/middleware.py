"""
Auth Middleware - JWT validation and tenant context injection for FastAPI.

Provides:
- Bearer token extraction
- JWT validation via JWTValidator
- Tenant context injection per-request
"""
import logging
from typing import Optional, Callable
from functools import wraps

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from backend.core.auth.context import set_current_tenant, set_current_user, clear_context
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
        # Skip auth for public paths
        if self._is_public_path(request.url.path):
            return await call_next(request)
        
        # Extract token
        token = self._extract_token(request)
        if not token:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing authorization token"},
                headers={"WWW-Authenticate": "Bearer"}
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
            
        except Exception as e:
            logger.warning(f"Token validation failed: {e}")
            return JSONResponse(
                status_code=401,
                content={"detail": str(e)},
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Process request
        try:
            response = await call_next(request)
            return response
        finally:
            # Clear context after request
            clear_context()
    
    def _is_public_path(self, path: str) -> bool:
        """Check if path is public (no auth required)."""
        # Exact match
        if path in self.PUBLIC_PATHS:
            return True
        # Prefix match for API docs
        if path.startswith("/docs") or path.startswith("/redoc"):
            return True
        return False
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """Extract Bearer token from Authorization header."""
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:]
        return None
    
    def _create_dev_payload(self, token: str) -> TokenPayload:
        """Create development payload (for testing without real JWT)."""
        return TokenPayload(
            sub="dev-user-001",
            tenant_id="dev-tenant-001",
            roles=["admin"],
            exp=9999999999
        )
