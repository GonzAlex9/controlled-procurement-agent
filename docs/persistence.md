# Persistence

The public portfolio demo defaults to an in-memory store so it remains free and zero-configuration.

When `DATABASE_URL` is set, the API switches to `PostgresEnterpriseStore` and persists workflow-owned mutable state in PostgreSQL.

## What is persisted

PostgreSQL owns:

- approval gates and required roles;
- granted approval roles;
- approval action history;
- append-only audit events.

Vendor-master and department-budget facts remain read-only fictional reference data in this repository. A real enterprise deployment would normally read those from ERP, procurement and finance systems rather than duplicate their system-of-record ownership here.

## Repository boundary

The workflow depends on the `EnterpriseStore` protocol rather than a database implementation.

```text
ProcurementWorkflow
        |
        v
 EnterpriseStore protocol
     /             \
    v               v
in-memory        PostgreSQL
 demo store      durable store
```

This keeps deterministic policy, agent analysis and approval semantics independent from persistence technology.

## Concurrency

Approval writes run inside a database transaction and lock the approval-gate row with `SELECT ... FOR UPDATE` before changing granted roles or status. This prevents concurrent approvals from blindly overwriting each other's state.

Audit events are inserted as independent rows and read back in insertion order.

## Local configuration

Install the PostgreSQL extra:

```bash
pip install -e ".[postgres]"
```

Then set a SQLAlchemy PostgreSQL URL:

```bash
export DATABASE_URL="postgresql+psycopg://user:password@localhost:5432/procurement"
uvicorn procurement_agent.api:app --reload
```

Common `postgres://` and `postgresql://` URLs are normalized to the Psycopg 3 dialect automatically.

The portfolio implementation creates its small schema through SQLAlchemy metadata. A production rollout with independently evolving schemas should replace that bootstrap step with a migration workflow such as Alembic.

## CI integration test

GitHub Actions starts a real PostgreSQL service container and runs an integration test that:

1. analyzes a request and creates an approval gate;
2. records an approval and an audit event;
3. creates a second `PostgresEnterpriseStore` instance;
4. reads the same gate, approval history and audit trail back from PostgreSQL.

That proves persistence across repository instances rather than only mocking database calls.
