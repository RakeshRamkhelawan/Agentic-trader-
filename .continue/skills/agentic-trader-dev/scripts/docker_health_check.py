#!/usr/bin/env python3
"""
Docker Health Check - Diagnose and fix common Docker/infrastructure issues.

Usage:
    python docker_health_check.py
    python docker_health_check.py --fix
    python docker_health_check.py --service api-server
"""

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ServiceStatus:
    """Status of a Docker service."""
    name: str
    container_status: str = "unknown"
    health_status: str = "unknown"
    ports: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    
    @property
    def is_healthy(self) -> bool:
        return self.health_status == "healthy" or (
            self.container_status == "running" and self.health_status == "unknown"
        )


def run_command(cmd: list[str], capture=True) -> tuple[int, str, str]:
    """Run a shell command and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=capture,
            text=True,
            timeout=30
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)


def get_compose_file() -> str:
    """Determine which docker-compose file to use."""
    import os
    if os.path.exists("docker-compose.yml"):
        return "docker-compose.yml"
    elif os.path.exists("docker-compose.yaml"):
        return "docker-compose.yaml"
    return "docker-compose.yml"


def get_service_status(service_name: str) -> ServiceStatus:
    """Get status of a specific service."""
    status = ServiceStatus(name=service_name)
    compose_file = get_compose_file()
    
    # Get container status
    exit_code, stdout, stderr = run_command([
        "docker", "compose", "-f", compose_file, 
        "ps", service_name, "--format", "json"
    ])
    
    if exit_code == 0 and stdout:
        try:
            # Handle both single JSON object and array
            data = json.loads(stdout)
            if isinstance(data, list):
                data = data[0] if data else {}
            
            status.container_status = data.get("State", "unknown")
            status.health_status = data.get("Health", "unknown")
            
            # Get ports
            publishers = data.get("Publishers", [])
            status.ports = [f"{p.get('PublishedPort', '?')}->{p.get('TargetPort', '?')}"
                          for p in publishers]
        except json.JSONDecodeError:
            # Fallback for non-JSON output
            if "running" in stdout.lower():
                status.container_status = "running"
    
    # Check for common issues
    if status.container_status != "running":
        status.issues.append(f"Container not running: {status.container_status}")
    
    if status.health_status == "unhealthy":
        status.issues.append("Health check failing")
    
    return status


def get_all_services() -> list[str]:
    """Get list of all services from docker-compose."""
    compose_file = get_compose_file()
    exit_code, stdout, _ = run_command([
        "docker", "compose", "-f", compose_file, "config", "--services"
    ])
    
    if exit_code == 0:
        return [s.strip() for s in stdout.strip().split("\n") if s.strip()]
    return []


def get_logs(service_name: str, tail: int = 20) -> str:
    """Get recent logs for a service."""
    compose_file = get_compose_file()
    exit_code, stdout, _ = run_command([
        "docker", "compose", "-f", compose_file, 
        "logs", service_name, "--tail", str(tail)
    ])
    return stdout if exit_code == 0 else "Failed to get logs"


def check_port_usage(port: int) -> list[dict]:
    """Check what processes are using a port."""
    exit_code, stdout, _ = run_command([
        "netstat", "-ano", "|", "findstr", f":{port}"
    ])
    
    # Fallback for different systems
    if exit_code != 0 or not stdout:
        exit_code, stdout, _ = run_command([
            "lsof", "-i", f":{port}"
        ])
    
    return stdout


def diagnose_service(service_name: str, fix: bool = False) -> ServiceStatus:
    """Diagnose a specific service and optionally fix issues."""
    status = get_service_status(service_name)
    
    print(f"\n{'='*70}")
    print(f"Service: {service_name}")
    print(f"{'='*70}")
    print(f"Container: {status.container_status}")
    print(f"Health:    {status.health_status}")
    if status.ports:
        print(f"Ports:     {', '.join(status.ports)}")
    
    if status.issues:
        print(f"\n⚠️  Issues Found:")
        for issue in status.issues:
            print(f"   - {issue}")
        
        if fix:
            print(f"\n🔧 Attempting fixes...")
            fix_service(service_name, status)
    else:
        print(f"\n✅ Service is healthy")
    
    # Show recent logs if unhealthy
    if not status.is_healthy:
        print(f"\n📋 Recent Logs (last 10 lines):")
        logs = get_logs(service_name, tail=10)
        for line in logs.split("\n")[-10:]:
            if line.strip():
                print(f"   {line}")
    
    return status


def fix_service(service_name: str, status: ServiceStatus):
    """Attempt to fix common issues with a service."""
    compose_file = get_compose_file()
    
    for issue in status.issues:
        if "curl not found" in issue.lower() or "health check" in issue.lower():
            print(f"   Rebuilding {service_name}...")
            run_command([
                "docker", "compose", "-f", compose_file, 
                "build", "--no-cache", service_name
            ])
            run_command([
                "docker", "compose", "-f", compose_file, 
                "up", "-d", "--build", service_name
            ])
            print(f"   ✅ Rebuilt {service_name}")
            
        elif "not running" in issue.lower():
            print(f"   Starting {service_name}...")
            run_command([
                "docker", "compose", "-f", compose_file, 
                "up", "-d", service_name
            ])
            print(f"   ✅ Started {service_name}")


def check_infrastructure():
    """Check infrastructure services (PostgreSQL, Redis, etc.)."""
    infra_services = ["db", "postgres", "redis", "clickhouse", "chromadb", "redpanda"]
    
    print(f"\n{'='*70}")
    print("Infrastructure Services")
    print(f"{'='*70}")
    
    all_services = get_all_services()
    
    for service in infra_services:
        if service in all_services:
            status = get_service_status(service)
            icon = "✅" if status.is_healthy else "❌"
            print(f"{icon} {service:<20} {status.container_status:<12} {status.health_status}")


def main():
    parser = argparse.ArgumentParser(
        description='Diagnose Docker service health'
    )
    parser.add_argument(
        '--service', '-s',
        help='Check specific service only'
    )
    parser.add_argument(
        '--fix', '-f',
        action='store_true',
        help='Attempt to fix issues automatically'
    )
    parser.add_argument(
        '--infrastructure', '-i',
        action='store_true',
        help='Check infrastructure services only'
    )
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='Check all services'
    )
    
    args = parser.parse_args()
    
    # Check docker is running
    exit_code, _, _ = run_command(["docker", "version"])
    if exit_code != 0:
        print("❌ Docker is not running or not installed")
        sys.exit(1)
    
    if args.service:
        diagnose_service(args.service, fix=args.fix)
    
    elif args.infrastructure:
        check_infrastructure()
    
    elif args.all:
        services = get_all_services()
        unhealthy_count = 0
        
        for service in services:
            status = diagnose_service(service, fix=args.fix)
            if not status.is_healthy:
                unhealthy_count += 1
        
        print(f"\n{'='*70}")
        print(f"Summary: {len(services) - unhealthy_count}/{len(services)} services healthy")
        print(f"{'='*70}")
    
    else:
        # Default: check common services
        common_services = ["api-server", "frontend", "postgres", "redis"]
        all_services = get_all_services()
        
        for service in common_services:
            if service in all_services:
                diagnose_service(service, fix=args.fix)
        
        # Also show quick infrastructure status
        check_infrastructure()
        
        print(f"\n💡 Tip: Use --all to check all services, --fix to auto-fix issues")


if __name__ == '__main__':
    main()
