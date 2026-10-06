from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    delete,
    insert,
    select,
    update,
)
from sqlalchemy.engine import Connection, Engine

from procurement_agent.models import (
    ApprovalAction,
    ApprovalRecord,
    ApprovalRole,
    ApprovalStatus,
    AuditEvent,
    Budget,
    Vendor,
)
from procurement_agent.store import DemoEnterpriseStore

metadata = MetaData()

approval_gates = Table(
    "approval_gates",
    metadata,
    Column("request_id", String(200), primary_key=True),
    Column("required", JSON, nullable=False),
    Column("granted", JSON, nullable=False),
    Column("status", String(40), nullable=False),
)

approval_actions = Table(
    "approval_actions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column(
        "request_id",
        String(200),
        ForeignKey("approval_gates.request_id"),
        nullable=False,
        index=True,
    ),
    Column("role", String(40), nullable=False),
    Column("actor", String(200), nullable=False),
    Column("approved", Boolean, nullable=False),
    Column("note", String(1000), nullable=False),
)

audit_events = Table(
    "audit_events",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("event_type", String(200), nullable=False),
    Column("request_id", String(200), nullable=False, index=True),
    Column("details", JSON, nullable=False),
    Column("occurred_at", DateTime(timezone=True), nullable=False),
)


def normalize_postgres_url(url: str) -> str:
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url.removeprefix("postgres://")
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url.removeprefix("postgresql://")
    return url


class PostgresEnterpriseStore:
    """Durable approval and audit state backed by PostgreSQL."""

    persistent = True

    def __init__(self, database_url: str, *, engine: Engine | None = None) -> None:
        self._reference = DemoEnterpriseStore()
        self.engine = engine or create_engine(
            normalize_postgres_url(database_url),
            pool_pre_ping=True,
        )
        metadata.create_all(self.engine)

    def get_vendor(self, vendor_id: str) -> Vendor | None:
        return self._reference.get_vendor(vendor_id)

    def get_budget(self, department: str) -> Budget | None:
        return self._reference.get_budget(department)

    def create_approval_gate(
        self,
        request_id: str,
        required: list[ApprovalRole],
    ) -> ApprovalRecord:
        required_values = [role.value for role in required]
        with self.engine.begin() as conn:
            existing = conn.execute(
                select(approval_gates.c.request_id).where(
                    approval_gates.c.request_id == request_id
                )
            ).first()

            if existing:
                conn.execute(
                    delete(approval_actions).where(
                        approval_actions.c.request_id == request_id
                    )
                )
                conn.execute(
                    update(approval_gates)
                    .where(approval_gates.c.request_id == request_id)
                    .values(
                        required=required_values,
                        granted=[],
                        status=ApprovalStatus.PENDING.value,
                    )
                )
            else:
                conn.execute(
                    insert(approval_gates).values(
                        request_id=request_id,
                        required=required_values,
                        granted=[],
                        status=ApprovalStatus.PENDING.value,
                    )
                )

            record = self._get_approval_with_connection(conn, request_id)
            assert record is not None
            return record

    def get_approval(self, request_id: str) -> ApprovalRecord | None:
        with self.engine.connect() as conn:
            return self._get_approval_with_connection(conn, request_id)

    def record_approval(
        self,
        request_id: str,
        action: ApprovalAction,
    ) -> ApprovalRecord:
        with self.engine.begin() as conn:
            row = conn.execute(
                select(approval_gates)
                .where(approval_gates.c.request_id == request_id)
                .with_for_update()
            ).mappings().first()

            if row is None:
                raise KeyError(f"No approval gate exists for request {request_id}")

            status = ApprovalStatus(row["status"])
            required = [ApprovalRole(role) for role in row["required"]]
            granted = [ApprovalRole(role) for role in row["granted"]]

            if status != ApprovalStatus.PENDING:
                raise ValueError(f"Approval gate is already {status}")
            if action.role not in required:
                raise ValueError(f"Role {action.role} is not required for this request")

            conn.execute(
                insert(approval_actions).values(
                    request_id=request_id,
                    role=action.role.value,
                    actor=action.actor,
                    approved=action.approved,
                    note=action.note,
                )
            )

            if not action.approved:
                status = ApprovalStatus.REJECTED
            elif action.role not in granted:
                granted.append(action.role)

            if set(granted) >= set(required):
                status = ApprovalStatus.APPROVED

            conn.execute(
                update(approval_gates)
                .where(approval_gates.c.request_id == request_id)
                .values(
                    granted=[role.value for role in granted],
                    status=status.value,
                )
            )

            record = self._get_approval_with_connection(conn, request_id)
            assert record is not None
            return record

    def append_event(self, event: AuditEvent) -> None:
        with self.engine.begin() as conn:
            conn.execute(
                insert(audit_events).values(
                    event_type=event.event_type,
                    request_id=event.request_id,
                    details=event.details,
                    occurred_at=event.occurred_at,
                )
            )

    def events_for(self, request_id: str) -> list[AuditEvent]:
        with self.engine.connect() as conn:
            rows = conn.execute(
                select(audit_events)
                .where(audit_events.c.request_id == request_id)
                .order_by(audit_events.c.id)
            ).mappings()

            return [
                AuditEvent(
                    event_type=row["event_type"],
                    request_id=row["request_id"],
                    details=dict(row["details"]),
                    occurred_at=row["occurred_at"],
                )
                for row in rows
            ]

    def _get_approval_with_connection(
        self,
        conn: Connection,
        request_id: str,
    ) -> ApprovalRecord | None:
        row = conn.execute(
            select(approval_gates).where(approval_gates.c.request_id == request_id)
        ).mappings().first()
        if row is None:
            return None

        history_rows = conn.execute(
            select(approval_actions)
            .where(approval_actions.c.request_id == request_id)
            .order_by(approval_actions.c.id)
        ).mappings()

        return ApprovalRecord(
            request_id=request_id,
            required=[ApprovalRole(role) for role in row["required"]],
            granted=[ApprovalRole(role) for role in row["granted"]],
            status=ApprovalStatus(row["status"]),
            history=[self._action_from_row(history_row) for history_row in history_rows],
        )

    @staticmethod
    def _action_from_row(row: Mapping[str, Any]) -> ApprovalAction:
        return ApprovalAction(
            role=ApprovalRole(row["role"]),
            actor=row["actor"],
            approved=row["approved"],
            note=row["note"],
        )
