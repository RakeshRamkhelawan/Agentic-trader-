"""
HTTP client optimizations for the prediction market intelligence service.

This module provides optimized HTTP client configurations with:
- Connection pooling
- Request caching
- Retry logic
- Circuit breaker pattern
- Request deduplication
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)


# =============================================================================
# HTTP CLIENT CONFIGURATION
# =============================================================================

def get_optimized_httpx_config() -> Dict[str, Any]:
    """
    Get optimized configuration for httpx client.
    
    Returns:
        Dictionary of httpx configuration parameters
        
    Usage:
        import httpx
        config = get_optimized_httpx_config()
        client = httpx.Client(**config)
    """
    return {
        "timeout": 30.0,              # 30 second timeout
        "limits": {
            "max_keepalive_connections": 20,
            "max_connections": 100,
            "keepalive_expiry": 15.0  # Keep-alive for 15 seconds
        },
        "verify": True,               # Verify SSL certificates
        "follow_redirects": True,
        "headers": {
            "User-Agent": "PredictionMarketIntelligence/1.0"
        }
    }


def get_optimized_httpx_async_config() -> Dict[str, Any]:
    """
    Get optimized configuration for async httpx client.
    
    Returns:
        Dictionary of async httpx configuration parameters
        
    Usage:
        import httpx
        config = get_optimized_httpx_async_config()
        async with httpx.AsyncClient(**config) as client:
            response = await client.get(url)
    """
    return {
        "timeout": 30.0,
        "limits": {
            "max_keepalive_connections": 30,
            "max_connections": 100,
            "keepalive_expiry": 15.0
        },
        "verify": True,
        "follow_redirects": True,
        "headers": {
            "User-Agent": "PredictionMarketIntelligence/1.0"
        }
    }


# =============================================================================
# REQUEST CACHING
# =============================================================================

class RequestCache:
    """
    Cache HTTP responses with TTL.
    
    Caches GET requests by default. Useful for frequently accessed
    endpoints with slowly-changing data.
    """
    
    def __init__(self, ttl_seconds: int = 300, max_size: int = 1000):
        self.cache: Dict[str, tuple[Any, float]] = {}
        self.ttl = ttl_seconds
        self.max_size = max_size
    
    def _cache_key(self, method: str, url: str, params: Optional[Dict] = None) -> str:
        """Generate cache key from request parameters."""
        key_data = f"{method}:{url}"
        if params:
            key_data += f":{sorted(params.items())}"
        
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, method: str, url: str, params: Optional[Dict] = None) -> Optional[Any]:
        """Get cached response if available and not expired."""
        # Only cache GET requests
        if method.upper() != "GET":
            return None
        
        key = self._cache_key(method, url, params)
        
        if key not in self.cache:
            return None
        
        response, timestamp = self.cache[key]
        
        # Check TTL
        if datetime.now().timestamp() - timestamp > self.ttl:
            del self.cache[key]
            return None
        
        logger.debug(f"Cache hit for {method} {url}")
        return response
    
    def set(self, method: str, url: str, response: Any, params: Optional[Dict] = None) -> None:
        """Cache a response."""
        if method.upper() != "GET":
            return
        
        # Prevent unbounded growth
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.keys(), 
                           key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
        
        key = self._cache_key(method, url, params)
        self.cache[key] = (response, datetime.now().timestamp())
    
    def clear(self) -> None:
        """Clear all cached responses."""
        self.cache.clear()


# =============================================================================
# REQUEST DEDUPLICATION
# =============================================================================

class RequestDeduplicator:
    """
    Prevent duplicate concurrent requests to same endpoint.
    
    If multiple callers request the same URL concurrently,
    reuse the first response for all callers.
    """
    
    def __init__(self):
        self.pending: Dict[str, object] = {}  # In-flight requests
    
    def _cache_key(self, method: str, url: str) -> str:
        """Generate cache key from request."""
        return f"{method}:{url}"
    
    def add_pending(self, method: str, url: str) -> bool:
        """
        Mark request as pending.
        
        Returns:
            True if this caller should make the request
            False if another caller is already making it
        """
        key = self._cache_key(method, url)
        
        if key in self.pending:
            return False
        
        self.pending[key] = object()  # Marker object
        return True
    
    def remove_pending(self, method: str, url: str) -> None:
        """Remove request from pending."""
        key = self._cache_key(method, url)
        if key in self.pending:
            del self.pending[key]


# =============================================================================
# RETRY LOGIC
# =============================================================================

def get_retry_config() -> Dict[str, Any]:
    """
    Get optimized retry configuration.
    
    Returns:
        Dictionary of retry parameters
        
    Usage:
        from httpx._client import _LOGGER
        from tenacity import retry, stop_after_attempt, wait_exponential
        
        config = get_retry_config()
        
        @retry(
            stop=stop_after_attempt(config['max_retries']),
            wait=wait_exponential(
                multiplier=config['backoff_factor'],
                min=config['min_wait'],
                max=config['max_wait']
            )
        )
        async def fetch_data(url):
            async with httpx.AsyncClient() as client:
                return await client.get(url)
    """
    return {
        "max_retries": 3,              # Maximum retry attempts
        "backoff_factor": 2,           # Exponential backoff multiplier
        "min_wait": 1,                 # Minimum wait time in seconds
        "max_wait": 30,                # Maximum wait time in seconds
        "retry_status_codes": [408, 429, 500, 502, 503, 504],  # Status codes to retry
    }


# =============================================================================
# BATCH REQUEST SUPPORT
# =============================================================================

class BatchRequestProcessor:
    """
    Process multiple HTTP requests in batches with concurrency control.
    
    Useful for APIs with rate limiting or batch endpoints.
    """
    
    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
    
    async def process_batch(self, client, requests: list) -> list:
        """
        Process multiple requests concurrently.
        
        Args:
            client: httpx.AsyncClient instance
            requests: List of (method, url, kwargs) tuples
            
        Returns:
            List of responses in same order as requests
        """
        import asyncio
        
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def fetch_with_limit(method: str, url: str, **kwargs):
            async with semaphore:
                try:
                    if method.upper() == "GET":
                        return await client.get(url, **kwargs)
                    elif method.upper() == "POST":
                        return await client.post(url, **kwargs)
                    else:
                        return await client.request(method, url, **kwargs)
                except Exception as e:
                    logger.error(f"Error fetching {method} {url}: {e}")
                    return None
        
        tasks = []
        for method, url, kwargs in requests:
            task = fetch_with_limit(method, url, **kwargs)
            tasks.append(task)
        
        return await asyncio.gather(*tasks)


# =============================================================================
# CIRCUIT BREAKER PATTERN
# =============================================================================

class CircuitBreakerState:
    """States for circuit breaker pattern."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Service unavailable
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Implement circuit breaker pattern for HTTP clients.
    
    Prevents cascading failures when external services are down.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Exception = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitBreakerState.CLOSED
    
    def call(self, func, *args, **kwargs):
        """
        Call function through circuit breaker.
        
        Args:
            func: Function to call
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception if circuit is open
        """
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        
        return datetime.now().timestamp() - self.last_failure_time > self.recovery_timeout
    
    def _on_success(self) -> None:
        """Reset failure count on successful call."""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED
    
    def _on_failure(self) -> None:
        """Increment failure count."""
        self.failure_count += 1
        self.last_failure_time = datetime.now().timestamp()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
    
    def get_state(self) -> str:
        """Get current circuit breaker state."""
        return self.state
