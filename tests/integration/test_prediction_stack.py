"""
Docker Stack Integration Tests for Prediction Market Intelligence.

These tests validate the full container stack is working correctly.
Run with: pytest tests/integration/test_prediction_stack.py -v --timeout=120
"""
import asyncio
import os
import subprocess
import time
from typing import Generator

import httpx
import pytest


# Test configuration
PREDICTION_SERVICE_URL = os.getenv("PREDICTION_SERVICE_URL", "http://localhost:8002")
API_SERVICE_URL = os.getenv("API_SERVICE_URL", "http://localhost:8003")
STARTUP_TIMEOUT = 60  # seconds
HEALTH_CHECK_INTERVAL = 2  # seconds


class TestDockerStackIntegration:
    """
    Integration tests for Docker stack.

    Prerequisites:
    - Docker and docker-compose installed
    - Stack started with: docker-compose up -d
    """

    @pytest.fixture(scope="class")
    def stack_ready(self) -> Generator[bool, None, None]:
        """
        Fixture that waits for stack to be ready.

        Waits for both prediction-intelligence and api-server
        to report healthy before running tests.
        """
        start_time = time.time()

        while time.time() - start_time < STARTUP_TIMEOUT:
            try:
                # Check prediction service
                pred_response = httpx.get(f"{PREDICTION_SERVICE_URL}/health", timeout=5)
                pred_healthy = pred_response.status_code == 200

                # Check main API
                api_response = httpx.get(f"{API_SERVICE_URL}/health", timeout=5)
                api_healthy = api_response.status_code == 200

                if pred_healthy and api_healthy:
                    yield True
                    return

            except httpx.RequestError:
                pass

            time.sleep(HEALTH_CHECK_INTERVAL)

        pytest.fail(f"Stack not ready after {STARTUP_TIMEOUT}s")

    # =========================================================================
    # HAPPY PATH TESTS
    # =========================================================================

    def test_happy_path_prediction_service_healthy(self, stack_ready):
        """Happy path: Prediction service is healthy."""
        response = httpx.get(f"{PREDICTION_SERVICE_URL}/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "prediction-intelligence"

    def test_happy_path_prediction_service_docs_available(self, stack_ready):
        """Happy path: OpenAPI docs zijn beschikbaar."""
        response = httpx.get(f"{PREDICTION_SERVICE_URL}/docs")
        assert response.status_code == 200

    def test_happy_path_signals_endpoint_works(self, stack_ready):
        """Happy path: Signals endpoint retourneert data."""
        response = httpx.get(f"{PREDICTION_SERVICE_URL}/api/v1/signals")

        assert response.status_code == 200
        data = response.json()
        assert "signals" in data
        assert isinstance(data["signals"], list)



    def test_happy_path_proxy_signals_works(self, stack_ready):
        """Happy path: Proxy signals endpoint werkt."""
        response = httpx.get(f"{API_SERVICE_URL}/api/v1/prediction/signals")

        assert response.status_code == 200
        data = response.json()
        assert "signals" in data

    def test_happy_path_analysis_can_be_triggered(self, stack_ready):
        """Happy path: Analysis kan getriggerd worden."""
        response = httpx.post(
            f"{PREDICTION_SERVICE_URL}/api/v1/analysis/run",
            json={
                "analysis_type": "maker_taker",
                "market": "kalshi"
            }
        )

        assert response.status_code == 202
        data = response.json()
        assert "analysis_id" in data

    # =========================================================================
    # UNHAPPY PATH TESTS
    # =========================================================================

    def test_unhappy_path_invalid_signal_id_returns_404(self, stack_ready):
        """Unhappy path: Invalid signal ID geeft 404."""
        response = httpx.get(
            f"{PREDICTION_SERVICE_URL}/api/v1/signals/nonexistent_id"
        )
        assert response.status_code == 404

    def test_unhappy_path_invalid_analysis_type_returns_422(self, stack_ready):
        """Unhappy path: Invalid analysis type geeft 422."""
        response = httpx.post(
            f"{PREDICTION_SERVICE_URL}/api/v1/analysis/run",
            json={
                "analysis_type": "invalid_type",
                "market": "kalshi"
            }
        )
        assert response.status_code == 422


class TestContainerNetworking:
    """Tests for container networking."""

    def test_happy_path_containers_on_same_network(self):
        """Happy path: Containers kunnen elkaar bereiken."""
        # This test runs inside docker-compose network
        # Verify DNS resolution works
        result = subprocess.run(
            ["docker-compose", "exec", "-T", "api-server",
             "python", "-c",
             "import socket; print(socket.gethostbyname('prediction-intelligence'))"],
            capture_output=True,
            text=True
        )

        # Should resolve to container IP, not fail
        assert result.returncode == 0 or "prediction-intelligence" in result.stdout


class TestDataFlow:
    """Tests for end-to-end data flow."""

    @pytest.fixture
    def async_client(self):
        """Async HTTP client."""
        return httpx.AsyncClient(timeout=30.0)

    @pytest.mark.asyncio
    async def test_happy_path_full_signal_flow(self, async_client):
        """
        Happy path: Complete signal flow van prediction -> main API.

        1. Trigger analysis op prediction service
        2. Wait for completion
        3. Fetch signals
        4. Verify signals via proxy API
        """
        # Step 1: Trigger analysis
        trigger_response = await async_client.post(
            f"{PREDICTION_SERVICE_URL}/api/v1/analysis/run",
            json={"analysis_type": "maker_taker", "market": "kalshi"}
        )
        assert trigger_response.status_code == 202
        analysis_id = trigger_response.json()["analysis_id"]

        # Step 2: Poll for completion (max 30 seconds)
        for _ in range(15):
            status_response = await async_client.get(
                f"{PREDICTION_SERVICE_URL}/api/v1/analysis/{analysis_id}"
            )
            status = status_response.json()

            if status["status"] in ["completed", "failed"]:
                break

            await asyncio.sleep(2)

        # Step 3: Get signals from prediction service
        pred_signals = await async_client.get(
            f"{PREDICTION_SERVICE_URL}/api/v1/signals?limit=5"
        )
        assert pred_signals.status_code == 200

        # Step 4: Verify signals via proxy
        proxy_signals = await async_client.get(
            f"{API_SERVICE_URL}/api/v1/prediction/signals?limit=5"
        )
        assert proxy_signals.status_code == 200

        # Both should return same structure
        pred_data = pred_signals.json()
        proxy_data = proxy_signals.json()

        assert "signals" in pred_data
        assert "signals" in proxy_data
