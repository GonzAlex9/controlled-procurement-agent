from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path

from procurement_agent.analyst import OpenAIAgentAnalyst
from procurement_agent.evaluation import CHECK_NAMES, evaluate_analysis
from procurement_agent.models import PurchaseRequest
from procurement_agent.store import DemoEnterpriseStore
from procurement_agent.workflow import ProcurementWorkflow


async def run(mode: str) -> int:
    if mode == "openai" and not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is required for --mode openai")
        return 2

    cases_path = Path(__file__).with_name("cases.jsonl")
    store = DemoEnterpriseStore()
    workflow = ProcurementWorkflow(store)
    analyst = OpenAIAgentAnalyst(store) if mode == "openai" else None
    analysis_mode = "openai-agent" if mode == "openai" else "deterministic"

    dimension_passes = {name: 0 for name in CHECK_NAMES}
    case_count = 0
    passed_checks = 0
    total_checks = 0

    for line in cases_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue

        case_count += 1
        case = json.loads(line)
        request = PurchaseRequest(**case["request"])
        analysis = await workflow.analyze(
            request,
            analyst=analyst,
            analysis_mode=analysis_mode,
        )
        result = evaluate_analysis(analysis)

        for name, passed in result.checks.items():
            dimension_passes[name] += int(passed)

        passed_checks += result.passed_count
        total_checks += result.total_count
        failed = [name for name, passed in result.checks.items() if not passed]
        status = "PASS" if result.passed else "FAIL"
        failure_text = f" failed={','.join(failed)}" if failed else ""

        print(
            f"{status:4} | {case['name']} | checks={result.passed_count}/{result.total_count} "
            f"trace={analysis.telemetry.trace_id[:8]} "
            f"latency={analysis.telemetry.total_duration_ms:.3f}ms{failure_text}"
        )

    score = passed_checks / total_checks if total_checks else 0
    print(f"\nAgent behavior score: {passed_checks}/{total_checks} checks = {score:.0%}")
    for name in CHECK_NAMES:
        print(f"- {name}: {dimension_passes[name]}/{case_count}")

    return 0 if passed_checks == total_checks else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate procurement analyst behavior.")
    parser.add_argument(
        "--mode",
        choices=("deterministic", "openai"),
        default="deterministic",
        help="Use deterministic analyst in CI or the real OpenAI analyst privately.",
    )
    args = parser.parse_args()
    return asyncio.run(run(args.mode))


if __name__ == "__main__":
    raise SystemExit(main())
