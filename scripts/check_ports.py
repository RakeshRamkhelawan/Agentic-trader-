#!/usr/bin/env python3
"""
DOCKER PORT CHECKER
Controleert welke poorten al bezet zijn in docker-compose.yml
"""

import subprocess
import socket
import sys
from datetime import datetime

# Poorten uit docker-compose.yml (host:container)
DOCKER_PORTS = [
    # Infrastructure
    ("Redpanda Kafka", 9094, "Kafka API"),
    ("Redpanda Console", 8081, "Web UI"),
    ("ClickHouse HTTP", 8124, "HTTP interface"),
    ("ClickHouse Native", 9001, "Native protocol"),
    ("PostgreSQL", 5456, "Database"),
    ("Redis", 6380, "Cache"),
    ("ChromaDB", 8005, "Vector DB"),
    ("Prometheus", 9091, "Metrics"),
    ("Grafana", 3100, "Dashboards"),

    # Application
    ("API Server", 8000, "FastAPI Backend"),
    ("Federated Triad", 8001, "AI Service"),
    ("Frontend", 5173, "React Dev"),
    ("Frontend Alt", 3000, "React Alt"),
    ("Frontend Prod", 80, "Nginx HTTP"),
    ("Frontend Prod SSL", 443, "Nginx HTTPS"),
]

def check_port(port):
    """Check if a port is in use"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result == 0
    except Exception:
        return False

def get_process_using_port(port):
    """Get process name using a port"""
    try:
        # Windows: use netstat
        result = subprocess.run(
            ['netstat', '-ano', '-p', 'TCP'],
            capture_output=True,
            text=True,
            timeout=5
        )
        for line in result.stdout.split('\n'):
            if f':{port}' in line and 'LISTENING' in line:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    try:
                        proc = subprocess.run(
                            ['tasklist', '/FI', f'PID eq {pid}'],
                            capture_output=True,
                            text=True,
                            timeout=2
                        )
                        for proc_line in proc.stdout.split('\n')[3:]:
                            if proc_line.strip():
                                return proc_line.split()[0]
                    except:
                        return f"PID:{pid}"
        return None
    except Exception as e:
        return None

def main():
    print("=" * 60)
    print("  DOCKER PORT CONFLICT CHECKER")
    print("=" * 60)
    print()

    print(f"Checking {len(DOCKER_PORTS)} ports...")
    print()

    conflicts = []
    available = []

    for service, port, description in DOCKER_PORTS:
        if check_port(port):
            process = get_process_using_port(port)
            status = f"IN USE by {process}" if process else "IN USE"
            print(f"[X] Port {port:5d} - {service:20s} [{status}]")
            conflicts.append((service, port, process, description))
        else:
            print(f"[OK] Port {port:5d} - {service:20s} [AVAILABLE]")
            available.append((service, port, description))

    # Summary
    print()
    print("=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print()

    if not conflicts:
        print("[SUCCESS] All ports are available!")
        print("   You can start Docker without conflicts.")
        print()
    else:
        print(f"[WARNING] Found {len(conflicts)} port conflicts!")
        print()

        print("Conflicting Ports:")
        print("-" * 60)
        for service, port, process, desc in conflicts:
            proc_str = f"({process})" if process else ""
            print(f"  {service:20s} Port {port:5d} {proc_str}")
        print()

        print("Suggested Alternative Ports:")
        print("-" * 60)
        for service, port, process, desc in conflicts:
            suggested = port + 1000
            # Check if suggested is also in use
            while check_port(suggested):
                suggested += 1000
            print(f"  {service}:")
            print(f"    Original:  {port}")
            print(f"    Suggested: {suggested}")
            print()

        print("To resolve conflicts:")
        print("  1. Stop the conflicting services")
        print("  2. Use: docker-compose -p agentic-trader up -d")
        print("  3. Or modify docker-compose.yml ports")
        print()

    # Check Docker
    print("=" * 60)
    print("  DOCKER STATUS")
    print("=" * 60)
    print()

    try:
        result = subprocess.run(
            ['docker', 'info'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("[OK] Docker is running")

            # Check containers
            result = subprocess.run(
                ['docker', 'ps', '--format', '{{.Names}}'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.stdout.strip():
                print()
                print("Running containers:")
                for name in result.stdout.strip().split('\n'):
                    print(f"  - {name}")
            else:
                print()
                print("No running containers")
        else:
            print("[ERROR] Docker is not running!")
            print("   Please start Docker Desktop.")
    except FileNotFoundError:
        print("[ERROR] Docker is not installed!")
    except Exception as e:
        print(f"[ERROR] Error checking Docker: {e}")

    print()
    print("=" * 60)

if __name__ == "__main__":
    main()
