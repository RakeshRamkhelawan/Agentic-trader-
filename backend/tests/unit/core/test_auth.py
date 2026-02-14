
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.requests import Request
from starlette.responses import Response

from backend.core.auth import context
from backend.core.auth.jwt_validator import (InvalidSignatureError,
                                             JWTValidator, TokenExpiredError)
from backend.core.auth.middleware import AuthMiddleware
from backend.core.auth.models import TokenPayload


@pytest.fixture
def mock_jwks_response():
    return {
        "keys": [
            {
                "kid": "test-key-id",
                "kty": "RSA",
                "use": "sig",
                "n": "test-modulus",
                "e": "AQAB"
            }
        ]
    }

@pytest.fixture
def jwt_validator():
    return JWTValidator(
        jwks_url="https://test.auth0.com/.well-known/jwks.json",
        issuer="https://test.auth0.com/",
        audience="https://api.test.com"
    )

@pytest.mark.asyncio
async def test_jwt_validator_fetch_jwks(jwt_validator, mock_jwks_response):
    with patch("backend.core.auth.jwt_validator.httpx.AsyncClient") as MockClient:
        # Config mock instance
        mock_instance = MockClient.return_value
        mock_instance.__aenter__.return_value = mock_instance
        mock_instance.__aexit__.return_value = None
        
        # Config get response
        mock_response = MagicMock()
        mock_response.json.return_value = mock_jwks_response
        mock_response.raise_for_status = MagicMock()
        
        mock_instance.get = AsyncMock(return_value=mock_response)
        
        await jwt_validator.refresh_jwks()
        
        assert jwt_validator._jwks_cache == mock_jwks_response
        mock_instance.get.assert_called_once()

@pytest.mark.asyncio
async def test_validate_token_success(jwt_validator):
    # Mock _get_signing_key to return a key
    jwt_validator._get_signing_key = AsyncMock(return_value={"kid": "test"})
    
    # Mock jwt.decode
    with patch("jose.jwt.decode") as mock_decode:
        mock_decode.return_value = {
            "sub": "user123",
            "tenant_id": "tenant-abc",
            "roles": ["admin"],
            "exp": 9999999999
        }
        
        payload = await jwt_validator.validate_token("valid.token.string")
        
        assert isinstance(payload, TokenPayload)
        assert payload.sub == "user123"
        assert payload.tenant_id == "tenant-abc"
        assert payload.roles == ["admin"]

@pytest.mark.asyncio
async def test_context_management():
    # Test setting and getting context
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
    
    # Mock JWT Validator
    mock_validator = AsyncMock()
    mock_validator.validate_token.return_value = TokenPayload(
        sub="user123",
        tenant_id="tenant-abc",
        roles=["trader"],
        exp=9999999999
    )
    middleware._jwt_validator = mock_validator
    
    # Mock Request
    request = MagicMock(spec=Request)
    request.url.path = "/api/protected"
    request.headers = {"Authorization": "Bearer valid_token"}
    request.state = MagicMock()
    
    # Mock Next Call
    call_next = AsyncMock(return_value=Response("OK"))
    
    # Run dispatch
    response = await middleware.dispatch(request, call_next)
    
    # Verify validator called
    mock_validator.validate_token.assert_called_with("valid_token")
    
    # Verify context set (we check direct context access as verification)
    # Note: Middleware clears context in finally block, so this checks logic inside dispatch
    # Since we can't easily check inside the `try` block of usage, we verify `call_next` was awaited properly
    call_next.assert_awaited_once_with(request)
    
    # Verify request state updated
    assert request.state.user_id == "user123"
    assert request.state.tenant_id == "tenant-abc"

