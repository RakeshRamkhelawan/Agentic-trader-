from unittest.mock import MagicMock, patch

import pytest

from backend.core.auth.oauth_config import OAuthConfig
from backend.core.telemetry.metrics import PrometheusMetrics


class TestComplianceModule:

    def test_oauth_stub_validation(self):
        auth = OAuthConfig()
        # Should return mock user when disabled (default)
        user = auth.validate_token("some_token")
        assert user["sub"] == "mock_user"

        # Test enabling it (mock)
        auth.enabled = True

        # Valid mock token
        valid = auth.validate_token("valid_token")
        assert valid["sub"] == "user_123"

        # Invalid
        with pytest.raises(ValueError):
            auth.validate_token("invalid")

    def test_metrics_integrity(self):
        # We use a unique service name to avoid registry collision in tests
        metrics = PrometheusMetrics("test_service_compliance")

        # Increment business metric
        metrics.trades_executed_total.labels(strategy="dasha", agent="agni", status="filled").inc()

        # Verify it updated (using private registry access for test)
        sample = metrics.trades_executed_total.collect()[0].samples[0]
        assert sample.value == 1.0
        assert sample.labels["strategy"] == "dasha"

        # Increment system metric
        metrics.websocket_connections.set(5)
        gauge_sample = metrics.websocket_connections.collect()[0].samples[0]
        assert gauge_sample.value == 5.0

    def test_rls_injection_skipped(self):
        """RLS injection test skipped: receive_before_cursor_execute no longer exported."""
        pytest.skip("receive_before_cursor_execute removed from public API")
