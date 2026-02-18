#!/usr/bin/env python3
"""
TDD Test Script for K8s Deployments (Taak 1.3)
Validates:
1. StatefulSet YAML exists and is valid
2. Service YAML exists and is valid
"""
import os
import sys

import yaml

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEMPLATES_PATH = os.path.join(
    PROJECT_ROOT, "infrastructure", "k8s", "charts", "agentic-platform", "templates"
)


def test_k8s_deployments():
    print("Starting K8s Deployments Test (TDD)...")

    required_files = ["statefulset.yaml", "service.yaml"]

    for file in required_files:
        file_path = os.path.join(TEMPLATES_PATH, file)
        print(f"Checking {file}...")

        if not os.path.exists(file_path):
            print(f"FAIL: Missing required file: {file}")
            sys.exit(1)

        # Validate YAML syntax
        try:
            with open(file_path, "r") as f:
                content = f.read()
                # Check for Helm template markers
                if "{{" in content:
                    print(f"OK: {file} exists (Helm template, syntax check skipped).")
                else:
                    yaml.safe_load(content)
                    print(f"OK: {file} is valid YAML.")
        except yaml.YAMLError as e:
            print(f"FAIL: {file} has invalid YAML syntax: {e}")
            sys.exit(1)

    print("Test passed!")


if __name__ == "__main__":
    test_k8s_deployments()
