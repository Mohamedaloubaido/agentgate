# AgentGate architecture

AgentGate separates **execution**, **evaluation**, **persistence**, and **presentation** so each layer can evolve independently.

## Runtime flow

```text
JSONL dataset
     │
     ▼
AgentGate CLI / GitHub Action
     │
     ▼
FastAPI Evaluator
     │
     ├── replay mode ───────► pre-recorded `actual`
     │
     └── endpoint mode ─────► live AI agent HTTP endpoint
                                │
                                └── answer + status + latency
     │
     ▼
Heuristic scorer / LLM judge
     │
     ▼
Quality gate
     │
     ├── run summary
     └── case-level execution details
              │
              ▼
        SQLite local store
              │
              ▼
        Next.js dashboard
```

## Components

### `services/evaluator`

FastAPI service responsible for:

- request validation;
- live HTTP agent execution;
- response extraction;
- timeout and HTTP error capture;
- heuristic or LLM-based scoring;
- aggregate quality metrics;
- quality-gate decisions;
- persisted run history.

### `packages/cli`

Dependency-light Node CLI that reads JSONL datasets and invokes the evaluator. It returns exit code `1` when the quality gate fails, which allows CI systems to block merges or deployments.

### `packages/action`

Reusable GitHub Action wrapper around the CLI. It supports both replay datasets and live agent endpoints.

### `apps/web`

Next.js dashboard that reads persisted run history from the evaluator. When the evaluator is unavailable, a demo fallback keeps the interface explorable.

### Persistence

The local adapter uses SQLite because it requires no external account and preserves run history during development. The schema stores queryable run metrics plus serialized case-level detail. A Supabase/PostgreSQL adapter is the planned hosted implementation.

## Design constraints

- Endpoint failures are represented as failed evaluation cases instead of aborting the complete run.
- Replay datasets remain supported for deterministic debugging and historical comparisons.
- Agent execution and judging are separate concerns; a future adapter can run agents through MCP, queues, or provider SDKs without changing scorer contracts.
- Authentication headers are accepted by the API model, but secure CLI/CI secret handling is intentionally deferred until a dedicated secret-loading interface is implemented.
