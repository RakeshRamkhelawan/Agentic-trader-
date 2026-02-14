"""
Integration test fixtures and configuration.
"""
import os
import pytest


def pytest_configure(config):
    """Configure pytest for integration tests."""
    config.addinivalue_line(
        "markers", 
        "integration: marks tests as integration tests (deselect with '-m \"not integration\"')"
    )


@pytest.fixture(scope="session")
def docker_compose_file():
    """Path to docker-compose file."""
    return os.path.join(
        os.path.dirname(__file__), 
        "..", "..", 
        "docker-compose.yml"
    )
