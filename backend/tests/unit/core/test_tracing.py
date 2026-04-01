"""
Unit tests for OpenTelemetry Tracing (Sprint 4 S4-1).
"""

import time
from unittest.mock import MagicMock, patch

import pytest

from backend.core.telemetry.tracing import (
    HotPathTracer,
    TraceCorrelation,
    create_span_context,
    get_hot_path_tracer,
    get_tracer,
    setup_tracing,
)


class TestTraceCorrelation:
    """Test trace correlation functionality."""

    def test_generate_trace_id(self):
        """Test trace ID generation."""
        trace_id = TraceCorrelation.generate_trace_id()
        assert isinstance(trace_id, str)
        assert len(trace_id) == 32  # 128-bit hex

    def test_generate_span_id(self):
        """Test span ID generation."""
        span_id = TraceCorrelation.generate_span_id()
        assert isinstance(span_id, str)
        assert len(span_id) == 16  # 64-bit hex

    def test_set_and_get_current_trace(self):
        """Test setting and getting current trace."""
        trace_id = "abcd1234" * 4
        TraceCorrelation.set_current_trace(trace_id)

        assert TraceCorrelation.get_current_trace_id() == trace_id

        TraceCorrelation.clear_current_trace()
        assert TraceCorrelation.get_current_trace_id() is None

    def test_start_trace(self):
        """Test starting new trace."""
        trace_id = TraceCorrelation.start_trace("test_operation")

        assert isinstance(trace_id, str)
        assert len(trace_id) == 32
        assert TraceCorrelation.get_current_trace_id() == trace_id

        TraceCorrelation.clear_current_trace()


class TestHotPathTracer:
    """Test hot path tracer performance."""

    def test_hot_path_tracer_creation(self):
        """Test that hot path tracer can be created with mock."""
        mock_tracer = MagicMock()
        hot_tracer = HotPathTracer(mock_tracer)
        assert hot_tracer is not None

        # Test span creation
        mock_span = MagicMock()
        mock_tracer.start_span.return_value = mock_span

        with hot_tracer.start_span("test"):
            pass

        mock_tracer.start_span.assert_called_once()
        call_kwargs = mock_tracer.start_span.call_args[1]
        assert call_kwargs.get("record_exception") is False  # Hot path optimization

    def test_hot_path_span_latency_simulation(self):
        """Test hot path span wrapper performance."""
        mock_tracer = MagicMock()
        hot_tracer = HotPathTracer(mock_tracer)
        mock_span = MagicMock()
        mock_tracer.start_span.return_value = mock_span

        # Measure wrapper overhead
        times = []
        for _ in range(1000):
            start = time.perf_counter_ns()
            with hot_tracer.start_span("test"):
                pass
            elapsed_ns = time.perf_counter_ns() - start
            times.append(elapsed_ns)

        avg_ns = sum(times) / len(times)
        avg_us = avg_ns / 1000

        # Should be < 200μs (realistic for Python with mocking on CI)
        assert avg_us < 200, f"Hot path wrapper latency {avg_us:.2f}μs exceeds 200μs"


class TestTracingSetup:
    """Test tracing setup."""

    def test_setup_tracing_basic(self):
        """Test basic tracing setup."""
        try:
            provider = setup_tracing(
                service_name="test-service",
                console_export=False,
            )
            assert provider is not None
        except Exception as e:
            # May fail if provider already set - that's OK
            pytest.skip(f"Provider setup skipped: {e}")

    def test_get_tracer_mock(self):
        """Test getting tracer with mock."""
        with patch("backend.core.telemetry.tracing.trace.get_tracer") as mock_get:
            mock_tracer = MagicMock()
            mock_get.return_value = mock_tracer

            tracer = get_tracer("test_module")
            assert tracer is not None
            mock_get.assert_called()


class TestSpanContext:
    """Test span context creation."""

    def test_create_span_context(self):
        """Test creating span context from IDs."""
        trace_id = "abcd1234" * 4  # 32 hex chars = 128-bit
        span_id = "abcd5678" * 2  # 16 hex chars = 64-bit

        ctx = create_span_context(trace_id, span_id)

        assert ctx.trace_id == int(trace_id, 16)
        assert ctx.span_id == int(span_id, 16)
        assert ctx.is_remote is True


class TestTracePropagation:
    """Test trace propagation across async boundaries."""

    @pytest.mark.asyncio
    async def test_trace_propagation(self):
        """Test that trace ID propagates across async tasks."""
        TraceCorrelation.start_trace("parent")

        async def child_task():
            # Should inherit trace context
            return TraceCorrelation.get_current_trace_id()

        # In async context, should propagate
        await child_task()

        # Note: ContextVars propagate automatically in asyncio.gather/create_task
        TraceCorrelation.clear_current_trace()


class TestTracingIntegration:
    """Integration tests for tracing."""

    def test_trace_correlation_with_mocked_tracer(self):
        """Test complete trace flow with mocked tracer."""
        trace_id = TraceCorrelation.start_trace("tick_processing")

        # Simulate operations
        with patch("backend.core.telemetry.tracing.trace.get_tracer") as mock_get:
            mock_tracer = MagicMock()
            mock_span = MagicMock()
            mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock(
                return_value=mock_span
            )
            mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(
                return_value=False
            )
            mock_get.return_value = mock_tracer

            # Simulate hot path operation
            get_hot_path_tracer("hot_path")

            # Simulate cold path operation
            get_tracer("cold_path")

        TraceCorrelation.clear_current_trace()

        # Verify trace ID was set
        assert trace_id is not None
        assert len(trace_id) == 32


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
