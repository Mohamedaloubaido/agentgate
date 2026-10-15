import json
from dataclasses import dataclass
from time import perf_counter
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .models import AgentTarget


@dataclass(frozen=True)
class AgentExecution:
    actual: str | None
    latency_ms: int
    status_code: int | None
    error: str | None = None


def _extract_path(payload: Any, path: str) -> Any:
    current = payload
    for segment in path.split('.'):
        if isinstance(current, dict) and segment in current:
            current = current[segment]
            continue
        raise KeyError(f'Response path `{path}` was not found')
    return current


def _extract_answer(raw: bytes, content_type: str, response_path: str | None) -> str:
    text = raw.decode('utf-8', errors='replace').strip()
    should_parse_json = 'application/json' in content_type.casefold()

    if should_parse_json or response_path:
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            if response_path:
                raise ValueError('Agent response was not valid JSON') from exc
            return text

        if response_path:
            value = _extract_path(payload, response_path)
        elif isinstance(payload, dict):
            value = next(
                (
                    payload[key]
                    for key in ('output', 'answer', 'response', 'message', 'content', 'text')
                    if key in payload
                ),
                payload,
            )
        else:
            value = payload

        if isinstance(value, str):
            return value.strip()
        return json.dumps(value, ensure_ascii=False, separators=(',', ':'))

    return text


def execute_agent(target: AgentTarget, case_id: str, input_text: str) -> AgentExecution:
    body = json.dumps(
        {target.input_field: input_text, 'case_id': case_id},
        ensure_ascii=False,
    ).encode('utf-8')
    headers = {'content-type': 'application/json', 'accept': 'application/json, text/plain'}
    headers.update(target.headers)

    request = Request(target.url, data=body, headers=headers, method=target.method)
    started = perf_counter()

    try:
        with urlopen(request, timeout=target.timeout_ms / 1000) as response:
            raw = response.read()
            latency_ms = round((perf_counter() - started) * 1000)
            status_code = getattr(response, 'status', 200)
            content_type = response.headers.get('content-type', '')
            actual = _extract_answer(raw, content_type, target.response_path)
            if not actual:
                return AgentExecution(
                    actual=None,
                    latency_ms=latency_ms,
                    status_code=status_code,
                    error='Agent returned an empty response',
                )
            return AgentExecution(
                actual=actual,
                latency_ms=latency_ms,
                status_code=status_code,
            )
    except HTTPError as exc:
        latency_ms = round((perf_counter() - started) * 1000)
        return AgentExecution(
            actual=None,
            latency_ms=latency_ms,
            status_code=exc.code,
            error=f'Agent returned HTTP {exc.code}',
        )
    except (URLError, TimeoutError, OSError) as exc:
        latency_ms = round((perf_counter() - started) * 1000)
        reason = getattr(exc, 'reason', exc)
        return AgentExecution(
            actual=None,
            latency_ms=latency_ms,
            status_code=None,
            error=f'Agent request failed: {reason}',
        )
    except (ValueError, KeyError) as exc:
        latency_ms = round((perf_counter() - started) * 1000)
        return AgentExecution(
            actual=None,
            latency_ms=latency_ms,
            status_code=200,
            error=str(exc),
        )
