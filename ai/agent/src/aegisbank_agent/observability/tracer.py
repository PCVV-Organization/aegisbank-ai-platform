"""OpenTelemetry distributed tracing configuration and span utilities."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Generator, TypeVar

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import Span, StatusCode, Tracer

T = TypeVar("T")

_MEMORY_EXPORTER = InMemorySpanExporter()
_PROVIDER: TracerProvider | None = None


def setup_tracer(service_name: str = "aegisbank-agent") -> TracerProvider:
    """Initialize and configure global OpenTelemetry TracerProvider with in-memory exporter."""
    global _PROVIDER
    if _PROVIDER is None:
        provider = TracerProvider()
        processor = SimpleSpanProcessor(_MEMORY_EXPORTER)
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
        _PROVIDER = provider
    return _PROVIDER


def get_memory_exporter() -> InMemorySpanExporter:
    """Retrieve in-memory span exporter for testing and local inspection."""
    return _MEMORY_EXPORTER


def get_tracer(name: str = "aegisbank.agent") -> Tracer:
    """Get standard OpenTelemetry Tracer instance."""
    setup_tracer()
    return trace.get_tracer(name)


def get_current_trace_and_span_id() -> tuple[str, str]:
    """Extract current active trace_id and span_id formatted as hex strings."""
    current_span = trace.get_current_span()
    ctx = current_span.get_span_context()
    if ctx.is_valid:
        return f"{ctx.trace_id:032x}", f"{ctx.span_id:016x}"
    return "0" * 32, "0" * 16


@contextmanager
def trace_span(
    name: str,
    attributes: dict[str, Any] | None = None,
    tracer_name: str = "aegisbank.agent",
) -> Generator[Span, None, None]:
    """Context manager for creating and automatically managing an OpenTelemetry span."""
    tracer = get_tracer(tracer_name)
    with tracer.start_as_current_span(name) as span:
        if attributes:
            for key, val in attributes.items():
                if val is not None:
                    span.set_attribute(
                        key,
                        str(val) if not isinstance(val, (int, float, bool, str)) else val,
                    )
        try:
            yield span
            span.set_status(StatusCode.OK)
        except Exception as exc:
            span.record_exception(exc)
            span.set_status(StatusCode.ERROR, description=str(exc))
            raise exc
