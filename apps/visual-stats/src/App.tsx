import { Activity, Cpu, Database, Gauge } from "lucide-react";

const metrics = [
  { label: "IPC Delta", value: "+10.4%", icon: Gauge },
  { label: "MPKI", value: "-15.8%", icon: Activity },
  { label: "AMAL", value: "-20.2%", icon: Cpu },
  { label: "Trace Rows", value: "1.2M", icon: Database },
];

export function App() {
  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Visual-Stats</p>
          <h1>IntelliCore Telemetry</h1>
        </div>
        <button type="button" aria-label="Refresh metrics">
          Refresh
        </button>
      </header>

      <section className="metric-grid" aria-label="Baseline comparison metrics">
        {metrics.map((metric) => {
          const Icon = metric.icon;
          return (
            <article className="metric" key={metric.label}>
              <Icon aria-hidden="true" size={20} />
              <span>{metric.label}</span>
              <strong>{metric.value}</strong>
            </article>
          );
        })}
      </section>

      <section className="panel">
        <div>
          <h2>Cache Residency Heatmap</h2>
          <p>Placeholder grid wired for Sprint 1 telemetry ingestion.</p>
        </div>
        <div className="heatmap" aria-label="Cache residency heatmap placeholder">
          {Array.from({ length: 64 }).map((_, index) => (
            <span key={index} style={{ opacity: 0.25 + (index % 8) * 0.09 }} />
          ))}
        </div>
      </section>
    </main>
  );
}
