# AgentGate

**Ship AI agents with confidence.**

AgentGate is an open-source reliability and CI platform for AI agents. It turns agent behavior into measurable tests so teams can detect regressions in answer quality, grounding, tool use, cost, and latency before merging or deploying changes.

> Status: **v0.2 alpha** — the first public foundation is intentionally small, testable, and extensible.

## Why AgentGate?

Traditional software has unit tests. AI agents need evaluation suites that understand non-deterministic output, tool calls, traces, and quality thresholds.

AgentGate is designed around a simple workflow:

```text
Prompt / Agent change
        ↓
Evaluation dataset
        ↓
Evaluator + optional LLM judge
        ↓
Quality metrics
        ↓
Quality gate
        ↓
Pass → merge     Fail → block
```

## v0.2 includes

- Evaluation API built with FastAPI.
- Deterministic heuristic scoring for local/offline testing.
- Optional OpenAI LLM-as-a-Judge provider.
- Dataset-driven evaluation cases using JSONL.
- Quality-gate thresholds for CI.
- CLI foundation: `agentgate eval`.
- Reusable GitHub Action wrapper.
- Next.js dashboard backed by persisted evaluator runs, with an offline demo fallback.
- Durable local SQLite run history and run lookup API.
- PostgreSQL/Supabase schema for projects, datasets, runs, cases, and traces.
- GitHub Actions CI for evaluator tests and CLI syntax checks.

## Architecture

```text
┌──────────────────────────────┐
│       Next.js Dashboard      │
│        React 19 / TS         │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│       FastAPI Evaluator      │
│ heuristic + LLM-as-a-Judge  │
└──────────────┬───────────────┘
               │
      ┌────────┴────────┐
      ▼                 ▼
SQLite local       Agent traces
Supabase hosted     + metrics

GitHub Actions ──► AgentGate CLI ──► Quality Gate
```

## Quick start

### 1. Run the evaluator

```bash
cd services/evaluator
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -e .
fastapi dev app/main.py
```

The API is available at `http://localhost:8000`.

### 2. Run the sample evaluation

From the repository root:

```bash
node packages/cli/bin/agentgate.mjs eval \
  --dataset examples/customer-support/evals.jsonl \
  --url http://localhost:8000
```

### 3. Run the web dashboard

```bash
npm install
npm run dev:web
```

Open `http://localhost:3000`.

## Example evaluation case

```json
{
  "id": "refund-window",
  "input": "Can I get a refund after 45 days?",
  "expected": "Refunds are only available within 30 days of purchase.",
  "actual": "Refunds are limited to purchases made in the last 30 days.",
  "required_terms": ["30 days"]
}
```

## API example

```bash
curl -X POST http://localhost:8000/v1/evaluate \
  -H "content-type: application/json" \
  -d '{
    "project": "support-agent",
    "thresholds": {"task_success": 0.8},
    "cases": [
      {
        "id": "refund-window",
        "input": "Can I get a refund after 45 days?",
        "expected": "Refunds are only available within 30 days of purchase.",
        "actual": "Refunds are limited to purchases made in the last 30 days.",
        "required_terms": ["30 days"]
      }
    ]
  }'
```

## Quality gate

AgentGate returns a non-zero CLI exit code when configured thresholds fail. That makes the evaluator usable as a required GitHub Actions check.

```yaml
- name: AgentGate quality gate
  uses: ./packages/action
  with:
    dataset: examples/customer-support/evals.jsonl
    evaluator_url: http://localhost:8000
```

## Roadmap

- [x] Evaluation core
- [x] Local heuristic judge
- [x] Optional LLM judge
- [x] CLI quality gate
- [x] Dashboard shell
- [x] Trace data model
- [x] Persistent local run ingestion
- [ ] Supabase hosted persistence adapter
- [ ] Prompt version comparison
- [ ] Tool-call accuracy scoring
- [ ] GitHub PR comment summaries
- [ ] Human review queue
- [ ] MCP tool evaluation
- [ ] Public hosted demo

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for milestone detail.

## Repository goals

AgentGate is intentionally built as a portfolio-grade open-source engineering project rather than a UI demo. The repository emphasizes testability, clear boundaries, CI, developer tooling, observability concepts, and an architecture that can evolve into a real hosted service.

## License

MIT © 2026 Mohammed Al-Obaido
