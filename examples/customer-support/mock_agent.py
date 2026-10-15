"""Tiny example agent endpoint for testing AgentGate live execution locally."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json


def answer(prompt: str) -> str:
    lowered = prompt.casefold()
    if 'refund' in lowered:
        return 'Refunds are limited to purchases made in the last 30 days.'
    if 'person' in lowered or 'human' in lowered:
        return 'I can connect you with a human support agent now.'
    if 'guarantee' in lowered or 'delivery' in lowered:
        return 'I cannot guarantee tomorrow delivery until I check the carrier status.'
    return 'I need more information before I can answer.'


class Handler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get('content-length', '0'))
        payload = json.loads(self.rfile.read(length) or b'{}')
        body = json.dumps({'data': {'answer': answer(str(payload.get('input', '')))}}).encode()
        self.send_response(200)
        self.send_header('content-type', 'application/json')
        self.send_header('content-length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args: object) -> None:
        return


if __name__ == '__main__':
    print('Mock agent listening on http://127.0.0.1:8090')
    ThreadingHTTPServer(('127.0.0.1', 8090), Handler).serve_forever()
