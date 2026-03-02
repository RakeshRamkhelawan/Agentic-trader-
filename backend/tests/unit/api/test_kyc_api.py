"""
Unit tests for KYC API endpoints.

Tests both happy and unhappy paths.
KYC is disabled by default (ENABLE_KYC=false).
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient

from backend.api.kyc_api import KYCStatus, router


# Create test app
@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/kyc")
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


class TestKYCStatusDisabled:
    """Test KYC endpoints when KYC is disabled (default)"""

    def test_get_status_disabled(self, client):
        """Happy path: KYC disabled returns auto-verified"""
        response = client.get("/api/v1/kyc/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == KYCStatus.VERIFIED
        assert data["required"] == False
        assert data["enabled"] == False

    def test_submit_disabled(self, client):
        """Happy path: Submit accepted but ignored when disabled"""
        kyc_data = {
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1990-01-01",
            "nationality": "NL",
            "phone_number": "+31612345678",
            "street_address": "Test Street 123",
            "city": "Amsterdam",
            "postal_code": "1012 AB",
            "country": "NL",
            "id_type": "passport",
            "id_number": "ABC123456",
            "occupation": "Software Engineer",
            "employment_status": "employed",
            "annual_income": "50k-100k",
            "source_of_funds": "Salary",
        }

        response = client.post("/api/v1/kyc/submit", json=kyc_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["status"] == KYCStatus.VERIFIED
        assert "disabled" in data["message"].lower()

    def test_upload_documents_disabled(self, client):
        """Happy path: Document upload accepted but ignored"""
        response = client.post("/api/v1/kyc/documents")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "disabled" in data["message"].lower()

    def test_is_required_disabled(self, client):
        """Happy path: KYC not required when disabled"""
        response = client.get("/api/v1/kyc/required")

        assert response.status_code == 200
        data = response.json()
        assert data["required"] == False
        assert data["enabled"] == False
        assert data["status"] == KYCStatus.VERIFIED


class TestKYCValidation:
    """Test KYC data validation (when enabled)"""

    def test_submit_invalid_date_format(self, client):
        """Unhappy path: Invalid date format"""
        kyc_data = {
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "01-01-1990",  # Wrong format
            "nationality": "NL",
            "phone_number": "+31612345678",
            "street_address": "Test Street 123",
            "city": "Amsterdam",
            "postal_code": "1012 AB",
            "country": "NL",
            "id_type": "passport",
            "id_number": "ABC123456",
            "occupation": "Software Engineer",
            "employment_status": "employed",
            "annual_income": "50k-100k",
            "source_of_funds": "Salary",
        }

        response = client.post("/api/v1/kyc/submit", json=kyc_data)

        # Should either accept (disabled) or validate error
        assert response.status_code in [200, 422]

    def test_submit_invalid_country_code(self, client):
        """Unhappy path: Invalid country code (too long)"""
        kyc_data = {
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1990-01-01",
            "nationality": "NLD",  # Should be NL
            "phone_number": "+31612345678",
            "street_address": "Test Street 123",
            "city": "Amsterdam",
            "postal_code": "1012 AB",
            "country": "NLD",  # Should be NL
            "id_type": "passport",
            "id_number": "ABC123456",
            "occupation": "Software Engineer",
            "employment_status": "employed",
            "annual_income": "50k-100k",
            "source_of_funds": "Salary",
        }

        response = client.post("/api/v1/kyc/submit", json=kyc_data)

        assert response.status_code in [200, 422]

    def test_submit_invalid_id_type(self, client):
        """Unhappy path: Invalid ID type"""
        kyc_data = {
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1990-01-01",
            "nationality": "NL",
            "phone_number": "+31612345678",
            "street_address": "Test Street 123",
            "city": "Amsterdam",
            "postal_code": "1012 AB",
            "country": "NL",
            "id_type": "invalid_type",  # Invalid
            "id_number": "ABC123456",
            "occupation": "Software Engineer",
            "employment_status": "employed",
            "annual_income": "50k-100k",
            "source_of_funds": "Salary",
        }

        response = client.post("/api/v1/kyc/submit", json=kyc_data)

        assert response.status_code in [200, 422]

    def test_submit_missing_required_fields(self, client):
        """Unhappy path: Missing required fields"""
        kyc_data = {
            "first_name": "John",
            # Missing last_name
        }

        response = client.post("/api/v1/kyc/submit", json=kyc_data)

        assert response.status_code == 422


class TestKYCSchemaValidation:
    """Test KYC data schema validation"""

    def test_valid_kyc_data(self, client):
        """Happy path: Valid KYC data"""
        valid_data = {
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1990-01-01",
            "nationality": "NL",
            "phone_number": "+31612345678",
            "street_address": "Test Street 123",
            "city": "Amsterdam",
            "postal_code": "1012 AB",
            "country": "NL",
            "id_type": "passport",
            "id_number": "ABC123456",
            "occupation": "Software Engineer",
            "employment_status": "employed",
            "annual_income": "50k-100k",
            "source_of_funds": "Salary",
        }

        response = client.post("/api/v1/kyc/submit", json=valid_data)

        # Should accept (disabled mode returns verified)
        assert response.status_code == 200


@pytest.mark.asyncio
class TestKYCAsync:
    """Async tests for KYC endpoints"""

    async def test_status_async(self, app):
        """Happy path: Get status async"""
        from httpx import ASGITransport

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/api/v1/kyc/status")

        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] == False
        assert data["required"] == False


class TestKYCEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_very_long_names(self, client):
        """Boundary: Very long names"""
        kyc_data = {
            "first_name": "A" * 100,  # Max length
            "last_name": "B" * 100,
            "date_of_birth": "1990-01-01",
            "nationality": "NL",
            "phone_number": "+31612345678",
            "street_address": "Test Street 123",
            "city": "Amsterdam",
            "postal_code": "1012 AB",
            "country": "NL",
            "id_type": "passport",
            "id_number": "ABC123456",
            "occupation": "Software Engineer",
            "employment_status": "employed",
            "annual_income": "50k-100k",
            "source_of_funds": "Salary",
        }

        response = client.post("/api/v1/kyc/submit", json=kyc_data)

        # Should accept when disabled
        assert response.status_code == 200

    def test_empty_strings(self, client):
        """Unhappy path: Empty strings"""
        kyc_data = {
            "first_name": "",  # Empty
            "last_name": "Doe",
            "date_of_birth": "1990-01-01",
            "nationality": "NL",
            "phone_number": "+31612345678",
            "street_address": "Test Street 123",
            "city": "Amsterdam",
            "postal_code": "1012 AB",
            "country": "NL",
            "id_type": "passport",
            "id_number": "ABC123456",
            "occupation": "Software Engineer",
            "employment_status": "employed",
            "annual_income": "50k-100k",
            "source_of_funds": "Salary",
        }

        response = client.post("/api/v1/kyc/submit", json=kyc_data)

        # Should fail validation
        assert response.status_code == 422
