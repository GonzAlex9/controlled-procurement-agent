import pytest
from fastapi import FastAPI

from procurement_agent.models import PurchaseRequest
from procurement_agent.observability import (
    configure_observability,
    otlp_export_configured,
)
from procurement_agent.store import DemoEnterpriseStore
from procurement_agent.workflow import ProcurementWorkflow


def test_observability_is_opt_in(monkeypatch):
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", raising=False)

    assert otlp_export_configured() is False
    assert configure_observability(FastAPI()) is False


@pytest.mark.asyncio
async def test_workflow_emits_expected_opentelemetry_spans():
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        SimpleSpanProcessor,
        SpanExporter,
        SpanExportResult,
    )

    exported = []

    class CollectingExporter(SpanExporter):
        def export(self, spans):
            exported.extend(spans)
            return SpanExportResult.SUCCESS

    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(CollectingExporter()))
    trace.set_tracer_provider(provider)

    store = DemoEnterpriseStore()
    request = PurchaseRequest(
        id="PR-OTEL-1",
        requester="observer",
        department="IT",
        category="hardware",
        vendor_id="vendor-cloud",
        amount_eur=800,
        justification="Replacement equipment for a controlled observability test.",
        quotes_count=1,
    )

    await ProcurementWorkflow(store).analyze(request)

    names = {span.name for span in exported}
    assert {
        "procurement.analyze",
        "procurement.policy.evaluate",
        "procurement.analyst.generate",
    } <= names

    root = next(span for span in exported if span.name == "procurement.analyze")
    assert root.attributes["procurement.decision"] == "auto_approve"
    assert root.attributes["procurement.analysis_mode"] == "deterministic"
    assert "justification" not in root.attributes
