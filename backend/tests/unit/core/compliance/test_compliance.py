from unittest.mock import MagicMock, patch

import pytest

from backend.core.auth.oauth_config import OAuthConfig
from backend.core.database import receive_before_cursor_execute
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

    def test_rls_injection(self):
        # Test the event listener logic

        # Mock connection
        mock_conn = MagicMock()

        # 1. Context set
        with patch(
            "backend.core.database.get_current_tenant_optional",
            return_value="tenant_123",
        ):
            receive_before_cursor_execute(mock_conn, None, None, None, None, None)

            # Should have called execute with SET app.current_tenant
            mock_conn.execute.assert_called()
            args, kwargs = mock_conn.execute.call_args

            # Verify the SQL text
            assert "SET app.current_tenant" in str(args[0])

            # Verify the parameters.
            # SQLAlchemy execution might pass params as the second positional arg OR as kwargs.
            # In our implementation: conn.execute(text(...), {"tenant_id": ...})
            # So it's likely the second positional argument.
            if len(args) > 1:
                assert args[1]["tenant_id"] == "tenant_123"
            else:
                # If passed as kwargs (less likely for core execute but possible in some mocks)
                assert kwargs["tenant_id"] == "tenant_123"

        # 2. No context
        mock_conn.reset_mock()
        with patch("backend.core.database.get_current_tenant_optional", return_value=None):
            receive_before_cursor_execute(mock_conn, None, None, None, None, None)

            # Should NOT have called execute (or handled gracefully)
            mock_conn.execute.assert_not_called()
