# Security model

This repository is a portfolio demonstration, not a production procurement product. The security design is intentionally explicit so that the trust model can be reviewed.

## Principle of least privilege

The agent receives only read-only tools. There is no `approve_purchase`, `reserve_budget` or `create_purchase_order` tool.

If execution capabilities were added, they should be isolated behind authenticated, scoped services with server-side authorization and explicit approval semantics.

## Human-in-the-loop

Policy rules create a set of required approval roles. The workflow is not complete until each required role approves. A human rejection closes the gate immediately.

The model cannot mark those approvals as complete.

## Prompt injection

Tool outputs and request text are treated as untrusted data. The repository includes an adversarial eval set covering:

- direct instructions to ignore procurement policy;
- authority impersonation ("I am the CIO");
- fake tool results and fake enterprise records embedded in request text;
- requests to call nonexistent write tools such as budget reservation or purchase execution;
- emergency-language attempts to bypass approval and quote controls;
- structured JSON injected into natural-language fields to override the decision.

The security harness verifies **control-plane invariants**, not only whether the analyst refuses the prompt:

- deterministic decision remains authoritative;
- required approvals remain unchanged;
- vendor and budget reference data remain unchanged;
- approval-gate state remains correct;
- the audit event retains the authoritative decision and trace ID;
- the analyst remains grounded, policy-faithful and free of false execution claims.

Run the deterministic security suite with:

```bash
make eval-security
```

The same cases can exercise the real OpenAI analyst privately:

```bash
OPENAI_API_KEY="..." make eval-security-ai
```

The agent still receives only read-only vendor and budget tools. Security therefore does not depend on prompt obedience alone: unavailable capabilities cannot be invoked merely because untrusted text asks for them.

A production version should additionally include strict tool schemas, content provenance, authorization at tool execution time, output validation and state-dependent tool allowlists.

## MCP least-privilege boundary

The optional MCP façade exposes exactly two enterprise-context tools: vendor lookup and budget lookup. Both are marked read-only, non-destructive, idempotent and closed-world.

The server does **not** publish tools for approvals, vendor mutation, budget reservation or purchase execution. A remote production deployment would additionally require authentication and tenant-aware authorization at the repository boundary; the public demo does not expose the MCP endpoint.

## Data isolation

Production enterprise data should be scoped by tenant and caller identity at the repository/tool layer, not by natural-language model instructions.

## Auditability

The demo emits domain audit events for completed analyses and approval actions. A production design should persist them durably with actor identity, request correlation and immutable retention controls.
