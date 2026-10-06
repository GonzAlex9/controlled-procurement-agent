import pytest

from procurement_agent.models import (
    ApprovalAction,
    ApprovalRole,
    ApprovalStatus,
    Decision,
    PurchaseRequest,
)
from procurement_agent.store import DemoEnterpriseStore
from procurement_agent.workflow import ProcurementWorkflow


@pytest.mark.asyncio
async def test_human_review_creates_approval_gate_and_audit_event():
    store = DemoEnterpriseStore()
    workflow = ProcurementWorkflow(store)
    request = PurchaseRequest(
        id="PR-200",
        requester="alex",
        department="IT",
        category="saas",
        vendor_id="vendor-ai",
        amount_eur=7_500,
        justification="Agentic workflow platform for a controlled enterprise pilot.",
        quotes_count=2,
        contains_personal_data=True,
    )

    analysis = await workflow.analyze(request)

    assert analysis.policy.decision == Decision.HUMAN_REVIEW
    assert request.id in store.approvals
    assert store.events_for(request.id)[0].event_type == "procurement.analysis.completed"


def test_all_required_human_approvals_close_gate():
    store = DemoEnterpriseStore()
    record = store.create_approval_gate(
        "PR-300", [ApprovalRole.MANAGER, ApprovalRole.FINANCE]
    )
    assert record.status == ApprovalStatus.PENDING

    store.record_approval(
        "PR-300", ApprovalAction(role=ApprovalRole.MANAGER, actor="manager@example", approved=True)
    )
    result = store.record_approval(
        "PR-300", ApprovalAction(role=ApprovalRole.FINANCE, actor="finance@example", approved=True)
    )

    assert result.status == ApprovalStatus.APPROVED


def test_rejection_closes_gate_immediately():
    store = DemoEnterpriseStore()
    store.create_approval_gate("PR-301", [ApprovalRole.MANAGER])
    result = store.record_approval(
        "PR-301", ApprovalAction(role=ApprovalRole.MANAGER, actor="manager@example", approved=False)
    )
    assert result.status == ApprovalStatus.REJECTED


@pytest.mark.asyncio
async def test_analysis_telemetry_is_correlated_with_audit_event():
    store = DemoEnterpriseStore()
    workflow = ProcurementWorkflow(store)
    request = PurchaseRequest(
        id="PR-TRACE-1",
        requester="alex",
        department="IT",
        category="hardware",
        vendor_id="vendor-cloud",
        amount_eur=800,
        justification="Replacement equipment for engineering workstation.",
        quotes_count=1,
    )

    analysis = await workflow.analyze(request)
    event = store.events_for(request.id)[0]

    assert analysis.telemetry.trace_id
    assert analysis.telemetry.analysis_mode == "deterministic"
    assert analysis.telemetry.decision == analysis.policy.decision
    assert analysis.telemetry.total_duration_ms >= 0
    assert analysis.telemetry.findings_count == len(analysis.policy.findings)
    assert event.details["trace_id"] == analysis.telemetry.trace_id
    assert event.details["timings_ms"]["total"] == analysis.telemetry.total_duration_ms
