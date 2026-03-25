# ADR-002: Client-side State Persistence via LocalStorage

- Status: Accepted
- Date: 2026-03-25
- Deciders: Federico Orsi

## Context

WorkflowArchitect requires state management for its agentic workflow (Plan -> Commit -> PR). For a local-first engineering tool, implementing a server-side database (PostgreSQL/MongoDB) adds infrastructure complexity and setup friction for new users.

## Decision

Assign `localStorage` as the primary state persistence mechanism for the following data:
- Workflow inputs (Plan, Commit, PR metadata).
- Generated LLM outputs history.
- Browser-session configuration settings.

## Rationale

1. **Zero Infrastructure Cost**: No external dependencies (databases) needed to run the software.
2. **Local-First Privacy**: Sensitive metadata is kept within the user's browser, aligning with the local-lean tool philosophy.
3. **Optimized Latency**: State transitions avoid network round-trips to a database.
4. **Developer Experience (DX)**: The "Setup-to-Execution" time is effectively zero; state works out-of-the-box.

## Consequences

### Positive:
- Simplified architecture and lowered maintenance overhead.
- High performance for state transitions.
- "Serverless-ready" stateless backend.

### Negative:
- No cross-browser/cross-device synchronization.
- 5MB browser storage limits.
- Vulnerability to data loss upon cache clearing.

### Future Considerations:
If multi-device collaboration is required, a move to a local-first sync layer (e.g., Replicache) or a lightweight persistence layer (SQLite) would be evaluated.
