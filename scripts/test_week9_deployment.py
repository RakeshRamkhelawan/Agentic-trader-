#!/usr/bin/env python
"""
Week 9 Test Suite - Deployment Validation

Tests:
1. Docker Compose configuration validation
2. Kubernetes manifests validation
3. CI/CD workflow validation
4. Security configuration checks
5. Documentation completeness
"""

import asyncio
import json
import logging
import os
import sys
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

sys.path.insert(0, ".")


def test_docker_compose():
    """Test Docker Compose configuration."""
    print("\n" + "=" * 60)
    print("Test 1: Docker Compose Configuration")
    print("=" * 60)

    compose_file = "docker-compose.full.yml"

    if not os.path.exists(compose_file):
        print(f"  [MISSING] {compose_file}")
        return False

    with open(compose_file, "r") as f:
        compose = yaml.safe_load(f)

    services = compose.get("services", {})
    print(f"  Services defined: {len(services)}")

    expected_services = [
        "api", "frontend", "postgres", "clickhouse",
        "redis", "chromadb", "redpanda", "prometheus", "grafana", "nginx"
    ]

    for svc in expected_services:
        status = "OK" if svc in services else "MISSING"
        print(f"    - {svc}: {status}")

    # Check volumes
    volumes = compose.get("volumes", {})
    print(f"\n  Volumes defined: {len(volumes)}")

    # Check networks
    networks = compose.get("networks", {})
    print(f"  Networks defined: {len(networks)}")

    return len(services) >= len(expected_services)


def test_kubernetes_manifests():
    """Test Kubernetes manifest files."""
    print("\n" + "=" * 60)
    print("Test 2: Kubernetes Manifests")
    print("=" * 60)

    k8s_dir = "infrastructure/k8s"

    expected_files = [
        "namespace.yml",
        "postgres.yml",
        "redis.yml",
        "api.yml",
        "monitoring.yml",
        "network-policy.yml",
        "kustomization.yml",
    ]

    found = []
    for filename in expected_files:
        filepath = os.path.join(k8s_dir, filename)
        if os.path.exists(filepath):
            print(f"  [OK] {filename}")
            found.append(filename)
        else:
            print(f"  [MISSING] {filename}")

    # Validate YAML syntax
    valid_yaml = 0
    for filename in found:
        filepath = os.path.join(k8s_dir, filename)
        try:
            with open(filepath, "r") as f:
                # Handle multi-document YAML files
                list(yaml.safe_load_all(f))
            valid_yaml += 1
        except yaml.YAMLError as e:
            print(f"  [ERROR] {filename}: {e}")

    print(f"\n  Valid YAML files: {valid_yaml}/{len(found)}")

    return len(found) == len(expected_files)


def test_cicd_workflows():
    """Test CI/CD workflow files."""
    print("\n" + "=" * 60)
    print("Test 3: CI/CD Workflows")
    print("=" * 60)

    workflows_dir = ".github/workflows"

    expected_workflows = [
        "ci.yml",
        "cd.yml",
    ]

    found = []
    for filename in expected_workflows:
        filepath = os.path.join(workflows_dir, filename)
        if os.path.exists(filepath):
            print(f"  [OK] {filename}")
            found.append(filename)
        else:
            print(f"  [MISSING] {filename}")

    # Check CI workflow structure
    ci_file = os.path.join(workflows_dir, "ci.yml")
    if os.path.exists(ci_file):
        with open(ci_file, "r", encoding="utf-8") as f:
            ci = yaml.safe_load(f)

        jobs = ci.get("jobs", {})
        print(f"\n  CI Jobs: {len(jobs)}")
        for job_name in jobs:
            print(f"    - {job_name}")

    # Check CD workflow structure
    cd_file = os.path.join(workflows_dir, "cd.yml")
    if os.path.exists(cd_file):
        with open(cd_file, "r", encoding="utf-8") as f:
            cd = yaml.safe_load(f)

        jobs = cd.get("jobs", {})
        print(f"\n  CD Jobs: {len(jobs)}")
        for job_name in jobs:
            print(f"    - {job_name}")

    return len(found) == len(expected_workflows)


def test_grafana_dashboards():
    """Test Grafana dashboard configurations."""
    print("\n" + "=" * 60)
    print("Test 4: Grafana Dashboards")
    print("=" * 60)

    dashboards_dir = "infrastructure/grafana/dashboards"

    expected_dashboards = [
        "trading-overview.json",
        "positions-pnl.json",
        "arbitrage-prices.json",
    ]

    found = []
    for filename in expected_dashboards:
        filepath = os.path.join(dashboards_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                dashboard = json.load(f)

            title = dashboard.get("dashboard", {}).get("title", "Unknown")
            panels = len(dashboard.get("dashboard", {}).get("panels", []))
            print(f"  [OK] {filename}: {title} ({panels} panels)")
            found.append(filename)
        else:
            print(f"  [MISSING] {filename}")

    return len(found) == len(expected_dashboards)


def test_prometheus_rules():
    """Test Prometheus alert rules."""
    print("\n" + "=" * 60)
    print("Test 5: Prometheus Alert Rules")
    print("=" * 60)

    rules_file = "infrastructure/prometheus/rules/trading_alerts.yml"

    if not os.path.exists(rules_file):
        print(f"  [MISSING] {rules_file}")
        return False

    with open(rules_file, "r") as f:
        rules = yaml.safe_load(f)

    groups = rules.get("groups", [])
    print(f"  Rule groups: {len(groups)}")

    total_rules = 0
    for group in groups:
        group_name = group.get("name", "unknown")
        group_rules = group.get("rules", [])
        print(f"\n  Group: {group_name} ({len(group_rules)} rules)")
        total_rules += len(group_rules)

        for rule in group_rules:
            alert_name = rule.get("alert", "unknown")
            severity = rule.get("labels", {}).get("severity", "unknown")
            print(f"    - {alert_name} [{severity}]")

    return total_rules > 0


def test_documentation():
    """Test documentation files."""
    print("\n" + "=" * 60)
    print("Test 6: Documentation")
    print("=" * 60)

    required_docs = [
        "DEPLOYMENT_GUIDE.md",
        "README.md",
        "WEEK8_IMPLEMENTATION_SUMMARY.md",
    ]

    found = []
    for doc in required_docs:
        if os.path.exists(doc):
            size = os.path.getsize(doc)
            print(f"  [OK] {doc} ({size} bytes)")
            found.append(doc)
        else:
            print(f"  [MISSING] {doc}")

    return len(found) == len(required_docs)


def test_security_configs():
    """Test security configurations."""
    print("\n" + "=" * 60)
    print("Test 7: Security Configuration")
    print("=" * 60)

    checks = []

    # Check network policies exist
    netpol_file = "infrastructure/k8s/network-policy.yml"
    if os.path.exists(netpol_file):
        with open(netpol_file, "r") as f:
            netpols = list(yaml.safe_load_all(f))
        print(f"  [OK] Network policies: {len(netpols)} policies defined")
        checks.append(True)
    else:
        print(f"  [MISSING] Network policies")
        checks.append(False)

    # Check secrets are not in plaintext
    compose_file = "docker-compose.full.yml"
    if os.path.exists(compose_file):
        with open(compose_file, "r") as f:
            content = f.read()

        # Check for placeholder secrets
        if "${" in content or "placeholder" in content.lower():
            print(f"  [OK] Docker Compose uses environment variables")
            checks.append(True)
        else:
            print(f"  [WARN] Docker Compose might have hardcoded secrets")
            checks.append(False)

    # Check .env.example exists
    if os.path.exists(".env.example"):
        print(f"  [OK] .env.example exists")
        checks.append(True)
    else:
        print(f"  [MISSING] .env.example")
        checks.append(False)

    return all(checks)


async def main():
    """Run all Week 9 tests."""
    print("=" * 60)
    print("Week 9: Deployment & DevOps Tests")
    print("=" * 60)

    results = {}

    # Run synchronous tests
    results["docker_compose"] = test_docker_compose()
    results["kubernetes_manifests"] = test_kubernetes_manifests()
    results["cicd_workflows"] = test_cicd_workflows()
    results["grafana_dashboards"] = test_grafana_dashboards()
    results["prometheus_rules"] = test_prometheus_rules()
    results["documentation"] = test_documentation()
    results["security_configs"] = test_security_configs()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        emoji = " " if passed else " "
        print(f"{emoji} {test_name}: {status}")

    all_passed = all(results.values())
    print("\n" + "=" * 60)
    if all_passed:
        print("All Week 9 tests passed! Deployment infrastructure ready.")
        print("\nInfrastructure includes:")
        print("  - Docker Compose (10 services)")
        print("  - Kubernetes manifests (7 files)")
        print("  - CI/CD pipelines (GitHub Actions)")
        print("  - Monitoring stack (Prometheus + Grafana)")
        print("  - Security policies (Network policies)")
    else:
        print("Some tests failed. Check logs above.")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
