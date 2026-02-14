"""
RBAC - Role-Based Access Control decorators.

Provides FastAPI dependency-style decorators for role enforcement.
"""

import logging
from functools import wraps
from typing import Any, Callable, List, Union

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.core.auth.models import TokenPayload

logger = logging.getLogger(__name__)

# Security scheme for OpenAPI docs
security = HTTPBearer()


class ForbiddenError(HTTPException):
    """Raised when user lacks required permissions."""

    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(status_code=403, detail=detail)


def require_role(role: str):
    """
    FastAPI dependency to require a specific role.

    Usage:
        @router.get("/admin", dependencies=[Depends(require_role("admin"))])
        async def admin_endpoint():
            ...
    """

    async def role_checker(request: Request):
        roles = getattr(request.state, "roles", [])
        if role not in roles:
            logger.warning(f"Access denied: required role '{role}', user has {roles}")
            raise ForbiddenError(f"Role '{role}' required")
        return True

    return role_checker


def require_any_role(roles: List[str]):
    """
    FastAPI dependency to require any of the specified roles.

    Usage:
        @router.get("/manage", dependencies=[Depends(require_any_role(["admin", "trader"]))])
        async def manage_endpoint():
            ...
    """

    async def role_checker(request: Request):
        user_roles = getattr(request.state, "roles", [])
        if not set(user_roles) & set(roles):
            logger.warning(
                f"Access denied: required any of {roles}, user has {user_roles}"
            )
            raise ForbiddenError(f"One of roles {roles} required")
        return True

    return role_checker


def require_admin():
    """Shortcut for requiring admin role."""
    return require_role("admin")


def require_trader():
    """Shortcut for requiring trader role."""
    return require_any_role(["admin", "trader"])


def require_viewer():
    """Shortcut for requiring any authenticated user."""
    return require_any_role(["admin", "trader", "viewer"])


# ---- Utility functions ----


def get_current_user_from_request(request: Request) -> TokenPayload:
    """
    Get current user's token payload from request.

    Usage in endpoint:
        @router.get("/profile")
        async def profile(request: Request):
            user = get_current_user_from_request(request)
            return {"user_id": user.sub}
    """
    payload = getattr(request.state, "token_payload", None)
    if not payload:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return payload


async def get_current_tenant_from_request(request: Request) -> str:
    """Get current tenant ID from request state."""
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="No tenant context")
    return tenant_id
