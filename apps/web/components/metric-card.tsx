type MetricCardProps = {
  label: string;
  value: string;
  detail: string;
  status?: 'positive' | 'neutral' | 'warning';
};

export function MetricCard({ label, value, detail, status = 'neutral' }: MetricCardProps) {
  return (
    <article className="metric-card">
      <div className="metric-label">{label}</div>
      <div className="metric-value">{value}</div>
      <div className={`metric-detail metric-detail-${status}`}>{detail}</div>
    </article>
  );
}
