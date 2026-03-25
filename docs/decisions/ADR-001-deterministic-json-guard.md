# ADR-001: Deterministic JSON Guard for LLM Output

- Status: Accepted
- Date: 2026-02-11
- Deciders: Dev Flow AI Maintainers

## Context

Dev Flow AI relies on structured LLM outputs for workflow-critical features:

- CommitSense (`/api/commit`)
- PR Builder (`/api/pr`)
- Planner (`/api/plan`)

LLM responses are probabilistic and can occasionally produce malformed or schema-incompatible JSON. Without a defensive contract layer, malformed output causes downstream parsing failures and unstable UX in the Plan -> Commit -> PR pipeline.

## Decision

Adopt a strict JSON Guard with retry logic as a mandatory boundary between raw LLM output and application services.

The guard:

- Validates output against explicit Pydantic/JSON schemas.
- Rejects malformed payloads deterministically.
- Triggers bounded automatic retries when validation fails.
- Returns typed, contract-safe objects to service layers.

Rationale: LLMs are non-deterministic. To ensure the CommitSense and PR Builder features work reliably, we enforce a strict schema validation layer that triggers automatic retries on malformed JSON, trading slight latency for high reliability.

## Consequences

Positive:

- Higher reliability and predictable API behavior.
- Reduced runtime parsing errors in production-like workflows.
- Easier observability because validation failures are explicit and traceable.

Negative:

- Slight latency increase on retry paths.
- Additional implementation complexity for schema evolution and retry tuning.

Operational trade-off:

- Reliability is prioritized over minimal response time for workflow-critical endpoints.
