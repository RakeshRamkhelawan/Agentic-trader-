#!/usr/bin/env python3
"""
Monitoring Setup Verification Script

This script verifies that the Prediction Market Intelligence monitoring
is properly configured and collecting metrics.

Usage:
    python scripts/verify_monitoring.py
    python scripts/verify_monitoring.py --prometheus-url http://localhost:9090
    python scripts/verify_monitoring.py --metrics-url http://localhost:8002/metrics

Exit codes:
    0 = All checks passed
    1 = Some checks failed
    2 = Critical checks failed
"""

import argparse
import sys
from datetime import datetime
from typing import List, Tuple

try:
    import httpx
except ImportError:
    print("Error: httpx not installed. Install with: pip install httpx")
    sys.exit(2)


class MonitoringVerifier:
    """Verifies monitoring setup and metric collection."""

    def __init__(self, metrics_url: str, prometheus_url: str):
        self.metrics_url = metrics_url
        self.prometheus_url = prometheus_url
        self.client = httpx.Client(timeout=10.0)
        self.checks: List[Tuple[str, bool, str]] = []

    def add_check(self, name: str, passed: bool, message: str = ""):
        """Record a check result."""
        self.checks.append((name, passed, message))
        status = "✓" if passed else "✗"
        print(f"  {status} {name}")
        if message:
            print(f"      {message}")

    def check_metrics_endpoint(self) -> bool:
        """Check if metrics endpoint is accessible."""
        try:
            response = self.client.get(self.metrics_url)
            if response.status_code == 200:
                self.add_check(
                    "Metrics endpoint accessible",
                    True,
                    f"Status: {response.status_code}",
                )
                return True
            else:
                self.add_check(
                    "Metrics endpoint accessible",
                    False,
                    f"Status: {response.status_code}",
                )
                return False
        except Exception as e:
            self.add_check("Metrics endpoint accessible", False, f"Error: {str(e)}")
            return False

    def check_metrics_format(self) -> bool:
        """Check if metrics are in Prometheus format."""
        try:
            response = self.client.get(self.metrics_url)
            if response.status_code != 200:
                return False

            text = response.text
            # Check for Prometheus metric format (HELP, TYPE, metric values)
            has_help = "# HELP" in text
            has_type = "# TYPE" in text
            has_metrics = "{" in text and "}" in text

            valid = has_help and has_type and has_metrics
            self.add_check(
                "Metrics format valid",
                valid,
                f"HELP: {has_help}, TYPE: {has_type}, Metrics: {has_metrics}",
            )
            return valid
        except Exception as e:
            self.add_check("Metrics format valid", False, f"Error: {str(e)}")
            return False

    def check_required_metrics(self) -> bool:
        """Check if required metrics are present."""
        try:
            response = self.client.get(self.metrics_url)
            if response.status_code != 200:
                return False

            text = response.text
            required_metrics = [
                "prediction_requests_total",
                "prediction_request_duration_seconds",
                "prediction_signals_generated_total",
                "prediction_analysis_jobs_total",
                "prediction_circuit_breaker_state",
            ]

            missing = []
            for metric in required_metrics:
                if metric not in text:
                    missing.append(metric)

            passed = len(missing) == 0
            self.add_check(
                "Required metrics present",
                passed,
                f"Found: {len(required_metrics) - len(missing)}/{len(required_metrics)}",
            )
            if missing:
                print(f"       Missing: {', '.join(missing)}")
            return passed
        except Exception as e:
            self.add_check("Required metrics present", False, f"Error: {str(e)}")
            return False

    def check_prometheus_connectivity(self) -> bool:
        """Check if Prometheus is accessible."""
        try:
            response = self.client.get(f"{self.prometheus_url}/api/v1/status/config")
            passed = response.status_code == 200
            self.add_check(
                "Prometheus connectivity", passed, f"Status: {response.status_code}"
            )
            return passed
        except Exception as e:
            self.add_check("Prometheus connectivity", False, f"Error: {str(e)}")
            return False

    def check_prometheus_targets(self) -> bool:
        """Check if prediction-intelligence target is healthy."""
        try:
            response = self.client.get(f"{self.prometheus_url}/api/v1/targets")
            if response.status_code != 200:
                self.add_check(
                    "Prometheus targets", False, f"Status: {response.status_code}"
                )
                return False

            data = response.json()
            targets = data.get("data", {}).get("activeTargets", [])

            # Find prediction-intelligence target
            pred_targets = [
                t
                for t in targets
                if t.get("labels", {}).get("job") == "prediction-intelligence"
            ]

            if not pred_targets:
                self.add_check(
                    "Prediction intelligence target",
                    False,
                    "Target not found in Prometheus",
                )
                return False

            target = pred_targets[0]
            state = target.get("health") == "up"
            self.add_check(
                "Prediction intelligence target",
                state,
                f"Health: {target.get('health')}",
            )
            return state
        except Exception as e:
            self.add_check("Prometheus targets", False, f"Error: {str(e)}")
            return False

    def check_metric_data(self) -> bool:
        """Check if metrics have recent data."""
        try:
            # Query for recent metric data
            query = "prediction_requests_total"
            url = f"{self.prometheus_url}/api/v1/query"
            params = {"query": query}

            response = self.client.get(url, params=params)
            if response.status_code != 200:
                self.add_check(
                    "Metric data available",
                    False,
                    f"Query failed: {response.status_code}",
                )
                return False

            data = response.json()
            results = data.get("data", {}).get("result", [])

            passed = len(results) > 0
            self.add_check(
                "Metric data available", passed, f"Found {len(results)} metric series"
            )
            return passed
        except Exception as e:
            self.add_check("Metric data available", False, f"Error: {str(e)}")
            return False

    def run_verification(self) -> int:
        """Run all checks and return exit code."""
        print(f"\n{'='*60}")
        print("Monitoring Setup Verification")
        print(f"{'='*60}")
        print(f"Metrics URL: {self.metrics_url}")
        print(f"Prometheus URL: {self.prometheus_url}")
        print(f"Time: {datetime.now().isoformat()}\n")

        # Run checks
        print("Metrics Endpoint Checks:")
        metrics_ok = self.check_metrics_endpoint()
        self.check_metrics_format()
        self.check_required_metrics()

        print("\nPrometheus Checks:")
        prometheus_ok = self.check_prometheus_connectivity()
        self.check_prometheus_targets()
        self.check_metric_data()

        # Summary
        print(f"\n{'='*60}")
        total = len(self.checks)
        passed = sum(1 for _, p, _ in self.checks if p)
        print(f"Summary: {passed}/{total} checks passed")

        if passed == total:
            print("✓ All monitoring checks passed - Monitoring is operational")
            return 0
        elif not metrics_ok:
            print("✗ Critical: Metrics endpoint not accessible")
            return 2
        elif not prometheus_ok:
            print("✗ Critical: Prometheus not accessible")
            return 2
        else:
            print("⚠ Warning: Some checks failed - See details above")
            return 1

    def close(self):
        """Close HTTP client."""
        self.client.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Verify Prediction Market Intelligence monitoring setup"
    )
    parser.add_argument(
        "--metrics-url",
        default="http://localhost:8002/metrics",
        help="Metrics endpoint URL (default: http://localhost:8002/metrics)",
    )
    parser.add_argument(
        "--prometheus-url",
        default="http://localhost:9090",
        help="Prometheus server URL (default: http://localhost:9090)",
    )

    args = parser.parse_args()

    verifier = MonitoringVerifier(args.metrics_url, args.prometheus_url)
    try:
        exit_code = verifier.run_verification()
    finally:
        verifier.close()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
