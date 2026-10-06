from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class VendorStatus(StrEnum):
    APPROVED = "approved"
    REVIEW = "review"
    BLOCKED = "blocked"


class VendorRisk(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Decision(StrEnum):
    AUTO_APPROVE = "auto_approve"
    HUMAN_REVIEW = "human_review"
    REJECT = "reject"


class ApprovalRole(StrEnum):
    MANAGER = "manager"
    PROCUREMENT = "procurement"
    FINANCE = "finance"
    SECURITY = "security"
    CIO = "cio"


class FindingSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    BLOCKING = "blocking"


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Vendor(BaseModel):
    id: str
    name: str
    status: VendorStatus
    risk: VendorRisk


class Budget(BaseModel):
    department: str
    remaining_eur: float = Field(ge=0)


class PurchaseRequest(BaseModel):
    id: str
    requester: str
    department: str
    category: str
    vendor_id: str
    amount_eur: float = Field(gt=0)
    justification: str = Field(min_length=5, max_length=2_000)
    quotes_count: int = Field(default=1, ge=0)
    contains_personal_data: bool = False
    recurring: bool = False
    emergency: bool = False


class PolicyFinding(BaseModel):
    code: str
    message: str
    severity: FindingSeverity


class PolicyAssessment(BaseModel):
    decision: Decision
    required_approvals: list[ApprovalRole] = Field(default_factory=list)
    findings: list[PolicyFinding] = Field(default_factory=list)


class AgentNarrative(BaseModel):
    summary: str
    risks: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    next_step: str


class AnalysisTelemetry(BaseModel):
    trace_id: str
    analysis_mode: str
    decision: Decision
    policy_duration_ms: float = Field(ge=0)
    analyst_duration_ms: float = Field(ge=0)
    total_duration_ms: float = Field(ge=0)
    findings_count: int = Field(ge=0)
    required_approvals_count: int = Field(ge=0)


class ProcurementAnalysis(BaseModel):
    request: PurchaseRequest
    vendor: Vendor | None
    budget: Budget | None
    policy: PolicyAssessment
    narrative: AgentNarrative
    analysis_mode: str
    telemetry: AnalysisTelemetry


class ApprovalAction(BaseModel):
    role: ApprovalRole
    actor: str = Field(min_length=2, max_length=200)
    approved: bool
    note: str = Field(default="", max_length=1_000)


class ApprovalRecord(BaseModel):
    request_id: str
    required: list[ApprovalRole]
    granted: list[ApprovalRole] = Field(default_factory=list)
    status: ApprovalStatus = ApprovalStatus.PENDING
    history: list[ApprovalAction] = Field(default_factory=list)


class AuditEvent(BaseModel):
    event_type: str
    request_id: str
    details: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
