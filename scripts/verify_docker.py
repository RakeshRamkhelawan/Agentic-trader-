#!/usr/bin/env python3
"""
Docker Setup Verification Script

Checks that all Docker files are correctly configured.
"""

import os
import sys


def check_files():
    """Check that all required Docker files exist."""
    print("=" * 60)
    print("DOCKER SETUP VERIFICATION")
    print("=" * 60)

    files = [
        'Dockerfile',
        'docker-compose.yml',
        'docker-compose.override.yml',
        'docker-compose.prod.yml',
        '.dockerignore',
        '.env.example',
        'redis.conf',
        'nginx/nginx.conf',
        'scripts/docker-start.sh',
        'scripts/docker-start.ps1'
    ]

    print("\n[1] Checking Docker files...")
    all_exist = True
    for f in files:
        exists = os.path.exists(f)
        status = "OK" if exists else "MISSING"
        print(f"  [{status}] {f}")
        if not exists:
            all_exist = False

    return all_exist


def check_requirements():
    """Check that requirements.txt has all dependencies."""
    print("\n[2] Checking requirements.txt...")

    try:
        with open('requirements.txt', 'r') as f:
            content = f.read().lower()

        deps = ['fastapi', 'uvicorn', 'redis', 'numpy', 'mcp']
        all_found = True

        for dep in deps:
            found = dep in content
            status = "OK" if found else "MISSING"
            print(f"  [{status}] {dep}")
            if not found:
                all_found = False

        return all_found
    except FileNotFoundError:
        print("  [ERROR] requirements.txt not found!")
        return False


def check_cache_config():
    """Check that CacheConfig reads from environment."""
    print("\n[3] Checking CacheConfig...")

    try:
        with open('backend/mcp_broker/performance/cache.py', 'r') as f:
            content = f.read()

        has_env = 'REDIS_URL' in content and 'os.getenv' in content
        has_post_init = '__post_init__' in content

        status = "OK" if (has_env and has_post_init) else "MISSING"
        print(f"  [{status}] REDIS_URL from environment")

        return has_env and has_post_init
    except FileNotFoundError:
        print("  [ERROR] cache.py not found!")
        return False


def main():
    """Run all checks."""
    checks = [
        ("Files", check_files),
        ("Requirements", check_requirements),
        ("Cache Config", check_cache_config),
    ]

    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n[ERROR] {name} check failed: {e}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    all_passed = True
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  [{status}] {name}")
        if not result:
            all_passed = False

    print("=" * 60)

    if all_passed:
        print("[SUCCESS] Docker setup complete!")
        print("\nNext steps:")
        print("  1. cp .env.example .env")
        print("  2. ./scripts/docker-start.sh dev  (or .\\scripts\\docker-start.ps1 dev on Windows)")
        print("  3. Visit http://localhost:8000/docs")
        return 0
    else:
        print("[WARNING] Some checks failed. Please review above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
