#!/usr/bin/env node

import { readFile } from 'node:fs/promises';
import process from 'node:process';

const args = process.argv.slice(2);
const command = args[0];

function valueAfter(flag, fallback) {
  const index = args.indexOf(flag);
  return index >= 0 && args[index + 1] ? args[index + 1] : fallback;
}

function numberAfter(flag, fallback) {
  const value = valueAfter(flag);
  if (value === undefined) return fallback;
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) throw new Error(`${flag} must be a number`);
  return parsed;
}

function help() {
  console.log(`AgentGate CLI v0.3.0

Usage:
  agentgate eval --dataset <path> [options]

Options:
  --url <url>             Evaluator URL (default: http://localhost:8000)
  --project <name>        Project name (default: agentgate-cli)
  --agent-url <url>       Execute each dataset input against a live agent endpoint
  --response-path <path>  Dot path for the answer in JSON (example: data.answer)
  --input-field <name>    JSON field sent to the agent (default: input)
  --timeout-ms <ms>       Per-agent request timeout (default: 10000)
  --judge <mode>          heuristic or llm (default: heuristic)

Commands:
  eval      Evaluate a JSONL dataset and enforce the quality gate
  help      Show this help
`);
}

async function readJsonl(path) {
  const raw = await readFile(path, 'utf8');
  return raw
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line, index) => {
      try {
        return JSON.parse(line);
      } catch (error) {
        throw new Error(`Invalid JSON on ${path}:${index + 1}: ${error.message}`);
      }
    });
}

async function evaluate() {
  const dataset = valueAfter('--dataset');
  const url = valueAfter('--url', 'http://localhost:8000');
  const project = valueAfter('--project', 'agentgate-cli');
  const agentUrl = valueAfter('--agent-url');
  const responsePath = valueAfter('--response-path');
  const inputField = valueAfter('--input-field', 'input');
  const timeoutMs = numberAfter('--timeout-ms', 10000);
  const judgeMode = valueAfter('--judge', 'heuristic');

  if (!dataset) throw new Error('Missing --dataset <path>');
  if (!['heuristic', 'llm'].includes(judgeMode)) {
    throw new Error('--judge must be "heuristic" or "llm"');
  }

  const cases = await readJsonl(dataset);
  if (cases.length === 0) throw new Error('Dataset contains no evaluation cases');

  const payload = {
    project,
    judge_mode: judgeMode,
    thresholds: { task_success: 0.8, groundedness: 0.8 },
    cases,
  };

  if (agentUrl) {
    payload.target = {
      url: agentUrl,
      input_field: inputField,
      timeout_ms: timeoutMs,
      ...(responsePath ? { response_path: responsePath } : {}),
    };
  }

  const response = await fetch(`${url.replace(/\/$/, '')}/v1/evaluate`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Evaluator returned HTTP ${response.status}: ${await response.text()}`);
  }

  const result = await response.json();
  const metrics = result.metrics;

  console.log(`\nAgentGate quality gate · ${result.run_id}`);
  console.log('────────────────────────────────');
  console.log(`Source           ${String(result.source).padStart(8)}`);
  console.log(`Cases            ${String(result.cases.length).padStart(8)}`);
  console.log(`Task success     ${(metrics.task_success * 100).toFixed(1).padStart(7)}%`);
  console.log(`Groundedness     ${(metrics.groundedness * 100).toFixed(1).padStart(7)}%`);
  console.log(`Average score    ${(metrics.average_score * 100).toFixed(1).padStart(7)}%`);
  if (metrics.average_latency_ms !== null) {
    console.log(`Avg latency      ${`${metrics.average_latency_ms.toFixed(0)}ms`.padStart(8)}`);
  }
  console.log('────────────────────────────────');
  console.log(result.gate_passed ? '✓ QUALITY GATE PASSED' : '✗ QUALITY GATE FAILED');

  const executionErrors = result.cases.filter((item) => item.execution_error);
  for (const item of executionErrors.slice(0, 5)) {
    console.error(`  ${item.id}: ${item.execution_error}`);
  }

  if (!result.gate_passed) {
    for (const failure of result.failures) console.error(`  - ${failure}`);
    process.exitCode = 1;
  }
}

try {
  if (!command || command === 'help' || command === '--help' || command === '-h') {
    help();
  } else if (command === 'eval') {
    await evaluate();
  } else {
    throw new Error(`Unknown command: ${command}`);
  }
} catch (error) {
  console.error(`AgentGate: ${error.message}`);
  process.exitCode = 1;
}
