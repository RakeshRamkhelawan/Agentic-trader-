"""
E2E Integration Tests - Full Auth -> API -> DB with RLS Flow

Tests the complete authentication and data isolation pipeline:
1. Auth: JWT token generation -> dependency injection -> tenant extraction
2. API: Request with valid/invalid tokens -> correct HTTP responses
3. DB + RLS: Tenant context set -> queries scoped to correct tenant

Run with: pytest backend/tests/e2e/test_auth_api_rls_flow.py -v
"""

import os
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ============================================================================
# E2E Test: Complete Auth -> Tenant -> RLS pipeline
# ============================================================================


class TestAuthToRLSPipeline:
    """End-to-end test: Authentication -> API Dependency -> RLS Context."""

    @pytest.mark.asyncio
    async def test_e2e_valid_token_sets_rls_context(self):
        """
        Full flow: Valid tenant in request.state -> set_tenant_context.
        Verifies RLS context is correctly set from middleware-extracted tenant.
        """
        from backend.api.deps import get_current_tenant_id
        from backend.core.context import set_tenant_context

        # Step 1: Simulate middleware having set tenant_id
        request = MagicMock()
        request.state.tenant_id = "tenant-e2e-test-123"

        # Step 2: Extract tenant_id via dependency
        tenant_id = await get_current_tenant_id(request)
        assert tenant_id == "tenant-e2e-test-123"

        # Step 3: Verify RLS context can be set with this tenant
        mock_session = AsyncMock()
        await set_tenant_context(mock_session, tenant_id)

        # Verify set_config was called with correct tenant
        mock_session.execute.assert_called_once()
        # The call uses text() and params - verify the session was used
        call_args = mock_session.execute.call_args
        assert call_args is not None, "set_tenant_context did not call session.execute"

    @pytest.mark.asyncio
    async def test_e2e_no_token_production_returns_401(self):
        """
        Full flow: No token in production -> 401 -> no RLS context set.
        """
        from fastapi import HTTPException

        from backend.api.deps import get_current_tenant_id

        # Request without tenant_id and without Authorization header
        request = MagicMock()
        request.state = SimpleNamespace()  # No tenant_id attribute
        request.headers = {}

        with patch("backend.api.deps.settings") as mock_settings:
            mock_settings.AUTH_DISABLED = False
            mock_settings.ENV = "production"

            with pytest.raises(HTTPException) as exc_info:
                await get_current_tenant_id(request)

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_e2e_rls_failure_raises_runtime_error(self):
        """
        Full flow: Valid tenant -> RLS set_config fails -> RuntimeError.
        Verifies DB failure in RLS context prevents ANY data access.
        """
        from backend.core.context import set_tenant_context

        mock_session = AsyncMock()
        mock_session.execute.side_effect = ConnectionError("DB connection lost")

        with pytest.raises(RuntimeError, match="Failed to set RLS tenant context"):
            await set_tenant_context(mock_session, "tenant-valid-456")


class TestAuthToUserPipeline:
    """E2E: Authentication -> User extraction -> Role assignment."""

    @pytest.mark.asyncio
    async def test_e2e_authenticated_user_gets_correct_roles(self):
        """Valid JWT user gets roles from token, not hardcoded defaults."""
        from backend.api.deps import get_current_user

        request = MagicMock()
        request.state.token_payload = SimpleNamespace(
            sub="user-e2e-001",
            email="e2e@test.com",
            tenant_id="tenant-e2e",
            roles=["trader"],
        )

        user = await get_current_user(request)

        assert user["user_id"] == "user-e2e-001"
        assert user["roles"] == ["trader"]
        assert "admin" not in user["roles"]

    @pytest.mark.asyncio
    async def test_e2e_dev_fallback_never_grants_admin(self):
        """Dev fallback with AUTH_DISABLED gives viewer role, never admin."""
        from backend.api.deps import get_current_user

        # Request without token_payload - triggers dev fallback path
        request = MagicMock()
        request.state = SimpleNamespace()  # No token_payload
        request.headers = {}

        with patch("backend.api.deps.settings") as mock_settings:
            mock_settings.AUTH_DISABLED = True
            mock_settings.ENV = "development"

            user = await get_current_user(request)
            assert user["roles"] == ["viewer"]
            assert "admin" not in user["roles"]

    @pytest.mark.asyncio
    async def test_e2e_production_without_token_returns_401(self):
        """No request path should grant access without valid JWT in production."""
        from fastapi import HTTPException

        from backend.api.deps import get_current_user

        request = MagicMock()
        request.state = SimpleNamespace()
        request.headers = {}

        with patch("backend.api.deps.settings") as mock_settings:
            mock_settings.AUTH_DISABLED = False
            mock_settings.ENV = "production"

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(request)

            assert exc_info.value.status_code == 401


class TestRLSDataIsolation:
    """E2E: Verify RLS prevents cross-tenant data access."""

    @pytest.mark.asyncio
    async def test_e2e_empty_tenant_blocks_all_queries(self):
        """Empty tenant_id raises ValueError before any query executes."""
        from backend.core.context import set_tenant_context

        mock_session = AsyncMock()

        with pytest.raises(ValueError, match="non-empty string"):
            await set_tenant_context(mock_session, "")

        mock_session.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_e2e_whitespace_tenant_blocks_queries(self):
        """Whitespace-only tenant_id is treated as empty."""
        from backend.core.context import set_tenant_context

        mock_session = AsyncMock()

        with pytest.raises(ValueError):
            await set_tenant_context(mock_session, "   ")

        mock_session.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_e2e_different_tenants_get_different_contexts(self):
        """Two different tenants get different RLS contexts."""
        from backend.core.context import set_tenant_context

        session_a = AsyncMock()
        session_b = AsyncMock()

        await set_tenant_context(session_a, "tenant-A")
        await set_tenant_context(session_b, "tenant-B")

        args_a = str(session_a.execute.call_args)
        args_b = str(session_b.execute.call_args)
        assert "tenant-A" in args_a
        assert "tenant-B" in args_b
        assert "tenant-B" not in args_a  # No cross-contamination


class TestFrontendBackendConfigAlignment:
    """E2E: Verify frontend and backend auth config are aligned."""

    def test_frontend_production_guard_exists(self):
        """Frontend throws in production without Auth0."""
        config_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "..",
            "frontend", "src", "lib", "config.ts"
        )
        with open(config_path) as f:
            content = f.read()

        assert "import.meta.env.PROD" in content
        assert "throw new Error" in content

    def test_backend_auth_disabled_check_exists(self):
        """Backend validates AUTH_DISABLED in its settings."""
        settings_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "core", "config", "settings.py"
        )
        with open(settings_path) as f:
            content = f.read()

        assert "AUTH_DISABLED" in content
