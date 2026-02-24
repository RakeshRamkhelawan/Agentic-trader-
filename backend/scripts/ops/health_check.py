import argparse
import asyncio
import os
import sys
import time
from dataclasses import dataclass
from enum import Enum

try:
    import httpx
    import psycopg
    import redis.asyncio as aioredis
except ImportError:
    print("Installing required dependencies...")
    import subprocess

    subprocess.check_call([sys.executable, "-m", "pip", "install", "redis", "psycopg", "httpx"])
    import httpx
    import psycopg
    import redis.asyncio as aioredis

# Import from backend package directly (assuming running as module)
try:
    from backend.execution.paper_exchange import PaperExchange
except ImportError:
    # Fallback for direct execution if PYTHONPATH isn't set
    sys.path.append(os.getcwd())
    from backend.execution.paper_exchange import PaperExchange


class HealthStatus(Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    UNKNOWN = "UNKNOWN"


@dataclass
class ServiceCheck:
    name: str
    status: HealthStatus
    latency_ms: float
    details: str
    endpoint: str = ""


class InfrastructureVerifier:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: list[ServiceCheck] = []

        self.config = {
            "redis_url": os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            "postgres_dsn": os.getenv(
                "DATABASE_URL",
                "postgresql://trader:trading_secure@localhost:5432/trading_db",
            ),
            "backend_url": os.getenv("BACKEND_URL", "http://localhost:8001"),
            "clickhouse_url": os.getenv("CLICKHOUSE_URL", "http://localhost:8123"),
        }

    async def check_redis(self) -> ServiceCheck:
        start_time = time.time()
        try:
            client = aioredis.from_url(
                self.config["redis_url"],
                decode_responses=True,
                socket_connect_timeout=5,
            )

            await client.ping()

            test_key = "health_check_test"
            await client.set(test_key, "ok", ex=10)
            await client.get(test_key)
            await client.delete(test_key)

            info = await client.info()
            connected_clients = info.get("connected_clients", 0)
            used_memory_human = info.get("used_memory_human", "N/A")

            await client.aclose()

            latency = (time.time() - start_time) * 1000

            return ServiceCheck(
                name="Redis Cache",
                status=HealthStatus.HEALTHY,
                latency_ms=round(latency, 2),
                details=f"Clients: {connected_clients}, Memory: {used_memory_human}",
                endpoint=self.config["redis_url"],
            )

        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return ServiceCheck(
                name="Redis Cache",
                status=HealthStatus.UNHEALTHY,
                latency_ms=round(latency, 2),
                details=f"Error: {str(e)[:100]}",
                endpoint=self.config["redis_url"],
            )

    async def check_postgres(self) -> ServiceCheck:
        start_time = time.time()
        try:
            # Handle SQLAlchemy DSNs (asyncpg) by removing +asyncpg if present for psycopg check
            dsn = self.config["postgres_dsn"].replace("+asyncpg", "")

            conn = await psycopg.AsyncConnection.connect(dsn, connect_timeout=5)

            async with conn.cursor() as cur:
                await cur.execute("SELECT version();")
                await cur.fetchone()

                await cur.execute("SELECT COUNT(*) FROM pg_stat_activity;")
                connections = await cur.fetchone()

            await conn.close()

            latency = (time.time() - start_time) * 1000

            return ServiceCheck(
                name="PostgreSQL Database",
                status=HealthStatus.HEALTHY,
                latency_ms=round(latency, 2),
                details=f"Active connections: {connections[0]}",
                endpoint=dsn.split("@")[1] if "@" in dsn else "Unknown",
            )

        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return ServiceCheck(
                name="PostgreSQL Database",
                status=HealthStatus.UNHEALTHY,
                latency_ms=round(latency, 2),
                details=f"Error: {str(e)[:100]}",
                endpoint="DB",
            )

    async def check_backend_api(self) -> ServiceCheck:
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.config['backend_url']}/health")

                latency = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    data = response.json()
                    return ServiceCheck(
                        name="Backend API",
                        status=HealthStatus.HEALTHY,
                        latency_ms=round(latency, 2),
                        details=f"Status: {data.get('status', 'ok')}",
                        endpoint=self.config["backend_url"],
                    )
                else:
                    return ServiceCheck(
                        name="Backend API",
                        status=HealthStatus.DEGRADED,
                        latency_ms=round(latency, 2),
                        details=f"HTTP {response.status_code}",
                        endpoint=self.config["backend_url"],
                    )

        except httpx.ConnectError:
            latency = (time.time() - start_time) * 1000
            return ServiceCheck(
                name="Backend API",
                status=HealthStatus.UNHEALTHY,
                latency_ms=round(latency, 2),
                details="Connection refused - service not running",
                endpoint=self.config["backend_url"],
            )
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return ServiceCheck(
                name="Backend API",
                status=HealthStatus.UNHEALTHY,
                latency_ms=round(latency, 2),
                details=f"Error: {str(e)[:100]}",
                endpoint=self.config["backend_url"],
            )

    async def check_clickhouse(self) -> ServiceCheck:
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.config['clickhouse_url']}/ping")

                latency = (time.time() - start_time) * 1000

                if response.status_code == 200 and response.text.strip() == "Ok.":
                    return ServiceCheck(
                        name="ClickHouse Analytics",
                        status=HealthStatus.HEALTHY,
                        latency_ms=round(latency, 2),
                        details="Service operational",
                        endpoint=self.config["clickhouse_url"],
                    )
                else:
                    return ServiceCheck(
                        name="ClickHouse Analytics",
                        status=HealthStatus.DEGRADED,
                        latency_ms=round(latency, 2),
                        details=f"HTTP {response.status_code}",
                        endpoint=self.config["clickhouse_url"],
                    )

        except httpx.ConnectError:
            latency = (time.time() - start_time) * 1000
            return ServiceCheck(
                name="ClickHouse Analytics",
                status=HealthStatus.UNHEALTHY,
                latency_ms=round(latency, 2),
                details="Connection refused - service not running",
                endpoint=self.config["clickhouse_url"],
            )
        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return ServiceCheck(
                name="ClickHouse Analytics",
                status=HealthStatus.UNHEALTHY,
                latency_ms=round(latency, 2),
                details=f"Error: {str(e)[:100]}",
                endpoint=self.config["clickhouse_url"],
            )

    async def check_broker_mock(self) -> ServiceCheck:
        start_time = time.time()
        try:
            exchange = PaperExchange()
            balance = exchange.fetch_balance()

            latency = (time.time() - start_time) * 1000

            return ServiceCheck(
                name="Mock/Paper Broker",
                status=HealthStatus.HEALTHY,
                latency_ms=round(latency, 2),
                details=f"Paper trading ready, accounts: {len(balance)}",
                endpoint="in-memory",
            )

        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return ServiceCheck(
                name="Mock/Paper Broker",
                status=HealthStatus.DEGRADED,
                latency_ms=round(latency, 2),
                details=f"Warning: {str(e)[:100]}",
                endpoint="in-memory",
            )

    def render_results(self):
        print("\n" + "=" * 80)
        print(" " * 20 + "INFRASTRUCTURE HEALTH CHECK RESULTS")
        print("=" * 80)
        print(f"{'Service':<25} {'Status':<12} {'Latency (ms)':<15} {'Details':<30}")
        print("-" * 80)

        status_symbols = {
            HealthStatus.HEALTHY: "[OK]",
            HealthStatus.DEGRADED: "[WARN]",
            HealthStatus.UNHEALTHY: "[FAIL]",
            HealthStatus.UNKNOWN: "[?]",
        }

        for result in self.results:
            symbol = status_symbols[result.status]
            print(
                f"{result.name:<25} {symbol:<12} {result.latency_ms:<15.2f} {result.details[:30]:<30}"
            )
            if self.verbose:
                print(f"  Endpoint: {result.endpoint}")

        print("-" * 80)

        healthy_count = sum(1 for r in self.results if r.status == HealthStatus.HEALTHY)
        total_count = len(self.results)

        print(f"\nSummary: {healthy_count}/{total_count} services healthy")

        if healthy_count == total_count:
            print("Status: ALL SYSTEMS OPERATIONAL")
            return True
        elif healthy_count >= total_count * 0.5:
            print("Status: PARTIAL OUTAGE")
            return False
        else:
            print("Status: CRITICAL FAILURES")
            return False

    async def run_all_checks(self):
        print("\nSamkhya Yoga Agentic Trader - Deep Infrastructure Health Check")
        print("Running health checks...")

        checks = [
            ("Redis Cache", self.check_redis()),
            ("PostgreSQL Database", self.check_postgres()),
            ("Backend API", self.check_backend_api()),
            ("ClickHouse Analytics", self.check_clickhouse()),
            ("Mock/Paper Broker", self.check_broker_mock()),
        ]

        for check_name, check_coro in checks:
            print(f"  Checking {check_name}...", end=" ")
            result = await check_coro
            self.results.append(result)
            print(f"{result.status.value}")

        success = self.render_results()
        return success


async def main():
    parser = argparse.ArgumentParser(description="Infrastructure health verification")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed information")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    args = parser.parse_args()

    verifier = InfrastructureVerifier(verbose=args.verbose)

    try:
        success = await verifier.run_all_checks()

        if args.json:
            import json

            output = {
                "timestamp": time.time(),
                "overall_status": "healthy" if success else "unhealthy",
                "services": [
                    {
                        "name": r.name,
                        "status": r.status.name.lower(),
                        "latency_ms": r.latency_ms,
                        "details": r.details,
                        "endpoint": r.endpoint,
                    }
                    for r in verifier.results
                ],
            }
            print("\n" + json.dumps(output, indent=2))

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\nHealth check interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
