# Architecture

## Design principles

1. **Evaluation is a first-class domain.** A run is immutable evidence about one version of an agent.
2. **Local-first.** Developers must be able to run a deterministic evaluator without paid model calls.
3. **Provider-optional.** LLM judging is an enhancement, not a hard dependency.
4. **CI-native.** Every run can collapse to a pass/fail quality gate.
5. **Trace-ready.** The storage model supports spans for model calls, tool calls, handoffs, and guardrails.

## Components

### Web dashboard

Next.js provides project/run views, scorecards, run comparisons, and trace exploration. v0.1 uses typed demo data while the persistence layer is being wired.

### Evaluator

The FastAPI service accepts evaluation cases and produces per-case scores plus aggregate metrics. The local heuristic scorer uses token overlap and required-term checks. When `judge_mode=llm` and `OPENAI_API_KEY` is configured, an OpenAI Responses API judge can be used.

### CLI

The CLI reads JSONL datasets, sends them to the evaluator, prints a summary, and exits with code `1` when the quality gate fails.

### Persistence

The Supabase migration models projects, datasets, runs, case results, and trace spans. Row-level security is enabled as a foundation for multi-tenant isolation.

## Planned event flow

```text
PR opened
  → GitHub Action
  → AgentGate CLI
  → Evaluation API
  → target agent execution
  → judge/scorers
  → persisted run
  → PR summary + status check
```
