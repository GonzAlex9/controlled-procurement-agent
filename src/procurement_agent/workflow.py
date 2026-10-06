from __future__ import annotations

from time import perf_counter
from uuid import uuid4

from procurement_agent.analyst import Analyst, DeterministicAnalyst
from procurement_agent.models import (
    AnalysisTelemetry,
    AuditEvent,
    Decision,
    ProcurementAnalysis,
    PurchaseRequest,
)
from procurement_agent.policy import ProcurementPolicyEngine
from procurement_agent.store import DemoEnterpriseStore


class ProcurementWorkflow:
    def __init__(
        self,
        store: DemoEnterpriseStore,
        policy: ProcurementPolicyEngine | None = None,
    ) -> None:
        self.store = store
        self.policy = policy or ProcurementPolicyEngine()

    async def analyze(
        self,
        request: PurchaseRequest,
        analyst: Analyst | None = None,
        analysis_mode: str = "deterministic",
    ) -> ProcurementAnalysis:
        trace_id = uuid4().hex
        started_at = perf_counter()

        vendor = self.store.get_vendor(request.vendor_id)
        budget = self.store.get_budget(request.department)

        policy_started_at = perf_counter()
        assessment = self.policy.evaluate(request, vendor, budget)
        policy_duration_ms = round((perf_counter() - policy_started_at) * 1_000, 3)

        analyst_started_at = perf_counter()
        narrative = await (analyst or DeterministicAnalyst()).generate(
            request=request,
            vendor=vendor,
            budget=budget,
            policy=assessment,
        )
        analyst_duration_ms = round((perf_counter() - analyst_started_at) * 1_000, 3)
        total_duration_ms = round((perf_counter() - started_at) * 1_000, 3)

        telemetry = AnalysisTelemetry(
            trace_id=trace_id,
            analysis_mode=analysis_mode,
            decision=assessment.decision,
            policy_duration_ms=policy_duration_ms,
            analyst_duration_ms=analyst_duration_ms,
            total_duration_ms=total_duration_ms,
            findings_count=len(assessment.findings),
            required_approvals_count=len(assessment.required_approvals),
        )

        if assessment.decision == Decision.HUMAN_REVIEW:
            self.store.create_approval_gate(request.id, assessment.required_approvals)

        self.store.append_event(
            AuditEvent(
                event_type="procurement.analysis.completed",
                request_id=request.id,
                details={
                    "trace_id": telemetry.trace_id,
                    "decision": assessment.decision.value,
                    "required_approvals": [role.value for role in assessment.required_approvals],
                    "analysis_mode": analysis_mode,
                    "findings_count": telemetry.findings_count,
                    "timings_ms": {
                        "policy": telemetry.policy_duration_ms,
                        "analyst": telemetry.analyst_duration_ms,
                        "total": telemetry.total_duration_ms,
                    },
                },
            )
        )

        return ProcurementAnalysis(
            request=request,
            vendor=vendor,
            budget=budget,
            policy=assessment,
            narrative=narrative,
            analysis_mode=analysis_mode,
            telemetry=telemetry,
        )
