import { MetricCard } from '../components/metric-card';

type RunSummary = {
  id: string;
  project: string;
  source: string;
  gate_passed: boolean;
  task_success: number;
  groundedness: number;
  average_score: number;
  average_latency_ms: number | null;
  total_cost_usd: number;
  failures: string[];
  case_count: number;
  judge_mode: string;
  created_at: string;
};

const demoRuns: RunSummary[] = [
  {
    id: 'run_demo1842',
    project: 'support-agent',
    source: 'endpoint',
    gate_passed: true,
    task_success: 0.948,
    groundedness: 0.92,
    average_score: 0.942,
    average_latency_ms: 2310,
    total_cost_usd: 0.018,
    failures: [],
    case_count: 50,
    judge_mode: 'heuristic',
    created_at: '2026-10-15T12:00:00Z',
  },
  {
    id: 'run_demo1841',
    project: 'support-agent',
    source: 'endpoint',
    gate_passed: true,
    task_success: 0.911,
    groundedness: 0.89,
    average_score: 0.911,
    average_latency_ms: 2420,
    total_cost_usd: 0.021,
    failures: [],
    case_count: 50,
    judge_mode: 'heuristic',
    created_at: '2026-10-15T11:30:00Z',
  },
  {
    id: 'run_demo1840',
    project: 'support-agent',
    source: 'endpoint',
    gate_passed: false,
    task_success: 0.827,
    groundedness: 0.81,
    average_score: 0.827,
    average_latency_ms: 2180,
    total_cost_usd: 0.019,
    failures: ['task_success 0.827 < 0.900'],
    case_count: 50,
    judge_mode: 'heuristic',
    created_at: '2026-10-15T11:00:00Z',
  },
];

const trace = [
  ['00ms', 'Agent', 'triage request'],
  ['128ms', 'Tool', 'search_customer(customer_id)'],
  ['431ms', 'Handoff', 'billing-agent'],
  ['692ms', 'Tool', 'get_invoice(invoice_id)'],
  ['1.24s', 'Model', 'final answer'],
];

async function loadRuns(): Promise<{ runs: RunSummary[]; live: boolean }> {
  const evaluatorUrl = process.env.AGENTGATE_API_URL ?? 'http://localhost:8000';

  try {
    const response = await fetch(`${evaluatorUrl.replace(/\/$/, '')}/v1/runs?limit=3`, {
      cache: 'no-store',
      signal: AbortSignal.timeout(1200),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const runs = (await response.json()) as RunSummary[];
    if (runs.length > 0) return { runs, live: true };
  } catch {
    // The dashboard remains explorable before the evaluator is started.
  }

  return { runs: demoRuns, live: false };
}

function percent(value: number) {
  return `${(value * 100).toFixed(1)}%`;
}

function money(value: number) {
  return `$${value.toFixed(3)}`;
}

export const dynamic = 'force-dynamic';

export default async function Home() {
  const { runs, live } = await loadRuns();
  const latest = runs[0];
  const baseline = runs[1] ?? latest;
  const scoreDelta = (latest.average_score - baseline.average_score) * 100;

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark">AG</span><span>AgentGate</span></div>
        <nav className="nav">
          <a className="nav-item active" href="#overview">Overview</a>
          <a className="nav-item" href="#runs">Runs</a>
          <a className="nav-item" href="#traces">Traces</a>
          <a className="nav-item" href="#datasets">Datasets</a>
          <a className="nav-item" href="#settings">Settings</a>
        </nav>
        <div className="sidebar-footer">v0.3 alpha<br/><span>{live ? 'Live evaluator' : 'Demo fallback'}</span></div>
      </aside>

      <section className="content">
        <header className="topbar">
          <div>
            <div className="eyebrow">PROJECT / {latest.project.toUpperCase()}</div>
            <h1>Reliability overview</h1>
          </div>
          <div className={`data-source ${live ? 'data-source-live' : ''}`}>
            <span className="status-dot" /> {live ? 'Live runs' : 'Demo data'}
          </div>
        </header>

        <section className={`gate-banner ${latest.gate_passed ? '' : 'gate-banner-failed'}`}>
          <div>
            <span className="status-dot" />
            <strong>Quality gate {latest.gate_passed ? 'passed' : 'failed'}</strong>
            <span>{latest.case_count} cases · {latest.judge_mode} judge · {latest.source}</span>
          </div>
          <code>{latest.id}</code>
        </section>

        <section className="metrics-grid" id="overview">
          <MetricCard label="Production score" value={percent(latest.average_score)} detail={`${scoreDelta >= 0 ? '▲' : '▼'} ${Math.abs(scoreDelta).toFixed(1)} pts vs previous`} status={scoreDelta >= 0 ? 'positive' : 'warning'} />
          <MetricCard label="Task success" value={percent(latest.task_success)} detail="quality-gate metric" status={latest.gate_passed ? 'positive' : 'warning'} />
          <MetricCard label="Groundedness" value={percent(latest.groundedness)} detail="required facts preserved" status="neutral" />
          <MetricCard label="Recorded cost" value={money(latest.total_cost_usd)} detail={latest.average_latency_ms ? `${latest.average_latency_ms.toFixed(0)}ms avg latency` : 'latency not recorded'} status="neutral" />
        </section>

        <section className="two-column">
          <article className="panel" id="runs">
            <div className="panel-header">
              <div><div className="eyebrow">PERSISTED HISTORY</div><h2>Recent evaluation runs</h2></div>
              <span className="trace-total">{live ? 'SQLite API' : 'fallback'}</span>
            </div>
            <div className="run-list">
              {runs.map((run) => (
                <div className="run-row" key={run.id}>
                  <div><strong>{run.project}</strong><span>{run.id} · {run.source}</span></div>
                  <div className="run-score"><strong>{percent(run.average_score)}</strong><span>{run.case_count} cases</span></div>
                  <span className={`pill ${run.gate_passed ? 'pill-passed' : 'pill-failed'}`}>{run.gate_passed ? 'Passed' : 'Failed'}</span>
                </div>
              ))}
            </div>
          </article>

          <article className="panel" id="traces">
            <div className="panel-header">
              <div><div className="eyebrow">TRACE REPLAY</div><h2>Execution preview</h2></div>
              <span className="trace-total">1.24s</span>
            </div>
            <div className="trace-list">
              {trace.map(([time, type, label], index) => (
                <div className="trace-row" key={`${time}-${label}`}>
                  <div className="trace-line">{index < trace.length - 1 && <span />}</div>
                  <code>{time}</code>
                  <span className="trace-type">{type}</span>
                  <strong>{label}</strong>
                </div>
              ))}
            </div>
          </article>
        </section>

        <section className="panel score-panel">
          <div className="panel-header"><div><div className="eyebrow">QUALITY PROFILE</div><h2>Latest persisted run</h2></div><code>{latest.id}</code></div>
          <div className="score-bars">
            {[
              ['Average score', Math.round(latest.average_score * 100)],
              ['Task success', Math.round(latest.task_success * 100)],
              ['Groundedness', Math.round(latest.groundedness * 100)],
            ].map(([label, value]) => (
              <div className="score-row" key={String(label)}>
                <span>{label}</span>
                <div className="bar"><i style={{ width: `${value}%` }} /></div>
                <strong>{value}%</strong>
              </div>
            ))}
          </div>
        </section>
      </section>
    </main>
  );
}
