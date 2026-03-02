"""
Fase 1 Integration Tests - Critical Security Fixes

Tests for:
- Taak 1.1: Auth dependency no longer falls open (deps.py)
- Taak 1.2: RLS context is fail-closed (context.py)
- Taak 1.3: Settings JWT_SECRET_KEY property/field works correctly (settings.py)

Run with: pytest backend/tests/security/test_fase1_integration.py -v
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ============================================================================
# Taak 1.1: Auth Dependency Tests (deps.py)
# ============================================================================


class TestGetCurrentTenantId:
    """Tests for get_current_tenant_id - fail-closed auth."""

    @pytest.mark.asyncio
    async def test_happy_path_valid_token_returns_tenant_id(self):
        """Request with valid JWT returns correct tenant_id."""
        from backend.api.deps import get_current_tenant_id

        request = MagicMock()
        request.state = MagicMock()
        request.state.tenant_id = "tenant-abc-123"

        result = await get_current_tenant_id(request)
        assert result == "tenant-abc-123"

    @pytest.mark.asyncio
    async def test_unhappy_no_header_production_returns_401(self):
        """Request without Authorization header in production raises 401."""
        from fastapi import HTTPException

        from backend.api.deps import get_current_tenant_id

        request = MagicMock()
        request.state = MagicMock(spec=[])  # no tenant_id attribute
        request.headers = {}

        with patch("backend.api.deps.settings") as mock_settings:
            mock_settings.AUTH_DISABLED = False
            mock_settings.ENV = "production"

            with pytest.raises(HTTPException) as exc_info:
                await get_current_tenant_id(request)
            assert exc_info.value.status_code == 401
            assert "Authorization" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_unhappy_invalid_token_returns_401(self):
        """Request with invalid/malformed JWT raises 401."""
        from fastapi import HTTPException

        from backend.api.deps import get_current_tenant_id

        request = MagicMock()
        request.state = MagicMock(spec=[])  # no tenant_id attribute
        request.headers = {"Authorization": "Bearer invalid.token.here"}

        with patch("backend.api.deps.settings") as mock_settings:
            mock_settings.AUTH_DISABLED = False
            mock_settings.ENV = "production"

            with pytest.raises(HTTPException) as exc_info:
                await get_current_tenant_id(request)
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_dev_fallback_allowed_when_auth_disabled_non_production(self):
        """Dev fallback works when AUTH_DISABLED=True and ENV=development."""
        from backend.api.deps import get_current_tenant_id

        request = MagicMock()
        request.state = MagicMock(spec=[])  # no tenant_id attribute
        request.headers = {}

        with patch("backend.api.deps.settings") as mock_settings:
            mock_settings.AUTH_DISABLED = True
            mock_settings.ENV = "development"

            result = await get_current_tenant_id(request)
            assert result == "tenant-dev"

    @pytest.mark.asyncio
    async def test_dev_fallback_blocked_in_production_even_with_auth_disabled(self):
        """AUTH_DISABLED=True is ignored when ENV=production."""
        from fastapi import HTTPException

        from backend.api.deps import get_current_tenant_id

        request = MagicMock()
        request.state = MagicMock(spec=[])  # no tenant_id attribute
        request.headers = {}

        with patch("backend.api.deps.settings") as mock_settings:
            mock_settings.AUTH_DISABLED = True
            mock_settings.ENV = "production"

            with pytest.raises(HTTPException) as exc_info:
                await get_current_tenant_id(request)
            assert exc_info.value.status_code == 401


class TestGetCurrentUser:
    """Tests for get_current_user - no admin fallback."""

    @pytest.mark.asyncio
    async def test_happy_path_authenticated_user_from_middleware(self):
        """User data from AuthMiddleware is returned correctly."""
        from backend.api.deps import get_current_user

        request = MagicMock()
        payload = MagicMock()
        payload.sub = "user-123"
        payload.email = "test@example.com"
        payload.tenant_id = "tenant-456"
        payload.roles = ["trader"]
        request.state.token_payload = payload

        result = await get_current_user(request)
        assert result["user_id"] == "user-123"
        assert result["tenant_id"] == "tenant-456"
        assert result["roles"] == ["trader"]
        # Verify NO admin role is given
        assert "admin" not in result["roles"]

    @pytest.mark.asyncio
    async def test_unhappy_no_auth_in_production_returns_401(self):
        """Unauthenticated request in production raises 401, not admin fallback."""
        from fastapi import HTTPException

        from backend.api.deps import get_current_user

        request = MagicMock()
        request.state = MagicMock(spec=[])  # no token_payload
        request.headers = {}

        with patch("backend.api.deps.settings") as mock_settings:
            mock_settings.AUTH_DISABLED = False
            mock_settings.ENV = "production"

            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(request)
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_dev_user_gets_viewer_role_not_admin(self):
        """Dev fallback user gets 'viewer' role, never 'admin' or 'trader'."""
        from backend.api.deps import get_current_user

        request = MagicMock()
        request.state = MagicMock(spec=[])  # no token_payload
        request.state.user_id = "user-dev"
        request.headers = {}

        with patch("backend.api.deps.settings") as mock_settings:
            mock_settings.AUTH_DISABLED = True
            mock_settings.ENV = "development"

            result = await get_current_user(request)
            assert result["roles"] == ["viewer"]
            assert "admin" not in result["roles"]
            assert "trader" not in result["roles"]


# ============================================================================
# Taak 1.2: RLS Context Tests (context.py)
# ============================================================================


class TestSetTenantContext:
    """Tests for set_tenant_context - fail-closed."""

    @pytest.mark.asyncio
    async def test_happy_path_sets_tenant_context(self):
        """Valid tenant_id is set via set_config."""
        from backend.core.context import set_tenant_context

        mock_session = AsyncMock()
        await set_tenant_context(mock_session, "tenant-123")
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_unhappy_empty_tenant_id_raises_value_error(self):
        """Empty tenant_id raises ValueError."""
        from backend.core.context import set_tenant_context

        mock_session = AsyncMock()

        with pytest.raises(ValueError, match="non-empty string"):
            await set_tenant_context(mock_session, "")

    @pytest.mark.asyncio
    async def test_unhappy_none_tenant_id_raises_value_error(self):
        """None tenant_id raises ValueError."""
        from backend.core.context import set_tenant_context

        mock_session = AsyncMock()

        with pytest.raises(ValueError, match="non-empty string"):
            await set_tenant_context(mock_session, None)

    @pytest.mark.asyncio
    async def test_unhappy_whitespace_tenant_id_raises_value_error(self):
        """Whitespace-only tenant_id raises ValueError."""
        from backend.core.context import set_tenant_context

        mock_session = AsyncMock()

        with pytest.raises(ValueError, match="non-empty string"):
            await set_tenant_context(mock_session, "   ")

    @pytest.mark.asyncio
    async def test_unhappy_db_failure_raises_runtime_error(self):
        """Database failure raises RuntimeError (fail-closed)."""
        from backend.core.context import set_tenant_context

        mock_session = AsyncMock()
        mock_session.execute.side_effect = Exception("Connection refused")

        with pytest.raises(RuntimeError, match="Failed to set RLS tenant context"):
            await set_tenant_context(mock_session, "tenant-123")

    @pytest.mark.asyncio
    async def test_unhappy_db_failure_does_not_swallow_exception(self):
        """Database failure exception is NOT silently ignored."""
        from backend.core.context import set_tenant_context

        mock_session = AsyncMock()
        mock_session.execute.side_effect = ConnectionError("DB down")

        # Must raise, not silently continue
        with pytest.raises(RuntimeError):
            await set_tenant_context(mock_session, "tenant-456")


# ============================================================================
# Taak 1.3: Settings Property/Field Tests (settings.py)
# ============================================================================


class TestSettingsJWTSecretKey:
    """Tests for Settings.JWT_SECRET_KEY property."""

    def test_happy_path_jwt_secret_key_loaded(self):
        """JWT_SECRET_KEY is loaded correctly from environment."""
        from backend.core.config.settings import Settings

        secret = "a" * 40  # 40 chars, meets min_length=32
        s = Settings(
            JWT_SECRET_KEY=secret,
            _env_file=None,
        )
        # Access via property
        assert s.JWT_SECRET_KEY == secret

    def test_happy_path_jwt_via_raw_field(self):
        """jwt_secret_key_raw field holds the raw value."""
        from backend.core.config.settings import Settings

        secret = "b" * 40
        s = Settings(
            JWT_SECRET_KEY=secret,
            _env_file=None,
        )
        assert s.jwt_secret_key_raw == secret

    def test_unhappy_short_jwt_secret_raises_validation_error(self):
        """JWT_SECRET_KEY shorter than 32 chars raises ValidationError."""
        from pydantic import ValidationError

        from backend.core.config.settings import Settings

        with pytest.raises(ValidationError):
            Settings(
                JWT_SECRET_KEY="tooshort",
                _env_file=None,
            )

    def test_unhappy_missing_jwt_secret_raises_validation_error(self):
        """Missing JWT_SECRET_KEY raises ValidationError."""
        from pydantic import ValidationError

        from backend.core.config.settings import Settings

        # Clear env to ensure no fallback
        env_backup = os.environ.get("JWT_SECRET_KEY")
        os.environ.pop("JWT_SECRET_KEY", None)

        try:
            with pytest.raises(ValidationError):
                Settings(_env_file=None)
        finally:
            if env_backup is not None:
                os.environ["JWT_SECRET_KEY"] = env_backup


class TestSettingsDatabaseUrl:
    """Tests for Settings.DATABASE_URL property."""

    def test_happy_path_database_url_from_env(self):
        """DATABASE_URL is loaded from environment."""
        from backend.core.config.settings import Settings

        s = Settings(
            JWT_SECRET_KEY="a" * 40,
            DATABASE_URL="postgresql+asyncpg://mydb:5432/test",
            _env_file=None,
        )
        assert s.DATABASE_URL == "postgresql+asyncpg://mydb:5432/test"

    def test_happy_path_database_url_default_fallback(self):
        """DATABASE_URL falls back to default when not set."""
        from backend.core.config.settings import Settings

        env_backup = os.environ.get("DATABASE_URL")
        os.environ.pop("DATABASE_URL", None)

        try:
            s = Settings(
                JWT_SECRET_KEY="a" * 40,
                _env_file=None,
            )
            assert "postgresql+asyncpg://localhost:5432/agentic_trader" in s.DATABASE_URL
        finally:
            if env_backup is not None:
                os.environ["DATABASE_URL"] = env_backup
