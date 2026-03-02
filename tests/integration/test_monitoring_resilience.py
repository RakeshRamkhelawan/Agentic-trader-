from fastapi.testclient import TestClient
import sys
import os
import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock

# Add project root to path
sys.path.append(os.getcwd())

from backend.api.main import app
from backend.llm.service import LLMService
from backend.llm.providers import MockProvider, LLMProvider
from backend.llm.resilience import CircuitBreaker, CircuitBreakerOpenException

client = TestClient(app)

def test_metrics_endpoint():
    """Test that /metrics endpoint is exposed and returns Prometheus data."""
    print("\n[TEST] Metrics Endpoint")
    response = client.get("/metrics")
    
    if response.status_code != 200:
        print(f"FAILED: /metrics returned {response.status_code}")
        print(response.text)
        assert False
        
    print("SUCCESS: /metrics returned 200 OK")
    assert "http_requests_total" in response.text
    assert "http_request_duration_seconds" in response.text
    print("SUCCESS: Found expected metrics keys.")

@pytest.mark.asyncio
async def test_circuit_breaker_fallback():
    """Test Circuit Breaker and Fallback logic."""
    print("\n[TEST] Circuit Breaker & Fallback")
    
    # 1. Setup Failing Provider
    failing_provider = MagicMock(spec=LLMProvider)
    failing_provider.generate_text = AsyncMock(side_effect=Exception("API Error"))
    failing_provider.__class__.__name__ = "FailingProvider"
    
    # 2. Setup Fallback Provider
    fallback_provider = MagicMock(spec=LLMProvider)
    fallback_provider.generate_text = AsyncMock(return_value="Fallback Response")
    fallback_provider.__class__.__name__ = "FallbackProvider"
    
    # 3. Init Service with short recovery timeout
    service = LLMService(provider=failing_provider, fallback_provider=fallback_provider)
    service.circuit_breaker.failure_threshold = 2
    service.circuit_breaker.recovery_timeout = 1
    
    # 4. Trigger Failures
    print("Triggering failures...")
    try:
        await service.generate_explanation("test") # Failure 1
    except:
        pass
        
    try:
        await service.generate_explanation("test") # Failure 2 -> Circuit OPENS
    except:
        pass
        
    # Circuit should be OPEN now (threshold 2 reached? logic says failure_count >= threshold)
    # Check if breaker state is OPEN
    # But wait, logic is: handle_failure increments count.
    # We need to ensure we hit the threshold.
    
    # 5. Verify Fallback (Circuit might be Open or Exception raised caught by service)
    # Service logic catches Exception AND CircuitBreakerOpenException and tries fallback.
    
    print("Testing Fallback...")
    response = await service.generate_explanation("test")
    
    print(f"Response: {response}")
    assert response == "Fallback Response"
    print("SUCCESS: Fallback provider was used.")
    
    # Verify primary was called
    assert failing_provider.generate_text.called
    # Verify fallback was called
    assert fallback_provider.generate_text.called

if __name__ == "__main__":
    # Run sync test
    test_metrics_endpoint()
    
    # Run async test
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(test_circuit_breaker_fallback())
    loop.close()
