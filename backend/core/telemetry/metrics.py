from prometheus_client import (
    Gauge,
    Counter,
    Histogram,
    generate_latest,
    CollectorRegistry,
)


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
