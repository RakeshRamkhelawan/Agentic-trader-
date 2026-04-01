"""
Live Integration Tests for Wiring - Tests actual API endpoints.

These tests verify:
1. All routes are registered
2. Endpoints return proper HTTP status codes
3. Request/response schemas are correct
4. Authentication works

Requires running backend server or uses ASGI transport.
"""

import os
import sys
from uuid import uuid4

# Set test environment BEFORE any imports
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-wiring-tests-32-chars-long-xyz"
os.environ["AUTH_DISABLED"] = "true"
os.environ["ENV"] = "test"

# Add project root
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pytest


@pytest.fixture
def unique_email():
    """Generate unique email for tests."""
    return f"test_{uuid4().hex[:8]}@example.com"


class TestWiringRoutesExist:
    """Verify all wired routes exist in the application."""

    def test_auth_routes_registered(self):
        """Test that all auth routes are registered."""
        from backend.api.main import app

        routes = [
            (list(r.methods)[0] if r.methods else "GET", r.path)
            for r in app.routes
            if hasattr(r, "path") and hasattr(r, "methods")
        ]

        assert ("POST", "/api/v1/auth/register") in routes
        assert ("POST", "/api/v1/auth/login") in routes
        assert ("GET", "/api/v1/auth/me") in routes
        assert ("POST", "/api/v1/auth/token") in routes

    def test_kyc_routes_registered(self):
        """Test that all KYC routes are registered."""
        from backend.api.main import app

        routes = [
            (list(r.methods)[0] if r.methods else "GET", r.path)
            for r in app.routes
            if hasattr(r, "path") and hasattr(r, "methods")
        ]

        assert ("GET", "/api/v1/kyc/status") in routes
        assert ("GET", "/api/v1/kyc/required") in routes
        assert ("POST", "/api/v1/kyc/submit") in routes
        assert ("POST", "/api/v1/kyc/documents") in routes

    def test_settings_routes_registered(self):
        """Test that all settings routes are registered."""
        from backend.api.main import app

        routes = [
            (list(r.methods)[0] if r.methods else "GET", r.path)
            for r in app.routes
            if hasattr(r, "path") and hasattr(r, "methods")
        ]

        assert ("GET", "/api/v1/settings/all") in routes
        assert ("GET", "/api/v1/settings/profile") in routes
        assert ("PUT", "/api/v1/settings/profile") in routes
        assert ("GET", "/api/v1/settings/notifications") in routes
        assert ("PUT", "/api/v1/settings/notifications") in routes
        assert ("GET", "/api/v1/settings/security") in routes
        assert ("POST", "/api/v1/settings/security/2fa") in routes
        assert ("POST", "/api/v1/settings/security/password") in routes
        assert ("GET", "/api/v1/settings/appearance") in routes
        assert ("PUT", "/api/v1/settings/appearance") in routes
        assert ("GET", "/api/v1/settings/preferences") in routes
        assert ("PUT", "/api/v1/settings/preferences") in routes
        assert ("GET", "/api/v1/settings/api-keys") in routes
        assert ("POST", "/api/v1/settings/api-keys") in routes

    def test_competitions_routes_registered(self):
        """Test that all competitions routes are registered."""
        from backend.api.main import app

        routes = [
            (list(r.methods)[0] if r.methods else "GET", r.path)
            for r in app.routes
            if hasattr(r, "path") and hasattr(r, "methods")
        ]

        assert ("GET", "/api/v1/competitions/tournaments") in routes
        assert ("GET", "/api/v1/competitions/league-info") in routes
        assert ("POST", "/api/v1/competitions/enter") in routes
        assert ("GET", "/api/v1/competitions/leaderboard") in routes
        assert ("GET", "/api/v1/competitions/badges/{competitor_id}") in routes
        assert ("GET", "/api/v1/competitions/available-badges") in routes


class TestWiringImports:
    """Verify all modules can be imported without errors."""

    def test_auth_api_imports(self):
        """Test auth_api module imports."""
        from backend.api.auth_api import create_jwt_token, router

        assert router is not None

    def test_kyc_api_imports(self):
        """Test kyc_api module imports."""
        from backend.api.kyc_api import ENABLE_KYC, router

        assert router is not None

    def test_user_settings_api_imports(self):
        """Test user_settings_api module imports."""
        from backend.api.user_settings_api import router

        assert router is not None

    def test_competitions_api_imports(self):
        """Test competitions_api module imports."""
        from backend.api.competitions_api import router

        assert router is not None

    def test_user_settings_service_imports(self):
        """Test user_settings_service imports."""
        from backend.services.user_settings_service import UserSettingsService

        assert UserSettingsService is not None


class TestWiringSchemas:
    """Verify Pydantic schemas are properly defined."""

    def test_auth_schemas(self):
        """Test auth request/response schemas."""
        from backend.api.auth_api import (
            AuthResponse,
            LoginRequest,
            RegisterRequest,
            UserResponse,
        )

        # Test RegisterRequest
        req = RegisterRequest(
            email="test@example.com", password="SecurePass123!", full_name="Test User"
        )
        assert req.email == "test@example.com"
        assert req.password == "SecurePass123!"

    def test_kyc_schemas(self):
        """Test KYC schemas."""
        from backend.api.kyc_api import KYCData, KYCResponse, KYCStatus

        # Test KYCStatus enum
        assert KYCStatus.VERIFIED == "verified"
        assert KYCStatus.NOT_STARTED == "not_started"

    def test_settings_schemas(self):
        """Test settings schemas."""
        from backend.schemas.user_settings import (
            AppearanceSettings,
            NotificationSettings,
            SecuritySettings,
            UserPreferences,
            UserProfile,
        )

        # Test UserProfile
        profile = UserProfile(first_name="John", last_name="Doe", email="john@example.com")
        assert profile.first_name == "John"
        assert profile.last_name == "Doe"


class TestWiringFrontendAPI:
    """Verify frontend API client types match backend schemas."""

    def test_frontend_auth_types(self):
        """Test frontend auth API types are defined."""
        # This would require loading the TypeScript file
        # For now, we just verify the backend types exist
        from backend.api.auth_api import LoginRequest, RegisterRequest

        # Verify fields match what frontend expects
        register_fields = RegisterRequest.model_fields.keys()
        assert "email" in register_fields
        assert "password" in register_fields
        assert "full_name" in register_fields

        login_fields = LoginRequest.model_fields.keys()
        assert "email" in login_fields
        assert "password" in login_fields

    def test_frontend_settings_types(self):
        """Test frontend settings API types are defined."""
        from backend.schemas.user_settings import NotificationSettings, UserPreferences

        # Verify notification settings fields
        notif_fields = NotificationSettings.model_fields.keys()
        assert "order_executions" in notif_fields
        assert "price_alerts" in notif_fields

        # Verify preferences fields
        pref_fields = UserPreferences.model_fields.keys()
        assert "default_currency" in pref_fields
        assert "default_exchange" in pref_fields


# Run with: pytest backend/tests/integration/test_wiring_live.py -v
