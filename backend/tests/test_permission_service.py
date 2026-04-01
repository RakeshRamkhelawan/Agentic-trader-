"""
Tests voor PermissionService.

Test RBAC enforcement en audit logging.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.core.database import Base
from backend.governance.permission_service import PermissionService
from backend.governance.trading_permissions import (
    PermissionDeniedError,
    TradingPermission,
    TradingRole,
)


@pytest.fixture
async def db_session():
    """In-memory test database session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    await engine.dispose()


class TestPermissionService:
    """Tests for PermissionService."""

    @pytest.mark.asyncio
    async def test_get_user_role_admin(self, db_session):
        """Get role voor admin user."""
        service = PermissionService(db_session)

        role = service.get_user_role("admin")

        assert role == TradingRole.ADMIN

    @pytest.mark.asyncio
    async def test_get_user_role_operator(self, db_session):
        """Get role voor operator user."""
        service = PermissionService(db_session)

        role = service.get_user_role("operator")

        assert role == TradingRole.OPERATOR

    @pytest.mark.asyncio
    async def test_get_user_role_unknown_defaults_viewer(self, db_session):
        """Unknown user defaults to VIEWER."""
        service = PermissionService(db_session)

        role = service.get_user_role("unknown_user")

        assert role == TradingRole.VIEWER

    @pytest.mark.asyncio
    async def test_check_permission_returns_true(self, db_session):
        """check_permission returns True voor valid permission."""
        service = PermissionService(db_session)

        has_perm = service.check_permission("admin", TradingPermission.SET_AUTO)

        assert has_perm is True

    @pytest.mark.asyncio
    async def test_check_permission_returns_false(self, db_session):
        """check_permission returns False voor invalid permission."""
        service = PermissionService(db_session)

        has_perm = service.check_permission("operator", TradingPermission.SET_AUTO)

        assert has_perm is False

    @pytest.mark.asyncio
    async def test_require_permission_success(self, db_session):
        """require_permission succeeds voor valid permission."""
        service = PermissionService(db_session)

        # Should not raise
        service.require_permission("admin", TradingPermission.SET_AUTO)

    @pytest.mark.asyncio
    async def test_require_permission_raises(self, db_session):
        """require_permission raises voor invalid permission."""
        service = PermissionService(db_session)

        with pytest.raises(PermissionDeniedError) as exc_info:
            service.require_permission("operator", TradingPermission.SET_AUTO)

        error = exc_info.value
        assert error.user_id == "operator"
        assert error.permission == TradingPermission.SET_AUTO
        assert error.role == TradingRole.OPERATOR

    @pytest.mark.asyncio
    async def test_log_mode_change_persists(self, db_session):
        """Mode change wordt gelogd in database."""
        service = PermissionService(db_session)

        change = await service.log_mode_change(
            user_id="admin",
            previous_mode="notify_only",
            new_mode="auto",
            reason="Testing AUTO mode",
        )

        assert change.id is not None
        assert change.user_id == "admin"
        assert change.user_role == "admin"
        assert change.previous_mode == "notify_only"
        assert change.new_mode == "auto"
        assert change.reason == "Testing AUTO mode"
        assert change.timestamp is not None

    @pytest.mark.asyncio
    async def test_get_mode_changes(self, db_session):
        """Get recent mode changes."""
        service = PermissionService(db_session)

        # Log 3 changes
        await service.log_mode_change("admin", "auto", "notify_only", "Test 1")
        await service.log_mode_change(
            "operator", "notify_only", "notify_only", "Test 2"
        )
        await service.log_mode_change("admin", "notify_only", "auto", "Test 3")

        # Get all
        changes = await service.get_mode_changes()

        assert len(changes) == 3
        # Most recent first
        assert changes[0].reason == "Test 3"

    @pytest.mark.asyncio
    async def test_get_mode_changes_filtered_by_user(self, db_session):
        """Filter mode changes by user."""
        service = PermissionService(db_session)

        # Log for different users
        await service.log_mode_change("admin", "auto", "notify_only")
        await service.log_mode_change("operator", "notify_only", "notify_only")

        # Filter admin only
        admin_changes = await service.get_mode_changes(user_id="admin")

        assert len(admin_changes) == 1
        assert admin_changes[0].user_id == "admin"

    @pytest.mark.asyncio
    async def test_set_user_role(self, db_session):
        """set_user_role wijzigt role mapping."""
        service = PermissionService(db_session)

        # Set new role
        service.set_user_role("newuser", TradingRole.OPERATOR)

        # Verify
        role = service.get_user_role("newuser")
        assert role == TradingRole.OPERATOR
