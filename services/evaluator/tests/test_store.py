import sys
import tempfile
import unittest
from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVICE_ROOT))

from app.models import AggregateMetrics, CaseScore, EvaluationResponse  # noqa: E402
from app.store import RunStore  # noqa: E402


class RunStoreTests(unittest.TestCase):
    def test_round_trip_run_detail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = RunStore(str(Path(directory) / 'runs.db'))
            response = EvaluationResponse(
                run_id='run_test123',
                created_at='2026-10-15T12:00:00+00:00',
                project='support-agent',
                source='endpoint',
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
                        actual='A grounded answer.',
                        latency_ms=250,
                        status_code=200,
                    )
                ],
                failures=[],
            )

            store.save(response, 'heuristic')
            runs = store.list()
            detail = store.get('run_test123')

            self.assertEqual(len(runs), 1)
            self.assertEqual(runs[0].id, 'run_test123')
            self.assertEqual(runs[0].source, 'endpoint')
            self.assertTrue(runs[0].gate_passed)
            self.assertEqual(runs[0].case_count, 1)
            self.assertIsNotNone(detail)
            self.assertEqual(detail.project, 'support-agent')
            self.assertEqual(detail.cases[0].actual, 'A grounded answer.')
            self.assertEqual(detail.cases[0].status_code, 200)


if __name__ == '__main__':
    unittest.main()
