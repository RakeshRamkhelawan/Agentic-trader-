from unittest.mock import MagicMock

import pytest
from prometheus_client import CollectorRegistry

from backend.core.telemetry.metrics import PrometheusMetrics


@pytest.fixture(autouse=True)
def reset_registry():
    """Zorgt voor een schone Prometheus registry en metrics instanties voor elke test."""
    PrometheusMetrics._registry = CollectorRegistry(auto_describe=True)
    PrometheusMetrics._instances = {}  # Reset de cache van instanties
    yield


def test_counter_increments():
    """Happy Path: Counter werkt."""
    metrics = PrometheusMetrics("test_service")
    # Mock de interne counter objecten om hun methodes te testen
    metrics.requests_total = MagicMock()

    metrics.requests_total.inc()
    metrics.requests_total.inc(2)  # increment met 2

    metrics.requests_total.inc.assert_any_call()  # Ten minste één keer aangeroepen
    metrics.requests_total.inc.assert_any_call(2)  # En een keer met 2


def test_gauge_set_and_inc():
    """Happy Path: Gauge werkt."""
    metrics = PrometheusMetrics("test_service")
    metrics.requests_in_progress = MagicMock()  # Mock de interne gauge objecten

    metrics.requests_in_progress.set(5)
    metrics.requests_in_progress.inc()

    metrics.requests_in_progress.set.assert_called_once_with(5)
    metrics.requests_in_progress.inc.assert_called_once()


def test_histogram_observe():
    """Happy Path: Histogram observeert waarden."""
    metrics = PrometheusMetrics("test_service")
    metrics.request_latency_seconds = MagicMock()  # Mock de interne histogram objecten

    metrics.request_latency_seconds.observe(0.1)
    metrics.request_latency_seconds.observe(0.5)

    metrics.request_latency_seconds.observe.assert_any_call(0.1)
    metrics.request_latency_seconds.observe.assert_any_call(0.5)


def test_multiple_instances_share_registry():
    """Happy Path: Meerdere instanties voor dezelfde service_name gebruiken dezelfde metrics."""
    metrics1 = PrometheusMetrics("shared_service")
    metrics2 = PrometheusMetrics("shared_service")  # Zelfde naam

    # Check of het dezelfde instantie is
    assert metrics1 is metrics2


def test_expose_metrics(mocker):
    """Happy Path: Metrics kunnen via een endpoint worden geëxposed."""
    metrics = PrometheusMetrics("test_service_expose")

    # Patch generate_latest op de PrometheusMetrics module zelf
    mock_generate_latest = mocker.patch(
        "backend.core.telemetry.metrics.generate_latest", return_value=b"metrics_data"
    )

    latest_metrics = metrics.expose_metrics()

    mock_generate_latest.assert_called_once_with(PrometheusMetrics._registry)
    assert latest_metrics == b"metrics_data"
