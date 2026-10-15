# Roadmap

## Milestone 0.1 — Foundation

- Evaluation request/response contracts.
- Deterministic scoring engine.
- Optional OpenAI judge.
- CLI quality gate.
- GitHub Action wrapper.
- Dashboard foundation.
- Supabase schema.
- CI.

## Milestone 0.2 — Real agent execution

- [x] Durable local run persistence + run history API.
- [x] Dashboard reads persisted evaluator runs with graceful fallback.
- [ ] Supabase hosted persistence adapter.
- [ ] HTTP target adapter.
- Prompt/version metadata.
- Cost and latency capture.
- Retry and timeout policy.
- Persisted evaluation runs.

## Milestone 0.3 — Regression intelligence

- Baseline vs candidate comparison.
- Metric deltas.
- Failure clustering.
- GitHub PR comments.
- Required quality checks.

## Milestone 0.4 — Observability

- Trace ingestion.
- Tool-call spans.
- Handoff spans.
- Token/cost accounting.
- Trace replay UI.

## Milestone 0.5 — Agent ecosystem

- Human review queue.
- MCP tool discovery/testing.
- Custom scorer SDK.
- Webhooks.
- Hosted demo.
