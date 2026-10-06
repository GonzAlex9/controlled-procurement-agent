from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI

DEFAULT_SERVICE_NAME = "controlled-procurement-agent"


def otlp_export_configured() -> bool:
    return bool(
        os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
        or os.getenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT")
    )


def configure_observability(
    app: FastAPI,
    *,
    span_processor: Any | None = None,
) -> bool:
    """Configure optional OTLP tracing without coupling the domain to a backend."""

    if span_processor is None and not otlp_export_configured():
        return False

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        raise RuntimeError(
            'OTLP tracing requires: pip install -e ".[observability]"'
        ) from exc

    service_name = os.getenv("OTEL_SERVICE_NAME", DEFAULT_SERVICE_NAME)
    provider = TracerProvider(
        resource=Resource.create(
            {
                "service.name": service_name,
                "service.version": "0.1.0",
            }
        )
    )

    processor = span_processor
    if processor is None:
        processor = BatchSpanProcessor(OTLPSpanExporter())

    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(
        app,
        tracer_provider=provider,
        excluded_urls="health",
        exclude_spans=["receive", "send"],
    )
    return True
