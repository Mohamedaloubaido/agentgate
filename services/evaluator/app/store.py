import json
import sqlite3
from pathlib import Path
from threading import Lock

from .models import CaseScore, EvaluationResponse, RunDetail, RunSummary


class RunStore:
    """SQLite-backed local run store.

    The schema deliberately keeps summary columns queryable while retaining the
    scored case payload for trace-like drilldown. New columns are migrated in
    place so existing v0.2 databases continue to work.
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

    @staticmethod
    def _columns(connection: sqlite3.Connection) -> set[str]:
        return {row['name'] for row in connection.execute('pragma table_info(eval_runs)').fetchall()}

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
                    created_at text not null,
                    source text not null default 'dataset',
                    cases_json text not null default '[]'
                )
                """
            )
            columns = self._columns(connection)
            if 'source' not in columns:
                connection.execute("alter table eval_runs add column source text not null default 'dataset'")
            if 'cases_json' not in columns:
                connection.execute("alter table eval_runs add column cases_json text not null default '[]'")
            connection.execute(
                'create index if not exists eval_runs_created_idx on eval_runs(created_at desc)'
            )

    def save(self, response: EvaluationResponse, judge_mode: str) -> None:
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                insert into eval_runs (
                    id, project, gate_passed, task_success, groundedness,
                    average_score, average_latency_ms, total_cost_usd,
                    failures_json, case_count, judge_mode, created_at,
                    source, cases_json
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    response.source,
                    json.dumps([case.model_dump() for case in response.cases], ensure_ascii=False),
                ),
            )

    def list(self, limit: int = 20) -> list[RunSummary]:
        safe_limit = max(1, min(limit, 100))
        with self._connect() as connection:
            rows = connection.execute(
                'select * from eval_runs order by created_at desc limit ?',
                (safe_limit,),
            ).fetchall()
        return [self._to_summary(row) for row in rows]

    def get(self, run_id: str) -> RunDetail | None:
        with self._connect() as connection:
            row = connection.execute(
                'select * from eval_runs where id = ?',
                (run_id,),
            ).fetchone()
        if not row:
            return None
        summary = self._to_summary(row)
        raw_cases = json.loads(row['cases_json']) if 'cases_json' in row.keys() else []
        return RunDetail(
            **summary.model_dump(),
            cases=[CaseScore.model_validate(item) for item in raw_cases],
        )

    @staticmethod
    def _to_summary(row: sqlite3.Row) -> RunSummary:
        keys = set(row.keys())
        return RunSummary(
            id=row['id'],
            project=row['project'],
            source=row['source'] if 'source' in keys else 'dataset',
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
