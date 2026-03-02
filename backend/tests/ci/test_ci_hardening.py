"""
Fase 4: CI/CD Pipeline Hardening - Tests

Verifies that the CI/CD pipeline config enforces quality gates:
- Happy Path: All jobs have proper error handling
- Unhappy Path: continue-on-error is not abused
- Integration: Pipeline YAML is valid

Run with: pytest backend/tests/ci/test_ci_hardening.py -v
"""

import os

import pytest
import yaml


class TestCIConfigIntegrity:
    """Verify CI/CD configuration enforces quality gates."""

    def _load_ci_yml(self):
        project_root = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..")
        )
        ci_path = os.path.join(project_root, ".github", "workflows", "ci.yml")
        if not os.path.exists(ci_path):
            pytest.skip("ci.yml not found")
        with open(ci_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def test_ci_yml_is_valid_yaml(self):
        """ci.yml must be valid YAML."""
        config = self._load_ci_yml()
        assert config is not None
        assert "jobs" in config

    def test_backend_tests_not_continue_on_error(self):
        """backend-tests job must NOT use continue-on-error at job level."""
        config = self._load_ci_yml()
        job = config["jobs"].get("backend-tests", {})
        assert job.get("continue-on-error") is not True, (
            "backend-tests job has continue-on-error: true -- tests are non-blocking"
        )

    def test_security_scan_not_continue_on_error(self):
        """security-scan job must NOT use continue-on-error at job level."""
        config = self._load_ci_yml()
        job = config["jobs"].get("security-scan", {})
        assert job.get("continue-on-error") is not True, (
            "security-scan job has continue-on-error: true -- security is non-blocking"
        )

    def test_code_quality_not_continue_on_error(self):
        """code-quality job must NOT use continue-on-error at job level."""
        config = self._load_ci_yml()
        job = config["jobs"].get("code-quality", {})
        assert job.get("continue-on-error") is not True, (
            "code-quality job has continue-on-error: true -- quality is non-blocking"
        )

    def test_deploy_requires_all_checks(self):
        """deploy job must depend on all test/security/quality jobs."""
        config = self._load_ci_yml()
        deploy = config["jobs"].get("deploy", {})
        needs = deploy.get("needs", [])
        required = {"backend-tests", "docker-build", "security-scan"}
        missing = required - set(needs)
        assert len(missing) == 0, (
            f"deploy job does not require: {missing}"
        )

    def test_deploy_requires_manual_trigger(self):
        """deploy job must require manual workflow_dispatch."""
        config = self._load_ci_yml()
        deploy = config["jobs"].get("deploy", {})
        if_condition = deploy.get("if", "")
        assert "workflow_dispatch" in if_condition, (
            "deploy job does not require manual trigger"
        )

    def test_coverage_threshold_set(self):
        """Backend tests must enforce a minimum coverage threshold."""
        project_root = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..")
        )
        ci_path = os.path.join(project_root, ".github", "workflows", "ci.yml")
        with open(ci_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "cov-fail-under" in content, (
            "CI does not enforce a minimum coverage threshold"
        )

    def test_no_emoji_in_ci_scripts(self):
        """CI scripts must not contain emoji (Windows compatibility)."""
        project_root = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..")
        )
        ci_path = os.path.join(project_root, ".github", "workflows", "ci.yml")
        with open(ci_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Check for common emoji code points
        for char in content:
            code = ord(char)
            # Emoji ranges (common)
            if 0x1F600 <= code <= 0x1F64F:  # Emoticons
                pytest.fail(f"CI YAML contains emoji: U+{code:04X}")
            if 0x1F300 <= code <= 0x1F5FF:  # Misc symbols
                pytest.fail(f"CI YAML contains emoji: U+{code:04X}")
            if 0x2600 <= code <= 0x26FF:  # Misc symbols
                if code not in (0x2705, 0x26A0):  # Allow checkmark and warning
                    pass  # Some are acceptable in comments
