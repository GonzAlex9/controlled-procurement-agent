from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse

from procurement_agent.analyst import OpenAIAgentAnalyst
from procurement_agent.models import (
    ApprovalAction,
    ApprovalRecord,
    AuditEvent,
    ProcurementAnalysis,
    PurchaseRequest,
)
from procurement_agent.store import DemoEnterpriseStore
from procurement_agent.workflow import ProcurementWorkflow

app = FastAPI(
    title="Controlled Procurement Agent",
    version="0.1.0",
    description=(
        "Portfolio API demonstrating agentic analysis with deterministic procurement policy gates "
        "and explicit human approval. All enterprise data is fictional demo data."
    ),
)

store = DemoEnterpriseStore()
workflow = ProcurementWorkflow(store)
DEMO_HTML = Path(__file__).with_name("demo.html").read_text(encoding="utf-8")


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/demo")


@app.get("/demo", response_class=HTMLResponse, include_in_schema=False)
def demo() -> HTMLResponse:
    return HTMLResponse(DEMO_HTML)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/purchase-requests/analyze", response_model=ProcurementAnalysis)
async def analyze_purchase_request(
    request: PurchaseRequest,
    use_ai: Annotated[
        bool, Query(description="Use OpenAI Agents SDK for read-only analysis.")
    ] = False,
) -> ProcurementAnalysis:
    try:
        analyst = OpenAIAgentAnalyst(store) if use_ai else None
        mode = "openai-agent" if use_ai else "deterministic"
        return await workflow.analyze(request, analyst=analyst, analysis_mode=mode)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/v1/approvals/{request_id}", response_model=ApprovalRecord)
def submit_approval(request_id: str, action: ApprovalAction) -> ApprovalRecord:
    try:
        record = store.record_approval(request_id, action)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    store.append_event(
        AuditEvent(
            event_type="procurement.approval.recorded",
            request_id=request_id,
            details={
                "role": action.role.value,
                "actor": action.actor,
                "approved": action.approved,
                "status": record.status.value,
            },
        )
    )
    return record


@app.get("/v1/approvals/{request_id}", response_model=ApprovalRecord)
def get_approval(request_id: str) -> ApprovalRecord:
    record = store.approvals.get(request_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Approval gate not found")
    return record


@app.get("/v1/audit/{request_id}", response_model=list[AuditEvent])
def get_audit_events(request_id: str) -> list[AuditEvent]:
    return store.events_for(request_id)
