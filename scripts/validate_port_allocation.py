#!/usr/bin/env python3
"""
Port Allocation Validator

This script validates that all configuration files follow the
PORT_ALLOCATION_SSOT.md specification.

Usage:
    python scripts/validate_port_allocation.py
    python scripts/validate_port_allocation.py --fix

Exit codes:
    0 - All validations passed
    1 - One or more validations failed
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

# Verborgen poorten (nooit gebruiken voor host mapping)
FORBIDDEN_HOST_PORTS = {
    "8123": "ClickHouse HTTP - use 5000 instead",
    "9092": "Redpanda Kafka - use 6000 instead",
    "9644": "Redpanda Admin - use 6001 instead",
    "3000": "Grafana - use 9000 instead",
}

# Verplichte poorten voor specifieke services
REQUIRED_PORTS = {
    "api": ["8000"],
    "mcp-broker": ["8001"],
    "postgres": ["5432"],
    "redis": ["6379"],
    "clickhouse": ["5000", "5001"],
    "redpanda": ["6000", "6001"],
    "chromadb": ["8100"],
    "grafana": ["9000"],
    "prometheus": ["9090"],
    "frontend": ["3000", "3080"],
}

# Correcte environment variable namen
VALID_ENV_VARS = {
    "API_PORT",
    "MCP_PORT",
    "POSTGRES_PORT",
    "REDIS_PORT",
    "CLICKHOUSE_HTTP_PORT",
    "CLICKHOUSE_NATIVE_PORT",
    "CLICKHOUSE_PORT",
    "KAFKA_BROKERS",
    "KAFKA_BOOTSTRAP_SERVERS",
    "REDPANDA_ADMIN_URL",
    "CHROMA_DB_PORT",
    "CHROMA_PORT",
    "GRAFANA_PORT",
    "PROMETHEUS_PORT",
    "METRICS_PORT",
    "METRICS_SERVER_PORT",
}


def check_docker_compose_file(filepath: Path) -> List[Tuple[str, str, int]]:
    """Check a docker-compose file for port violations."""
    errors = []
    content = filepath.read_text()
    lines = content.split('\n')

    in_service = None

    for line_num, line in enumerate(lines, 1):
        # Track which service we're in
        if re.match(r'^\s{2}[a-z-]+:', line) and not line.strip().startswith('ports'):
            in_service = line.strip().rstrip(':')

        # Check for port mappings
        port_match = re.search(r'["\']?(\d+):(\d+)["\']?', line)
        if port_match:
            host_port = port_match.group(1)
            container_port = port_match.group(2)

            # Check forbidden ports
            if host_port in FORBIDDEN_HOST_PORTS:
                errors.append((
                    filepath.name,
                    f"Line {line_num}: Forbidden host port {host_port} ({FORBIDDEN_HOST_PORTS[host_port]})",
                    line_num
                ))

    return errors


def check_env_file(filepath: Path) -> List[Tuple[str, str, int]]:
    """Check an environment file for port violations."""
    errors = []
    content = filepath.read_text()
    lines = content.split('\n')

    for line_num, line in enumerate(lines, 1):
        # Skip comments and empty lines
        if not line.strip() or line.strip().startswith('#'):
            continue

        # Check for forbidden ports in values
        for forbidden_port, reason in FORBIDDEN_HOST_PORTS.items():
            # Match port in URLs like localhost:8123 or 127.0.0.1:8123
            pattern = rf'[=:](//)?[^:]*:{forbidden_port}(/|\s|$)'
            if re.search(pattern, line):
                # Check if this is a comment explaining the change
                if 'intern' in line.lower() or 'container' in line.lower():
                    continue
                errors.append((
                    filepath.name,
                    f"Line {line_num}: Forbidden port {forbidden_port} ({reason})",
                    line_num
                ))

        # Check for deprecated env var names
        if 'CHROMA_HOST=' in line and 'CHROMA_DB_HOST' not in line:
            if not line.startswith('#'):
                errors.append((
                    filepath.name,
                    f"Line {line_num}: Use CHROMA_DB_HOST instead of CHROMA_HOST",
                    line_num
                ))

    return errors


def check_python_file(filepath: Path) -> List[Tuple[str, str, int]]:
    """Check Python files for hardcoded ports."""
    errors = []
    content = filepath.read_text()
    lines = content.split('\n')

    for line_num, line in enumerate(lines, 1):
        # Skip comments
        if line.strip().startswith('#'):
            continue

        # Check for hardcoded localhost with forbidden ports
        for forbidden_port, reason in FORBIDDEN_HOST_PORTS.items():
            pattern = rf'["\']localhost:{forbidden_port}["\']'
            if re.search(pattern, line):
                # Allow if it's in a comment about the change
                if 'was' in line.lower() or 'old' in line.lower() or 'zie' in line.lower():
                    continue
                errors.append((
                    filepath.name,
                    f"Line {line_num}: Hardcoded forbidden port {forbidden_port} ({reason})",
                    line_num
                ))

    return errors


def main():
    """Main validation function."""
    import argparse

    parser = argparse.ArgumentParser(description='Validate port allocation')
    parser.add_argument('--fix', action='store_true', help='Attempt to fix issues')
    args = parser.parse_args()

    print("🔍 Validating Port Allocation against PORT_ALLOCATION_SSOT.md...")
    print()

    all_errors = []

    # Check docker-compose files
    compose_files = list(Path('.').glob('docker-compose*.yml'))
    for filepath in compose_files:
        errors = check_docker_compose_file(filepath)
        all_errors.extend(errors)

    # Check environment files
    env_files = [Path('.env'), Path('.env.example'), Path('.env.prod')]
    for filepath in env_files:
        if filepath.exists():
            errors = check_env_file(filepath)
            all_errors.extend(errors)

    # Check key Python files
    py_files = [
        Path('backend/core/config/settings.py'),
        Path('backend/events/kafka_broker.py'),
        Path('backend/scripts/ops/health_check.py'),
    ]
    for filepath in py_files:
        if filepath.exists():
            errors = check_python_file(filepath)
            all_errors.extend(errors)

    # Report results
    if all_errors:
        print("❌ PORT ALLOCATION VIOLATIONS FOUND:")
        print()
        for filename, message, line_num in all_errors:
            print(f"  📁 {filename}:{line_num}")
            print(f"     {message}")
            print()

        print("⚠️  These violations must be fixed according to PORT_ALLOCATION_SSOT.md")
        print("📖 Read: https://github.com/your-repo/blob/main/PORT_ALLOCATION_SSOT.md")
        sys.exit(1)
    else:
        print("✅ All port allocations are valid!")
        print()
        print("Core ports:")
        print("  API: 8000, MCP: 8001, Postgres: 5432, Redis: 6379")
        print("Extended:")
        print("  ClickHouse: 5000/5001, Redpanda: 6000/6001, ChromaDB: 8100")
        print("Monitoring:")
        print("  Grafana: 9000, Prometheus: 9090")
        sys.exit(0)


if __name__ == '__main__':
    main()
