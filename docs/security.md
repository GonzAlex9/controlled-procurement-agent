# Security model

This repository is a portfolio demonstration, not a production procurement product. The security design is intentionally explicit so that the trust model can be reviewed.

## Principle of least privilege

The agent receives only read-only tools. There is no `approve_purchase`, `reserve_budget` or `create_purchase_order` tool.

If execution capabilities were added, they should be isolated behind authenticated, scoped services with server-side authorization and explicit approval semantics.

## Human-in-the-loop

Policy rules create a set of required approval roles. The workflow is not complete until each required role approves. A human rejection closes the gate immediately.

The model cannot mark those approvals as complete.

## Prompt injection

Tool outputs should be treated as untrusted data, particularly when they originate from documents or external systems. A production version should include:

- strict tool schemas;
- content provenance;
- authorization at tool execution time;
- separation between retrieved data and system instructions;
- output validation;
- tool allowlists per workflow state;
- red-team and indirect prompt-injection evals.

## Data isolation

Production enterprise data should be scoped by tenant and caller identity at the repository/tool layer, not by natural-language model instructions.

## Auditability

The demo emits domain audit events for completed analyses and approval actions. A production design should persist them durably with actor identity, request correlation and immutable retention controls.
