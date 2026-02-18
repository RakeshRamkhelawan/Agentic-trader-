from prometheus_client import (CollectorRegistry, Counter, Gauge, Histogram,
                               generate_latest)


class PrometheusMetrics:
    """
    Centrale klasse voor het definiëren en exposen van Prometheus metrics.
    Gebruikt een enkele registry om duplicaten te voorkomen en consistentie te waarborgen.
    """

    _registry = CollectorRegistry(auto_describe=True)  # Globale registry
    _instances = {}  # Dict om metrics per service_name te cachen

    def __new__(cls, service_name: str):
        """Implementeer een singleton-achtig patroon voor metrics per service_name."""
        if service_name not in cls._instances:
            instance = super().__new__(cls)
            cls._instances[service_name] = instance
        return cls._instances[service_name]

    def __init__(self, service_name: str):
        # Voorkom herinitialisatie als de instantie al bestaat
        if hasattr(self, "_initialized") and self._initialized:
            return

        self.service_name = service_name

        # --- Common Metrics ---
        # Alle metrics moeten nu uniek zijn, of ze moeten gelabeld zijn.
        # Voor nu, maken we ze uniek per service.
        self.requests_total = Counter(
            f"{service_name}_requests_total",
            "Total number of requests.",
            registry=self._registry,
        )
        self.requests_in_progress = Gauge(
            f"{service_name}_requests_in_progress",
            "Number of requests currently in progress.",
            registry=self._registry,
        )
        self.request_latency_seconds = Histogram(
            f"{service_name}_request_latency_seconds",
            "Request latency in seconds.",
            registry=self._registry,
        )
        self.errors_total = Counter(
            f"{service_name}_errors_total",
            "Total number of errors.",
            registry=self._registry,
        )

        # --- Business Logic Metrics ---
        self.trades_executed_total = Counter(
            f"{service_name}_trades_executed_total",
            "Total trades executed.",
            ["strategy", "agent", "status"],  # Labels
            registry=self._registry,
        )

        self.pnl_realized_total = Counter(
            f"{service_name}_pnl_realized_total",
            "Total Realized PnL.",
            registry=self._registry,
        )

        self.compliance_blocks_total = Counter(
            f"{service_name}_compliance_blocks_total",
            "Total trades blocked by compliance.",
            ["reason"],
            registry=self._registry,
        )

        self.websocket_connections = Gauge(
            f"{service_name}_websocket_connections_active",
            "Active WebSocket connections.",
            registry=self._registry,
        )

        self.security_violations_total = Counter(
            f"{service_name}_security_violations_total",
            "Total number of security violations.",
            ["violator", "action"],
            registry=self._registry,
        )

        # --- Phase 5: Observability Metrics ---
        self.market_regime_state = Gauge(
            f"{service_name}_market_regime_state",
            "Current Market Regime (0=Sideways, 1=Bull, 2=Bear, 3=Volatile).",
            registry=self._registry,
        )

        self.strategy_signal_total = Counter(
            f"{service_name}_strategy_signal_total",
            "Total strategy signals generated.",
            ["strategy", "action"],
            registry=self._registry,
        )

        self.order_execution_latency_seconds = Histogram(
            f"{service_name}_order_execution_latency_seconds",
            "Latency from Intent generation to Reflex execution.",
            buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0),
            registry=self._registry,
        )

        self.generated_shm_updates_total = Counter(
            f"{service_name}_generated_shm_updates_total",
            "Total updates written to Shared Memory.",
            ["shm_name"],
            registry=self._registry,
        )

        # --- Guna Metrics (Globaal, dus zonder service_name prefix) ---
        # Only register if not already registered
        try:
            self.global_guna_sattva = Gauge(
                "global_guna_sattva",
                "Current global Sattva level.",
                registry=self._registry,
            )
        except ValueError:
            # Already registered
            self.global_guna_sattva = self._registry._names_to_collectors.get(
                "global_guna_sattva"
            )

        try:
            self.global_guna_rajas = Gauge(
                "global_guna_rajas",
                "Current global Rajas level.",
                registry=self._registry,
            )
        except ValueError:
            self.global_guna_rajas = self._registry._names_to_collectors.get(
                "global_guna_rajas"
            )

        try:
            self.global_guna_tamas = Gauge(
                "global_guna_tamas",
                "Current global Tamas level.",
                registry=self._registry,
            )
        except ValueError:
            self.global_guna_tamas = self._registry._names_to_collectors.get(
                "global_guna_tamas"
            )

        try:
            self.guna_deviation_score = Gauge(
                "guna_deviation_score",
                "Deviation from ideal Guna balance.",
                registry=self._registry,
            )
        except ValueError:
            self.guna_deviation_score = self._registry._names_to_collectors.get(
                "guna_deviation_score"
            )
        self._initialized = True

    def expose_metrics(self) -> bytes:
        """
        Genereert de actuele metrics in Prometheus tekstformaat.
        """
        return generate_latest(self._registry)
