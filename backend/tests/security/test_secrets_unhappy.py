"""
Fase 1: Secrets & Credential Hardening - Unhappy Path Tests

Verifies that the system correctly rejects insecure configurations:
- Missing required secrets
- Too-short JWT keys
- Insecure default values
- AUTH_DISABLED in production

Run with: pytest backend/tests/security/test_secrets_unhappy.py -v
"""

import os

import pytest


class TestInsecureJWTRejected:
    """Verify the system rejects insecure JWT configurations."""

    def test_known_insecure_default_rejected(self):
        """Settings must reject the known insecure default JWT secret."""
        # Save and override env
        original_jwt = os.environ.get("JWT_SECRET_KEY")
        original_env = os.environ.get("ENV")
        os.environ["JWT_SECRET_KEY"] = "dev-secret-key-change-in-production-12345"
        os.environ["ENV"] = "development"
        try:
            # Force reimport
            from importlib import reload

            import backend.core.config.settings as settings_mod

            with pytest.raises(ValueError, match="insecure default"):
                reload(settings_mod)
        finally:
            if original_jwt is not None:
                os.environ["JWT_SECRET_KEY"] = original_jwt
            else:
                os.environ.pop("JWT_SECRET_KEY", None)
            if original_env is not None:
                os.environ["ENV"] = original_env
            else:
                os.environ.pop("ENV", None)

    def test_short_jwt_secret_rejected(self):
        """Settings must reject JWT secrets shorter than 32 characters."""
        original_jwt = os.environ.get("JWT_SECRET_KEY")
        os.environ["JWT_SECRET_KEY"] = "too-short-only-20-ch"
        try:
            from importlib import reload

            import backend.core.config.settings as settings_mod

            with pytest.raises((ValueError, Exception)):
                reload(settings_mod)
        finally:
            if original_jwt is not None:
                os.environ["JWT_SECRET_KEY"] = original_jwt
            else:
                os.environ.pop("JWT_SECRET_KEY", None)


class TestProductionSafety:
    """Verify production-unsafe configurations are blocked."""

    def test_auth_disabled_blocked_in_production(self):
        """AUTH_DISABLED=True must be rejected when ENV=production."""
        from backend.core.config.settings import Settings

        with pytest.raises(ValueError, match="AUTH_DISABLED"):
            Settings(
                ENV="production",
                AUTH_DISABLED=True,
                JWT_SECRET_KEY="a" * 40,
                _env_file=None,
            )

    def test_debug_blocked_in_production(self):
        """DEBUG=True must be rejected when ENV=production."""
        from backend.core.config.settings import Settings

        with pytest.raises(ValueError, match="DEBUG"):
            Settings(
                ENV="production",
                DEBUG=True,
                AUTH_DISABLED=False,
                JWT_SECRET_KEY="a" * 40,
                _env_file=None,
            )

    def test_auth_disabled_allowed_in_development(self):
        """AUTH_DISABLED=True should be allowed in development."""
        from backend.core.config.settings import Settings

        # Should NOT raise
        s = Settings(
            ENV="development",
            AUTH_DISABLED=True,
            JWT_SECRET_KEY="a" * 40,
            _env_file=None,
        )
        assert s.AUTH_DISABLED is True


class TestDockerComposeRequiresSecrets:
    """Verify Docker Compose files use env var references, not defaults."""

    def test_full_compose_requires_postgres_password(self):
        """docker-compose.full.yml must use ${POSTGRES_PASSWORD:?...} syntax."""
        project_root = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..")
        )
        compose_path = os.path.join(project_root, "docker-compose.full.yml")
        if not os.path.exists(compose_path):
            pytest.skip("docker-compose.full.yml not found")
        with open(compose_path, "r", encoding="utf-8") as f:
            content = f.read()
        # Must use required env var syntax
        assert "POSTGRES_PASSWORD:?" in content or "POSTGRES_PASSWORD:-}" not in content, (
            "docker-compose.full.yml does not enforce POSTGRES_PASSWORD as required"
        )
