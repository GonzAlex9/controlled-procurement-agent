# Evaluation strategy

Agentic systems need two different evaluation layers because deterministic policy logic and model behavior fail differently.

## 1. Deterministic regression suite

`evals/cases.jsonl` defines procurement scenarios with expected decisions and approval roles.

Run:

```bash
make eval
```

This layer should remain exact: a model change must never alter the policy result.

## 2. Agent behavior evaluation

`evals/run_agent_evals.py` runs the same procurement cases through the analyst and grades five explicit behavioral properties:

- **grounding** — vendor, requested amount and budget evidence must match enterprise context;
- **policy fidelity** — the narrative and next step must stay consistent with the deterministic decision and required roles;
- **action safety** — the analyst must not claim that it approved, rejected, reserved budget or placed an order;
- **risk recall** — non-informational policy findings must be represented in the surfaced risks;
- **clarity** — the structured output must contain a usable summary, evidence and next step.

The default mode is deterministic and runs in CI without credentials:

```bash
make eval-agent
```

The same harness can exercise the real read-only OpenAI analyst in a private environment:

```bash
OPENAI_API_KEY="..." make eval-agent-ai
```

Live model evals are intentionally not executed in public CI because they would introduce external cost and model variability. The deterministic CI run protects the behavioral contract and the evaluator itself is covered by tests, including a negative case that must catch a false execution claim.

Each evaluated analysis also emits its trace ID and total latency, linking behavior evaluation to the workflow observability layer.

## 3. Workflow observability

Every analysis exposes lightweight, provider-neutral telemetry:

- a unique `trace_id`;
- policy-engine latency;
- analyst latency;
- total workflow latency;
- decision;
- finding count;
- required-approval count.

The same `trace_id` is written into the `procurement.analysis.completed` audit event. This makes it possible to correlate execution behavior with business audit history without coupling the domain model to a specific observability vendor.

The public demo renders this telemetry directly so the execution path is inspectable without external infrastructure.

## 4. Production monitoring

A production version should export the same trace context to OpenTelemetry or another vendor-neutral telemetry pipeline and combine offline evals with trace-level monitoring for:

- tool errors;
- approval bypass attempts;
- hallucinated enterprise facts;
- latency and token cost;
- model/version regressions;
- unusual tool-call patterns.
