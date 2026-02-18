#!/usr/bin/env python3
"""
TDD Test Script for all Taak 1 K8s components.
Validates existence of all required Helm chart files.
"""
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CHART_PATH = os.path.join(
    PROJECT_ROOT, "infrastructure", "k8s", "charts", "agentic-platform"
)
TEMPLATES_PATH = os.path.join(CHART_PATH, "templates")


def test_all_k8s_components():
    print("Starting Full Taak 1 Validation...")

    # Chart files
    chart_files = ["Chart.yaml", "values.yaml", "templates/_helpers.tpl"]

    # Template files
    template_files = [
        "statefulset.yaml",
        "service.yaml",
        "ingress.yaml",
        "cluster-issuer.yaml",
        "resource-quota.yaml",
        "network-policy.yaml",
    ]

    print("\n--- Checking Chart Structure ---")
    for file in chart_files:
        file_path = os.path.join(CHART_PATH, file)
        if not os.path.exists(file_path):
            print(f"FAIL: Missing {file}")
            sys.exit(1)
        print(f"OK: {file}")

    print("\n--- Checking Templates ---")
    for file in template_files:
        file_path = os.path.join(TEMPLATES_PATH, file)
        if not os.path.exists(file_path):
            print(f"FAIL: Missing {file}")
            sys.exit(1)
        print(f"OK: {file}")

    print("\n=== All Taak 1 files validated successfully! ===")


if __name__ == "__main__":
    test_all_k8s_components()
