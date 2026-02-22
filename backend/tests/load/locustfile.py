"""
Load Testing with Locust (Sprint 4 S4-3).

Tests platform under load:
- 10k events/s throughput
- 100 concurrent tenants
- WebSocket tick ingestion
- Rate limit stress tests
- Cold-path queue saturation

Usage:
    locust -f backend/tests/load/locustfile.py --host=http://localhost:8000
    
Or via Docker:
    docker run -p 8089:8089 -v $(pwd)/backend/tests/load:/mnt/locust locustio/locust -f /mnt/locust/locustfile.py
"""

import json
import random
import uuid
from datetime import datetime, timezone

from locust import HttpUser, between, events, task
from locust.runners import MasterRunner

# Test configuration
TENANT_COUNT = 100
SYMBOLS = ["BTC-EUR", "ETH-EUR", "SOL-EUR", "ADA-EUR", "DOT-EUR"]


class TradingPlatformUser(HttpUser):
    """
    Simulated trading platform user.
    
    Behavior:
    - Authenticates with JWT
    - Ingests market data (WebSocket simulation via HTTP)
    - Places orders
    - Checks positions
    """
    
    wait_time = between(0.001, 0.1)  # 1-100ms between requests (high frequency)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tenant_id = f"tenant_{random.randint(1, TENANT_COUNT)}"
        self.user_id = f"user_{uuid.uuid4().hex[:8]}"
        self.token = None
        self.symbol = random.choice(SYMBOLS)
    
    def on_start(self):
        """Login and get JWT token."""
        # Simulate login
        response = self.client.post(
            "/api/v1/auth/login",
            json={
                "username": f"test_{self.user_id}",
                "password": "test_password",
            },
            headers={"X-Tenant-ID": self.tenant_id},
        )
        
        if response.status_code == 200:
            self.token = response.json().get("access_token")
        else:
            # For load testing, create a mock token if auth fails
            self.token = f"mock_token_{self.user_id}"
    
    @task(10)
    def ingest_tick(self):
        """
        Simulate WebSocket tick ingestion.
        High frequency - 10x weight
        """
        tick_data = {
            "symbol": self.symbol,
            "price": random.uniform(100, 50000),
            "volume": random.uniform(0.1, 100),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trace_id": str(uuid.uuid4()),
        }
        
        self.client.post(
            "/api/v1/market/tick",
            json=tick_data,
            headers={
                "Authorization": f"Bearer {self.token}",
                "X-Tenant-ID": self.tenant_id,
                "X-Trace-ID": tick_data["trace_id"],
            },
            name="/api/v1/market/tick",
        )
    
    @task(3)
    def place_order(self):
        """
        Place order.
        Medium frequency - 3x weight
        """
        order = {
            "symbol": self.symbol,
            "side": random.choice(["buy", "sell"]),
            "quantity": random.uniform(0.01, 1.0),
            "order_type": "market",
        }
        
        self.client.post(
            "/api/v1/orders",
            json=order,
            headers={
                "Authorization": f"Bearer {self.token}",
                "X-Tenant-ID": self.tenant_id,
            },
            name="/api/v1/orders",
        )
    
    @task(2)
    def get_positions(self):
        """Get current positions."""
        self.client.get(
            "/api/v1/positions",
            headers={
                "Authorization": f"Bearer {self.token}",
                "X-Tenant-ID": self.tenant_id,
            },
            name="/api/v1/positions",
        )
    
    @task(1)
    def get_analytics(self):
        """Get analytics (cold path query)."""
        self.client.get(
            "/api/v1/analytics/portfolio",
            headers={
                "Authorization": f"Bearer {self.token}",
                "X-Tenant-ID": self.tenant_id,
            },
            name="/api/v1/analytics/portfolio",
        )


class HighFrequencyUser(TradingPlatformUser):
    """
    High-frequency trading user.
    Sends more requests with less delay.
    """
    wait_time = between(0.0001, 0.01)  # 0.1-10ms
    weight = 1  # 1 in 10 users is HFT
    
    @task(100)
    def ingest_tick(self):
        """Ultra-high frequency tick ingestion."""
        super().ingest_tick()


class RateLimitTester(HttpUser):
    """
    User that tests rate limiting.
    Sends requests rapidly to trigger rate limits.
    """
    wait_time = between(0, 0.001)  # Minimal delay
    
    @task
    def hammer_api(self):
        """Rapid-fire API calls."""
        endpoints = [
            "/api/v1/market/ticker",
            "/api/v1/market/orderbook",
            "/health",
        ]
        
        for endpoint in endpoints:
            self.client.get(
                endpoint,
                headers={"X-Tenant-ID": f"tenant_{random.randint(1, 10)}"},
                name=f"{endpoint} [rate-test]",
            )


class ColdPathSaturator(HttpUser):
    """
    User that saturates cold path (LLM queue).
    Sends anomaly detection requests.
    """
    wait_time = between(0.1, 1.0)
    
    @task
    def trigger_anomaly_analysis(self):
        """Trigger LLM-based anomaly detection."""
        anomaly_data = {
            "symbol": random.choice(SYMBOLS),
            "anomaly_type": random.choice(["volume_spike", "price_gap", "pattern_break"]),
            "severity": random.choice(["low", "medium", "high"]),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        with self.client.post(
            "/api/v1/anomaly/detect",
            json=anomaly_data,
            catch_response=True,
        ) as response:
            # DLQ should handle overflow gracefully
            if response.status_code == 202:
                response.success()
            elif response.status_code == 503:
                # Queue saturated - expected under extreme load
                response.success()
            elif response.status_code == 429:
                # Rate limited - expected
                response.success()


# Custom events for metrics
tick_counter = 0
order_counter = 0


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, 
               response, context, exception, **kwargs):
    """Track custom metrics."""
    global tick_counter, order_counter
    
    if "tick" in name and request_type == "POST":
        tick_counter += 1
    elif "orders" in name and request_type == "POST":
        order_counter += 1


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print summary at end of test."""
    print(f"\n{'='*60}")
    print(f"LOAD TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Total ticks ingested: {tick_counter}")
    print(f"Total orders placed: {order_counter}")
    print(f"Target: 10k events/s")
    
    if isinstance(environment.runner, MasterRunner):
        # Aggregated stats from master
        stats = environment.runner.stats
        total_reqs = stats.total.num_requests
        total_failures = stats.total.num_failures
        avg_rps = stats.total.total_rps
        
        print(f"\nAggregated Results:")
        print(f"  Total Requests: {total_reqs}")
        print(f"  Failed Requests: {total_failures}")
        print(f"  Average RPS: {avg_rps:.2f}")
        print(f"  Failure Rate: {(total_failures/max(total_reqs,1)*100):.2f}%")
    
    print(f"{'='*60}\n")


# Run configuration
# locust -f backend/tests/load/locustfile.py \
#        --host=http://localhost:8000 \
#        --users=1000 \
#        --spawn-rate=100 \
#        --run-time=5m \
#        --headless
