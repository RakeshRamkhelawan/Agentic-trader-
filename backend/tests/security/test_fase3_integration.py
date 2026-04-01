"""
Fase 3 Integration Tests - Architecture & Tech Debt Fixes

Tests for:
- Taak 3.1: RLS uses pool checkin event instead of before_cursor_execute
- Taak 3.2: Trading mode is configuration-driven with double opt-in
- Taak 3.3: pytest.ini has strict markers and DeprecationWarning errors
- Taak 3.4: Nginx has HSTS and CSP headers
- Taak 3.5: K8s deployment uses immutable image tags

Run with: pytest backend/tests/security/test_fase3_integration.py -v
"""

import os

# ============================================================================
# Taak 3.1: RLS Pool Lifecycle Tests (database.py)
# ============================================================================


class TestRLSPoolLifecycle:
    """Verify RLS uses pool events, not before_cursor_execute."""

    def test_no_before_cursor_execute_listener(self):
        """database.py must NOT register a before_cursor_execute event listener."""
        db_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "core", "database.py"
        )
        with open(db_path) as f:
            content = f.read()

        # Check for the actual event listener registration, not comments about it
        assert (
            "@event.listens_for" not in content
            or "before_cursor_execute"
            not in content.split("@event.listens_for")[-1].split("\n")[0]
            if "@event.listens_for" in content
            else True
        )
        assert (
            'listens_for(Engine, "before_cursor_execute")' not in content
        ), "database.py still registers a before_cursor_execute event listener."

    def test_pool_checkin_event_exists(self):
        """database.py must have a pool checkin event listener."""
        db_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "core", "database.py"
        )
        with open(db_path) as f:
            content = f.read()

        assert "checkin" in content, "Missing pool checkin event listener"
        assert "set_config" in content, "Checkin must clear tenant via set_config"


# ============================================================================
# Taak 3.2: Trading Mode Configuration Tests (main.py)
# ============================================================================


class TestTradingModeConfiguration:
    """Verify trading mode is configuration-driven."""

    def test_main_supports_multiple_modes(self):
        """main.py must validate against paper/live/backtest modes."""
        main_path = os.path.join(os.path.dirname(__file__), "..", "..", "main.py")
        with open(main_path) as f:
            content = f.read()

        assert "paper" in content, "Missing paper mode support"
        assert "live" in content, "Missing live mode support"
        assert "backtest" in content, "Missing backtest mode support"

    def test_live_mode_requires_double_opt_in(self):
        """Live trading requires ENABLE_LIVE_TRADING=true."""
        main_path = os.path.join(os.path.dirname(__file__), "..", "..", "main.py")
        with open(main_path) as f:
            content = f.read()

        assert (
            "ENABLE_LIVE_TRADING" in content
        ), "Missing ENABLE_LIVE_TRADING double opt-in for live mode"

    def test_no_hardcoded_paper_only_check(self):
        """main.py must NOT have hardcoded 'paper only' check."""
        main_path = os.path.join(os.path.dirname(__file__), "..", "..", "main.py")
        with open(main_path) as f:
            content = f.read()

        assert (
            "ONLY configured for paper trading" not in content
        ), "Still has hardcoded paper-only message. Should support multiple modes."


# ============================================================================
# Taak 3.3: pytest.ini Hardening Tests
# ============================================================================


class TestPytestIniHardening:
    """Verify pytest.ini has strict configuration."""

    def test_strict_markers_enabled(self):
        """pytest.ini must have --strict-markers."""
        ini_path = os.path.join(os.path.dirname(__file__), "..", "..", "pytest.ini")
        with open(ini_path) as f:
            content = f.read()

        assert "--strict-markers" in content, "Missing --strict-markers"

    def test_deprecation_warnings_filtered(self):
        """pytest.ini must handle DeprecationWarnings."""
        ini_path = os.path.join(os.path.dirname(__file__), "..", "..", "pytest.ini")
        with open(ini_path) as f:
            content = f.read()

        assert "filterwarnings" in content, "Missing filterwarnings section"

    def test_security_marker_defined(self):
        """pytest.ini must define 'security' marker."""
        ini_path = os.path.join(os.path.dirname(__file__), "..", "..", "pytest.ini")
        with open(ini_path) as f:
            content = f.read()

        assert "security" in content, "Missing 'security' marker definition"


# ============================================================================
# Taak 3.4: Nginx Security Headers Tests
# ============================================================================


class TestNginxSecurityHeaders:
    """Verify Nginx has HSTS and CSP headers."""

    def _read_nginx_conf(self):
        nginx_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "infrastructure",
            "docker",
            "nginx.conf",
        )
        with open(nginx_path) as f:
            return f.read()

    def test_hsts_header_present(self):
        """Nginx must have Strict-Transport-Security header."""
        content = self._read_nginx_conf()
        assert "Strict-Transport-Security" in content, "Missing HSTS header"
        assert "max-age=" in content, "HSTS missing max-age directive"

    def test_csp_header_present(self):
        """Nginx must have Content-Security-Policy header."""
        content = self._read_nginx_conf()
        assert "Content-Security-Policy" in content, "Missing CSP header"
        assert "default-src" in content, "CSP missing default-src directive"

    def test_x_frame_options_deny(self):
        """X-Frame-Options must be DENY, not SAMEORIGIN."""
        content = self._read_nginx_conf()
        assert '"DENY"' in content, "X-Frame-Options should be DENY for trading app"
        assert '"SAMEORIGIN"' not in content, "X-Frame-Options should NOT be SAMEORIGIN"


# ============================================================================
# Taak 3.5: K8s Immutable Image Tags Tests
# ============================================================================


class TestK8sImmutableImageTags:
    """Verify K8s deployment uses immutable image tags."""

    def _read_deployment(self):
        k8s_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "infrastructure",
            "k8s",
            "deployment.yaml",
        )
        with open(k8s_path) as f:
            return f.read()

    def test_no_latest_tag(self):
        """K8s deployment must NOT use :latest tag."""
        content = self._read_deployment()
        assert (
            ":latest" not in content
        ), "K8s deployment still uses :latest tag. Use immutable tags."

    def test_image_pull_policy_not_always(self):
        """imagePullPolicy should be IfNotPresent for immutable tags."""
        content = self._read_deployment()
        assert (
            "imagePullPolicy: Always" not in content
        ), "imagePullPolicy should be IfNotPresent for immutable tags"
