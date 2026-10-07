# Security Policy

## Supported version

This repository is a portfolio project. The currently documented release is **v1.0.0**.

Security fixes, if needed, are applied to the latest version of the project rather than maintained across multiple support branches.

## Reporting a vulnerability

Please **do not publish exploit details, credentials, secrets, personal data, or other sensitive information in a public issue**.

If GitHub's private vulnerability-reporting option is available for this repository, use that channel.

If a private reporting channel is not available, open a minimal public issue stating that you would like to report a security concern privately, without including sensitive technical details.

## Security model

The project is intentionally designed around constrained authority:

- AI-facing enterprise tools are read-only.
- Procurement policy decisions are enforced by deterministic code.
- Human approval roles are represented outside the model.
- Protected workflow state is not writable by the analyst.
- Adversarial checks exercise authority-boundary and prompt-injection scenarios.
- Audit and telemetry are correlated without intentionally placing request justifications, credentials, prompts, or enterprise payloads in custom telemetry attributes.

See the README and project documentation for the full architecture.

## Public demo boundary

The public demo is provided for portfolio review and uses **fictional procurement data**.

It is not a production procurement service and should not be used with real company credentials, confidential procurement data, personal information, or production secrets.

The public demo intentionally runs without an OpenAI API key and uses in-memory persistence unless a database is explicitly configured.

## Scope

Useful reports include issues involving:

- unintended write capability;
- approval or authorization bypass;
- sensitive-data exposure;
- cross-request state leakage;
- prompt-injection paths that cross a documented authority boundary;
- dependency vulnerabilities that materially affect this project.

General product suggestions and non-security bugs can be reported through normal GitHub issues.
