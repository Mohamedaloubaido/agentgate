from typing import Literal

from pydantic import BaseModel, Field


class EvaluationCase(BaseModel):
    id: str = Field(min_length=1, max_length=200)
    input: str
    expected: str
    actual: str
    required_terms: list[str] = Field(default_factory=list)
    latency_ms: int | None = Field(default=None, ge=0)
    cost_usd: float | None = Field(default=None, ge=0)


class Thresholds(BaseModel):
    task_success: float = Field(default=0.80, ge=0, le=1)
    groundedness: float = Field(default=0.80, ge=0, le=1)
    max_latency_ms: int | None = Field(default=None, ge=0)
    max_cost_usd: float | None = Field(default=None, ge=0)


class EvaluationRequest(BaseModel):
    project: str = Field(min_length=1, max_length=200)
    cases: list[EvaluationCase] = Field(min_length=1)
    thresholds: Thresholds = Field(default_factory=Thresholds)
    judge_mode: Literal["heuristic", "llm"] = "heuristic"


class CaseScore(BaseModel):
    id: str
    correctness: float
    groundedness: float
    required_terms: float
    score: float
    passed: bool
    reason: str


class AggregateMetrics(BaseModel):
    task_success: float
    groundedness: float
    average_score: float
    average_latency_ms: float | None
    total_cost_usd: float


class EvaluationResponse(BaseModel):
    project: str
    gate_passed: bool
    metrics: AggregateMetrics
    cases: list[CaseScore]
    failures: list[str]
