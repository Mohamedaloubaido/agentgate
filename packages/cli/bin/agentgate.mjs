#!/usr/bin/env node

import { readFile } from 'node:fs/promises';
import process from 'node:process';

const args = process.argv.slice(2);
const command = args[0];

function valueAfter(flag, fallback) {
  const index = args.indexOf(flag);
  return index >= 0 && args[index + 1] ? args[index + 1] : fallback;
}

function help() {
  console.log(`AgentGate CLI v0.2.0

Usage:
  agentgate eval --dataset <path> [--url http://localhost:8000]

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

  if (!dataset) {
    throw new Error('Missing --dataset <path>');
  }

  const cases = await readJsonl(dataset);
  if (cases.length === 0) {
    throw new Error('Dataset contains no evaluation cases');
  }

  const response = await fetch(`${url.replace(/\/$/, '')}/v1/evaluate`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      project: 'agentgate-cli',
      thresholds: { task_success: 0.8, groundedness: 0.8 },
      cases,
    }),
  });

  if (!response.ok) {
    throw new Error(`Evaluator returned HTTP ${response.status}: ${await response.text()}`);
  }

  const result = await response.json();
  const metrics = result.metrics;

  console.log(`\nAgentGate quality gate · ${result.run_id}`);
  console.log('────────────────────────────────');
  console.log(`Cases            ${String(result.cases.length).padStart(8)}`);
  console.log(`Task success     ${(metrics.task_success * 100).toFixed(1).padStart(7)}%`);
  console.log(`Groundedness     ${(metrics.groundedness * 100).toFixed(1).padStart(7)}%`);
  console.log(`Average score    ${(metrics.average_score * 100).toFixed(1).padStart(7)}%`);
  console.log('────────────────────────────────');
  console.log(result.gate_passed ? '✓ QUALITY GATE PASSED' : '✗ QUALITY GATE FAILED');

  if (!result.gate_passed) {
    for (const failure of result.failures) {
      console.error(`  - ${failure}`);
    }
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
