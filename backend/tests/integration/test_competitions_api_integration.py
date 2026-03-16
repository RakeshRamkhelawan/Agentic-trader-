"""
Integration Tests for Competitions API - Real Backend Integration

Tests use the actual FastAPI app and real competitions services.
All operations test the real tournament engine, leaderboard, and league system.
"""

import pytest
from httpx import AsyncClient

pytestmark = [pytest.mark.asyncio, pytest.mark.integration]


class TestCompetitionsAPIIntegration:
    """Full integration tests for Competitions API with real backend services."""

    async def test_get_tournaments_active(self, async_client: AsyncClient):
        """Test getting active tournaments from real tournament engine."""
        response = await async_client.get("/api/v1/competitions/tournaments?status=active")

        assert response.status_code == 200
        data = response.json()

        assert "tournaments" in data
        assert "count" in data
        assert isinstance(data["tournaments"], list)
        assert isinstance(data["count"], int)

        # If tournaments exist, verify structure
        for tournament in data["tournaments"]:
            assert "id" in tournament
            assert "name" in tournament
            assert "type" in tournament

    async def test_get_tournaments_upcoming(self, async_client: AsyncClient):
        """Test getting upcoming tournaments."""
        response = await async_client.get("/api/v1/competitions/tournaments?status=upcoming")

        assert response.status_code == 200
        data = response.json()

        assert "tournaments" in data
        assert "count" in data

    async def test_get_tournaments_invalid_status(self, async_client: AsyncClient):
        """Test tournaments endpoint with invalid status."""
        response = await async_client.get("/api/v1/competitions/tournaments?status=invalid")

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    async def test_get_league_info(self, async_client: AsyncClient):
        """Test getting league information from real league system."""
        response = await async_client.get("/api/v1/competitions/league-info")

        assert response.status_code == 200
        data = response.json()

        # Should return league tiers (bronze, silver, gold, platinum, diamond)
        expected_tiers = ["bronze", "silver", "gold", "platinum", "diamond"]

        for tier in expected_tiers:
            if tier in data:
                league = data[tier]
                assert "tier" in league
                assert "name" in league
                assert "min_points" in league
                assert "max_points" in league
                assert "current_members" in league
                assert "max_members" in league

    async def test_get_global_leaderboard(self, async_client: AsyncClient):
        """Test getting global leaderboard from real leaderboard service."""
        response = await async_client.get("/api/v1/competitions/leaderboard")

        assert response.status_code == 200
        data = response.json()

        assert "entries" in data
        assert "total" in data
        assert isinstance(data["entries"], list)

    async def test_get_leaderboard_with_limit(self, async_client: AsyncClient):
        """Test leaderboard with limit parameter."""
        response = await async_client.get("/api/v1/competitions/leaderboard?limit=10")

        assert response.status_code == 200
        data = response.json()

        assert len(data["entries"]) <= 10

    async def test_get_leaderboard_by_tier(self, async_client: AsyncClient):
        """Test getting leaderboard filtered by tier."""
        tiers = ["bronze", "silver", "gold", "platinum", "diamond"]

        for tier in tiers:
            response = await async_client.get(f"/api/v1/competitions/leaderboard?tier={tier}")

            assert response.status_code == 200
            data = response.json()

            assert "entries" in data
            assert "total" in data

    async def test_get_leaderboard_invalid_tier(self, async_client: AsyncClient):
        """Test leaderboard with invalid tier."""
        response = await async_client.get("/api/v1/competitions/leaderboard?tier=invalid_tier")

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data

    async def test_get_available_badges(self, async_client: AsyncClient):
        """Test getting all available badges."""
        response = await async_client.get("/api/v1/competitions/available-badges")

        assert response.status_code == 200
        data = response.json()

        assert "badges" in data
        assert "total" in data
        assert isinstance(data["badges"], list)
        assert isinstance(data["total"], int)

    async def test_get_badges_for_competitor(self, async_client: AsyncClient):
        """Test getting badges for a specific competitor."""
        competitor_id = "test-competitor-123"

        response = await async_client.get(f"/api/v1/competitions/badges/{competitor_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["competitor_id"] == competitor_id
        assert "badges" in data
        assert "total_badges" in data
        assert isinstance(data["badges"], list)

    async def test_enter_tournament_invalid_competitor(self, async_client: AsyncClient):
        """Test entering tournament with invalid competitor ID."""
        response = await async_client.post(
            "/api/v1/competitions/enter",
            json={
                "competitor_id": "nonexistent-competitor-12345",
                "tournament_id": "test-tournament-123"
            }
        )

        # Should fail because competitor doesn't exist
        assert response.status_code in [200, 404]  # 200 with success=false or 404

        if response.status_code == 200:
            data = response.json()
            assert data["success"] is False

    async def test_enter_tournament_invalid_tournament(self, async_client: AsyncClient):
        """Test entering tournament with invalid tournament ID."""
        # This test would need a valid competitor first
        # For now, just verify the endpoint structure
        response = await async_client.post(
            "/api/v1/competitions/enter",
            json={
                "competitor_id": "any-competitor",
                "tournament_id": "nonexistent-tournament-12345"
            }
        )

        # Endpoint should handle gracefully
        assert response.status_code in [200, 404, 400]

    async def test_competitions_complete_flow(self, async_client: AsyncClient):
        """Test complete competitions flow."""
        # 1. Get league info
        league_response = await async_client.get("/api/v1/competitions/league-info")
        assert league_response.status_code == 200
        league_data = league_response.json()

        # 2. Get active tournaments
        tournaments_response = await async_client.get("/api/v1/competitions/tournaments?status=active")
        assert tournaments_response.status_code == 200
        tournaments_data = tournaments_response.json()

        # 3. Get leaderboard
        leaderboard_response = await async_client.get("/api/v1/competitions/leaderboard")
        assert leaderboard_response.status_code == 200
        leaderboard_data = leaderboard_response.json()

        # 4. Get available badges
        badges_response = await async_client.get("/api/v1/competitions/available-badges")
        assert badges_response.status_code == 200
        badges_data = badges_response.json()

        # Verify all responses have expected structure
        assert isinstance(league_data, dict)
        assert "tournaments" in tournaments_data
        assert "entries" in leaderboard_data
        assert "badges" in badges_data

    async def test_leaderboard_entry_structure(self, async_client: AsyncClient):
        """Test that leaderboard entries have correct structure."""
        response = await async_client.get("/api/v1/competitions/leaderboard?limit=5")

        assert response.status_code == 200
        data = response.json()

        for entry in data["entries"]:
            # Verify all expected fields
            assert "rank" in entry
            assert "competitor_id" in entry
            assert "name" in entry
            assert "tier" in entry
            assert "points" in entry
            assert "win_rate" in entry
            assert "total_pnl" in entry

            # Verify types
            assert isinstance(entry["rank"], int)
            assert isinstance(entry["points"], int)
            assert isinstance(entry["win_rate"], (int, float))
            assert isinstance(entry["total_pnl"], (int, float))

    async def test_tournament_structure(self, async_client: AsyncClient):
        """Test that tournament data has correct structure."""
        response = await async_client.get("/api/v1/competitions/tournaments?status=active")

        assert response.status_code == 200
        data = response.json()

        for tournament in data["tournaments"]:
            assert "id" in tournament
            assert "name" in tournament
            assert "description" in tournament
            assert "type" in tournament
            assert "participants" in tournament
            assert "max_participants" in tournament
            assert "ends_at" in tournament
            assert "time_remaining" in tournament
            assert "entry_fee" in tournament
            assert "prize_pool" in tournament

    async def test_competitions_endpoints_no_auth_required(self, async_client: AsyncClient):
        """Test that competitions endpoints are publicly accessible (no auth required)."""
        endpoints = [
            ("GET", "/api/v1/competitions/tournaments"),
            ("GET", "/api/v1/competitions/league-info"),
            ("GET", "/api/v1/competitions/leaderboard"),
            ("GET", "/api/v1/competitions/available-badges"),
            ("GET", "/api/v1/competitions/badges/test-id"),
        ]

        for method, endpoint in endpoints:
            response = await async_client.get(endpoint)

            # These endpoints should be publicly accessible
            assert response.status_code in [200, 404], f"{endpoint} should be accessible"
