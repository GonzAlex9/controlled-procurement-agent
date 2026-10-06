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
