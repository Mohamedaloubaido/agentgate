from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class EvaluationCase(BaseModel):
    id: str = Field(min_length=1, max_length=200)
    input: str
    expected: str
    actual: str | None = None
    required_terms: list[str] = Field(default_factory=list)
    latency_ms: int | None = Field(default=None, ge=0)
    cost_usd: float | None = Field(default=None, ge=0)


class AgentTarget(BaseModel):
    url: str = Field(min_length=1)
    method: Literal['POST'] = 'POST'
    input_field: str = Field(default='input', min_length=1, max_length=100)
    response_path: str | None = Field(default=None, max_length=300)
    timeout_ms: int = Field(default=10_000, ge=100, le=120_000)
    headers: dict[str, str] = Field(default_factory=dict)


class Thresholds(BaseModel):
    task_success: float = Field(default=0.80, ge=0, le=1)
    groundedness: float = Field(default=0.80, ge=0, le=1)
    max_latency_ms: int | None = Field(default=None, ge=0)
    max_cost_usd: float | None = Field(default=None, ge=0)


class EvaluationRequest(BaseModel):
    project: str = Field(min_length=1, max_length=200)
    cases: list[EvaluationCase] = Field(min_length=1)
    thresholds: Thresholds = Field(default_factory=Thresholds)
    judge_mode: Literal['heuristic', 'llm'] = 'heuristic'
    target: AgentTarget | None = None

    @model_validator(mode='after')
    def require_actual_or_target(self) -> 'EvaluationRequest':
        if self.target is None:
            missing = [case.id for case in self.cases if case.actual is None]
            if missing:
                raise ValueError(
                    'Cases without `actual` require a `target` agent endpoint. '
                    f'Missing actual for: {", ".join(missing[:5])}'
                )
        return self


class CaseScore(BaseModel):
    id: str
    correctness: float
    groundedness: float
    required_terms: float
    score: float
    passed: bool
    reason: str
    actual: str | None = None
    latency_ms: int | None = None
    status_code: int | None = None
    execution_error: str | None = None


class AggregateMetrics(BaseModel):
    task_success: float
    groundedness: float
    average_score: float
    average_latency_ms: float | None
    total_cost_usd: float


class EvaluationResponse(BaseModel):
    run_id: str
    created_at: str
    project: str
    source: Literal['dataset', 'endpoint'] = 'dataset'
    gate_passed: bool
    metrics: AggregateMetrics
    cases: list[CaseScore]
    failures: list[str]


class RunSummary(BaseModel):
    id: str
    project: str
    source: str = 'dataset'
    gate_passed: bool
    task_success: float
    groundedness: float
    average_score: float
    average_latency_ms: float | None
    total_cost_usd: float
    failures: list[str]
    case_count: int
    judge_mode: str
    created_at: str


class RunDetail(RunSummary):
    cases: list[CaseScore] = Field(default_factory=list)
