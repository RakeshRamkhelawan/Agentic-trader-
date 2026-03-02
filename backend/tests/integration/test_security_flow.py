from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from backend.core.auth.middleware import AuthMiddleware
from backend.core.auth.models import TokenPayload
from backend.core.security.dependencies import (
    TenantContext,
    get_current_tenant,
    get_current_user_id,
    require_roles,
)
from backend.core.security.secrets import EnvBackend, SecretManager


@pytest.fixture
def app_with_auth():
    app = FastAPI()

    mock_validator = AsyncMock()
    mock_validator.validate_token.return_value = TokenPayload(
        sub="integration-user",
        tenant_id="tenant-integration",
        roles=["trader", "admin"],
        exp=9999999999,
    )

    auth_middleware = AuthMiddleware(app, jwt_validator=mock_validator)
    app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware.dispatch)

    @app.get("/protected")
    async def protected_route(tenant_id: str = Depends(get_current_tenant)):
        return {"tenant_id": tenant_id, "message": "Access granted"}

    @app.get("/user-info")
    async def user_info(user_id: str = Depends(get_current_user_id)):
        return {"user_id": user_id}

    @app.get("/admin-only")
    async def admin_only(token: TokenPayload = Depends(require_roles("admin"))):
        return {"message": "Admin access", "user": token.sub}

    @app.get("/tenant-context")
    async def tenant_context_route(ctx: TenantContext = Depends()):
        return {"tenant_id": ctx.tenant_id, "rls_filter": ctx.get_rls_filter()}

    return app


def test_integration_auth_flow(app_with_auth):
    client = TestClient(app_with_auth)

    response = client.get("/protected", headers={"Authorization": "Bearer valid_token"})

    assert response.status_code == 200
    data = response.json()
    assert data["tenant_id"] == "tenant-integration"
    assert data["message"] == "Access granted"


def test_integration_user_info(app_with_auth):
    client = TestClient(app_with_auth)

    response = client.get("/user-info", headers={"Authorization": "Bearer valid_token"})

    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "integration-user"


def test_integration_role_check(app_with_auth):
    client = TestClient(app_with_auth)

    response = client.get("/admin-only", headers={"Authorization": "Bearer valid_token"})

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Admin access"
    assert data["user"] == "integration-user"


def test_integration_tenant_context(app_with_auth):
    client = TestClient(app_with_auth)

    response = client.get("/tenant-context", headers={"Authorization": "Bearer valid_token"})

    assert response.status_code == 200
    data = response.json()
    assert data["tenant_id"] == "tenant-integration"
    assert data["rls_filter"] == {"tenant_id": "tenant-integration"}


def test_integration_missing_token(app_with_auth):
    client = TestClient(app_with_auth)

    response = client.get("/protected")

    assert response.status_code == 401
    assert "Missing authorization token" in response.json()["detail"]


def test_integration_public_path(app_with_auth):
    client = TestClient(app_with_auth)

    response = client.get("/health")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_integration_secret_manager_vault_fallback():
    mock_vault = MagicMock()
    mock_vault.get_secret.side_effect = Exception("Vault down")
    mock_vault.is_connected = False

    from backend.core.security.secrets import VaultBackend

    vault_backend = VaultBackend(mock_vault)
    env_backend = EnvBackend()

    manager = SecretManager(
        primary_backend=vault_backend, fallback_backend=env_backend, cache_enabled=True
    )

    with patch.dict(
        "os.environ", {"REVOLUT_API_KEY": "fallback_key_123", "DATABASE_URL": "postgres://fallback"}
    ):
        api_key = manager.get_api_key("revolut")
        db_url = manager.get_database_url()

        assert api_key == "fallback_key_123"
        assert db_url == "postgres://fallback"

        assert not manager.is_vault_connected


@pytest.mark.asyncio
async def test_integration_secret_manager_caching_flow():
    mock_vault = MagicMock()
    mock_vault.get_secret.return_value = "vault_secret_value"
    mock_vault.is_connected = True

    from backend.core.security.secrets import VaultBackend

    vault_backend = VaultBackend(mock_vault)

    manager = SecretManager(primary_backend=vault_backend, cache_enabled=True)

    value1 = manager.get_secret("service", "key")
    value2 = manager.get_secret("service", "key")

    assert value1 == "vault_secret_value"
    assert value2 == "vault_secret_value"
    mock_vault.get_secret.assert_called_once_with("service", "key")

    manager.clear_cache()
    manager.get_secret("service", "key")
    assert mock_vault.get_secret.call_count == 2
