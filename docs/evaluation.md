# Evaluation strategy

Agentic systems need two different evaluation layers because deterministic policy logic and model behavior fail differently.

## 1. Deterministic regression suite

`evals/cases.jsonl` defines procurement scenarios with expected decisions and approval roles.

Run:

```bash
make eval
```

This layer should remain exact: a model change must never alter the policy result.

## 2. Agent quality evaluation

The read-only analyst should be evaluated on dimensions such as:

- **grounding** — does the explanation use facts returned by tools?
- **policy fidelity** — does it respect the deterministic decision?
- **action safety** — does it avoid claiming that it approved or executed spend?
- **risk recall** — does it surface relevant policy findings?
- **clarity** — can a human approver understand the evidence and next step?
- **cost / latency** — is the model choice justified for this workflow?

A future evaluation harness can grade stored traces against a fixed dataset and fail CI when quality regresses below a threshold.

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
