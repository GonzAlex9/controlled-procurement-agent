from __future__ import annotations

import json
import os
from typing import Protocol

from procurement_agent.models import (
    AgentNarrative,
    Budget,
    Decision,
    PolicyAssessment,
    PurchaseRequest,
    Vendor,
)
from procurement_agent.store import DemoEnterpriseStore


class Analyst(Protocol):
    async def generate(
        self,
        request: PurchaseRequest,
        vendor: Vendor | None,
        budget: Budget | None,
        policy: PolicyAssessment,
    ) -> AgentNarrative: ...


class DeterministicAnalyst:
    """Offline explanation mode used in tests and local demos without an API key."""

    async def generate(
        self,
        request: PurchaseRequest,
        vendor: Vendor | None,
        budget: Budget | None,
        policy: PolicyAssessment,
    ) -> AgentNarrative:
        vendor_name = vendor.name if vendor else f"unknown vendor ({request.vendor_id})"
        budget_text = (
            f"EUR {budget.remaining_eur:,.2f} remaining"
            if budget
            else "budget unavailable"
        )
        risks = [finding.message for finding in policy.findings if finding.severity != "info"]
        evidence = [
            f"Requested amount: EUR {request.amount_eur:,.2f}",
            f"Vendor: {vendor_name}",
            f"Department budget: {budget_text}",
            f"Quotes supplied: {request.quotes_count}",
        ]
        if policy.decision == Decision.AUTO_APPROVE:
            next_step = (
                "Policy checks passed; the request can proceed to the next "
                "deterministic workflow step."
            )
        elif policy.decision == Decision.HUMAN_REVIEW:
            roles = ", ".join(role.value for role in policy.required_approvals)
            next_step = f"Collect required human approvals: {roles}."
        else:
            next_step = "Stop the workflow and resolve the blocking policy findings."

        return AgentNarrative(
            summary=(
                f"Procurement request {request.id} for {vendor_name} was evaluated under "
                f"the deterministic policy engine: {policy.decision.value}."
            ),
            risks=risks,
            evidence=evidence,
            next_step=next_step,
        )


class OpenAIAgentAnalyst:
    """Read-only agentic analysis. The model can inspect context but cannot approve spend."""

    def __init__(self, store: DemoEnterpriseStore) -> None:
        try:
            from agents import Agent, Runner, function_tool
        except ImportError as exc:  # pragma: no cover - depends on optional extra
            raise RuntimeError(
                'AI mode requires the optional dependency: pip install -e ".[ai]"'
            ) from exc

        self._runner = Runner

        @function_tool
        def lookup_vendor(vendor_id: str) -> str:
            """Read vendor-master facts for a vendor ID. This tool never changes vendor state."""
            vendor = store.get_vendor(vendor_id)
            if vendor is None:
                return json.dumps({"found": False, "vendor_id": vendor_id})
            return vendor.model_dump_json()

        @function_tool
        def lookup_budget(department: str) -> str:
            """Read demo budget for a department without reserving or spending funds."""
            budget = store.get_budget(department)
            if budget is None:
                return json.dumps({"found": False, "department": department})
            return budget.model_dump_json()

        model = os.getenv("OPENAI_MODEL", "gpt-5.6-sol")
        self._agent = Agent(
            name="Procurement Analyst",
            model=model,
            instructions=(
                "You are a read-only enterprise procurement analyst. "
                "Always use the vendor and budget tools to verify enterprise facts. "
                "The deterministic policy assessment in the input is authoritative. "
                "Never claim to approve, reject, reserve budget, place an order, or "
                "override policy. Explain the request, surface risks, cite concrete "
                "evidence, and state the next step."
            ),
            tools=[lookup_vendor, lookup_budget],
            output_type=AgentNarrative,
        )

    async def generate(
        self,
        request: PurchaseRequest,
        vendor: Vendor | None,
        budget: Budget | None,
        policy: PolicyAssessment,
    ) -> AgentNarrative:
        payload = {
            "purchase_request": request.model_dump(mode="json"),
            "deterministic_policy_assessment": policy.model_dump(mode="json"),
        }
        result = await self._runner.run(
            self._agent,
            "Analyze this request. Verify vendor and budget facts with tools before responding.\n"
            + json.dumps(payload, indent=2),
            max_turns=6,
        )
        output = result.final_output
        if not isinstance(output, AgentNarrative):  # defensive boundary
            raise TypeError("Agent returned an unexpected output type")
        return output
