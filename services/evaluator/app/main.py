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
    RunDetail,
    RunSummary,
)
from .runner import execute_agent
from .scoring import score_case
from .store import RunStore

VERSION = '0.3.0'

app = FastAPI(
    title='AgentGate Evaluator',
    version=VERSION,
    description='Evaluation, agent execution, persistence, and quality-gate API for AI agents.',
)

store = RunStore(os.getenv('AGENTGATE_DB_PATH', '.agentgate/agentgate.db'))


@app.get('/health')
def health() -> dict[str, str]:
    return {'status': 'ok', 'service': 'agentgate-evaluator', 'version': VERSION}


@app.get('/v1/runs', response_model=list[RunSummary])
def list_runs(limit: int = Query(default=20, ge=1, le=100)) -> list[RunSummary]:
    return store.list(limit)


@app.get('/v1/runs/{run_id}', response_model=RunDetail)
def get_run(run_id: str) -> RunDetail:
    run = store.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail='Run not found')
    return run


@app.post('/v1/evaluate', response_model=EvaluationResponse)
def evaluate(request: EvaluationRequest) -> EvaluationResponse:
    case_scores: list[CaseScore] = []
    observed_latencies: list[int] = []

    for case in request.cases:
        actual = case.actual
        latency_ms = case.latency_ms
        status_code: int | None = None
        execution_error: str | None = None

        if request.target is not None:
            execution = execute_agent(request.target, case.id, case.input)
            actual = execution.actual
            latency_ms = execution.latency_ms
            status_code = execution.status_code
            execution_error = execution.error

        if latency_ms is not None:
            observed_latencies.append(latency_ms)

        if execution_error or actual is None:
            case_scores.append(
                CaseScore(
                    id=case.id,
                    correctness=0.0,
                    groundedness=0.0,
                    required_terms=0.0,
                    score=0.0,
                    passed=False,
                    reason=execution_error or 'No candidate answer was available for evaluation.',
                    actual=actual,
                    latency_ms=latency_ms,
                    status_code=status_code,
                    execution_error=execution_error,
                )
            )
            continue

        try:
            raw = (
                llm_judge(case.input, case.expected, actual, case.required_terms)
                if request.judge_mode == 'llm'
                else score_case(case.expected, actual, case.required_terms)
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
                actual=actual,
                latency_ms=latency_ms,
                status_code=status_code,
            )
        )

    total = len(case_scores)
    task_success = sum(1 for case in case_scores if case.passed) / total
    groundedness = sum(case.groundedness for case in case_scores) / total
    average_score = sum(case.score for case in case_scores) / total

    average_latency_ms = (
        sum(observed_latencies) / len(observed_latencies) if observed_latencies else None
    )
    total_cost_usd = sum(case.cost_usd or 0 for case in request.cases)

    failures: list[str] = []
    execution_failures = sum(1 for case in case_scores if case.execution_error)
    if execution_failures:
        failures.append(f'agent_execution_errors {execution_failures}/{total}')
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
        source='endpoint' if request.target is not None else 'dataset',
        gate_passed=not failures,
        metrics=AggregateMetrics(
            task_success=round(task_success, 4),
            groundedness=round(groundedness, 4),
            average_score=round(average_score, 4),
            average_latency_ms=(
                round(average_latency_ms, 2) if average_latency_ms is not None else None
            ),
            total_cost_usd=round(total_cost_usd, 6),
        ),
        cases=case_scores,
        failures=failures,
    )
    store.save(response, request.judge_mode)
    return response
