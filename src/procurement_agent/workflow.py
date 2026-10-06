from __future__ import annotations

from procurement_agent.analyst import Analyst, DeterministicAnalyst
from procurement_agent.models import (
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
        vendor = self.store.get_vendor(request.vendor_id)
        budget = self.store.get_budget(request.department)
        assessment = self.policy.evaluate(request, vendor, budget)
        narrative = await (analyst or DeterministicAnalyst()).generate(
            request=request,
            vendor=vendor,
            budget=budget,
            policy=assessment,
        )

        if assessment.decision == Decision.HUMAN_REVIEW:
            self.store.create_approval_gate(request.id, assessment.required_approvals)

        self.store.append_event(
            AuditEvent(
                event_type="procurement.analysis.completed",
                request_id=request.id,
                details={
                    "decision": assessment.decision.value,
                    "required_approvals": [role.value for role in assessment.required_approvals],
                    "analysis_mode": analysis_mode,
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
        )
