import json
import sqlite3
from pathlib import Path
from threading import Lock

from .models import EvaluationResponse, RunSummary


class RunStore:
    """Small SQLite-backed run store used by the local AgentGate evaluator.

    SQLite gives local development durable history without requiring a cloud
    account. The database contract mirrors the hosted persistence model closely
    enough that a Supabase adapter can replace it without changing the API.
    """

    def __init__(self, path: str) -> None:
        self.path = Path(path)
        if self.path.parent != Path('.'):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                create table if not exists eval_runs (
                    id text primary key,
                    project text not null,
                    gate_passed integer not null,
                    task_success real not null,
                    groundedness real not null,
                    average_score real not null,
                    average_latency_ms real,
                    total_cost_usd real not null,
                    failures_json text not null,
                    case_count integer not null,
                    judge_mode text not null,
                    created_at text not null
                )
                """
            )
            connection.execute(
                "create index if not exists eval_runs_created_idx on eval_runs(created_at desc)"
            )

    def save(self, response: EvaluationResponse, judge_mode: str) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                insert into eval_runs (
                    id, project, gate_passed, task_success, groundedness,
                    average_score, average_latency_ms, total_cost_usd,
                    failures_json, case_count, judge_mode, created_at
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    response.run_id,
                    response.project,
                    int(response.gate_passed),
                    response.metrics.task_success,
                    response.metrics.groundedness,
                    response.metrics.average_score,
                    response.metrics.average_latency_ms,
                    response.metrics.total_cost_usd,
                    json.dumps(response.failures),
                    len(response.cases),
                    judge_mode,
                    response.created_at,
                ),
            )

    def list(self, limit: int = 20) -> list[RunSummary]:
        safe_limit = max(1, min(limit, 100))
        with self._connect() as connection:
            rows = connection.execute(
                "select * from eval_runs order by created_at desc limit ?",
                (safe_limit,),
            ).fetchall()
        return [self._to_summary(row) for row in rows]

    def get(self, run_id: str) -> RunSummary | None:
        with self._connect() as connection:
            row = connection.execute(
                "select * from eval_runs where id = ?",
                (run_id,),
            ).fetchone()
        return self._to_summary(row) if row else None

    @staticmethod
    def _to_summary(row: sqlite3.Row) -> RunSummary:
        return RunSummary(
            id=row['id'],
            project=row['project'],
            gate_passed=bool(row['gate_passed']),
            task_success=row['task_success'],
            groundedness=row['groundedness'],
            average_score=row['average_score'],
            average_latency_ms=row['average_latency_ms'],
            total_cost_usd=row['total_cost_usd'],
            failures=json.loads(row['failures_json']),
            case_count=row['case_count'],
            judge_mode=row['judge_mode'],
            created_at=row['created_at'],
        )
