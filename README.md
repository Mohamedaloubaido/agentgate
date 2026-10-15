# AgentGate

**Ship AI agents with confidence.**

AgentGate is an open-source reliability and CI platform for AI agents. It executes agent endpoints against repeatable evaluation datasets, scores non-deterministic answers, stores run history, and turns reliability thresholds into merge-blocking quality gates.

> Status: **v0.3 alpha** — live HTTP agent execution is now part of the evaluation path.

## Why AgentGate?

Traditional software has unit tests. AI agents need evaluation suites that understand non-deterministic output, required facts, execution failures, latency, tool behavior, and quality thresholds.

```text
Agent / prompt change
        ↓
Evaluation dataset
        ↓
Live HTTP agent execution
        ↓
Heuristic or LLM judge
        ↓
Persisted metrics + case details
        ↓
Quality gate
        ↓
Pass → merge     Fail → block
```

## v0.3 includes

- FastAPI evaluation service.
- Live HTTP agent target execution.
- Per-case latency, HTTP status, response, and execution-error capture.
- Nested JSON response extraction with configurable dot paths.
- Deterministic local heuristic scoring.
- Optional OpenAI LLM-as-a-Judge provider.
- JSONL evaluation datasets with or without pre-recorded `actual` answers.
- Quality thresholds and non-zero CLI exit codes for CI.
- Reusable GitHub Action wrapper.
- SQLite run persistence with summary and case-level drilldown APIs.
- Next.js dashboard backed by persisted evaluator runs.
- PostgreSQL/Supabase schema for the hosted architecture.
- Unit tests plus a live-agent CI smoke test.

## Architecture

```text
┌──────────────────────────────┐
│       Next.js Dashboard      │
│        React / TypeScript    │
└──────────────┬───────────────┘
               │ run history
               ▼
┌──────────────────────────────┐
│       FastAPI Evaluator      │
│ execution + scoring + gate  │
└───────┬──────────────┬───────┘
        │              │
        │ HTTP         │ persistence
        ▼              ▼
┌──────────────┐   ┌──────────────┐
│  AI Agent    │   │ SQLite local │
│  endpoint    │   │ Supabase next│
└──────────────┘   └──────────────┘

GitHub Actions ──► AgentGate CLI ──► Evaluator ──► Quality Gate
```

## Quick start

### 1. Run the evaluator

```bash
cd services/evaluator
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
fastapi dev app/main.py
```

The API is available at `http://localhost:8000`.

### 2. Evaluate a pre-recorded dataset

```bash
node packages/cli/bin/agentgate.mjs eval \
  --dataset examples/customer-support/evals.jsonl \
  --url http://localhost:8000
```

### 3. Evaluate a live agent endpoint

A tiny example endpoint is included:

```bash
python examples/customer-support/mock_agent.py
```

Then execute every dataset input against it:

```bash
node packages/cli/bin/agentgate.mjs eval \
  --dataset examples/customer-support/evals.live.jsonl \
  --agent-url http://127.0.0.1:8090 \
  --response-path data.answer \
  --project customer-support-agent
```

Example output:

```text
AgentGate quality gate · run_f75b91fa8269
────────────────────────────────
Source           endpoint
Cases                   3
Task success       100.0%
Groundedness        84.0%
Average score       70.0%
Avg latency           4ms
────────────────────────────────
✓ QUALITY GATE PASSED
```

### 4. Run the dashboard

```bash
npm install
npm run dev:web
```

Open `http://localhost:3000`.

## Evaluation case formats

For a live endpoint, no candidate answer is required in the dataset:

```json
{
  "id": "refund-window",
  "input": "Can I get a refund after 45 days?",
  "expected": "Refunds are only available within 30 days of purchase.",
  "required_terms": ["30 days"]
}
```

For offline/replay evaluation, keep `actual` in the case:

```json
{
  "id": "refund-window",
  "input": "Can I get a refund after 45 days?",
  "expected": "Refunds are only available within 30 days of purchase.",
  "actual": "Refunds are limited to purchases made in the last 30 days.",
  "required_terms": ["30 days"]
}
```

## HTTP target contract

By default AgentGate sends:

```json
{
  "input": "the evaluation prompt",
  "case_id": "refund-window"
}
```

The input key can be changed with `--input-field`. For JSON responses, AgentGate can automatically read common fields such as `output`, `answer`, `response`, `message`, `content`, or `text`, or use an explicit nested path:

```bash
--response-path data.answer
```

Per-case execution failures are scored as failed cases instead of aborting the whole run.

## Run APIs

```text
POST /v1/evaluate
GET  /v1/runs
GET  /v1/runs/{run_id}
```

Run detail includes the evaluated answer, score breakdown, latency, HTTP status, and execution error for every case.

## GitHub quality gate

AgentGate exits non-zero when configured thresholds fail, making it suitable for required CI checks.

```yaml
- name: AgentGate quality gate
  uses: ./packages/action
  with:
    dataset: examples/customer-support/evals.live.jsonl
    evaluator_url: http://localhost:8000
    agent_url: http://localhost:8090
    response_path: data.answer
```

## Roadmap

- [x] Evaluation core
- [x] Local heuristic judge
- [x] Optional LLM judge
- [x] CLI quality gate
- [x] Dashboard shell
- [x] Persistent local run ingestion
- [x] Live HTTP agent execution
- [x] Per-case HTTP/latency capture
- [ ] Baseline vs candidate regression comparison
- [ ] Supabase hosted persistence adapter
- [ ] Tool-call accuracy scoring
- [ ] GitHub PR comment summaries
- [ ] Human review queue
- [ ] MCP tool evaluation
- [ ] Public hosted demo

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for milestone detail.

## Repository goals

AgentGate is intentionally built as a portfolio-grade open-source engineering project rather than a UI demo. The repository emphasizes testability, developer tooling, CI, evaluation infrastructure, observability concepts, and an architecture that can evolve into a hosted reliability platform.

## License

MIT © 2026 Mohammed Al-Obaido
