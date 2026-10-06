# Architecture

The project deliberately separates **probabilistic reasoning** from **authoritative business state**.

```text
Purchase request
      │
      ├───────────────┐
      ▼               ▼
Enterprise facts     Read-only AI analyst
(vendor / budget)    (tools + structured output)
      │               │
      ▼               │
Deterministic policy ◄┘
      │
      ├── auto_approve ──► next deterministic step
      ├── human_review ──► explicit approval gate
      └── reject ─────────► stop + explain blockers
                              │
                              ▼
                         Audit events
```

## Trust boundaries

### The agent may

- read enterprise facts through narrow tools;
- explain the request;
- identify risks in natural language;
- organize evidence;
- recommend a next step consistent with the policy result.

### The agent may not

- approve spend;
- change vendor status;
- reserve or modify budget;
- overwrite the deterministic policy result;
- bypass required human approval;
- execute a purchase.

## Why a deterministic policy engine?

Approval thresholds, blocked vendors, quote requirements and security gates are objective rules. Encoding them in model instructions would make them harder to test, audit and reproduce.

The LLM is therefore used only where ambiguity and interpretation are useful.

## Observability boundary

Each analysis receives a unique application trace ID and records policy, analyst and total execution latency. The trace ID is mirrored into the business audit event so runtime behavior can be correlated with the authoritative workflow history.

The workflow also emits OpenTelemetry spans through the vendor-neutral API:

- `procurement.analyze`;
- `procurement.policy.evaluate`;
- `procurement.analyst.generate`.

Only control-plane metadata is attached to spans: trace correlation, analysis mode, decision and aggregate counts. Request justification, actor identity, prompts and enterprise payloads are deliberately excluded from custom span attributes.

OTLP export is optional. When an `OTEL_EXPORTER_OTLP_ENDPOINT` or `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` is configured and the `observability` extra is installed, the app initializes an OpenTelemetry SDK tracer provider, batches spans to an OTLP/HTTP exporter and instruments FastAPI requests. Without an endpoint, the OpenTelemetry API remains a no-op and the public demo has no external telemetry dependency.

## MCP enterprise-context façade

The same vendor and budget boundary is exposed through a separate MCP server using the official Python SDK v2.

It deliberately publishes only:

- `procurement_lookup_vendor`;
- `procurement_lookup_budget`.

Both tools are typed, structured, idempotent and explicitly annotated as read-only/non-destructive. No approval, budget-reservation, vendor-mutation or purchase-execution capability exists in the MCP server.

The façade can run over stdio for local MCP hosts or stateless Streamable HTTP with JSON responses for a separately secured remote deployment. It is intentionally not exposed by the public portfolio demo.

This keeps the integration boundary reusable: the internal OpenAI analyst may use direct adapters, while another MCP-compatible agent can consume the same enterprise context without receiving business authority.

## State

The demo uses an in-memory store to remain easy to run. In a production design this boundary would be replaced with repositories backed by an ERP/database and an append-only or durable audit system.

## Agent runtime

AI mode uses the OpenAI Agents SDK with:

- read-only function tools;
- structured Pydantic output;
- bounded turns;
- SDK tracing;
- explicit instructions that deterministic policy is authoritative.

The core policy workflow remains usable and testable without an AI provider.
