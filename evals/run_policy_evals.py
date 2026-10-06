from __future__ import annotations

import json
from pathlib import Path

from procurement_agent.models import PurchaseRequest
from procurement_agent.policy import ProcurementPolicyEngine
from procurement_agent.store import DemoEnterpriseStore


def main() -> int:
    cases_path = Path(__file__).with_name("cases.jsonl")
    store = DemoEnterpriseStore()
    policy = ProcurementPolicyEngine()
    passed = 0
    total = 0

    for line in cases_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        total += 1
        case = json.loads(line)
        request = PurchaseRequest(**case["request"])
        result = policy.evaluate(
            request,
            store.get_vendor(request.vendor_id),
            store.get_budget(request.department),
        )
        actual_approvals = {role.value for role in result.required_approvals}
        expected_approvals = set(case["expected_approvals"])
        ok = (
            result.decision.value == case["expected_decision"]
            and actual_approvals == expected_approvals
        )
        passed += int(ok)
        status = "PASS" if ok else "FAIL"
        print(
            f"{status:4} | {case['name']} | decision={result.decision.value} "
            f"approvals={sorted(actual_approvals)}"
        )

    score = passed / total if total else 0
    print(f"\nPolicy regression score: {passed}/{total} = {score:.0%}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
