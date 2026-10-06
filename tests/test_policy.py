from procurement_agent.models import Decision, PurchaseRequest
from procurement_agent.policy import ProcurementPolicyEngine
from procurement_agent.store import DemoEnterpriseStore


def make_request(**overrides):
    data = {
        "id": "PR-100",
        "requester": "alex",
        "department": "IT",
        "category": "hardware",
        "vendor_id": "vendor-cloud",
        "amount_eur": 800,
        "justification": "Replacement equipment for engineering workstation.",
        "quotes_count": 1,
    }
    data.update(overrides)
    return PurchaseRequest(**data)


def test_low_risk_small_purchase_auto_approves():
    store = DemoEnterpriseStore()
    request = make_request()
    result = ProcurementPolicyEngine().evaluate(
        request, store.get_vendor(request.vendor_id), store.get_budget(request.department)
    )
    assert result.decision == Decision.AUTO_APPROVE
    assert result.required_approvals == []


def test_medium_purchase_requires_manager_and_finance():
    store = DemoEnterpriseStore()
    request = make_request(amount_eur=8_000, quotes_count=2)
    result = ProcurementPolicyEngine().evaluate(
        request, store.get_vendor(request.vendor_id), store.get_budget(request.department)
    )
    assert result.decision == Decision.HUMAN_REVIEW
    assert {role.value for role in result.required_approvals} == {"manager", "finance"}


def test_personal_data_software_requires_security():
    store = DemoEnterpriseStore()
    request = make_request(category="saas", amount_eur=2_000, contains_personal_data=True)
    result = ProcurementPolicyEngine().evaluate(
        request, store.get_vendor(request.vendor_id), store.get_budget(request.department)
    )
    assert result.decision == Decision.HUMAN_REVIEW
    assert "security" in {role.value for role in result.required_approvals}


def test_blocked_vendor_rejects():
    store = DemoEnterpriseStore()
    request = make_request(vendor_id="vendor-legacy")
    result = ProcurementPolicyEngine().evaluate(
        request, store.get_vendor(request.vendor_id), store.get_budget(request.department)
    )
    assert result.decision == Decision.REJECT
    assert any(f.code == "VENDOR_BLOCKED" for f in result.findings)


def test_budget_overrun_rejects():
    store = DemoEnterpriseStore()
    request = make_request(department="Marketing", amount_eur=9_000, quotes_count=2)
    result = ProcurementPolicyEngine().evaluate(
        request, store.get_vendor(request.vendor_id), store.get_budget(request.department)
    )
    assert result.decision == Decision.REJECT
    assert any(f.code == "BUDGET_EXCEEDED" for f in result.findings)
