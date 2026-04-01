"""
Fase 1: Secrets & Credential Hardening - Happy Path Tests

Verifies that all secret management fixes are correctly applied:
- .gitignore is clean and complete
- settings.py JWT Field works without property override
- No hardcoded secrets in config files
- No .pem files in root directory

Run with: pytest backend/tests/security/test_secrets_hardening.py -v
"""

import glob
import os

import pytest


class TestGitignoreIntegrity:
    """Verify .gitignore is clean - no null bytes, no duplicates."""

    def test_no_null_bytes(self):
        """Gitignore must not contain null bytes (corruption indicator)."""
        gitignore_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".gitignore")
        gitignore_path = os.path.normpath(gitignore_path)
        with open(gitignore_path, "rb") as f:
            content = f.read()
        assert b"\x00" not in content, ".gitignore contains null bytes -- file is corrupt"

    def test_no_duplicate_lines(self):
        """Gitignore must not have fully duplicated blocks."""
        gitignore_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".gitignore")
        gitignore_path = os.path.normpath(gitignore_path)
        with open(gitignore_path, "r", encoding="utf-8") as f:
            lines = [
                line.strip()
                for line in f.readlines()
                if line.strip() and not line.strip().startswith("#")
            ]
        duplicates = {line for line in lines if lines.count(line) > 1}
        assert len(duplicates) == 0, f"Duplicate entries in .gitignore: {duplicates}"

    def test_env_files_ignored(self):
        """Gitignore must block .env files but allow .env.example."""
        gitignore_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".gitignore")
        gitignore_path = os.path.normpath(gitignore_path)
        with open(gitignore_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert ".env" in content
        assert "!.env.example" in content
        assert "!.env.prod.example" in content

    def test_pem_key_crt_ignored(self):
        """Gitignore must block .pem, .key, and .crt files."""
        gitignore_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".gitignore")
        gitignore_path = os.path.normpath(gitignore_path)
        with open(gitignore_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "*.pem" in content
        assert "*.key" in content
        assert "*.crt" in content


class TestSettingsJWTField:
    """Verify JWT_SECRET_KEY works as a Pydantic Field, not a broken @property."""

    def test_jwt_field_is_not_property(self):
        """JWT_SECRET_KEY must be a Pydantic Field, not a @property override."""

        from backend.core.config.settings import Settings

        # Check class-level attributes for property descriptor
        for name in dir(Settings):
            if name == "JWT_SECRET_KEY":
                attr = getattr(Settings, name, None)
                if isinstance(attr, property):
                    pytest.fail(
                        "JWT_SECRET_KEY is a @property -- this overrides the "
                        "Pydantic Field and causes AttributeError at runtime."
                    )

    def test_settings_has_get_jwt_secret_method(self):
        """Settings must have get_jwt_secret() for Vault-aware secret retrieval."""
        from backend.core.config.settings import Settings

        assert hasattr(
            Settings, "get_jwt_secret"
        ), "Settings is missing get_jwt_secret() method for Vault integration"

    def test_settings_has_production_validator(self):
        """Settings must have a production safety validator."""
        from backend.core.config.settings import Settings

        validators = [
            name
            for name in dir(Settings)
            if "validate" in name.lower() and "production" in name.lower()
        ]
        assert len(validators) > 0, "Settings is missing a production safety validator"


class TestNoHardcodedSecrets:
    """Verify no hardcoded secrets in config and compose files."""

    def test_env_example_no_real_secrets(self):
        """env.example must not contain real API keys or passwords."""
        env_example_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env.example")
        env_example_path = os.path.normpath(env_example_path)
        with open(env_example_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Known real secret fragments that must NOT appear
        real_secret_fragments = [
            "4NlFXRRcUKDhcIYtbJ5Vn",  # Revolut key fragment
            "36bb859f4f5f56d2",  # Bitvavo key fragment
            "sk-bfcf03fad1e5",  # DeepSeek key fragment
            "dev-secret-key-change-in-production",  # Known insecure JWT default
        ]
        for fragment in real_secret_fragments:
            assert (
                fragment not in content
            ), f".env.example contains a real secret fragment: {fragment[:15]}..."

    def test_docker_compose_no_hardcoded_passwords(self):
        """Docker Compose files must not have hardcoded passwords."""
        project_root = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        forbidden_passwords = ["trading_secure", "admin123"]
        compose_files = [
            "docker-compose.yml",
            "docker-compose.full.yml",
            "docker-compose.prod.yml",
        ]
        for compose_file in compose_files:
            path = os.path.join(project_root, compose_file)
            if not os.path.exists(path):
                continue
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            for password in forbidden_passwords:
                assert (
                    password not in content
                ), f"{compose_file} contains hardcoded password: {password}"


class TestNoSecretsInRoot:
    """Verify no credential files are in the project root."""

    def test_no_pem_in_root(self):
        """No .pem files should exist in the project root directory."""
        project_root = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        pem_files = glob.glob(os.path.join(project_root, "*.pem"))
        assert (
            len(pem_files) == 0
        ), f".pem files found in project root: {[os.path.basename(f) for f in pem_files]}"

    def test_no_key_in_root(self):
        """No .key files should exist in the project root directory."""
        project_root = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        key_files = glob.glob(os.path.join(project_root, "*.key"))
        assert (
            len(key_files) == 0
        ), f".key files found in project root: {[os.path.basename(f) for f in key_files]}"
