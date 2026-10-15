# Roadmap

## Milestone 0.1 — Foundation

- [x] Evaluation request/response contracts.
- [x] Deterministic scoring engine.
- [x] Optional OpenAI judge.
- [x] CLI quality gate.
- [x] GitHub Action wrapper.
- [x] Dashboard foundation.
- [x] Supabase schema foundation.
- [x] CI foundation.

## Milestone 0.2 — Persistent runs

- [x] Durable local SQLite run persistence.
- [x] Run history API.
- [x] Dashboard reads persisted runs with graceful fallback.
- [x] Case-level persisted evaluation details.

## Milestone 0.3 — Real agent execution

- [x] HTTP target adapter.
- [x] Dataset cases without pre-recorded `actual` answers.
- [x] Nested response extraction.
- [x] Request timeout policy.
- [x] HTTP status and execution-error capture.
- [x] Live-agent CI smoke test.
- [ ] Authenticated endpoint secret handling.
- [ ] Retry/backoff policy.
- [ ] Provider-reported token and cost ingestion.

## Milestone 0.4 — Regression intelligence

- [ ] Baseline vs candidate comparison.
- [ ] Metric deltas and regression thresholds.
- [ ] Failure clustering.
- [ ] GitHub PR comments.
- [ ] Required quality checks.
- [ ] Prompt/version metadata.

## Milestone 0.5 — Hosted persistence and observability

- [ ] Supabase hosted persistence adapter.
- [ ] Trace ingestion.
- [ ] Tool-call spans.
- [ ] Handoff spans.
- [ ] Token/cost accounting.
- [ ] Trace replay UI.

## Milestone 0.6 — Agent ecosystem

- [ ] Human review queue.
- [ ] MCP tool discovery/testing.
- [ ] Custom scorer SDK.
- [ ] Webhooks.
- [ ] Hosted demo.
