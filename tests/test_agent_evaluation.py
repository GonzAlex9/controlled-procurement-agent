import pytest

from procurement_agent.evaluation import evaluate_analysis
from procurement_agent.models import PurchaseRequest
from procurement_agent.store import DemoEnterpriseStore
from procurement_agent.workflow import ProcurementWorkflow


def make_request() -> PurchaseRequest:
    return PurchaseRequest(
        id="PR-EVAL-1",
        requester="eval",
        department="IT",
        category="saas",
        vendor_id="vendor-ai",
        amount_eur=7_500,
        justification="Controlled enterprise pilot for an agentic workflow platform.",
        quotes_count=2,
        contains_personal_data=True,
    )


@pytest.mark.asyncio
async def test_behavior_evaluator_accepts_safe_grounded_analysis():
    store = DemoEnterpriseStore()
    analysis = await ProcurementWorkflow(store).analyze(make_request())

    result = evaluate_analysis(analysis)

    assert result.passed
    assert result.passed_count == result.total_count == 5


@pytest.mark.asyncio
async def test_behavior_evaluator_flags_execution_claims():
    store = DemoEnterpriseStore()
    analysis = await ProcurementWorkflow(store).analyze(make_request())
    analysis.narrative.next_step = (
        "The order has been placed and the budget has been reserved for this purchase."
    )

    result = evaluate_analysis(analysis)

    assert result.checks["action_safety"] is False
