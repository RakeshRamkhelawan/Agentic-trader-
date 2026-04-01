"""
Integration Tests for KYC API - Real Backend Integration

Tests use the actual FastAPI app and real database.
KYC is disabled by default (ENABLE_KYC=false), so tests verify both disabled and enabled behaviors.
"""

import os

import pytest
from httpx import AsyncClient

pytestmark = [pytest.mark.asyncio, pytest.mark.integration]


class TestKYCAPIIntegration:
    """Full integration tests for KYC API with real backend."""

    async def test_kyc_status_disabled_by_default(self, async_client: AsyncClient):
        """Test that KYC returns auto-verified status when disabled."""
        # KYC is disabled by default (ENABLE_KYC=false)
        response = await async_client.get("/api/v1/kyc/status")

        assert response.status_code == 200
        data = response.json()

        # When disabled, should return auto-verified
        assert data["status"] == "verified"
        assert data["required"] is False
        assert data["enabled"] is False

    async def test_kyc_required_disabled_by_default(self, async_client: AsyncClient):
        """Test that KYC required check returns false when disabled."""
        response = await async_client.get("/api/v1/kyc/required")

        assert response.status_code == 200
        data = response.json()

        assert data["required"] is False
        assert data["enabled"] is False
        assert data["status"] == "verified"

    async def test_kyc_submit_disabled_by_default(self, async_client: AsyncClient):
        """Test that KYC submit accepts but ignores data when disabled."""
        kyc_data = {
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1990-01-15",
            "nationality": "US",
            "phone_number": "+1234567890",
            "street_address": "123 Test Street",
            "city": "New York",
            "postal_code": "10001",
            "country": "US",
            "id_type": "passport",
            "id_number": "AB123456",
            "occupation": "Software Engineer",
            "employment_status": "employed",
            "annual_income": "50k-100k",
            "source_of_funds": "Salary",
        }

        response = await async_client.post("/api/v1/kyc/submit", json=kyc_data)

        assert response.status_code == 200
        data = response.json()

        # When disabled, should accept but indicate it's disabled
        assert data["success"] is True
        assert "disabled" in data["message"].lower() or "KYC submitted" in data["message"]
        assert data["status"] == "verified"

    async def test_kyc_submit_validation_error(self, async_client: AsyncClient):
        """Test KYC submit with invalid data returns validation error."""
        invalid_data = {
            "first_name": "",  # Empty - should fail
            "last_name": "Doe",
            "date_of_birth": "invalid-date",  # Wrong format
            "nationality": "USA",  # Should be 2 chars
            "phone_number": "+1234567890",
            "street_address": "123 Test Street",
            "city": "New York",
            "postal_code": "10001",
            "country": "US",
            "id_type": "invalid_type",  # Should be passport, drivers_license, or national_id
            "id_number": "AB123456",
            "occupation": "Engineer",
            "employment_status": "invalid_status",  # Should be specific values
            "annual_income": "invalid",
            "source_of_funds": "Salary",
        }

        response = await async_client.post("/api/v1/kyc/submit", json=invalid_data)

        assert response.status_code == 422  # Validation error

    async def test_kyc_document_upload_disabled(self, async_client: AsyncClient):
        """Test document upload endpoint when KYC is disabled."""
        # Create a test file
        files = {"id_front": ("test.jpg", b"fake_image_data", "image/jpeg")}

        response = await async_client.post("/api/v1/kyc/documents", files=files)

        assert response.status_code == 200
        data = response.json()

        # When disabled, should accept but indicate it's disabled
        assert data["success"] is True
        assert "disabled" in data["message"].lower()

    async def test_kyc_document_upload_invalid_file_type(self, async_client: AsyncClient):
        """Test document upload with invalid file type."""
        files = {"id_front": ("test.txt", b"not an image", "text/plain")}

        response = await async_client.post("/api/v1/kyc/documents", files=files)

        # Should either succeed with warning (disabled mode) or fail validation
        assert response.status_code in [200, 400]

    async def test_kyc_complete_flow_when_disabled(self, async_client: AsyncClient):
        """Test complete KYC flow when KYC is disabled (default behavior)."""
        # Step 1: Check if KYC is required
        required_response = await async_client.get("/api/v1/kyc/required")
        assert required_response.status_code == 200
        required_data = required_response.json()

        # When disabled, should not be required
        assert required_data["required"] is False
        assert required_data["enabled"] is False

        # Step 2: Check status
        status_response = await async_client.get("/api/v1/kyc/status")
        assert status_response.status_code == 200
        status_data = status_response.json()

        assert status_data["status"] == "verified"
        assert status_data["enabled"] is False

        # Step 3: Submit KYC (should be auto-verified)
        kyc_data = {
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1990-01-15",
            "nationality": "US",
            "phone_number": "+1234567890",
            "street_address": "123 Test Street",
            "city": "New York",
            "postal_code": "10001",
            "country": "US",
            "id_type": "passport",
            "id_number": "AB123456",
            "occupation": "Software Engineer",
            "employment_status": "employed",
            "annual_income": "50k-100k",
            "source_of_funds": "Salary",
        }

        submit_response = await async_client.post("/api/v1/kyc/submit", json=kyc_data)
        assert submit_response.status_code == 200
        submit_data = submit_response.json()

        assert submit_data["success"] is True
        assert submit_data["status"] == "verified"

    @pytest.mark.skipif(
        os.getenv("ENABLE_KYC", "false").lower() != "true",
        reason="KYC is disabled - set ENABLE_KYC=true to run this test",
    )
    async def test_kyc_status_when_enabled(self, async_client: AsyncClient, unique_email: str):
        """Test KYC status when KYC is enabled (requires ENABLE_KYC=true)."""
        # This test only runs when KYC is explicitly enabled
        response = await async_client.get("/api/v1/kyc/status")

        assert response.status_code == 200
        data = response.json()

        # When enabled, should show actual status
        assert data["enabled"] is True
        assert data["required"] is True
        assert data["status"] in [
            "not_started",
            "in_progress",
            "pending_review",
            "verified",
            "rejected",
        ]

    @pytest.mark.skipif(
        os.getenv("ENABLE_KYC", "false").lower() != "true",
        reason="KYC is disabled - set ENABLE_KYC=true to run this test",
    )
    async def test_kyc_submit_when_enabled(self, async_client: AsyncClient, unique_email: str):
        """Test KYC submission when KYC is enabled (requires ENABLE_KYC=true)."""
        kyc_data = {
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1990-01-15",
            "nationality": "US",
            "phone_number": "+1234567890",
            "street_address": "123 Test Street",
            "city": "New York",
            "postal_code": "10001",
            "country": "US",
            "id_type": "passport",
            "id_number": "AB123456",
            "occupation": "Software Engineer",
            "employment_status": "employed",
            "annual_income": "50k-100k",
            "source_of_funds": "Salary",
        }

        response = await async_client.post("/api/v1/kyc/submit", json=kyc_data)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["status"] == "pending_review"

        # Verify status was updated
        status_response = await async_client.get("/api/v1/kyc/status")
        status_data = status_response.json()

        assert status_data["status"] == "pending_review"
        assert status_data["submitted_at"] is not None
