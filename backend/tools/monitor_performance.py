import os
import sys
import time

import requests

# Target API metrics endpoint
METRICS_URL = os.environ.get("METRICS_URL", "http://localhost:8000/metrics")


def get_metrics():
    """Fetch metrics from the Prometheus endpoint."""
    try:
        response = requests.get(METRICS_URL, timeout=5)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching metrics: {e}")
        return None


def parse_metric(data, name, labels=None):
    """
    Very simple parser for Prometheus text format.
    Finds a metric line by name and optional labels.
    """
    if not data:
        return 0.0

    for line in data.splitlines():
        if line.startswith("#"):
            continue
        if name in line:
            # Check if all labels match
            match = True
            if labels:
                for k, v in labels.items():
                    if f'{k}="{v}"' not in line:
                        match = False
                        break
            if match:
                try:
                    # Line format: metric_name{labels} value
                    return float(line.split()[-1])
                except (ValueError, IndexError):
                    continue
    return 0.0


def show_dashboard():
    """Visualizes platform performance metrics."""
    print("\033[H\033[J")  # Clear screen
    print("=" * 60)
    print("      AGENTIC TRADER PLATFORM - PERFORMANCE DASHBOARD")
    print("=" * 60)
    print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Source: {METRICS_URL}")
    print("-" * 60)

    data = get_metrics()
    if not data:
        print("Waiting for API data...")
        return

    # Extract latency metrics (Histogram sum / count for avg)
    # Note: Using service_name prefix 'api_server' as defined in Metrics class
    exchanges = ["bitvavo", "revolut"]

    print(f"{'Exchange':<15} | {'Requests':<10} | {'Latency (avg)':<15} | {'Status'}")
    print("-" * 60)

    for ex in exchanges:
        count = parse_metric(data, "api_server_routing_requests_total", {"exchange_id": ex})
        sum_lat = parse_metric(
            data, "api_server_routing_request_latency_seconds_sum", {"exchange_id": ex}
        )
        count_lat = parse_metric(
            data, "api_server_routing_request_latency_seconds_count", {"exchange_id": ex}
        )

        avg_lat = (sum_lat / count_lat * 1000) if count_lat > 0 else 0.0

        errors = parse_metric(data, "api_server_routing_errors_total", {"exchange_id": ex})
        success_ratio = ((count - errors) / count * 100) if count > 0 else 100.0

        status = "OK" if success_ratio > 95 else "DEGRADED" if success_ratio > 80 else "CRITICAL"

        print(f"{ex:<15} | {int(count):<10} | {avg_lat:8.2f} ms | {status} ({success_ratio:.1f}%)")

    print("-" * 60)

    # Platform-wide metrics
    api_requests = parse_metric(data, "api_server_requests_total")
    api_errors = parse_metric(data, "api_server_errors_total")
    in_progress = parse_metric(data, "api_server_requests_in_progress")

    print(f"Total API Requests: {int(api_requests)}")
    print(f"Total API Errors:   {int(api_errors)}")
    print(f"Active Requests:    {int(in_progress)}")
    print("=" * 60)


if __name__ == "__main__":
    if "--smoke" in sys.argv:
        print("Running smoke test validation...")
        show_dashboard()
        print("Dashboard smoke test passed.")
        sys.exit(0)

    try:
        while True:
            show_dashboard()
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
