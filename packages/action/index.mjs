import { spawnSync } from 'node:child_process';
import { resolve } from 'node:path';
import process from 'node:process';

const dataset = process.env.INPUT_DATASET;
const evaluatorUrl = process.env.INPUT_EVALUATOR_URL || 'http://localhost:8000';
const agentUrl = process.env.INPUT_AGENT_URL;
const responsePath = process.env.INPUT_RESPONSE_PATH;
const inputField = process.env.INPUT_INPUT_FIELD || 'input';
const timeoutMs = process.env.INPUT_TIMEOUT_MS || '10000';
const actionPath = process.env.GITHUB_ACTION_PATH || resolve('packages/action');
const cliPath = resolve(actionPath, '..', 'cli', 'bin', 'agentgate.mjs');

if (!dataset) {
  console.error('AgentGate: input "dataset" is required.');
  process.exit(1);
}

const cliArgs = [cliPath, 'eval', '--dataset', dataset, '--url', evaluatorUrl];
if (agentUrl) cliArgs.push('--agent-url', agentUrl);
if (responsePath) cliArgs.push('--response-path', responsePath);
if (inputField) cliArgs.push('--input-field', inputField);
if (timeoutMs) cliArgs.push('--timeout-ms', timeoutMs);

const result = spawnSync(process.execPath, cliArgs, { stdio: 'inherit' });
process.exit(result.status ?? 1);
