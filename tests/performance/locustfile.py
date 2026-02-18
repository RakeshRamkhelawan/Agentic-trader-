"""
Performance tests for Prediction Market Intelligence.

Run with:
    locust -f tests/performance/locustfile.py --host=http://localhost:8002

Or headless (CI):
    locust -f tests/performance/locustfile.py \
        --host=http://localhost:8002 \
        --headless \
        --users 50 \
        --spawn-rate 10 \
        --run-time 60s \
        --csv=results/perf
"""

import logging

from locust import HttpUser, between, events, task

logger = logging.getLogger(__name__)


class PredictionServiceUser(HttpUser):
    """
    Simulated user for prediction service load testing.

    Simulates typical usage patterns:
    - Frequent signal requests (most common)
    - Occasional filtered signal requests
    - Rare analysis triggers
    - Health checks
    """

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    @task(10)
    def get_signals(self):
        """Fetch signals - most common operation."""
        with self.client.get(
            "/api/v1/signals?limit=10", catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status: {response.status_code}")

    @task(5)
    def get_signals_with_filter(self):
        """Fetch filtered signals."""
        with self.client.get(
            "/api/v1/signals?category=crypto&min_confidence=0.5&limit=20",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status: {response.status_code}")

    @task(3)
    def get_signals_paginated(self):
        """Fetch signals with pagination."""
        with self.client.get(
            "/api/v1/signals?limit=5&offset=10", catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status: {response.status_code}")

    @task(2)
    def health_check(self):
        """Health check endpoint."""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status: {response.status_code}")

    @task(1)
    def trigger_analysis(self):
        """Trigger analysis - least frequent."""
        with self.client.post(
            "/api/v1/analysis/run",
            json={"analysis_type": "maker_taker", "market": "kalshi"},
            catch_response=True,
        ) as response:
            if response.status_code in [200, 202]:
                response.success()
            else:
                response.failure(f"Got status: {response.status_code}")


class MainAPIProxyUser(HttpUser):
    """
    Simulated user for main API proxy endpoints.
    Tests the proxy path through api-server to prediction service.
    """

    wait_time = between(2, 5)

    @task(10)
    def get_proxy_signals(self):
        """Fetch signals via proxy."""
        with self.client.get(
            "/api/v1/signals?limit=10", catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status: {response.status_code}")

    @task(5)
    def get_proxy_health(self):
        """Check health endpoint through proxy."""
        with self.client.get("/health", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status: {response.status_code}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when the load test starts."""
    logger.info("=" * 80)
    logger.info("PERFORMANCE TEST STARTED")
    logger.info("=" * 80)
    logger.info(f"Target: {environment.host}")
    logger.info(f"Users: {len(environment.runner.locusts)}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when the load test ends."""
    logger.info("=" * 80)
    logger.info("PERFORMANCE TEST COMPLETED")
    logger.info("=" * 80)

    # Print statistics
    stats = environment.stats
    logger.info("\n" + "=" * 80)
    logger.info("PERFORMANCE STATISTICS")
    logger.info("=" * 80)

    # Aggregate stats
    total_requests = 0
    total_failures = 0

    for name, request in stats.entries.items():
        total_requests += request.num_requests
        total_failures += request.num_failures

        if request.num_requests > 0:
            avg_response_time = request.avg_response_time
            p50 = request.get_response_time_percentile(0.5)
            p95 = request.get_response_time_percentile(0.95)
            p99 = request.get_response_time_percentile(0.99)

            logger.info(f"\n{name}:")
            logger.info(f"  Requests: {request.num_requests}")
            logger.info(f"  Failures: {request.num_failures}")
            logger.info(f"  Average: {avg_response_time:.2f}ms")
            logger.info(f"  P50: {p50:.2f}ms")
            logger.info(f"  P95: {p95:.2f}ms")
            logger.info(f"  P99: {p99:.2f}ms")

    logger.info("\n" + "=" * 80)
    logger.info("OVERALL RESULTS")
    logger.info("=" * 80)
    logger.info(f"Total Requests: {total_requests}")
    logger.info(f"Total Failures: {total_failures}")

    if total_requests > 0:
        failure_rate = (total_failures / total_requests) * 100
        logger.info(f"Failure Rate: {failure_rate:.2f}%")
        logger.info("=" * 80)

        # Check if performance targets met
        logger.info("\nPERFORMANCE TARGETS:")
        logger.info(
            "  P50 latency < 50ms: "
            + ("✓ PASS" if stats.total.avg_response_time < 50 else "✗ FAIL")
        )
        logger.info(
            "  P95 latency < 200ms: "
            + (
                "✓ PASS"
                if stats.total.get_response_time_percentile(0.95) < 200
                else "✗ FAIL"
            )
        )
        logger.info(
            "  P99 latency < 500ms: "
            + (
                "✓ PASS"
                if stats.total.get_response_time_percentile(0.99) < 500
                else "✗ FAIL"
            )
        )
        logger.info(
            "  Error rate < 1%: " + ("✓ PASS" if failure_rate < 1 else "✗ FAIL")
        )
        logger.info("=" * 80)
