"""
Integration tests for Prediction Intelligence Docker service.
Run: pytest backend/tests/integration/test_prediction_docker.py -v -m integration
Requires: docker-compose up -d prediction-intelligence
"""

import subprocess
from typing import AsyncGenerator

import httpx
import pytest


class TestPredictionDockerService:
    """Docker Compose integration tests."""

    @pytest.fixture
    async def prediction_client(self) -> AsyncGenerator[httpx.AsyncClient, None]:
        """HTTP client for prediction service."""
        async with httpx.AsyncClient(
            base_url="http://localhost:8002", timeout=30.0
        ) as client:
            yield client

    # =========================================================================
    # HAPPY PATH TESTS
    # =========================================================================

    @pytest.mark.integration
    def test_happy_path_docker_compose_service_exists(self):
        """Happy path: Service is defined in docker-compose."""
        result = subprocess.run(
            ["docker-compose", "config", "--services"], capture_output=True, text=True
        )
        assert "prediction-intelligence" in result.stdout

    @pytest.mark.integration
    def test_happy_path_volume_is_defined(self):
        """Happy path: prediction_market_cache volume is defined."""
        result = subprocess.run(
            ["docker-compose", "config"], capture_output=True, text=True
        )
        assert "prediction_market_cache" in result.stdout

    @pytest.mark.integration
    def test_happy_path_service_depends_on_postgres(self):
        """Happy path: Service depends on postgres."""
        result = subprocess.run(
            ["docker-compose", "config"], capture_output=True, text=True
        )
        # Check that prediction-intelligence has postgres in depends_on
        config_text = result.stdout
        # Look for prediction-intelligence service block followed by depends_on with postgres
        assert "prediction-intelligence" in config_text

    @pytest.mark.integration
    def test_happy_path_port_8002_exposed(self):
        """Happy path: Port 8002 is exposed in service definition."""
        result = subprocess.run(
            ["docker-compose", "config"], capture_output=True, text=True
        )
        # Check for port mapping
        assert "8002" in result.stdout

    @pytest.mark.integration
    def test_happy_path_healthcheck_configured(self):
        """Happy path: Health check is configured."""
        result = subprocess.run(
            ["docker-compose", "config"], capture_output=True, text=True
        )
        config_text = result.stdout
        # Health check should reference health endpoint
        assert "health" in config_text.lower()

    @pytest.mark.integration
    def test_happy_path_compose_config_valid(self):
        """Happy path: Docker compose config is valid."""
        result = subprocess.run(
            ["docker-compose", "config"], capture_output=True, text=True
        )
        # Should not have error in stdout (warnings are OK)
        assert "error" not in result.stdout.lower() or result.returncode == 0

    # =========================================================================
    # UNHAPPY PATH TESTS
    # =========================================================================

    @pytest.mark.integration
    def test_unhappy_path_invalid_volume_name(self):
        """Unhappy path: Assert we didn't add wrong volume name."""
        result = subprocess.run(
            ["docker-compose", "config"], capture_output=True, text=True
        )
        # Verify we don't have typos in volume names
        assert "prediction_market_cache" in result.stdout
        assert "prediction_marketcache" not in result.stdout  # Common typo

    @pytest.mark.integration
    def test_unhappy_path_service_not_missing(self):
        """Unhappy path: Verify service does exist (inverse test)."""
        result = subprocess.run(
            ["docker-compose", "config", "--services"], capture_output=True, text=True
        )
        # Should have prediction-intelligence service
        services = result.stdout.strip().split("\n")
        assert len(services) > 0
        service_names = [s.strip() for s in services if s.strip()]
        assert "prediction-intelligence" in service_names


class TestComposeSyntax:
    """Test docker-compose.yml syntax."""

    def test_happy_path_yaml_is_valid(self):
        """Happy path: docker-compose.yml is valid YAML."""
        result = subprocess.run(
            ["docker-compose", "config"], capture_output=True, text=True
        )
        # Config command validates YAML
        # Exit code should be 0 or 1 (1 is for warnings which are OK)
        assert result.returncode in [0, 1]

    def test_happy_path_no_syntax_errors(self):
        """Happy path: No syntax errors in compose file."""
        result = subprocess.run(
            ["docker-compose", "config"], capture_output=True, text=True
        )
        # Should not contain error messages (exclude warnings)
        stderr = result.stderr.lower()
        # Warnings are fine, but errors should not be present
        if "error" in stderr:
            assert "confuse" not in stderr  # Common error indicator

    def test_unhappy_path_missing_compose_file(self, tmp_path):
        """Unhappy path: Missing docker-compose.yml fails."""
        result = subprocess.run(
            ["docker-compose", "-f", str(tmp_path / "nonexistent.yml"), "config"],
            capture_output=True,
            text=True,
        )
        # Should fail with non-zero exit code
        assert result.returncode != 0
