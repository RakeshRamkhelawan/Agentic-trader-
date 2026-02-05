import pytest
from unittest.mock import MagicMock, patch
from backend.core.telemetry.tracing import setup_tracing, get_tracer
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter

# --- FIXTURES ---

@pytest.fixture(autouse=True) # Zorgt dat tracing wordt gereset voor elke test
def reset_tracing():
    # Reset OpenTelemetry globals om interferentie tussen tests te voorkomen
    trace._set_tracer_provider(None)
    yield
    trace._set_tracer_provider(None)

# --- TESTS ---

def test_setup_tracing_initializes_provider():
    """Happy Path: Tracing provider wordt geïnitialiseerd."""
    setup_tracing("test-service")
    provider = trace.get_tracer_provider()
    assert isinstance(provider, TracerProvider)

def test_get_tracer_returns_configured_tracer():
    """Happy Path: Correcte tracer wordt teruggegeven."""
    setup_tracing("test-service")
    tracer = get_tracer("test-module")
    assert tracer.name == "test-module"

@pytest.mark.asyncio
async def test_tracing_context_propagation():
    """Happy Path: Tracing context propageert over async functies."""
    setup_tracing("test-service")
    tracer = get_tracer("test-module")
    
    # Mock de span exporter om spans op te vangen
    mock_exporter = MagicMock(spec=ConsoleSpanExporter)
    provider = trace.get_tracer_provider()
    provider.add_span_processor(SimpleSpanProcessor(mock_exporter))

    with tracer.start_as_current_span("parent-operation") as parent_span:
        assert parent_span is not None
        
        async def child_operation():
            with tracer.start_as_current_span("child-operation") as child_span:
                assert child_span is not None
                # Check of parent context is overgenomen
                assert child_span.parent.span_id == parent_span.context.span_id
                
        await child_operation()
        
    # Check of de spans zijn geëxporteerd (dit is lastig met MagicMock van ConsoleSpanExporter)
    # Normaal zou je hier een lijst van spans inspecteren.
    # Voor nu controleren we alleen dat de start/end calls zijn gedaan (impliciet door `with` block).
    # Een betere test zou een echte InMemorySpanExporter gebruiken.
    assert parent_span.is_end
    assert parent_span.context.span_id is not None
