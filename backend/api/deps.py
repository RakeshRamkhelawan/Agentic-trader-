"""
API Dependencies.
Shares common logic like Tenant ID extraction and Database Session setup with RLS context.

Security: Authentication is enforced by default. Dev-mode fallbacks are ONLY
available when AUTH_DISABLED=True AND ENV != 'production'.
"""

import logging
import os
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config.settings import settings

# Import SessionManager from database.py
from backend.core.database import SessionManager

logger = logging.getLogger(__name__)

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


def _is_dev_fallback_allowed() -> bool:
    """Check if development fallback authentication is permitted.

    Dev fallback is ONLY allowed when:
    - AUTH_DISABLED is explicitly set to True, AND
    - ENV is NOT 'production'

    This prevents accidental authentication bypass in production.
    """
    return settings.AUTH_DISABLED is True and settings.ENV != "production"


async def get_current_tenant_id(request: Request) -> str:
    """
    Extract tenant_id from JWT token in Authorization header.

    Flow:
    1. Check if AuthMiddleware already set tenant_id in request.state
    2. If not, try to parse JWT directly from header
    3. If no valid token: 401 Unauthorized (or dev fallback if explicitly allowed)
    """
    # Check if AuthMiddleware already processed the token
    if hasattr(request.state, "tenant_id") and request.state.tenant_id:
        return request.state.tenant_id

    # Try to extract from Authorization header directly
    auth_header = request.headers.get("Authorization", "")

    if not auth_header or not auth_header.startswith("Bearer "):
        if _is_dev_fallback_allowed():
            logger.debug(
                "Dev fallback: using tenant-dev (AUTH_DISABLED=True, ENV=%s)", settings.ENV
            )
            return "tenant-dev"
        raise HTTPException(
            status_code=401,
            detail="Authorization header required. Provide a valid Bearer token.",
        )

    token = auth_header[7:]  # Remove "Bearer "

    if not JOSE_AVAILABLE:
        logger.error("python-jose library not available. Cannot verify JWT tokens.")
        raise HTTPException(
            status_code=500,
            detail="Authentication service unavailable.",
        )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"], options={"verify_aud": False})
        tenant_id = payload.get("tenant_id")
        if not tenant_id:
            raise HTTPException(
                status_code=401,
                detail="Token missing required 'tenant_id' claim.",
            )
        return tenant_id
    except JWTError as e:
        logger.warning("JWT verification failed: %s", e)
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token.",
        )
    except Exception as e:
        logger.error("Unexpected error during token verification: %s", e)
        raise HTTPException(
            status_code=401,
            detail="Token verification failed.",
        )


async def get_current_user(request: Request) -> dict[str, Any]:
    """
    Dependency to get the current authenticated user from request.

    Uses data set by AuthMiddleware or parses JWT directly.
    Returns 401 if no valid authentication is present (unless dev fallback is allowed).
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

    # Try to get tenant from header (this will raise 401 if not authenticated)
    tenant_id = await get_current_tenant_id(request)

    # If we reach here with tenant-dev, it means dev fallback is allowed
    if tenant_id == "tenant-dev" and _is_dev_fallback_allowed():
        user_id = getattr(request.state, "user_id", "user-dev")
        logger.debug("Dev fallback: using dev user with limited roles (AUTH_DISABLED=True)")
        return {
            "sub": user_id,
            "user_id": user_id,
            "email": f"{user_id}@agentic-trader.com",
            "tenant_id": tenant_id,
            "roles": ["viewer"],  # Dev users get minimal roles, NOT admin
        }

    # For authenticated requests: extract user_id from request state
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="User identity could not be determined from token.",
        )

    return {
        "sub": user_id,
        "user_id": user_id,
        "email": f"{user_id}@agentic-trader.com",
        "tenant_id": tenant_id,
        "roles": getattr(request.state, "roles", ["viewer"]),
    }


async def get_db(request: Request) -> AsyncGenerator[AsyncSession]:
    """
    Dependency to get a Database Session with RLS context set for the current Tenant.
    Extracts tenant_id from request to set RLS context.
    Uses SessionManager.tenant_session factory.
    """
    tenant_id = await get_current_tenant_id(request)

    async with SessionManager.tenant_session(tenant_id) as session:
        yield session


async def get_admin_db() -> AsyncGenerator[AsyncSession]:
    """
    Dependency to get a Database Session with System Admin privileges.
    Bypasses RLS. Use ONLY for Auth/Registration/Background tasks.
    """
    async with SessionManager.system_admin_session() as session:
        yield session
