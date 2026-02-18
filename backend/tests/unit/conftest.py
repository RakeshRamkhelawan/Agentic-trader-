"""
Pytest configuration for proper test isolation.
"""

import sys

import pytest


@pytest.fixture(scope="function", autouse=True)
def reset_modules():
    """Reset problematic modules before each test."""
    # Remove modules that register Prometheus metrics
    modules_to_remove = [
        m for m in sys.modules if "cognitive_orchestrator" in m or "telemetry" in m
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]

    yield

    # Clean up after test
    modules_to_remove = [
        m for m in sys.modules if "cognitive_orchestrator" in m or "telemetry" in m
    ]
    for mod in modules_to_remove:
        del sys.modules[mod]


@pytest.fixture(scope="session", autouse=True)
def configure_prometheus():
    """Configure Prometheus before any tests run."""
    try:
        from prometheus_client import REGISTRY

        # Clear the default registry
        collectors = list(REGISTRY._collector_to_names.keys())
        for collector in collectors:
            try:
                if hasattr(collector, "_name"):
                    if any(
                        x in collector._name
                        for x in ["guna", "trading", "order", "orchestrator"]
                    ):
                        REGISTRY.unregister(collector)
            except Exception:
                pass
    except Exception:
        pass
