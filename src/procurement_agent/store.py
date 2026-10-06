from __future__ import annotations

import os
from typing import Protocol

from procurement_agent.models import (
    ApprovalAction,
    ApprovalRecord,
    ApprovalRole,
    ApprovalStatus,
    AuditEvent,
    Budget,
    Vendor,
    VendorRisk,
    VendorStatus,
)


class EnterpriseStore(Protocol):
    persistent: bool

    def get_vendor(self, vendor_id: str) -> Vendor | None: ...

    def get_budget(self, department: str) -> Budget | None: ...

    def create_approval_gate(
        self,
        request_id: str,
        required: list[ApprovalRole],
    ) -> ApprovalRecord: ...

    def get_approval(self, request_id: str) -> ApprovalRecord | None: ...

    def record_approval(
        self,
        request_id: str,
        action: ApprovalAction,
    ) -> ApprovalRecord: ...

    def append_event(self, event: AuditEvent) -> None: ...

    def events_for(self, request_id: str) -> list[AuditEvent]: ...


class DemoEnterpriseStore:
    """In-memory enterprise context for a safe, reproducible portfolio demo."""

    persistent = False

    def __init__(self) -> None:
        self.vendors = {
            "vendor-cloud": Vendor(
                id="vendor-cloud",
                name="CloudWorks Europe",
                status=VendorStatus.APPROVED,
                risk=VendorRisk.LOW,
            ),
            "vendor-ai": Vendor(
                id="vendor-ai",
                name="Agent Labs",
                status=VendorStatus.REVIEW,
                risk=VendorRisk.MEDIUM,
            ),
            "vendor-legacy": Vendor(
                id="vendor-legacy",
                name="Legacy Services Ltd",
                status=VendorStatus.BLOCKED,
                risk=VendorRisk.HIGH,
            ),
        }
        self.budgets = {
            "IT": Budget(department="IT", remaining_eur=50_000),
            "Operations": Budget(department="Operations", remaining_eur=18_000),
            "Marketing": Budget(department="Marketing", remaining_eur=8_000),
        }
        self.approvals: dict[str, ApprovalRecord] = {}
        self.audit_events: list[AuditEvent] = []

    def get_vendor(self, vendor_id: str) -> Vendor | None:
        return self.vendors.get(vendor_id)

    def get_budget(self, department: str) -> Budget | None:
        return self.budgets.get(department)

    def create_approval_gate(
        self,
        request_id: str,
        required: list[ApprovalRole],
    ) -> ApprovalRecord:
        record = ApprovalRecord(request_id=request_id, required=required)
        self.approvals[request_id] = record
        return record

    def get_approval(self, request_id: str) -> ApprovalRecord | None:
        return self.approvals.get(request_id)

    def record_approval(self, request_id: str, action: ApprovalAction) -> ApprovalRecord:
        record = self.get_approval(request_id)
        if record is None:
            raise KeyError(f"No approval gate exists for request {request_id}")
        if record.status != ApprovalStatus.PENDING:
            raise ValueError(f"Approval gate is already {record.status}")
        if action.role not in record.required:
            raise ValueError(f"Role {action.role} is not required for this request")

        record.history.append(action)
        if not action.approved:
            record.status = ApprovalStatus.REJECTED
        elif action.role not in record.granted:
            record.granted.append(action.role)

        if set(record.granted) >= set(record.required):
            record.status = ApprovalStatus.APPROVED

        return record

    def append_event(self, event: AuditEvent) -> None:
        self.audit_events.append(event)

    def events_for(self, request_id: str) -> list[AuditEvent]:
        return [event for event in self.audit_events if event.request_id == request_id]


def build_enterprise_store(database_url: str | None = None) -> EnterpriseStore:
    url = database_url if database_url is not None else os.getenv("DATABASE_URL")
    if not url:
        return DemoEnterpriseStore()

    try:
        from procurement_agent.postgres_store import PostgresEnterpriseStore
    except ImportError as exc:  # pragma: no cover - optional dependency boundary
        raise RuntimeError(
            'PostgreSQL mode requires: pip install -e ".[postgres]"'
        ) from exc

    return PostgresEnterpriseStore(url)
