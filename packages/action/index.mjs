import { spawnSync } from 'node:child_process';
import { resolve } from 'node:path';
import process from 'node:process';

const dataset = process.env.INPUT_DATASET;
const evaluatorUrl = process.env.INPUT_EVALUATOR_URL || 'http://localhost:8000';
const actionPath = process.env.GITHUB_ACTION_PATH || resolve('packages/action');
const cliPath = resolve(actionPath, '..', 'cli', 'bin', 'agentgate.mjs');

if (!dataset) {
  console.error('AgentGate: input "dataset" is required.');
  process.exit(1);
}

const result = spawnSync(
  process.execPath,
  [cliPath, 'eval', '--dataset', dataset, '--url', evaluatorUrl],
  { stdio: 'inherit' },
);

process.exit(result.status ?? 1);
