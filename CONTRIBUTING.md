# Contributing

Thanks for your interest in improving the Controlled Procurement Agent.

This repository is primarily a portfolio project, but focused contributions are welcome when they improve clarity, reliability, evaluation coverage, security boundaries, or developer experience.

## Before opening a pull request

For behavior-changing work, please open an issue first and describe:

- the problem being solved;
- the proposed change;
- which trust or authority boundary is affected;
- how the change should be tested.

Small documentation fixes can go directly to a pull request.

## Design constraints

Please preserve the core architecture:

- **AI reasoning is not business authority.**
- Deterministic code owns procurement policy.
- AI-facing enterprise tools should remain narrow and read-only unless a change explicitly introduces and justifies a stronger control model.
- Human approval state must remain outside the model.
- Vendor and budget facts represent external systems of record.
- Security should rely on capabilities, authorization, validation, and workflow controls rather than prompt instructions alone.

A contribution that changes one of these constraints should explain the trade-off explicitly.

## Development setup

Create a virtual environment and install the project dependencies according to the README.

Run the relevant checks before submitting a pull request.

Typical validation includes:

```bash
pytest
```

and the deterministic evaluation commands documented in the repository.

If your change affects optional integrations such as PostgreSQL, MCP, OpenTelemetry, or live-model evaluation, include the corresponding focused test coverage.

## Evaluation expectations

Tests and evals should be chosen by failure mode.

Prefer deterministic assertions for exact invariants such as:

- policy decisions;
- required approvers;
- schemas;
- state transitions;
- tool permissions;
- audit integrity.

Use behavioral evaluation for semantic properties such as grounding, clarity, risk recall, and action safety.

Security-sensitive changes should add or update adversarial cases where appropriate.

## Pull request scope

Prefer small pull requests with:

- one clear purpose;
- explicit rationale;
- tests or eval coverage where relevant;
- no unrelated refactoring.

## Data and secrets

Do not commit:

- real company procurement data;
- personal data;
- API keys;
- credentials;
- private prompts or logs containing sensitive content.

Use the fictional demo data and environment-variable patterns already present in the repository.

## Commit and PR language

Repository documentation, code comments, commit messages, and pull request descriptions should remain in **English**.

## Security reports

For vulnerabilities or authority-boundary concerns, follow [SECURITY.md](SECURITY.md).
