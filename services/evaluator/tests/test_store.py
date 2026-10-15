import sys
import tempfile
import unittest
from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVICE_ROOT))

from app.models import AggregateMetrics, CaseScore, EvaluationResponse  # noqa: E402
from app.store import RunStore  # noqa: E402


class RunStoreTests(unittest.TestCase):
    def test_round_trip_run_summary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = RunStore(str(Path(directory) / 'runs.db'))
            response = EvaluationResponse(
                run_id='run_test123',
                created_at='2026-10-15T12:00:00+00:00',
                project='support-agent',
                gate_passed=True,
                metrics=AggregateMetrics(
                    task_success=1.0,
                    groundedness=0.95,
                    average_score=0.91,
                    average_latency_ms=250.0,
                    total_cost_usd=0.012,
                ),
                cases=[
                    CaseScore(
                        id='case-1',
                        correctness=0.9,
                        groundedness=0.95,
                        required_terms=1.0,
                        score=0.91,
                        passed=True,
                        reason='ok',
                    )
                ],
                failures=[],
            )

            store.save(response, 'heuristic')
            runs = store.list()

            self.assertEqual(len(runs), 1)
            self.assertEqual(runs[0].id, 'run_test123')
            self.assertTrue(runs[0].gate_passed)
            self.assertEqual(runs[0].case_count, 1)
            self.assertEqual(store.get('run_test123').project, 'support-agent')


if __name__ == '__main__':
    unittest.main()
