"""
Integration Tests: OODA Coordinator + RBAC.

Test RBAC enforcement in OODACoordinator.set_trading_mode().
"""

from unittest.mock import MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from backend.core.database import Base
from backend.governance.permission_service import PermissionService
from backend.governance.trading_permissions import (
    PermissionDeniedError,
    TradingRole,
)
from backend.orchestration.ooda_coordinator import OODALoopCoordinator, TradingMode


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


@pytest.fixture
def mock_agents():
    """Mock agents voor OODACoordinator."""
    return {
        "data_scout": MagicMock(),
        "analyst": MagicMock(),
        "trader": MagicMock(),
        "risk_manager": MagicMock(),
        "cognitive_bridge": MagicMock(),
    }


@pytest.fixture
def coordinator(mock_agents):
    """OODACoordinator instance."""
    return OODALoopCoordinator(
        data_scout=mock_agents["data_scout"],
        analyst=mock_agents["analyst"],
        trader=mock_agents["trader"],
        risk_manager=mock_agents["risk_manager"],
        cognitive_bridge=mock_agents["cognitive_bridge"],
        trading_mode=TradingMode.NOTIFY_ONLY,
    )


class TestOODACoordinatorRBAC:
    """Integration tests voor RBAC in OODACoordinator."""

    @pytest.mark.asyncio
    async def test_get_trading_mode(self, coordinator):
        """get_trading_mode returns current mode."""
        mode = coordinator.get_trading_mode()

        assert mode == TradingMode.NOTIFY_ONLY

    @pytest.mark.asyncio
    async def test_set_mode_without_permission_service(self, coordinator):
        """set_trading_mode works zonder PermissionService (bypass)."""
        result = await coordinator.set_trading_mode(new_mode=TradingMode.AUTO, user_id="test_user")

        assert result is True
        assert coordinator.get_trading_mode() == TradingMode.AUTO

    @pytest.mark.asyncio
    async def test_set_mode_with_permission_admin(self, coordinator, db_session):
        """Admin kan AUTO mode zetten."""
        perm_service = PermissionService(db_session)

        result = await coordinator.set_trading_mode(
            new_mode=TradingMode.AUTO,
            user_id="admin",
            reason="Testing AUTO mode",
            permission_service=perm_service,
        )

        assert result is True
        assert coordinator.get_trading_mode() == TradingMode.AUTO

        # Check audit log
        changes = await perm_service.get_mode_changes()
        assert len(changes) == 1
        assert changes[0].user_id == "admin"
        assert changes[0].new_mode == "auto"
        assert changes[0].reason == "Testing AUTO mode"

    @pytest.mark.asyncio
    async def test_set_mode_denied_operator_to_auto(self, coordinator, db_session):
        """Operator CANNOT set AUTO mode."""
        perm_service = PermissionService(db_session)

        with pytest.raises(PermissionDeniedError) as exc_info:
            await coordinator.set_trading_mode(
                new_mode=TradingMode.AUTO,
                user_id="operator",
                permission_service=perm_service,
            )

        error = exc_info.value
        assert error.user_id == "operator"
        assert error.role == TradingRole.OPERATOR

        # Mode should NOT have changed
        assert coordinator.get_trading_mode() == TradingMode.NOTIFY_ONLY

    @pytest.mark.asyncio
    async def test_set_mode_operator_can_set_notify_only(self, coordinator, db_session):
        """Operator CAN set NOTIFY_ONLY mode."""
        # First set to AUTO (as admin)
        coordinator.trading_mode = TradingMode.AUTO

        perm_service = PermissionService(db_session)

        result = await coordinator.set_trading_mode(
            new_mode=TradingMode.NOTIFY_ONLY,
            user_id="operator",
            reason="Rolling back to safe mode",
            permission_service=perm_service,
        )

        assert result is True
        assert coordinator.get_trading_mode() == TradingMode.NOTIFY_ONLY

        # Check audit log
        changes = await perm_service.get_mode_changes()
        assert len(changes) == 1
        assert changes[0].user_id == "operator"
        assert changes[0].previous_mode == "auto"
        assert changes[0].new_mode == "notify_only"

    @pytest.mark.asyncio
    async def test_set_mode_viewer_cannot_set_any(self, coordinator, db_session):
        """Viewer CANNOT set any mode."""
        perm_service = PermissionService(db_session)

        with pytest.raises(PermissionDeniedError):
            await coordinator.set_trading_mode(
                new_mode=TradingMode.NOTIFY_ONLY,
                user_id="viewer",
                permission_service=perm_service,
            )

        # Mode unchanged
        assert coordinator.get_trading_mode() == TradingMode.NOTIFY_ONLY

    @pytest.mark.asyncio
    async def test_mode_change_audit_trail(self, coordinator, db_session):
        """Mode changes worden volledig gelogd."""
        perm_service = PermissionService(db_session)

        # Change 1: admin sets AUTO
        await coordinator.set_trading_mode(
            TradingMode.AUTO,
            "admin",
            "Enable automation",
            permission_service=perm_service,
        )

        # Change 2: operator rolls back
        await coordinator.set_trading_mode(
            TradingMode.NOTIFY_ONLY,
            "operator",
            "Safety rollback",
            permission_service=perm_service,
        )

        # Verify audit trail
        changes = await perm_service.get_mode_changes()
        assert len(changes) == 2

        # Most recent first
        assert changes[0].user_id == "operator"
        assert changes[0].previous_mode == "auto"
        assert changes[0].new_mode == "notify_only"

        assert changes[1].user_id == "admin"
        assert changes[1].previous_mode == "notify_only"
        assert changes[1].new_mode == "auto"

    @pytest.mark.asyncio
    async def test_set_mode_with_custom_role(self, coordinator, db_session):
        """Custom role assignment werkt."""
        perm_service = PermissionService(db_session)

        # Assign custom role
        perm_service.set_user_role("custom_user", TradingRole.ADMIN)

        # Should succeed
        result = await coordinator.set_trading_mode(
            TradingMode.AUTO, user_id="custom_user", permission_service=perm_service
        )

        assert result is True
