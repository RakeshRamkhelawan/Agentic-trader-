from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.requests import Request
from starlette.responses import Response

from backend.core.auth import context
from backend.core.auth.jwt_validator import JWTValidator
from backend.core.auth.middleware import AuthMiddleware
from backend.core.auth.models import TokenPayload
from backend.core.security.schemas import IdentityPayload, OIDCUserInfo, SecretMetadata, TokenClaims
from backend.core.security.secrets import EnvBackend, SecretManager, VaultBackend


@pytest.fixture
def mock_jwks_response():
    return {
        "keys": [
            {"kid": "test-key-id", "kty": "RSA", "use": "sig", "n": "test-modulus", "e": "AQAB"}
        ]
    }


@pytest.fixture
def jwt_validator():
    return JWTValidator(
        jwks_url="https://test.auth0.com/.well-known/jwks.json",
        issuer="https://test.auth0.com/",
        audience="https://api.test.com",
    )


@pytest.mark.asyncio
async def test_jwt_validator_fetch_jwks(jwt_validator, mock_jwks_response):
    with patch("backend.core.auth.jwt_validator.httpx.AsyncClient") as MockClient:
        mock_instance = MockClient.return_value
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None

        mock_response = MagicMock()
        mock_response.json.return_value = mock_jwks_response
        mock_response.raise_for_status = MagicMock()

        mock_instance.get = AsyncMock(return_value=mock_response)

        await jwt_validator.refresh_jwks()

        assert jwt_validator._jwks_cache == mock_jwks_response
        mock_instance.get.assert_called_once()


@pytest.mark.asyncio
async def test_validate_token_success(jwt_validator):
    jwt_validator._get_signing_key = AsyncMock(return_value={"kid": "test"})

    with patch("jose.jwt.decode") as mock_decode:
        mock_decode.return_value = {
            "sub": "user123",
            "tenant_id": "tenant-abc",
            "roles": ["admin"],
            "exp": 9999999999,
        }

        payload = await jwt_validator.validate_token("valid.token.string")

        assert isinstance(payload, TokenPayload)
        assert payload.sub == "user123"
        assert payload.tenant_id == "tenant-abc"
        assert payload.roles == ["admin"]


@pytest.mark.asyncio
async def test_context_management():
    context.set_current_tenant("tenant-1")
    assert context.get_current_tenant() == "tenant-1"

    context.set_current_user("user-1")
    assert context.get_current_user() == "user-1"

    context.clear_context()
    with pytest.raises(context.UnauthorizedError):
        context.get_current_tenant()


@pytest.mark.asyncio
async def test_auth_middleware_success():
    app = MagicMock()
    middleware = AuthMiddleware(app)

    mock_validator = AsyncMock()
    mock_validator.validate_token.return_value = TokenPayload(
        sub="user123", tenant_id="tenant-abc", roles=["trader"], exp=9999999999
    )
    middleware._jwt_validator = mock_validator

    request = MagicMock(spec=Request)
    request.url.path = "/api/protected"
    request.headers = {"Authorization": "Bearer valid_token"}
    request.state = MagicMock()

    call_next = AsyncMock(return_value=Response("OK"))

    await middleware.dispatch(request, call_next)

    mock_validator.validate_token.assert_called_with("valid_token")
    call_next.assert_awaited_once_with(request)

    assert request.state.user_id == "user123"
    assert request.state.tenant_id == "tenant-abc"


def test_identity_payload_schema():
    payload = IdentityPayload(
        sub="auth0|123", email="test@example.com", email_verified=True, name="Test User"
    )

    assert payload.sub == "auth0|123"
    assert payload.email == "test@example.com"
    assert payload.email_verified is True
    assert payload.name == "Test User"


def test_token_claims_schema():
    claims = TokenClaims(
        sub="user123",
        tenant_id="tenant-abc",
        roles=["admin", "trader"],
        exp=9999999999,
        iat=1735603200,
        iss="https://auth.test.com/",
        aud="https://api.test.com",
    )

    assert claims.sub == "user123"
    assert claims.tenant_id == "tenant-abc"
    assert claims.has_role("admin")
    assert claims.has_any_role(["trader", "viewer"])
    assert not claims.is_expired()


def test_oidc_userinfo_schema():
    userinfo = OIDCUserInfo(
        sub="auth0|123",
        email="test@example.com",
        email_verified=True,
        name="Test User",
        given_name="Test",
        family_name="User",
    )

    assert userinfo.sub == "auth0|123"
    assert userinfo.email == "test@example.com"
    assert userinfo.given_name == "Test"


def test_secret_metadata_schema():
    metadata = SecretMetadata(
        path="revolut/production", key="api_key", version=3, rotation_policy="monthly"
    )

    assert metadata.path == "revolut/production"
    assert metadata.key == "api_key"
    assert metadata.version == 3
    assert metadata.rotation_policy == "monthly"


def test_env_backend():
    backend = EnvBackend()

    with patch.dict("os.environ", {"TEST_SECRET_API_KEY": "env_value"}):
        value = backend.get_secret("test/secret", "api_key")
        assert value == "env_value"

    assert backend.is_connected()


def test_secret_manager_with_fallback():
    mock_vault = MagicMock()
    mock_vault.get_secret.side_effect = Exception("Vault unavailable")
    mock_vault.is_connected.return_value = False

    vault_backend = VaultBackend(mock_vault)
    env_backend = EnvBackend()

    manager = SecretManager(
        primary_backend=vault_backend, fallback_backend=env_backend, cache_enabled=True
    )

    with patch.dict("os.environ", {"DATABASE_URL": "postgres://localhost"}):
        url = manager.get_secret("database", "url")
        assert url == "postgres://localhost"


def test_secret_manager_caching():
    mock_vault = MagicMock()
    mock_vault.get_secret.return_value = "cached_value"
    mock_vault.is_connected.return_value = True

    vault_backend = VaultBackend(mock_vault)
    manager = SecretManager(primary_backend=vault_backend, cache_enabled=True)

    value1 = manager.get_secret("test", "key")
    value2 = manager.get_secret("test", "key")

    assert value1 == "cached_value"
    assert value2 == "cached_value"
    mock_vault.get_secret.assert_called_once()

    manager.clear_cache()
    manager.get_secret("test", "key")
    assert mock_vault.get_secret.call_count == 2


def test_secret_manager_get_api_key():
    mock_vault = MagicMock()
    mock_vault.get_secret.return_value = "test_api_key_123"
    mock_vault.is_connected.return_value = True

    vault_backend = VaultBackend(mock_vault)
    manager = SecretManager(primary_backend=vault_backend)

    api_key = manager.get_api_key("revolut")
    assert api_key == "test_api_key_123"
    mock_vault.get_secret.assert_called_with("revolut", "api_key")


def test_secret_manager_default_fallback():
    mock_vault = MagicMock()
    mock_vault.get_secret.return_value = ""
    mock_vault.is_connected.return_value = True

    vault_backend = VaultBackend(mock_vault)
    env_backend = EnvBackend()

    manager = SecretManager(primary_backend=vault_backend, fallback_backend=env_backend)

    value = manager.get_secret("missing", "key", default="default_value")
    assert value == "default_value"
