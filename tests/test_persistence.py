import os
from uuid import uuid4

import pytest

from procurement_agent.models import (
    ApprovalAction,
    ApprovalRole,
    ApprovalStatus,
    AuditEvent,
    PurchaseRequest,
)
from procurement_agent.postgres_store import (
    PostgresEnterpriseStore,
    normalize_postgres_url,
)
from procurement_agent.store import DemoEnterpriseStore, build_enterprise_store
from procurement_agent.workflow import ProcurementWorkflow

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


def test_store_factory_defaults_to_memory(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    store = build_enterprise_store()

    assert isinstance(store, DemoEnterpriseStore)
    assert store.persistent is False


def test_postgres_url_normalizes_to_psycopg():
    assert (
        normalize_postgres_url("postgresql://user:pass@db.example/procurement")
        == "postgresql+psycopg://user:pass@db.example/procurement"
    )
    assert (
        normalize_postgres_url("postgres://user:pass@db.example/procurement")
        == "postgresql+psycopg://user:pass@db.example/procurement"
    )


@pytest.mark.skipif(not TEST_DATABASE_URL, reason="TEST_DATABASE_URL is not configured")
@pytest.mark.asyncio
async def test_postgres_persists_workflow_state_across_store_instances():
    assert TEST_DATABASE_URL is not None
    request_id = f"PR-PG-{uuid4().hex}"
    first = PostgresEnterpriseStore(TEST_DATABASE_URL)
    request = PurchaseRequest(
        id=request_id,
        requester="persistence.test",
        department="IT",
        category="saas",
        vendor_id="vendor-ai",
        amount_eur=7_500,
        justification="Persistent approval workflow integration test.",
        quotes_count=2,
        contains_personal_data=True,
    )

    analysis = await ProcurementWorkflow(first).analyze(request)
    assert analysis.policy.decision.value == "human_review"

    first.record_approval(
        request_id,
        ApprovalAction(
            role=ApprovalRole.MANAGER,
            actor="manager.persistence.test",
            approved=True,
            note="Validated in PostgreSQL integration test.",
        ),
    )
    first.append_event(
        AuditEvent(
            event_type="procurement.persistence.test",
            request_id=request_id,
            details={"phase": "first-store"},
        )
    )

    second = PostgresEnterpriseStore(TEST_DATABASE_URL)
    restored = second.get_approval(request_id)
    events = second.events_for(request_id)

    assert restored is not None
    assert restored.status == ApprovalStatus.PENDING
    assert restored.granted == [ApprovalRole.MANAGER]
    assert restored.history[0].actor == "manager.persistence.test"
    assert [event.event_type for event in events] == [
        "procurement.analysis.completed",
        "procurement.persistence.test",
    ]
    assert events[0].details["trace_id"] == analysis.telemetry.trace_id
