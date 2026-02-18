"""
API Dependencies.
Shares common logic like Tenant ID extraction and Database Session setup with RLS context.
"""

import os
from typing import Any, AsyncGenerator, Dict

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

# Import raw session maker from database.py
# Import SessionManager from database.py
from backend.core.database import SessionManager

# JWT handling
try:
    from jose import JWTError, jwt

    JOSE_AVAILABLE = True
except ImportError:
    JOSE_AVAILABLE = False
    jwt = None
    JWTError = Exception

# Secret key from environment (never hardcoded in production)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")


async def get_current_tenant_id(request: Request) -> str:
    """
    Extract tenant_id from JWT token in Authorization header.

    Flow:
    1. Check if AuthMiddleware already set tenant_id in request.state
    2. If not, try to parse JWT directly from header
    3. Fallback to dev tenant for development
    """
    # Check if AuthMiddleware already processed the token
    if hasattr(request.state, "tenant_id") and request.state.tenant_id:
        return request.state.tenant_id

    # Fallback: try to extract from Authorization header directly
    auth_header = request.headers.get("Authorization", "")

    if not auth_header or not auth_header.startswith("Bearer "):
        # No token provided - for protected routes, middleware should have blocked this
        # But for dev/testing, allow fallback
        return "tenant-dev"

    token = auth_header[7:]  # Remove "Bearer "

    if not JOSE_AVAILABLE:
        return "tenant-dev"

    try:
        payload = jwt.decode(
            token, SECRET_KEY, algorithms=["HS256"], options={"verify_aud": False}
        )
        return payload.get("tenant_id", "tenant-dev")
    except Exception:
        return "tenant-dev"


async def get_current_user(request: Request) -> Dict[str, Any]:
    """
    Dependency to get the current authenticated user from request.

    Uses data set by AuthMiddleware or parses JWT directly.
    """
    # Check if AuthMiddleware already processed the token
    if hasattr(request.state, "token_payload") and request.state.token_payload:
        payload = request.state.token_payload
        return {
            "sub": payload.sub,
            "user_id": payload.sub,
            "email": payload.email or f"{payload.sub}@agentic-trader.com",
            "tenant_id": payload.tenant_id,
            "roles": payload.roles,
        }

    # Fallback: Get tenant from header
    tenant_id = await get_current_tenant_id(request)

    # Check for user_id in request state
    user_id = getattr(request.state, "user_id", "user-dev")

    return {
        "sub": user_id,
        "user_id": user_id,
        "email": f"{user_id}@agentic-trader.com",
        "tenant_id": tenant_id,
        "roles": ["admin", "trader"],
    }


async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get a Database Session with RLS context set for the current Tenant.
    Extracts tenant_id from request to set RLS context.
    Uses SessionManager.tenant_session factory.
    """
    tenant_id = await get_current_tenant_id(request)

    async with SessionManager.tenant_session(tenant_id) as session:
        yield session


async def get_admin_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get a Database Session with System Admin privileges.
    Bypasses RLS. Use ONLY for Auth/Registration/Background tasks.
    """
    async with SessionManager.system_admin_session() as session:
        yield session
