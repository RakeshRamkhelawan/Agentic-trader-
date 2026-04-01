"""
End-to-End Integration Test for Frontend-Backend Wiring

This test verifies the complete flow of a user:
1. Register/Login
2. Check KYC status
3. Update settings (profile, notifications, preferences)
4. View competitions data
5. All using REAL backend APIs - NO MOCKS
"""

import pytest
from httpx import AsyncClient

pytestmark = [pytest.mark.asyncio, pytest.mark.integration]


class TestWiringEndToEndIntegration:
    """Complete end-to-end test of all wired APIs."""

    async def test_complete_user_journey(self, async_client: AsyncClient, unique_email: str):
        """
        Test complete user journey through all newly wired APIs.

        Flow:
        1. Register new user
        2. Login
        3. Get current user info
        4. Check KYC status
        5. Get all settings
        6. Update profile
        7. Update notifications
        8. Update preferences
        9. View competitions (tournaments, leagues, leaderboard)
        """
        print(f"\n🔍 Starting E2E test with email: {unique_email}")

        # ========================================
        # STEP 1: Register
        # ========================================
        print("  Step 1: Registering new user...")
        register_response = await async_client.post(
            "/api/v1/auth/register",
            json={
                "email": unique_email,
                "password": "SecurePass123!",
                "full_name": "E2E Test User",
            },
        )
        assert register_response.status_code == 201, f"Register failed: {register_response.text}"
        register_data = register_response.json()

        assert "access_token" in register_data
        assert "user" in register_data
        assert register_data["user"]["email"] == unique_email

        token = register_data["access_token"]
        user_id = register_data["user"]["id"]
        tenant_id = register_data["user"]["tenant_id"]

        print(f"    ✅ Registered user: {user_id}, tenant: {tenant_id}")

        # ========================================
        # STEP 2: Login
        # ========================================
        print("  Step 2: Logging in...")
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": unique_email, "password": "SecurePass123!"},
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        login_data = login_response.json()

        assert "access_token" in login_data
        # Use the new token
        token = login_data["access_token"]

        print("    ✅ Login successful")

        # ========================================
        # STEP 3: Get current user (/me)
        # ========================================
        print("  Step 3: Getting current user...")
        me_response = await async_client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert me_response.status_code == 200, f"Get me failed: {me_response.text}"
        me_data = me_response.json()

        assert me_data["id"] == user_id
        assert me_data["email"] == unique_email
        assert me_data["tenant_id"] == tenant_id

        print(f"    ✅ User verified: {me_data.get('full_name', 'N/A')}")

        # ========================================
        # STEP 4: Check KYC status
        # ========================================
        print("  Step 4: Checking KYC status...")
        kyc_response = await async_client.get("/api/v1/kyc/status")
        assert kyc_response.status_code == 200, f"KYC status failed: {kyc_response.text}"
        kyc_data = kyc_response.json()

        # KYC is disabled by default, so should be auto-verified
        assert "status" in kyc_data
        assert "required" in kyc_data
        assert "enabled" in kyc_data

        print(f"    ✅ KYC status: {kyc_data['status']} (required: {kyc_data['required']})")

        # Also check KYC required endpoint
        kyc_required_response = await async_client.get("/api/v1/kyc/required")
        assert kyc_required_response.status_code == 200
        kyc_required_data = kyc_required_response.json()
        assert "required" in kyc_required_data

        # ========================================
        # STEP 5: Get all settings
        # ========================================
        print("  Step 5: Getting all settings...")
        settings_response = await async_client.get(
            "/api/v1/settings/all", headers={"Authorization": f"Bearer {token}"}
        )
        assert (
            settings_response.status_code == 200
        ), f"Get settings failed: {settings_response.text}"
        settings_data = settings_response.json()

        assert "profile" in settings_data
        assert "notifications" in settings_data
        assert "security" in settings_data
        assert "appearance" in settings_data
        assert "preferences" in settings_data
        assert "api_keys" in settings_data

        print("    ✅ Settings loaded")

        # ========================================
        # STEP 6: Update profile
        # ========================================
        print("  Step 6: Updating profile...")
        profile_update = {
            "first_name": "E2E",
            "last_name": "Test",
            "email": unique_email,
        }
        profile_response = await async_client.put(
            "/api/v1/settings/profile",
            headers={"Authorization": f"Bearer {token}"},
            json=profile_update,
        )
        assert (
            profile_response.status_code == 200
        ), f"Update profile failed: {profile_response.text}"
        profile_data = profile_response.json()

        assert profile_data["first_name"] == "E2E"
        assert profile_data["last_name"] == "Test"

        print("    ✅ Profile updated")

        # ========================================
        # STEP 7: Update notifications
        # ========================================
        print("  Step 7: Updating notifications...")
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
        assert (
            notifications_response.status_code == 200
        ), f"Update notifications failed: {notifications_response.text}"
        notifications_data = notifications_response.json()

        assert notifications_data["ai_signals"] is False

        print("    ✅ Notifications updated")

        # ========================================
        # STEP 8: Update preferences
        # ========================================
        print("  Step 8: Updating preferences...")
        preferences_update = {"default_currency": "EUR", "default_exchange": "bitvavo"}
        preferences_response = await async_client.put(
            "/api/v1/settings/preferences",
            headers={"Authorization": f"Bearer {token}"},
            json=preferences_update,
        )
        assert (
            preferences_response.status_code == 200
        ), f"Update preferences failed: {preferences_response.text}"
        preferences_data = preferences_response.json()

        assert preferences_data["default_currency"] == "EUR"
        assert preferences_data["default_exchange"] == "bitvavo"

        print("    ✅ Preferences updated")

        # ========================================
        # STEP 9: View competitions data
        # ========================================
        print("  Step 9: Loading competitions data...")

        # Get tournaments
        tournaments_response = await async_client.get(
            "/api/v1/competitions/tournaments?status=active"
        )
        assert (
            tournaments_response.status_code == 200
        ), f"Get tournaments failed: {tournaments_response.text}"
        tournaments_data = tournaments_response.json()
        assert "tournaments" in tournaments_data
        assert "count" in tournaments_data

        # Get league info
        league_response = await async_client.get("/api/v1/competitions/league-info")
        assert league_response.status_code == 200, f"Get league info failed: {league_response.text}"
        league_data = league_response.json()
        assert isinstance(league_data, dict)

        # Get leaderboard
        leaderboard_response = await async_client.get("/api/v1/competitions/leaderboard")
        assert (
            leaderboard_response.status_code == 200
        ), f"Get leaderboard failed: {leaderboard_response.text}"
        leaderboard_data = leaderboard_response.json()
        assert "entries" in leaderboard_data
        assert "total" in leaderboard_data

        # Get available badges
        badges_response = await async_client.get("/api/v1/competitions/available-badges")
        assert badges_response.status_code == 200, f"Get badges failed: {badges_response.text}"
        badges_data = badges_response.json()
        assert "badges" in badges_data

        print("    ✅ Competitions data loaded:")
        print(f"       - Tournaments: {tournaments_data['count']}")
        print(f"       - Leaderboard entries: {leaderboard_data['total']}")
        print(
            f"       - Available badges: {badges_data.get('total', len(badges_data.get('badges', [])))}"
        )

        # ========================================
        # STEP 10: Verify all changes persisted
        # ========================================
        print("  Step 10: Verifying persistence...")

        final_settings_response = await async_client.get(
            "/api/v1/settings/all", headers={"Authorization": f"Bearer {token}"}
        )
        assert final_settings_response.status_code == 200
        final_settings = final_settings_response.json()

        assert final_settings["profile"]["first_name"] == "E2E"
        assert final_settings["notifications"]["ai_signals"] is False
        assert final_settings["preferences"]["default_currency"] == "EUR"

        print("    ✅ All changes persisted correctly")

        print("\n" + "=" * 70)
        print("✅ COMPLETE E2E JOURNEY SUCCESSFUL")
        print("=" * 70)
        print(f"   User: {unique_email}")
        print(f"   Tenant: {tenant_id}")
        print("   All APIs verified and working!")
        print("=" * 70)

    async def test_api_endpoints_availability(self, async_client: AsyncClient):
        """
        Verify all wired API endpoints are available and responding.
        This is a quick smoke test for all endpoints.
        """
        print("\n🔍 Running API availability smoke test...")

        # Public endpoints (no auth required)
        public_endpoints = [
            ("GET", "/api/v1/kyc/status", "KYC Status"),
            ("GET", "/api/v1/kyc/required", "KYC Required"),
            ("GET", "/api/v1/competitions/tournaments", "Competitions Tournaments"),
            ("GET", "/api/v1/competitions/league-info", "Competitions League Info"),
            ("GET", "/api/v1/competitions/leaderboard", "Competitions Leaderboard"),
            ("GET", "/api/v1/competitions/available-badges", "Competitions Badges"),
        ]

        for method, endpoint, name in public_endpoints:
            response = await async_client.get(endpoint)
            status = "✅" if response.status_code == 200 else "❌"
            print(f"  {status} {name}: {endpoint} (HTTP {response.status_code})")
            assert response.status_code == 200, f"{name} endpoint failed"

        # Auth endpoints (can check they're accessible, even if they return 401 without token)
        auth_endpoints = [
            ("POST", "/api/v1/auth/register", "Auth Register"),
            ("POST", "/api/v1/auth/login", "Auth Login"),
            ("GET", "/api/v1/auth/me", "Auth Me"),
        ]

        for method, endpoint, name in auth_endpoints:
            if method == "GET":
                response = await async_client.get(endpoint)
            else:
                # Send empty JSON to trigger validation error (endpoint is accessible)
                response = await async_client.request(method, endpoint, json={})

            # Accept 200, 201, 400 (validation error), 401 (auth required), 422 (validation)
            accessible = response.status_code in [200, 201, 400, 401, 422]
            status = "✅" if accessible else "❌"
            print(f"  {status} {name}: {endpoint} (HTTP {response.status_code})")
            assert accessible, f"{name} endpoint not accessible"

        # Settings endpoints (require auth - should return 401 without token)
        settings_endpoints = [
            ("GET", "/api/v1/settings/all", "Settings All"),
            ("GET", "/api/v1/settings/profile", "Settings Profile"),
            ("GET", "/api/v1/settings/notifications", "Settings Notifications"),
            ("GET", "/api/v1/settings/security", "Settings Security"),
            ("GET", "/api/v1/settings/appearance", "Settings Appearance"),
            ("GET", "/api/v1/settings/preferences", "Settings Preferences"),
            ("GET", "/api/v1/settings/api-keys", "Settings API Keys"),
        ]

        for method, endpoint, name in settings_endpoints:
            response = await async_client.get(endpoint)
            # Should return 401 (Unauthorized) without token
            status = "✅" if response.status_code == 401 else "❌"
            print(f"  {status} {name}: {endpoint} (HTTP {response.status_code})")
            assert response.status_code == 401, f"{name} should require auth"

        print("\n✅ All API endpoints verified!")
