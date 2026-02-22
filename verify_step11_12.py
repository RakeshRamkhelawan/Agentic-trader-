#!/usr/bin/env python3
"""STAP 11-12: Docker Compose & Health Checks"""

import subprocess

print("=" * 60)
print("STAP 11-12: Docker Compose & Health Checks")
print("=" * 60)

print("\n1. DOCKER CONTAINERS STATUS:")
try:
    result = subprocess.run(
        ["docker", "ps", "--format", "{{.Names}}|{{.Status}}|{{.Ports}}"],
        capture_output=True,
        text=True,
        timeout=10,
    )

    if result.returncode == 0:
        containers = result.stdout.strip().split("\n")
        required_services = ["api-server", "redis", "postgres"]
        found_services = []

        for container in containers:
            if container:
                parts = container.split("|")
                if len(parts) >= 2:
                    name, status = parts[0], parts[1]
                    print(f"   [{status.split()[0]}] {name}")
                    found_services.append(name)

        print("\n2. VERPLICHTE SERVICES CHECK:")
        for service in required_services:
            # Zoek service in containers (kan verschillende namen hebben)
            found = any(service in s for s in found_services)
            status = "OK" if found else "FAIL"
            print(f"   [{status}] {service}")

except Exception as e:
    print(f"   [INFO] Docker check error: {e}")

print("\n3. HEALTH ENDPOINTS:")
import asyncio

import aiohttp


async def check_health():
    endpoints = [
        ("API Server", "http://localhost:8003/health"),
        ("API Server (alt)", "http://localhost:8000/health"),
    ]

    for name, url in endpoints:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=3) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        print(f"   [OK] {name}: {data}")
                    else:
                        print(f"   [FAIL] {name}: Status {resp.status}")
        except Exception as e:
            print(f"   [INFO] {name}: {str(e)[:50]}")


asyncio.run(check_health())

print("\n4. DOCKER COMPOSE CONFIGURATIE CHECK:")
# Check of docker-compose.yml de juiste configuratie heeft
try:
    with open("docker-compose.yml", "r") as f:
        compose_content = f.read()

    checks = [
        ("TRADING_MODE=paper", "TRADING_MODE=paper in compose"),
        ("ipc: host", "IPC host mode"),
        ("redis", "Redis service"),
        ("postgres", "PostgreSQL service"),
        ("api-server", "API server service"),
    ]

    for check, desc in checks:
        status = "OK" if check in compose_content else "INFO"
        print(f"   [{status}] {desc}")

except Exception as e:
    print(f"   [INFO] Docker compose check: {e}")

print("\n5. ENVIRONMENT VARIABLES:")
import os

env_checks = [
    ("TRADING_MODE", "paper"),
    ("REDIS_URL", None),
    ("DATABASE_URL", None),
]

for var, expected in env_checks:
    value = os.getenv(var)
    if expected:
        status = "OK" if value == expected else "FAIL"
        print(f"   [{status}] {var}={value} (expected: {expected})")
    else:
        status = "OK" if value else "INFO"
        print(f'   [{status}] {var}={value[:30] if value else "not set"}')

print("\n" + "=" * 60)
print("STAP 11-12: DOCKER & HEALTH CHECKS VOLTOOID")
print("=" * 60)
