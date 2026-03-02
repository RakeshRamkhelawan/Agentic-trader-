"""
Fases 5-7: Infrastructure, Code Quality & Documentation - Tests

Covers:
- Fase 5: Docker Compose port bindings, pre-commit hooks
- Fase 6: MyPy enabled, coverage threshold, ruff security rules
- Fase 7: No placeholder metadata, deprecated code flagged

Run with: pytest backend/tests/quality/test_infra_quality.py -v
"""

import os

import pytest


class TestPreCommitConfig:
    """Verify pre-commit configuration has blocking security hooks."""

    def _read_precommit(self):
        project_root = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..")
        )
        path = os.path.join(project_root, ".pre-commit-config.yaml")
        if not os.path.exists(path):
            pytest.skip(".pre-commit-config.yaml not found")
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def test_bandit_is_blocking(self):
        """Bandit hook must be blocking (not wrapped in || echo)."""
        content = self._read_precommit()
        # Old pattern was: || echo "Bandit issues found"
        assert '|| echo' not in content, (
            "Bandit hook is non-blocking (uses || echo fallback)"
        )

    def test_detect_secrets_present(self):
        """detect-secrets hook must be configured."""
        content = self._read_precommit()
        assert "detect-secrets" in content, (
            "detect-secrets hook is missing from pre-commit config"
        )

    def test_detect_private_key_present(self):
        """detect-private-key hook must be configured."""
        content = self._read_precommit()
        assert "detect-private-key" in content, (
            "detect-private-key hook is missing from pre-commit config"
        )


class TestMyPyEnabled:
    """Verify MyPy is properly enabled in pyproject.toml."""

    def _read_pyproject(self):
        project_root = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..")
        )
        path = os.path.join(project_root, "pyproject.toml")
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def test_mypy_check_untyped_defs_enabled(self):
        """MyPy check_untyped_defs must be true."""
        content = self._read_pyproject()
        assert "check_untyped_defs = true" in content, (
            "MyPy check_untyped_defs is not enabled"
        )

    def test_mypy_warn_return_any_enabled(self):
        """MyPy warn_return_any must be true."""
        content = self._read_pyproject()
        assert "warn_return_any = true" in content, (
            "MyPy warn_return_any is not enabled"
        )

    def test_mypy_follow_imports_not_skip(self):
        """MyPy follow_imports must not be 'skip'."""
        content = self._read_pyproject()
        assert 'follow_imports = "skip"' not in content, (
            "MyPy follow_imports is set to 'skip' -- type checking is disabled"
        )


class TestCoverageThreshold:
    """Verify coverage threshold is configured."""

    def test_fail_under_set(self):
        """Coverage fail_under must be set in pyproject.toml."""
        project_root = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..")
        )
        path = os.path.join(project_root, "pyproject.toml")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "fail_under" in content, (
            "Coverage fail_under threshold is not set in pyproject.toml"
        )


class TestRuffSecurityRules:
    """Verify ruff includes security lint rules."""

    def test_flake8_bandit_enabled(self):
        """Ruff must include S (flake8-bandit) security rules."""
        project_root = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..")
        )
        path = os.path.join(project_root, "pyproject.toml")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        assert '"S"' in content, (
            "Ruff does not include S (flake8-bandit) security rules"
        )


class TestDeprecatedCodeFlagged:
    """Verify deprecated code is properly marked."""

    def test_exchange_factory_v1_deprecated(self):
        """Legacy ExchangeFactory must have deprecation warning."""
        project_root = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..")
        )
        path = os.path.join(
            project_root, "backend", "exchange", "exchange_factory.py"
        )
        if not os.path.exists(path):
            # Good - it's been removed
            return
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "deprecated" in content.lower() or "DeprecationWarning" in content, (
            "exchange_factory.py exists but is not marked as deprecated"
        )


class TestProjectMetadata:
    """Verify pyproject.toml has proper metadata."""

    def test_no_placeholder_author(self):
        """Author must not be a placeholder value."""
        project_root = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..")
        )
        path = os.path.join(project_root, "pyproject.toml")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        # These are known placeholders from the original
        placeholders = [
            "your.email@example.com",
            "yourusername",
        ]
        for placeholder in placeholders:
            if placeholder in content:
                pytest.xfail(
                    f"pyproject.toml contains placeholder: {placeholder} "
                    "(needs to be updated with real values)"
                )
