import os
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query

from .judge import llm_judge
from .models import (
    AggregateMetrics,
    CaseScore,
    EvaluationRequest,
    EvaluationResponse,
    RunSummary,
)
from .scoring import score_case
from .store import RunStore

app = FastAPI(
    title='AgentGate Evaluator',
    version='0.2.0',
    description='Evaluation, persistence, and quality-gate API for AI agents.',
)

store = RunStore(os.getenv('AGENTGATE_DB_PATH', '.agentgate/agentgate.db'))


@app.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok', 'service': 'agentgate-evaluator', 'version': '0.2.0'}


@app.get('/v1/runs', response_model=list[RunSummary])
def list_runs(limit: int = Query(default=20, ge=1, le=100)) -> list[RunSummary]:
    return store.list(limit)


@app.get('/v1/runs/{run_id}', response_model=RunSummary)
def get_run(run_id: str) -> RunSummary:
    run = store.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail='Run not found')
    return run


@app.post('/v1/evaluate', response_model=EvaluationResponse)
def evaluate(request: EvaluationRequest) -> EvaluationResponse:
    case_scores: list[CaseScore] = []

    for case in request.cases:
        try:
            raw = (
                llm_judge(case.input, case.expected, case.actual, case.required_terms)
                if request.judge_mode == 'llm'
                else score_case(case.expected, case.actual, case.required_terms)
            )
        except RuntimeError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f'Judge provider failed: {exc}') from exc

        case_scores.append(
            CaseScore(
                id=case.id,
                correctness=raw.correctness,
                groundedness=raw.groundedness,
                required_terms=raw.required_terms,
                score=raw.score,
                passed=raw.passed,
                reason=raw.reason,
            )
        )

    total = len(case_scores)
    task_success = sum(1 for case in case_scores if case.passed) / total
    groundedness = sum(case.groundedness for case in case_scores) / total
    average_score = sum(case.score for case in case_scores) / total

    latencies = [case.latency_ms for case in request.cases if case.latency_ms is not None]
    average_latency_ms = sum(latencies) / len(latencies) if latencies else None
    total_cost_usd = sum(case.cost_usd or 0 for case in request.cases)

    failures: list[str] = []
    if task_success < request.thresholds.task_success:
        failures.append(
            f'task_success {task_success:.3f} < {request.thresholds.task_success:.3f}'
        )
    if groundedness < request.thresholds.groundedness:
        failures.append(
            f'groundedness {groundedness:.3f} < {request.thresholds.groundedness:.3f}'
        )
    if (
        request.thresholds.max_latency_ms is not None
        and average_latency_ms is not None
        and average_latency_ms > request.thresholds.max_latency_ms
    ):
        failures.append(
            f'average_latency_ms {average_latency_ms:.0f} > {request.thresholds.max_latency_ms}'
        )
    if (
        request.thresholds.max_cost_usd is not None
        and total_cost_usd > request.thresholds.max_cost_usd
    ):
        failures.append(
            f'total_cost_usd {total_cost_usd:.4f} > {request.thresholds.max_cost_usd:.4f}'
        )

    response = EvaluationResponse(
        run_id=f'run_{uuid4().hex[:12]}',
        created_at=datetime.now(timezone.utc).isoformat(),
        project=request.project,
        gate_passed=not failures,
        metrics=AggregateMetrics(
            task_success=round(task_success, 4),
            groundedness=round(groundedness, 4),
            average_score=round(average_score, 4),
            average_latency_ms=(round(average_latency_ms, 2) if average_latency_ms is not None else None),
            total_cost_usd=round(total_cost_usd, 6),
        ),
        cases=case_scores,
        failures=failures,
    )
    store.save(response, request.judge_mode)
    return response
