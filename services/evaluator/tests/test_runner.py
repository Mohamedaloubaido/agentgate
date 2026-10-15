import json
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SERVICE_ROOT))

from app.models import AgentTarget, EvaluationCase, EvaluationRequest  # noqa: E402
from app.runner import execute_agent  # noqa: E402


class _Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get('content-length', '0'))
        payload = json.loads(self.rfile.read(length) or b'{}')
        if payload.get('input') == 'explode':
            self.send_response(503)
            self.end_headers()
            return
        body = json.dumps({'data': {'answer': f"echo: {payload.get('input', '')}"}}).encode()
        self.send_response(200)
        self.send_header('content-type', 'application/json')
        self.send_header('content-length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args: object) -> None:
        return


class RunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), _Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def test_executes_agent_and_extracts_nested_answer(self) -> None:
        execution = execute_agent(
            AgentTarget(url=self.base_url, response_path='data.answer'),
            'case-1',
            'hello',
        )
        self.assertEqual(execution.actual, 'echo: hello')
        self.assertEqual(execution.status_code, 200)
        self.assertIsNone(execution.error)
        self.assertGreaterEqual(execution.latency_ms, 0)

    def test_http_error_becomes_case_execution_error(self) -> None:
        execution = execute_agent(
            AgentTarget(url=self.base_url, response_path='data.answer'),
            'case-2',
            'explode',
        )
        self.assertIsNone(execution.actual)
        self.assertEqual(execution.status_code, 503)
        self.assertIn('HTTP 503', execution.error or '')

    def test_cases_without_actual_require_target(self) -> None:
        with self.assertRaises(ValueError):
            EvaluationRequest(
                project='demo',
                cases=[EvaluationCase(id='case-1', input='hello', expected='echo: hello')],
            )

    def test_target_allows_dataset_without_actual(self) -> None:
        request = EvaluationRequest(
            project='demo',
            target=AgentTarget(url=self.base_url, response_path='data.answer'),
            cases=[EvaluationCase(id='case-1', input='hello', expected='echo: hello')],
        )
        self.assertEqual(request.target.url, self.base_url)


if __name__ == '__main__':
    unittest.main()
