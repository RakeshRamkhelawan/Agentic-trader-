
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock, patch
from backend.api.main import app
from backend.core.auth.middleware import AuthMiddleware

client = TestClient(app)

@pytest.fixture
def mock_middleware_validator():
    """
    Locate the AuthMiddleware in the app and replace its validator.
    Restores original on teardown.
    """
    # Find AuthMiddleware
    auth_middleware = None
    for middleware in app.user_middleware:
        if middleware.cls == AuthMiddleware:
            # In Starlette/FastAPI, middleware is wrapped. 
            # We might need to access the app's middleware stack differently if this doesn't work directly 
            # depending on how TestClient/Starlette handles it. 
            # However, app.user_middleware contains the configuration. 
            # The actual running middleware stack is built when request comes in? 
            # No, `add_middleware` behaves differently.
            pass
            
    # Easier approach for identifying the running middleware instance serves request:
    # We can patch the class 'backend.core.auth.middleware.AuthMiddleware' BEFORE app is created? 
    # No, app is already created in main.py.
    
    # Strategy: Inspect `app.middleware_stack`? 
    # Actually, modifying `token_validator` in `backend.api.main` might work if we could reload, but effectively 
    # the middleware instance holds the reference.
    
    # Let's try to patch the specific instance being used.
    # But finding the instance is hard.
    
    # Alternative: Patch `backend.core.auth.jwt_validator.JWTValidator.validate_token` 
    # This matches the class method. Since `token_validator` is an instance of `JWTValidator`, 
    # patching the class method `validate_token` with `autospec=True` should affect all instances.
    
    from backend.core.auth.jwt_validator import JWTValidator
    
    with patch.object(JWTValidator, 'validate_token', new_callable=AsyncMock) as mock_method:
        yield mock_method

def test_missing_authorization_header(mock_middleware_validator):
    response = client.get("/api/v1/trading/orders/active")
    assert response.status_code == 401
    assert response.json() == {"detail": "Missing authorization token"}

def test_invalid_authorization_header_format(mock_middleware_validator):
    response = client.get(
        "/api/v1/trading/orders/active",
        headers={"Authorization": "Basic somebase64"}
    )
    # Middleware extracts "Bearer ". If strict check, return 401. 
    # Code: if auth_header.startswith("Bearer "): return token else None
    # If None, returns "Missing authorization token"
    assert response.status_code == 401
    assert response.json() == {"detail": "Missing authorization token"}

def test_invalid_token_content(mock_middleware_validator):
    """Test Authorization header with invalid token string."""
    mock_middleware_validator.side_effect = Exception("Invalid token signature")
    
    response = client.get(
        "/api/v1/trading/orders/active",
        headers={"Authorization": "Bearer invalid.token.string"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid token signature"}

def test_expired_token(mock_middleware_validator):
    """Test Authorization header with expired token."""
    mock_middleware_validator.side_effect = Exception("Signature has expired")
    
    response = client.get(
        "/api/v1/trading/orders/active",
        headers={"Authorization": "Bearer expired.token.string"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Signature has expired"}

def test_valid_token_access(mock_middleware_validator):
    """Happy path confirm to ensure test setup is correct."""
    from backend.core.auth.models import TokenPayload
    
    # Mock successful validation
    mock_middleware_validator.return_value = TokenPayload(
        sub="user123",
        tenant_id="tenant-A",
        roles=["user"],
        exp=9999999999
    )
    mock_middleware_validator.side_effect = None
    
    # Mock database or service call
    # The endpoint uses TradingService.get_active_orders
    # We need to mock the dependency get_service or the method on the class
    with patch("backend.services.trading_service.TradingService.get_active_orders", return_value=[]):
        response = client.get(
            "/api/v1/trading/orders/active",
            headers={"Authorization": "Bearer valid.token"}
        )
        # Should be 200 OK
        assert response.status_code == 200
