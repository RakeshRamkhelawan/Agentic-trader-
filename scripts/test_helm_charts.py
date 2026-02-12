#!/usr/bin/env python3
"""
TDD Test Script for Helm Charts (Taak 1.2)
Validates:
1. Chart structure exists
2. helm lint passes
3. helm template generates valid YAML
"""
import subprocess
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CHART_PATH = os.path.join(PROJECT_ROOT, 'infrastructure', 'k8s', 'charts', 'agentic-platform')

def run_command(command, cwd=None):
    process = subprocess.run(
        command, 
        shell=True, 
        capture_output=True, 
        text=True, 
        cwd=cwd,
        encoding='utf-8',
        errors='replace'
    )
    return process

def test_helm_charts():
    print("Starting Helm Charts Test (TDD)...")
    
    # 1. Check chart structure exists
    print("Checking chart structure...")
    required_files = [
        'Chart.yaml',
        'values.yaml',
        'templates/_helpers.tpl'
    ]
    
    for file in required_files:
        file_path = os.path.join(CHART_PATH, file)
        if not os.path.exists(file_path):
            print(f"FAIL: Missing required file: {file}")
            sys.exit(1)
    print("OK: Chart structure exists.")
    
    # 2. Run helm lint (if helm is available)
    print("Running helm lint...")
    result = run_command("helm version")
    if result.returncode != 0:
        print("SKIP: helm CLI not installed, skipping lint and template tests.")
        print("NOTE: Run 'helm lint' and 'helm template' manually in a K8s environment.")
        print("Test passed (structure only)!")
        return
    
    result = run_command(f"helm lint {CHART_PATH}")
    if result.returncode != 0:
        print(f"FAIL: helm lint failed.")
        print(result.stdout)
        print(result.stderr)
        sys.exit(1)
    print("OK: helm lint passed.")
    
    # 3. Run helm template
    print("Running helm template...")
    result = run_command(f"helm template test-release {CHART_PATH}")
    if result.returncode != 0:
        print(f"FAIL: helm template failed.")
        print(result.stdout)
        print(result.stderr)
        sys.exit(1)
    print("OK: helm template generates valid YAML.")
    
    print("Test passed!")

if __name__ == "__main__":
    test_helm_charts()
