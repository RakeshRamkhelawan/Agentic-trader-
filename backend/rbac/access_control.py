"""Access control enforcement."""

from collections.abc import Callable
from functools import wraps

from fastapi import HTTPException

from .roles import Permission, role_manager


class AccessControl:
    """
    Access control enforcement for API endpoints.

    Provides decorators and utilities for permission checking.
    """

    @staticmethod
    def check(
        tenant_id: str,
        user_id: str,
        permission: Permission,
    ) -> bool:
        """Check if user has permission."""
        return role_manager.check_permission(tenant_id, user_id, permission)

    @staticmethod
    def require(permission: Permission):
        """
        Decorator to require permission for endpoint.

        Usage:
            @app.get("/tournaments")
            @AccessControl.require(Permission.TOURNAMENT_READ)
            async def list_tournaments(request: Request):
                ...
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Extract request
                request = kwargs.get("request")
                if not request and args:
                    request = args[0]

                if not request:
                    raise HTTPException(status_code=500, detail="Request not found")

                # Get tenant and user from request
                tenant_id = getattr(request.state, "tenant_id", None)
                user_id = request.headers.get("X-User-ID")

                if not tenant_id or not user_id:
                    raise HTTPException(status_code=401, detail="Authentication required")

                # Check permission
                if not AccessControl.check(tenant_id, user_id, permission):
                    raise HTTPException(
                        status_code=403,
                        detail=f"Permission denied: {permission.value}",
                    )

                return await func(*args, **kwargs)
            return wrapper
        return decorator

    @staticmethod
    def require_any(*permissions: Permission):
        """Require any of the specified permissions."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                request = kwargs.get("request")
                if not request and args:
                    request = args[0]

                if not request:
                    raise HTTPException(status_code=500, detail="Request not found")

                tenant_id = getattr(request.state, "tenant_id", None)
                user_id = request.headers.get("X-User-ID")

                if not tenant_id or not user_id:
                    raise HTTPException(status_code=401, detail="Authentication required")

                # Check any permission
                user_permissions = role_manager.get_user_permissions(tenant_id, user_id)
                if not any(p in user_permissions for p in permissions):
                    raise HTTPException(
                        status_code=403,
                        detail="Permission denied",
                    )

                return await func(*args, **kwargs)
            return wrapper
        return decorator

    @staticmethod
    def require_all(*permissions: Permission):
        """Require all specified permissions."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                request = kwargs.get("request")
                if not request and args:
                    request = args[0]

                if not request:
                    raise HTTPException(status_code=500, detail="Request not found")

                tenant_id = getattr(request.state, "tenant_id", None)
                user_id = request.headers.get("X-User-ID")

                if not tenant_id or not user_id:
                    raise HTTPException(status_code=401, detail="Authentication required")

                # Check all permissions
                user_permissions = role_manager.get_user_permissions(tenant_id, user_id)
                if not all(p in user_permissions for p in permissions):
                    missing = [p.value for p in permissions if p not in user_permissions]
                    raise HTTPException(
                        status_code=403,
                        detail=f"Missing permissions: {', '.join(missing)}",
                    )

                return await func(*args, **kwargs)
            return wrapper
        return decorator


def require_permission(permission: Permission):
    """Convenience decorator for requiring a single permission."""
    return AccessControl.require(permission)


class TenantResourceAccess:
    """
    Resource-level access control within tenants.

    Controls access to specific resources (tournaments, strategies, etc.)
    based on ownership and permissions.
    """

    @staticmethod
    def can_view_tournament(
        tenant_id: str,
        user_id: str,
        tournament_id: str,
        tournament_owner_id: str,
    ) -> bool:
        """Check if user can view tournament."""
        # Public tournaments
        if role_manager.check_permission(tenant_id, user_id, Permission.TOURNAMENT_READ):
            return True

        # Own tournament
        if user_id == tournament_owner_id:
            return True

        return False

    @staticmethod
    def can_edit_tournament(
        tenant_id: str,
        user_id: str,
        tournament_id: str,
        tournament_owner_id: str,
    ) -> bool:
        """Check if user can edit tournament."""
        # Admin or manager
        if role_manager.check_permission(tenant_id, user_id, Permission.TOURNAMENT_UPDATE):
            return True

        # Own tournament
        if user_id == tournament_owner_id:
            return True

        return False

    @staticmethod
    def can_view_strategy(
        tenant_id: str,
        user_id: str,
        strategy_owner_id: str,
        is_public: bool,
    ) -> bool:
        """Check if user can view strategy."""
        # Public strategy
        if is_public:
            return role_manager.check_permission(tenant_id, user_id, Permission.STRATEGY_READ)

        # Own strategy
        if user_id == strategy_owner_id:
            return True

        # Admin
        if role_manager.check_permission(tenant_id, user_id, Permission.ADMIN_USERS):
            return True

        return False

    @staticmethod
    def can_trade(
        tenant_id: str,
        user_id: str,
        competitor_id: str,
    ) -> bool:
        """Check if user can execute trades."""
        # Must have trade permission
        if not role_manager.check_permission(tenant_id, user_id, Permission.TRADE_EXECUTE):
            return False

        # Must be trading for themselves or have manage permission
        if user_id == competitor_id:
            return True

        if role_manager.check_permission(tenant_id, user_id, Permission.TRADE_MANAGE):
            return True

        return False
