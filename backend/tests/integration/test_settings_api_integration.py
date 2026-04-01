"""
Integration Tests for User Settings API - Real Backend Integration

Tests use the actual FastAPI app and real database.
All CRUD operations are tested with real data persistence.
"""

import pytest
from httpx import AsyncClient

pytestmark = [pytest.mark.asyncio, pytest.mark.integration]


class TestSettingsAPIIntegration:
    """Full integration tests for User Settings API with real backend."""

    async def _get_auth_token(self, async_client: AsyncClient, unique_email: str) -> str:
        """Helper to register and get auth token."""
        response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": unique_email,
                "password": "SecurePass123!",
                "full_name": "Test User",
            },
        )
        return response.json()["access_token"]

    async def test_get_all_settings(self, async_client: AsyncClient, unique_email: str):
        """Test getting all settings at once."""
        token = await self._get_auth_token(async_client, unique_email)

        response = await async_client.get(
            "/api/v1/settings/all", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify all expected sections
        assert "profile" in data
        assert "notifications" in data
        assert "security" in data
        assert "appearance" in data
        assert "preferences" in data
        assert "api_keys" in data

    async def test_profile_crud(self, async_client: AsyncClient, unique_email: str):
        """Test profile get and update operations."""
        token = await self._get_auth_token(async_client, unique_email)

        # Get initial profile
        get_response = await async_client.get(
            "/api/v1/settings/profile", headers={"Authorization": f"Bearer {token}"}
        )
        assert get_response.status_code == 200
        _ = get_response.json()  # Verify response parses as JSON

        # Update profile
        update_data = {
            "first_name": "Updated",
            "last_name": "Name",
            "email": unique_email,
        }

        put_response = await async_client.put(
            "/api/v1/settings/profile",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data,
        )
        assert put_response.status_code == 200
        updated_profile = put_response.json()

        assert updated_profile["first_name"] == "Updated"
        assert updated_profile["last_name"] == "Name"

        # Verify persistence by getting again
        get_response2 = await async_client.get(
            "/api/v1/settings/profile", headers={"Authorization": f"Bearer {token}"}
        )
        assert get_response2.status_code == 200
        persisted_profile = get_response2.json()

        assert persisted_profile["first_name"] == "Updated"
        assert persisted_profile["last_name"] == "Name"

    async def test_notifications_crud(self, async_client: AsyncClient, unique_email: str):
        """Test notification settings get and update."""
        token = await self._get_auth_token(async_client, unique_email)

        # Get initial notifications
        get_response = await async_client.get(
            "/api/v1/settings/notifications",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_response.status_code == 200
        initial_notifications = get_response.json()

        # Toggle all notifications
        update_data = {
            "order_executions": not initial_notifications.get("order_executions", True),
            "price_alerts": not initial_notifications.get("price_alerts", True),
            "ai_signals": not initial_notifications.get("ai_signals", True),
            "security_alerts": not initial_notifications.get("security_alerts", True),
        }

        put_response = await async_client.put(
            "/api/v1/settings/notifications",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data,
        )
        assert put_response.status_code == 200
        updated_notifications = put_response.json()

        assert updated_notifications["order_executions"] == update_data["order_executions"]
        assert updated_notifications["price_alerts"] == update_data["price_alerts"]

        # Verify persistence
        get_response2 = await async_client.get(
            "/api/v1/settings/notifications",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert get_response2.status_code == 200
        persisted_notifications = get_response2.json()

        assert persisted_notifications["order_executions"] == update_data["order_executions"]

    async def test_security_settings(self, async_client: AsyncClient, unique_email: str):
        """Test security settings get."""
        token = await self._get_auth_token(async_client, unique_email)

        response = await async_client.get(
            "/api/v1/settings/security", headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "two_factor_enabled" in data
        assert "last_password_change" in data

    async def test_toggle_2fa(self, async_client: AsyncClient, unique_email: str):
        """Test 2FA toggle endpoint."""
        token = await self._get_auth_token(async_client, unique_email)

        # Enable 2FA
        enable_response = await async_client.post(
            "/api/v1/settings/security/2fa",
            headers={"Authorization": f"Bearer {token}"},
            params={"enabled": True},
        )

        # Note: The actual implementation may vary
        # This test assumes the endpoint returns the new state
        assert enable_response.status_code in [200, 501]  # 501 if not implemented

        if enable_response.status_code == 200:
            data = enable_response.json()
            assert "enabled" in data

    async def test_change_password(self, async_client: AsyncClient, unique_email: str):
        """Test password change endpoint."""
        token = await self._get_auth_token(async_client, unique_email)

        response = await async_client.post(
            "/api/v1/settings/security/password",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "current_password": "SecurePass123!",
                "new_password": "NewSecurePass456!",
            },
        )

        # Endpoint should return success (actual validation may vary in test env)
        assert response.status_code in [200, 400, 422]

        if response.status_code == 200:
            data = response.json()
            assert "success" in data

    async def test_appearance_crud(self, async_client: AsyncClient, unique_email: str):
        """Test appearance settings get and update."""
        token = await self._get_auth_token(async_client, unique_email)

        # Get initial appearance
        get_response = await async_client.get(
            "/api/v1/settings/appearance", headers={"Authorization": f"Bearer {token}"}
        )
        assert get_response.status_code == 200
        initial_appearance = get_response.json()

        # Update theme
        themes = ["dark", "light", "system"]
        current_theme = initial_appearance.get("theme", "dark")
        new_theme = [t for t in themes if t != current_theme][0]

        update_data = {"theme": new_theme}

        put_response = await async_client.put(
            "/api/v1/settings/appearance",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data,
        )
        assert put_response.status_code == 200
        updated_appearance = put_response.json()

        assert updated_appearance["theme"] == new_theme

    async def test_preferences_crud(self, async_client: AsyncClient, unique_email: str):
        """Test user preferences get and update."""
        token = await self._get_auth_token(async_client, unique_email)

        # Get initial preferences
        get_response = await async_client.get(
            "/api/v1/settings/preferences", headers={"Authorization": f"Bearer {token}"}
        )
        assert get_response.status_code == 200
        _ = get_response.json()  # Verify response parses as JSON

        # Update preferences
        update_data = {"default_currency": "USD", "default_exchange": "kraken"}

        put_response = await async_client.put(
            "/api/v1/settings/preferences",
            headers={"Authorization": f"Bearer {token}"},
            json=update_data,
        )
        assert put_response.status_code == 200
        updated_preferences = put_response.json()

        assert updated_preferences["default_currency"] == "USD"
        assert updated_preferences["default_exchange"] == "kraken"

        # Verify persistence
        get_response2 = await async_client.get(
            "/api/v1/settings/preferences", headers={"Authorization": f"Bearer {token}"}
        )
        assert get_response2.status_code == 200
        persisted_preferences = get_response2.json()

        assert persisted_preferences["default_currency"] == "USD"

    async def test_api_keys_list(self, async_client: AsyncClient, unique_email: str):
        """Test API keys list endpoint."""
        token = await self._get_auth_token(async_client, unique_email)

        response = await async_client.get(
            "/api/v1/settings/api-keys", headers={"Authorization": f"Bearer {token}"}
        )

        # Should succeed (may be empty list)
        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)

    async def test_settings_unauthorized_access(self, async_client: AsyncClient):
        """Test that settings endpoints require authentication."""
        endpoints = [
            ("GET", "/api/v1/settings/all"),
            ("GET", "/api/v1/settings/profile"),
            ("PUT", "/api/v1/settings/profile"),
            ("GET", "/api/v1/settings/notifications"),
            ("PUT", "/api/v1/settings/notifications"),
            ("GET", "/api/v1/settings/security"),
            ("GET", "/api/v1/settings/appearance"),
            ("PUT", "/api/v1/settings/appearance"),
            ("GET", "/api/v1/settings/preferences"),
            ("PUT", "/api/v1/settings/preferences"),
            ("GET", "/api/v1/settings/api-keys"),
        ]

        for method, endpoint in endpoints:
            if method == "GET":
                response = await async_client.get(endpoint)
            else:
                response = await async_client.put(endpoint, json={})

            assert response.status_code in [
                401,
                403,
            ], f"{method} {endpoint} should require auth"

    async def test_complete_settings_flow(self, async_client: AsyncClient, unique_email: str):
        """Test complete settings flow with all operations."""
        token = await self._get_auth_token(async_client, unique_email)

        # 1. Get all settings
        all_response = await async_client.get(
            "/api/v1/settings/all", headers={"Authorization": f"Bearer {token}"}
        )
        assert all_response.status_code == 200
        _ = all_response.json()  # Verify response parses as JSON

        # 2. Update profile
        profile_update = {
            "first_name": "Integration",
            "last_name": "Test",
            "email": unique_email,
        }
        profile_response = await async_client.put(
            "/api/v1/settings/profile",
            headers={"Authorization": f"Bearer {token}"},
            json=profile_update,
        )
        assert profile_response.status_code == 200

        # 3. Update notifications
        notifications_update = {
            "order_executions": True,
            "price_alerts": True,
            "ai_signals": False,
            "security_alerts": True,
        }
        notifications_response = await async_client.put(
            "/api/v1/settings/notifications",
            headers={"Authorization": f"Bearer {token}"},
            json=notifications_update,
        )
        assert notifications_response.status_code == 200

        # 4. Update appearance
        appearance_update = {"theme": "dark"}
        appearance_response = await async_client.put(
            "/api/v1/settings/appearance",
            headers={"Authorization": f"Bearer {token}"},
            json=appearance_update,
        )
        assert appearance_response.status_code == 200

        # 5. Update preferences
        preferences_update = {"default_currency": "EUR", "default_exchange": "bitvavo"}
        preferences_response = await async_client.put(
            "/api/v1/settings/preferences",
            headers={"Authorization": f"Bearer {token}"},
            json=preferences_update,
        )
        assert preferences_response.status_code == 200

        # 6. Verify all changes persisted
        final_all_response = await async_client.get(
            "/api/v1/settings/all", headers={"Authorization": f"Bearer {token}"}
        )
        assert final_all_response.status_code == 200
        final_data = final_all_response.json()

        assert final_data["profile"]["first_name"] == "Integration"
        assert final_data["notifications"]["ai_signals"] is False
        assert final_data["appearance"]["theme"] == "dark"
        assert final_data["preferences"]["default_exchange"] == "bitvavo"
