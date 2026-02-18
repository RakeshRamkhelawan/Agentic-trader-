"""
Prometheus metrics for Prediction Market Intelligence service.

Defines all metrics exposed via the /metrics endpoint.
"""

from prometheus_client import Counter, Gauge, Histogram, Info

# Service information
SERVICE_INFO = Info(
    "prediction_intelligence_service",
    "Prediction Intelligence Service Information",
    labelnames=["version", "environment"],
)
SERVICE_INFO.info({"version": "1.0.0", "environment": "production"})

# ============================================================================
# REQUEST METRICS
# ============================================================================

REQUEST_COUNT = Counter(
    "prediction_requests_total",
    "Total HTTP requests processed",
    labelnames=["method", "endpoint", "status"],
    help="Counter for HTTP requests by method, endpoint, and status code",
)

REQUEST_LATENCY = Histogram(
    "prediction_request_duration_seconds",
    "HTTP request latency in seconds",
    labelnames=["method", "endpoint"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
    help="Histogram of request latencies in seconds",
)

# ============================================================================
# SIGNAL METRICS
# ============================================================================

SIGNALS_GENERATED = Counter(
    "prediction_signals_generated_total",
    "Total prediction signals generated",
    labelnames=["market", "category", "signal_type"],
    help="Counter for generated signals by market, category, and type",
)

SIGNAL_CONFIDENCE = Histogram(
    "prediction_signal_confidence",
    "Distribution of signal confidence scores",
    labelnames=["market"],
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
    help="Histogram of signal confidence values",
)

# ============================================================================
# ANALYSIS METRICS
# ============================================================================

ANALYSIS_JOBS = Counter(
    "prediction_analysis_jobs_total",
    "Total analysis jobs executed",
    labelnames=["analysis_type", "status"],
    help="Counter for analysis jobs by type and completion status",
)

ANALYSIS_DURATION = Histogram(
    "prediction_analysis_duration_seconds",
    "Analysis job execution duration in seconds",
    labelnames=["analysis_type"],
    buckets=[1, 5, 10, 30, 60, 120, 300],
    help="Histogram of analysis job durations",
)

# ============================================================================
# DUCKDB METRICS
# ============================================================================

DUCKDB_QUERIES = Counter(
    "prediction_duckdb_queries_total",
    "Total DuckDB queries executed",
    labelnames=["query_type"],
    help="Counter for DuckDB query operations",
)

DUCKDB_QUERY_DURATION = Histogram(
    "prediction_duckdb_query_duration_seconds",
    "DuckDB query execution duration in seconds",
    labelnames=["query_type"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
    help="Histogram of DuckDB query durations",
)

# ============================================================================
# CIRCUIT BREAKER METRICS
# ============================================================================

CIRCUIT_BREAKER_STATE = Gauge(
    "prediction_circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=open, 2=half_open)",
    labelnames=["service"],
    help="Gauge indicating circuit breaker state for external services",
)

CIRCUIT_BREAKER_TRANSITIONS = Counter(
    "prediction_circuit_breaker_transitions_total",
    "Total circuit breaker state transitions",
    labelnames=["service", "from_state", "to_state"],
    help="Counter for circuit breaker state transitions",
)

# ============================================================================
# CACHE METRICS
# ============================================================================

CACHE_HITS = Counter(
    "prediction_cache_hits_total",
    "Total cache hits",
    labelnames=["cache_type"],
    help="Counter for cache hits",
)

CACHE_MISSES = Counter(
    "prediction_cache_misses_total",
    "Total cache misses",
    labelnames=["cache_type"],
    help="Counter for cache misses",
)

CACHE_SIZE = Gauge(
    "prediction_cache_size_bytes",
    "Current cache size in bytes",
    labelnames=["cache_type"],
    help="Gauge for current cache size",
)

# ============================================================================
# ERROR METRICS
# ============================================================================

ERRORS_TOTAL = Counter(
    "prediction_errors_total",
    "Total errors occurred",
    labelnames=["error_type", "endpoint"],
    help="Counter for errors by type and endpoint",
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def record_request(
    method: str, endpoint: str, status_code: int, duration: float
) -> None:
    """
    Record request metrics.

    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: Request endpoint path
        status_code: HTTP response status code
        duration: Request duration in seconds
    """
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status_code).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)


def record_signal(
    market: str, category: str, signal_type: str, confidence: float
) -> None:
    """
    Record signal generation metrics.

    Args:
        market: Market source (e.g., 'kalshi', 'polymarket')
        category: Signal category
        signal_type: Type of signal (e.g., 'bullish', 'bearish')
        confidence: Confidence score (0.0-1.0)
    """
    SIGNALS_GENERATED.labels(
        market=market, category=category, signal_type=signal_type
    ).inc()
    SIGNAL_CONFIDENCE.labels(market=market).observe(confidence)


def record_analysis_job(
    analysis_type: str, duration: float, status: str = "completed"
) -> None:
    """
    Record analysis job metrics.

    Args:
        analysis_type: Type of analysis performed
        duration: Job execution duration in seconds
        status: Job status ('completed', 'failed', etc.)
    """
    ANALYSIS_JOBS.labels(analysis_type=analysis_type, status=status).inc()
    ANALYSIS_DURATION.labels(analysis_type=analysis_type).observe(duration)


def record_duckdb_query(query_type: str, duration: float) -> None:
    """
    Record DuckDB query metrics.

    Args:
        query_type: Type of query executed
        duration: Query execution duration in seconds
    """
    DUCKDB_QUERIES.labels(query_type=query_type).inc()
    DUCKDB_QUERY_DURATION.labels(query_type=query_type).observe(duration)


def record_error(error_type: str, endpoint: str) -> None:
    """
    Record error metrics.

    Args:
        error_type: Type of error
        endpoint: Endpoint where error occurred
    """
    ERRORS_TOTAL.labels(error_type=error_type, endpoint=endpoint).inc()


def set_circuit_breaker_state(service: str, state: int) -> None:
    """
    Set circuit breaker state.

    Args:
        service: Service name
        state: State code (0=closed, 1=open, 2=half_open)
    """
    CIRCUIT_BREAKER_STATE.labels(service=service).set(state)


def record_cache_hit(cache_type: str) -> None:
    """
    Record cache hit.

    Args:
        cache_type: Type of cache
    """
    CACHE_HITS.labels(cache_type=cache_type).inc()


def record_cache_miss(cache_type: str) -> None:
    """
    Record cache miss.

    Args:
        cache_type: Type of cache
    """
    CACHE_MISSES.labels(cache_type=cache_type).inc()


def set_cache_size(cache_type: str, size_bytes: float) -> None:
    """
    Set cache size.

    Args:
        cache_type: Type of cache
        size_bytes: Cache size in bytes
    """
    CACHE_SIZE.labels(cache_type=cache_type).set(size_bytes)
