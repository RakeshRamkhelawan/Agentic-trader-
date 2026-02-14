"""
Tenant Context Management - Thread-safe context variables for multi-tenancy.

Uses Python's contextvars for async-safe tenant isolation.
"""

from contextvars import ContextVar
from typing import Optional
from contextlib import contextmanager

# Thread-safe, async-safe context variable for tenant_id
_tenant_context: ContextVar[Optional[str]] = ContextVar("tenant_id", default=None)
_user_context: ContextVar[Optional[str]] = ContextVar("user_id", default=None)


class UnauthorizedError(Exception):
    """Raised when no tenant/user context is available."""

    pass


def set_current_tenant(tenant_id: str) -> None:
    """
    Set the current tenant for this request context.

    Args:
        tenant_id: Tenant identifier
    """
    _tenant_context.set(tenant_id)


def get_current_tenant() -> str:
    """
    Get the current tenant from request context.

    Returns:
        Current tenant_id

    Raises:
        UnauthorizedError: If no tenant context is set
    """
    tenant_id = _tenant_context.get()
    if not tenant_id:
        raise UnauthorizedError("No tenant context available")
    return tenant_id


def get_current_tenant_optional() -> Optional[str]:
    """
    Get the current tenant, returning None if not set.

    Returns:
        Current tenant_id or None
    """
    return _tenant_context.get()


def set_current_user(user_id: str) -> None:
    """
    Set the current user for this request context.

    Args:
        user_id: User identifier
    """
    _user_context.set(user_id)


def get_current_user() -> str:
    """
    Get the current user from request context.

    Returns:
        Current user_id

    Raises:
        UnauthorizedError: If no user context is set
    """
    user_id = _user_context.get()
    if not user_id:
        raise UnauthorizedError("No user context available")
    return user_id


def get_current_user_optional() -> Optional[str]:
    """
    Get the current user, returning None if not set.

    Returns:
        Current user_id or None
    """
    return _user_context.get()


def clear_context() -> None:
    """Clear all context variables (useful for testing)."""
    _tenant_context.set(None)
    _user_context.set(None)


@contextmanager
def tenant_context(tenant_id: str):
    """
    Context manager to set tenant context temporarily.
    Restores previous context on exit.
    """
    token = _tenant_context.set(tenant_id)
    try:
        yield
    finally:
        _tenant_context.reset(token)
