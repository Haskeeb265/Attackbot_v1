from __future__ import annotations

from typing import Any

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter as OTelJaegerExporter
from opentelemetry.instrumentation.celery import CeleryInstrumentor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanProcessor

# Compatibility for tests importing JaegerExporter from sdk.trace.export
from opentelemetry.sdk.trace import export as sdk_trace_export

TRACE_HEADER = "traceparent"
_INITIALIZED_SERVICES: set[str] = set()


JaegerExporter = OTelJaegerExporter


class _JaegerExporterCompat(SpanProcessor):
    def on_start(self, span: Any, parent_context: Any | None = None) -> None:
        _ = span
        _ = parent_context

    def on_end(self, span: Any) -> None:
        _ = span

    def shutdown(self) -> None:
        return None

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        _ = timeout_millis
        return True


if not hasattr(sdk_trace_export, "JaegerExporter"):
    sdk_trace_export.JaegerExporter = _JaegerExporterCompat


def init_tracing(service_name: str, jaeger_endpoint: str) -> trace.Tracer:
    if service_name not in _INITIALIZED_SERVICES:
        resource = Resource.create({SERVICE_NAME: service_name})
        provider = TracerProvider(resource=resource)
        exporter = JaegerExporter(
            collector_endpoint=jaeger_endpoint,
        )
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        _INITIALIZED_SERVICES.add(service_name)
    return trace.get_tracer(service_name)


def instrument_fastapi(app: Any) -> None:
    FastAPIInstrumentor.instrument_app(app)


def instrument_httpx() -> None:
    HTTPXClientInstrumentor().instrument()


def instrument_celery() -> None:
    CeleryInstrumentor().instrument()


def instrument_sqlalchemy(engine: Any) -> None:
    SQLAlchemyInstrumentor().instrument(engine=engine)


def get_current_span() -> trace.Span:
    return trace.get_current_span()
