"""
Prediction Market Intelligence Client

HTTP client for communicating with the prediction-intelligence container.
Provides resilient access to market signals and analysis.
"""

import asyncio
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""

    failure_threshold: int = 5
    recovery_timeout: int = 30
    half_open_max_calls: int = 3


class PredictionSignal(BaseModel):
    """Signal response from prediction service."""

    id: str
    market: str
    category: str
    signal_type: str
    confidence: float
    symbol: str | None
    indicators: dict[str, float]
    timestamp: datetime
    metadata: dict[str, Any]


class PredictionMarketClient:
    """
    Async HTTP client for Prediction Market Intelligence service.

    Features:
    - Async/await support for FastAPI
    - Circuit breaker for resilience
    - Retry with exponential backoff
    - Connection pooling

    Usage:
        client = PredictionMarketClient()
        signals = await client.get_signals(category="crypto")
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        circuit_config: CircuitBreakerConfig | None = None,
    ):
        """
        Initialize client.

        Args:
            base_url: Service URL (default from env)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            circuit_config: Circuit breaker configuration
        """
        self.base_url = base_url or os.getenv(
            "PREDICTION_SERVICE_URL", "http://prediction-intelligence:8002"
        )
        self.timeout = timeout
        self.max_retries = max_retries
        self.enabled = os.getenv("PREDICTION_SERVICE_ENABLED", "true").lower() == "true"

        # Circuit breaker state
        self._circuit_config = circuit_config or CircuitBreakerConfig()
        self._circuit_state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: datetime | None = None
        self._half_open_calls = 0

        # HTTP client with connection pooling
        self._client: httpx.AsyncClient | None = None

        logger.info(f"PredictionMarketClient initialized: {self.base_url}, enabled={self.enabled}")

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            )
        return self._client

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    # =========================================================================
    # CIRCUIT BREAKER
    # =========================================================================

    def _check_circuit(self) -> bool:
        """Check if circuit allows requests."""
        if self._circuit_state == CircuitState.CLOSED:
            return True

        if self._circuit_state == CircuitState.OPEN:
            # Check if recovery timeout passed
            if self._last_failure_time:
                elapsed = datetime.now() - self._last_failure_time
                if elapsed > timedelta(seconds=self._circuit_config.recovery_timeout):
                    logger.info("Circuit breaker: OPEN -> HALF_OPEN")
                    self._circuit_state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    return True
            return False

        if self._circuit_state == CircuitState.HALF_OPEN:
            if self._half_open_calls < self._circuit_config.half_open_max_calls:
                self._half_open_calls += 1
                return True
            return False

        return False

    def _record_success(self):
        """Record successful request."""
        if self._circuit_state == CircuitState.HALF_OPEN:
            logger.info("Circuit breaker: HALF_OPEN -> CLOSED (success)")
            self._circuit_state = CircuitState.CLOSED
        self._failure_count = 0

    def _record_failure(self):
        """Record failed request."""
        self._failure_count += 1
        self._last_failure_time = datetime.now()

        if self._circuit_state == CircuitState.HALF_OPEN:
            logger.warning("Circuit breaker: HALF_OPEN -> OPEN (failure)")
            self._circuit_state = CircuitState.OPEN
        elif self._failure_count >= self._circuit_config.failure_threshold:
            logger.warning(f"Circuit breaker: CLOSED -> OPEN (failures={self._failure_count})")
            self._circuit_state = CircuitState.OPEN

    # =========================================================================
    # API METHODS
    # =========================================================================

    async def health_check(self) -> dict[str, Any]:
        """
        Check prediction service health.

        Returns:
            Health status dict
        """
        if not self.enabled:
            return {"status": "disabled", "service": "prediction-intelligence"}

        try:
            client = await self._get_client()
            response = await client.get("/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    async def get_signals(
        self,
        market: str | None = None,
        category: str | None = None,
        signal_type: str | None = None,
        min_confidence: float = 0.0,
        symbol: str | None = None,
        limit: int = 10,
    ) -> list[PredictionSignal]:
        """
        Get market signals from prediction service.

        Args:
            market: Filter by market (kalshi/polymarket)
            category: Filter by category
            signal_type: Filter by signal type (bullish/bearish/neutral)
            min_confidence: Minimum confidence threshold
            symbol: Filter by trading symbol
            limit: Maximum results

        Returns:
            List of PredictionSignal objects
        """
        if not self.enabled:
            logger.debug("Prediction service disabled, returning empty signals")
            return []

        if not self._check_circuit():
            logger.warning("Circuit breaker OPEN, skipping request")
            return []

        params = {"limit": limit, "min_confidence": min_confidence}
        if market:
            params["market"] = market
        if category:
            params["category"] = category
        if signal_type:
            params["signal_type"] = signal_type
        if symbol:
            params["symbol"] = symbol

        try:
            response = await self._request_with_retry("GET", "/api/v1/signals", params=params)
            self._record_success()

            data = response.json()
            return [PredictionSignal(**s) for s in data.get("signals", [])]

        except Exception as e:
            self._record_failure()
            logger.error(f"Failed to get signals: {e}")
            return []

    async def get_signal_by_id(self, signal_id: str) -> PredictionSignal | None:
        """Get specific signal by ID."""
        if not self.enabled or not self._check_circuit():
            return None

        try:
            response = await self._request_with_retry("GET", f"/api/v1/signals/{signal_id}")
            self._record_success()
            return PredictionSignal(**response.json())
        except Exception as e:
            self._record_failure()
            logger.error(f"Failed to get signal {signal_id}: {e}")
            return None

    async def run_analysis(
        self, analysis_type: str, market: str = "kalshi", category: str | None = None
    ) -> dict[str, Any]:
        """
        Trigger analysis job.

        Args:
            analysis_type: Type of analysis (maker_taker, volume_trends, etc.)
            market: Target market
            category: Optional category filter

        Returns:
            Analysis job info with ID
        """
        if not self.enabled or not self._check_circuit():
            return {"status": "disabled"}

        payload = {"analysis_type": analysis_type, "market": market}
        if category:
            payload["category"] = category

        try:
            response = await self._request_with_retry("POST", "/api/v1/analysis/run", json=payload)
            self._record_success()
            return response.json()
        except Exception as e:
            self._record_failure()
            logger.error(f"Failed to run analysis: {e}")
            return {"status": "error", "error": str(e)}

    async def get_analysis_status(self, analysis_id: str) -> dict[str, Any]:
        """Get status of an analysis job."""
        if not self.enabled or not self._check_circuit():
            return {"status": "disabled"}

        try:
            response = await self._request_with_retry("GET", f"/api/v1/analysis/{analysis_id}")
            self._record_success()
            return response.json()
        except Exception as e:
            self._record_failure()
            logger.error(f"Failed to get analysis status: {e}")
            return {"status": "error", "error": str(e)}

    async def get_market_summary(self, market: str = "kalshi") -> dict[str, Any]:
        """Get market summary statistics."""
        if not self.enabled or not self._check_circuit():
            return {"status": "disabled"}

        try:
            response = await self._request_with_retry(
                "GET", "/api/v1/markets/summary", params={"market": market}
            )
            self._record_success()
            return response.json()
        except Exception as e:
            self._record_failure()
            logger.error(f"Failed to get market summary: {e}")
            return {"status": "error", "error": str(e)}

    # =========================================================================
    # PRIVATE METHODS
    # =========================================================================

    async def _request_with_retry(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        json: dict | None = None,
    ) -> httpx.Response:
        """Execute request with retry logic."""
        client = await self._get_client()
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                response = await client.request(method=method, url=path, params=params, json=json)
                response.raise_for_status()
                return response

            except httpx.HTTPStatusError as e:
                if e.response.status_code < 500:
                    # Client error, don't retry
                    raise
                last_exception = e

            except (httpx.ConnectError, httpx.TimeoutException) as e:
                last_exception = e

            # Exponential backoff
            if attempt < self.max_retries - 1:
                delay = 2**attempt
                logger.warning(f"Request failed, retrying in {delay}s (attempt {attempt + 1})")
                await asyncio.sleep(delay)

        raise last_exception or Exception("Max retries exceeded")


# Global client instance
_prediction_client: PredictionMarketClient | None = None


def get_prediction_client() -> PredictionMarketClient:
    """Get or create prediction market client."""
    global _prediction_client
    if _prediction_client is None:
        _prediction_client = PredictionMarketClient()
    return _prediction_client
