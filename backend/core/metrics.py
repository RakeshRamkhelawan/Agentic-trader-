import functools
import time

from prometheus_client import Counter, Enum, Gauge, Histogram

ooda_cycles_total = Counter(
    "samkhya_ooda_cycles_total", "Total number of OODA cycles completed", ["tenant_id"]
)

ooda_phase_duration = Histogram(
    "samkhya_ooda_phase_duration_seconds",
    "Duration of each OODA phase",
    ["phase", "tenant_id"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)

decisions_total = Counter(
    "samkhya_decisions_total",
    "Total decisions made by type",
    ["decision", "tenant_id", "agent_element"],
)

cache_hits_total = Counter(
    "samkhya_cache_hits_total",
    "Cache hits by level and namespace",
    ["level", "namespace"],
)

cache_misses_total = Counter(
    "samkhya_cache_misses_total",
    "Cache misses by level and namespace",
    ["level", "namespace"],
)

ephemeris_calc_duration = Histogram(
    "samkhya_ephemeris_calc_duration_seconds",
    "Swiss Ephemeris calculation duration",
    ["calculation_type"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0],
)

ephemeris_errors_total = Counter(
    "samkhya_ephemeris_errors_total", "Ephemeris calculation errors", ["error_type"]
)

planet_longitude = Gauge(
    "samkhya_planet_longitude",
    "Current planetary longitude degrees",
    ["planet", "tenant_id"],
)

planet_retrograde = Gauge(
    "samkhya_planet_retrograde",
    "Planet retrograde status (1=retrograde, 0=direct)",
    ["planet", "tenant_id"],
)

rahu_kala_active = Gauge(
    "samkhya_rahu_kala_active", "Rahu Kala window active status", ["tenant_id"]
)

rahu_kala_violations_total = Counter(
    "samkhya_rahu_kala_violations_total",
    "Attempted trades during Rahu Kala",
    ["tenant_id"],
)

guna_weights = Gauge(
    "samkhya_guna_weights", "Current guna weight distribution", ["guna", "tenant_id"]
)

agent_prana = Gauge("samkhya_agent_prana", "Elemental agent prana level", ["element", "tenant_id"])

circuit_breaker_state = Enum(
    "samkhya_circuit_breaker_state",
    "Circuit breaker current state",
    ["name", "tenant_id"],
    states=["closed", "open", "half_open"],
)

circuit_breaker_trips_total = Counter(
    "samkhya_circuit_breaker_trips_total",
    "Total circuit breaker trips",
    ["name", "tenant_id"],
)

position_size_ratio = Gauge(
    "samkhya_position_size_ratio",
    "Position size as ratio of portfolio",
    ["symbol", "tenant_id"],
)

mifid_violations_total = Counter(
    "samkhya_mifid_violations_total",
    "MiFID II compliance violations",
    ["violation_type", "tenant_id"],
)

trade_approval_duration = Histogram(
    "samkhya_trade_approval_duration_seconds",
    "Trade approval check duration",
    ["tenant_id"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0],
)

errors_total = Counter("samkhya_errors_total", "Total errors by type", ["error_type", "component"])

portfolio_pnl = Gauge("samkhya_portfolio_pnl", "Current portfolio PnL", ["tenant_id", "currency"])

audit_logs_total = Counter(
    "samkhya_audit_logs_total", "Audit log entries by action", ["action", "tenant_id"]
)

best_execution_deviation = Gauge(
    "samkhya_best_execution_deviation",
    "Price deviation from best available venue",
    ["symbol", "venue", "tenant_id"],
)


def track_ooda_phase(phase: str, tenant_id: str):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                ooda_phase_duration.labels(phase=phase, tenant_id=tenant_id).observe(duration)

        return wrapper

    return decorator


def track_cache_access(level: int, namespace: str):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            if result is not None:
                cache_hits_total.labels(level=f"L{level}", namespace=namespace).inc()
            else:
                cache_misses_total.labels(level=f"L{level}", namespace=namespace).inc()
            return result

        return wrapper

    return decorator
