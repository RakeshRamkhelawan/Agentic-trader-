"""
Trading Permissions - RBAC voor TRADING_MODE.

Role-Based Access Control voor veilige switching tussen trading modes.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Optional


class TradingPermission(str, Enum):
    """Trading permissions."""

    VIEW_MODE = "trading:view_mode"
    SET_NOTIFY_ONLY = "trading:set_notify_only"
    SET_AUTO = "trading:set_auto"
    EMERGENCY_SHUTDOWN = "trading:emergency_shutdown"


class TradingRole(str, Enum):
    """Trading user roles."""

    VIEWER = "viewer"  # Read-only access
    OPERATOR = "operator"  # Can set NOTIFY_ONLY mode
    ADMIN = "admin"  # Full access including AUTO mode


# Role → Permissions mapping
ROLE_PERMISSIONS = {
    TradingRole.VIEWER: {TradingPermission.VIEW_MODE},
    TradingRole.OPERATOR: {
        TradingPermission.VIEW_MODE,
        TradingPermission.SET_NOTIFY_ONLY,
    },
    TradingRole.ADMIN: {
        TradingPermission.VIEW_MODE,
        TradingPermission.SET_NOTIFY_ONLY,
        TradingPermission.SET_AUTO,
        TradingPermission.EMERGENCY_SHUTDOWN,
    },
}


class PermissionDeniedError(Exception):
    """Exception raised when user lacks required permission."""

    def __init__(
        self,
        user_id: str,
        permission: TradingPermission,
        role: Optional[TradingRole] = None,
    ):
        self.user_id = user_id
        self.permission = permission
        self.role = role
        super().__init__(
            f"User '{user_id}' (role={role}) lacks permission: {permission}"
        )


def has_permission(role: TradingRole, permission: TradingPermission) -> bool:
    """
    Check of role een specifieke permission heeft.

    Args:
        role: User role
        permission: Required permission

    Returns:
        True if role has permission
    """
    return permission in ROLE_PERMISSIONS.get(role, set())


def get_required_permission_for_mode(mode: str) -> TradingPermission:
    """
    Get required permission voor trading mode.

    Args:
        mode: Trading mode ('notify_only' or 'auto')

    Returns:
        Required permission
    """
    if mode == "auto":
        return TradingPermission.SET_AUTO
    elif mode == "notify_only":
        return TradingPermission.SET_NOTIFY_ONLY
    else:
        raise ValueError(f"Unknown trading mode: {mode}")
