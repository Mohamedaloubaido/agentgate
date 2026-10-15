import { MetricCard } from '../components/metric-card';

const runs = [
  { id: 'run_01842', branch: 'feat/refund-policy', score: '94.2%', delta: '+3.1%', status: 'Passed' },
  { id: 'run_01841', branch: 'main', score: '91.1%', delta: 'baseline', status: 'Passed' },
  { id: 'run_01840', branch: 'fix/tool-routing', score: '82.7%', delta: '-8.4%', status: 'Failed' },
];

const trace = [
  ['00ms', 'Agent', 'triage request'],
  ['128ms', 'Tool', 'search_customer(customer_id)'],
  ['431ms', 'Handoff', 'billing-agent'],
  ['692ms', 'Tool', 'get_invoice(invoice_id)'],
  ['1.24s', 'Model', 'final answer'],
];

export default function Home() {
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
        <div className="sidebar-footer">v0.1 alpha<br/><span>Open source</span></div>
      </aside>

      <section className="content">
        <header className="topbar">
          <div>
            <div className="eyebrow">PROJECT / SUPPORT-AGENT</div>
            <h1>Reliability overview</h1>
          </div>
          <button className="primary-button">Run evaluation</button>
        </header>

        <section className="gate-banner">
          <div>
            <span className="status-dot" />
            <strong>Quality gate passed</strong>
            <span>Candidate beats baseline across 4 of 5 tracked metrics.</span>
          </div>
          <code>feat/refund-policy</code>
        </section>

        <section className="metrics-grid" id="overview">
          <MetricCard label="Production score" value="94.2" detail="▲ 3.1% vs baseline" status="positive" />
          <MetricCard label="Task success" value="94.8%" detail="threshold 90%" status="positive" />
          <MetricCard label="P95 latency" value="2.31s" detail="limit 3.00s" status="neutral" />
          <MetricCard label="Avg. cost" value="$0.018" detail="▼ 12.4% per run" status="positive" />
        </section>

        <section className="two-column">
          <article className="panel" id="runs">
            <div className="panel-header">
              <div><div className="eyebrow">REGRESSION</div><h2>Recent evaluation runs</h2></div>
              <button className="text-button">View all</button>
            </div>
            <div className="run-list">
              {runs.map((run) => (
                <div className="run-row" key={run.id}>
                  <div><strong>{run.branch}</strong><span>{run.id}</span></div>
                  <div className="run-score"><strong>{run.score}</strong><span>{run.delta}</span></div>
                  <span className={`pill ${run.status === 'Failed' ? 'pill-failed' : 'pill-passed'}`}>{run.status}</span>
                </div>
              ))}
            </div>
          </article>

          <article className="panel" id="traces">
            <div className="panel-header">
              <div><div className="eyebrow">TRACE REPLAY</div><h2>Latest execution</h2></div>
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
          <div className="panel-header"><div><div className="eyebrow">QUALITY PROFILE</div><h2>Candidate vs baseline</h2></div><code>run_01842</code></div>
          <div className="score-bars">
            {[
              ['Correctness', 96], ['Groundedness', 92], ['Tool accuracy', 98], ['Safety', 100]
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
