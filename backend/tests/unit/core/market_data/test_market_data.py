from unittest.mock import AsyncMock

import pytest

from backend.core.market_data.circuit_breaker import CircuitBreaker, CircuitState

# Ensure ccxt is mocked if not installed, but here we import ExchangeInterface
# which imports ccxt. If ccxt is missing, this import fails.
# Assuming ccxt is present or mocked via other means if needed.
from backend.core.market_data.exchange_interface import ExchangeInterface


class TestMarketData:

    @pytest.mark.asyncio
    async def test_circuit_breaker_trip(self):
        breaker = CircuitBreaker(name="test_breaker", fail_threshold=2)

        # State should be CLOSED initially
        assert breaker.state == CircuitState.CLOSED

        # 1st failure
        await breaker.record_failure()
        assert breaker.state == CircuitState.CLOSED

        # 2nd failure -> Trip
        await breaker.record_failure()
        assert breaker.state == CircuitState.OPEN

        # Request should be blocked
        assert breaker.allow_request() is False

    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery(self):
        breaker = CircuitBreaker(name="test_recovery", fail_threshold=1, recovery_timeout=0.1)

        await breaker.record_failure()
        assert breaker.state == CircuitState.OPEN

        # Wait for timeout
        import asyncio

        await asyncio.sleep(0.15)

        # Probe request allowed -> Half Open
        assert breaker.allow_request() is True
        assert breaker.state == CircuitState.HALF_OPEN

        # Success -> Closed
        await breaker.record_success()
        assert breaker.state == CircuitState.CLOSED

    @pytest.mark.asyncio
    async def test_exchange_fetch_ticker_protected(self):
        # Create a mock exchange with AsyncMock methods
        mock_exchange = AsyncMock()
        mock_exchange.fetch_ticker.return_value = {"symbol": "BTC/USD", "last": 50000.0}

        # Inject mock exchange
        interface = ExchangeInterface(exchange_override=mock_exchange)

        # Test successful fetch
        ticker = await interface.fetch_ticker("BTC/USD")
        assert ticker["last"] == 50000.0
        assert interface.circuit_breaker.failure_count == 0

        # Test failure
        mock_exchange.fetch_ticker.side_effect = Exception("API Error")

        # Should return None and record failure
        ticker = await interface.fetch_ticker("BTC/USD")
        assert ticker is None
        assert interface.circuit_breaker.failure_count == 1
