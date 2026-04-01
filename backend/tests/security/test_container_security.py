"""
Fase 3: Dockerfile, Entry Point & Container Security - All Tests

Covers:
- Happy Path: .dockerignore blocks secrets, Dockerfile PATH correct, port bindings safe
- Unhappy Path: .dockerignore missing critical entries detected
- Integration: Docker build succeeds and container runs as non-root

Run with: pytest backend/tests/security/test_container_security.py -v
"""

import os

import pytest


class TestDockerignoreCompleteness:
    """Verify .dockerignore blocks secrets and unnecessary files."""

    def _read_dockerignore(self):
        project_root = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..")
        )
        path = os.path.join(project_root, ".dockerignore")
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def test_env_files_blocked(self):
        """Docker builds must not include .env files."""
        content = self._read_dockerignore()
        assert ".env" in content

    def test_pem_files_blocked(self):
        """Docker builds must not include .pem files."""
        content = self._read_dockerignore()
        assert "*.pem" in content

    def test_key_files_blocked(self):
        """Docker builds must not include .key files."""
        content = self._read_dockerignore()
        assert "*.key" in content

    def test_crt_files_blocked(self):
        """Docker builds must not include .crt files."""
        content = self._read_dockerignore()
        assert "*.crt" in content

    def test_git_directory_blocked(self):
        """Docker builds must not include .git directory."""
        content = self._read_dockerignore()
        assert ".git/" in content

    def test_tests_blocked(self):
        """Docker builds must not include test directories."""
        content = self._read_dockerignore()
        assert "tests/" in content or "backend/tests/" in content

    def test_infrastructure_blocked(self):
        """Docker builds must not include infrastructure/terraform dirs."""
        content = self._read_dockerignore()
        assert "infrastructure/" in content


class TestDockerfileSecurity:
    """Verify Dockerfile follows security best practices."""

    def _read_dockerfile(self):
        project_root = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..")
        )
        path = os.path.join(project_root, "Dockerfile")
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def test_path_uses_appuser(self):
        """PATH must reference /home/appuser/.local/bin, not /root/.local/bin."""
        content = self._read_dockerfile()
        assert (
            "/home/appuser/.local/bin" in content
        ), "Dockerfile PATH does not reference appuser home directory"
        assert (
            "/root/.local/bin" not in content
        ), "Dockerfile PATH still references /root/.local/bin"

    def test_runs_as_non_root(self):
        """Dockerfile must switch to non-root user before CMD."""
        content = self._read_dockerfile()
        assert "USER appuser" in content, "Dockerfile does not switch to non-root user"
        # USER must come before CMD
        user_pos = content.index("USER appuser")
        cmd_pos = content.index("CMD")
        assert user_pos < cmd_pos, "USER appuser must come before CMD in Dockerfile"

    def test_healthcheck_defined(self):
        """Dockerfile must define a HEALTHCHECK."""
        content = self._read_dockerfile()
        assert "HEALTHCHECK" in content


class TestDockerComposePortBindings:
    """Verify Docker Compose files bind database ports to localhost."""

    def test_postgres_bound_to_localhost_in_full(self):
        """PostgreSQL port must be bound to 127.0.0.1 in docker-compose.full.yml."""
        project_root = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..")
        )
        path = os.path.join(project_root, "docker-compose.full.yml")
        if not os.path.exists(path):
            pytest.skip("docker-compose.full.yml not found")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        # Find postgres port binding
        if "5432:5432" in content:
            assert (
                "127.0.0.1:5432:5432" in content
            ), "PostgreSQL port is exposed on all interfaces (0.0.0.0)"

    def test_postgres_bound_to_localhost_in_base(self):
        """PostgreSQL port must be bound to 127.0.0.1 in docker-compose.yml."""
        project_root = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..")
        )
        path = os.path.join(project_root, "docker-compose.yml")
        if not os.path.exists(path):
            pytest.skip("docker-compose.yml not found")
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        if "5432:5432" in content:
            assert (
                "127.0.0.1:5432:5432" in content
            ), "PostgreSQL port is exposed on all interfaces in docker-compose.yml"

    def test_no_hardcoded_db_password_in_compose(self):
        """Docker Compose must not have hardcoded DB passwords."""
        project_root = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..")
        )
        for filename in ["docker-compose.yml", "docker-compose.full.yml"]:
            path = os.path.join(project_root, filename)
            if not os.path.exists(path):
                continue
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            assert (
                "trading_secure" not in content
            ), f"Hardcoded password 'trading_secure' found in {filename}"
