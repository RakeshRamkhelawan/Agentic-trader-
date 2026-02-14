from opentelemetry import trace
from opentelemetry.instrumentation.asyncio import \
    AsyncioInstrumentor  # Voor async context
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (ConsoleSpanExporter,
                                            SimpleSpanProcessor)


def setup_tracing(service_name: str):
    """
    Initialiseert OpenTelemetry tracing voor de service.
    """
    # Resource definieert de service (naam, attributen)
    resource = Resource.create(
        attributes={"service.name": service_name, "service.version": "0.1.0"}
    )

    # Provider creëert tracers
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    # Exporter stuurt de traces weg (voor nu: console)
    exporter = ConsoleSpanExporter()
    processor = SimpleSpanProcessor(exporter)
    provider.add_span_processor(processor)

    # Instrumenteer asyncio om async contexten correct te propageren
    AsyncioInstrumentor().instrument()


def get_tracer(name: str):
    """
    Haalt een tracer op voor een specifieke module.
    """
    return trace.get_tracer(name)
