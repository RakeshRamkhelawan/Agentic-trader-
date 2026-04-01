"""
Tests voor Trading Permissions (RBAC).

Test role-based access control voor TRADING_MODE switching.
"""

import pytest

from backend.governance.trading_permissions import (
    ROLE_PERMISSIONS,
    PermissionDeniedError,
    TradingPermission,
    TradingRole,
    get_required_permission_for_mode,
    has_permission,
)


class TestTradingPermissions:
    """Tests for permission model."""

    def test_viewer_permissions(self):
        """Viewer heeft alleen VIEW_MODE."""
        role = TradingRole.VIEWER

        assert has_permission(role, TradingPermission.VIEW_MODE)
        assert not has_permission(role, TradingPermission.SET_NOTIFY_ONLY)
        assert not has_permission(role, TradingPermission.SET_AUTO)
        assert not has_permission(role, TradingPermission.EMERGENCY_SHUTDOWN)

    def test_operator_permissions(self):
        """Operator kan VIEW en SET_NOTIFY_ONLY."""
        role = TradingRole.OPERATOR

        assert has_permission(role, TradingPermission.VIEW_MODE)
        assert has_permission(role, TradingPermission.SET_NOTIFY_ONLY)
        assert not has_permission(role, TradingPermission.SET_AUTO)
        assert not has_permission(role, TradingPermission.EMERGENCY_SHUTDOWN)

    def test_admin_permissions(self):
        """Admin heeft alle permissions."""
        role = TradingRole.ADMIN

        assert has_permission(role, TradingPermission.VIEW_MODE)
        assert has_permission(role, TradingPermission.SET_NOTIFY_ONLY)
        assert has_permission(role, TradingPermission.SET_AUTO)
        assert has_permission(role, TradingPermission.EMERGENCY_SHUTDOWN)

    def test_get_required_permission_notify_only(self):
        """NOTIFY_ONLY mode vereist SET_NOTIFY_ONLY permission."""
        perm = get_required_permission_for_mode("notify_only")
        assert perm == TradingPermission.SET_NOTIFY_ONLY

    def test_get_required_permission_auto(self):
        """AUTO mode vereist SET_AUTO permission."""
        perm = get_required_permission_for_mode("auto")
        assert perm == TradingPermission.SET_AUTO

    def test_get_required_permission_invalid_mode(self):
        """Unknown mode raises ValueError."""
        with pytest.raises(ValueError, match="Unknown trading mode"):
            get_required_permission_for_mode("invalid_mode")

    def test_permission_denied_error_message(self):
        """PermissionDeniedError bevat context."""
        error = PermissionDeniedError(
            user_id="user123",
            permission=TradingPermission.SET_AUTO,
            role=TradingRole.OPERATOR,
        )

        assert error.user_id == "user123"
        assert error.permission == TradingPermission.SET_AUTO
        assert error.role == TradingRole.OPERATOR
        assert "user123" in str(error)
        assert "OPERATOR" in str(error)  # Enum string representation

    def test_role_permissions_mapping_complete(self):
        """Alle roles hebben permission set."""
        assert TradingRole.VIEWER in ROLE_PERMISSIONS
        assert TradingRole.OPERATOR in ROLE_PERMISSIONS
        assert TradingRole.ADMIN in ROLE_PERMISSIONS
