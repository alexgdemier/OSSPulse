import Link from "next/link";
import { notFound } from "next/navigation";

const apiBase = (process.env.OSSPULSE_API_URL ?? "http://127.0.0.1:8002/api/v1").replace(/\/$/, "");

type Finding = {
  code: string;
  category: string;
  title: string;
  description: string;
  severity: string;
  recommendation: string;
  source_url: string | null;
  evidence: Record<string, unknown>;
};

type Report = {
  report_id: string;
  analyzed_at: string;
  engine_version: string;
  health_score: number | null;
  coverage: number;
  classification: string;
  repository: { full_name: string; url: string; description: string | null; language: string | null; stars: number; forks: number };
  dimensions: Record<string, number | null>;
  findings: Finding[];
  insights: (Finding & { priority_score: number })[];
};

const labels: Record<string, string> = {
  maintenance: "Maintenance",
  community: "Community",
  development: "Development",
  documentation: "Documentation",
  sustainability: "Sustainability",
};

export default async function ReportPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  let response: Response;
  try {
    response = await fetch(`${apiBase}/reports/${encodeURIComponent(id)}`, { cache: "no-store" });
  } catch {
    return <main className="shell report-shell"><p className="error-banner">The report service is unavailable. Start or check the OSS Pulse API and try again.</p><Link href="/">← Back to OSS Pulse</Link></main>;
  }
  if (response.status === 404) notFound();
  if (!response.ok) return <main className="shell report-shell"><p className="error-banner">The report could not be loaded. Please try again.</p><Link href="/">← Back to OSS Pulse</Link></main>;
  const report: Report = await response.json();

  const analyzed = new Date(report.analyzed_at).toLocaleString("en", { dateStyle: "medium", timeStyle: "short", timeZone: "UTC", timeZoneName: "short" });
  return (
    <main className="shell report-shell">
      <nav className="nav"><Link className="brand" href="/"><span className="brand-mark">◉</span> OSS PULSE</Link><Link className="back-link" href="/">← Analyze another</Link></nav>
      <header className="report-heading">
        <div className="eyebrow"><span className="live-dot" /> REPOSITORY HEALTH REPORT</div>
        <h1><a href={report.repository.url} target="_blank" rel="noreferrer">{report.repository.full_name} ↗</a></h1>
        <p className="lead">{report.repository.description ?? "No repository description provided."}</p>
        <div className="repo-meta"><span>{report.repository.language ?? "Language unavailable"}</span><span>{report.repository.stars.toLocaleString()} stars</span><span>{report.repository.forks.toLocaleString()} forks</span></div>
      </header>
      <section className="report-grid">
        <article className="report-card main-score"><span className="section-label">HEALTH SCORE</span><div className="report-score">{report.health_score ?? "—"}<small>/100</small></div><span className="report-status">{report.classification}</span><div className="score-track"><i style={{ width: `${report.health_score ?? 0}%` }} /></div><p>{report.coverage}% data coverage · Engine {report.engine_version}</p></article>
        <article className="report-card dimension-card"><span className="section-label">HEALTH DIMENSIONS</span>{Object.entries(report.dimensions).map(([name, score]) => <div className="dimension" key={name}><div><span>{labels[name] ?? name}</span><b>{score === null ? "Not evaluated" : score}</b></div><div className="bar"><i className={score !== null && score >= 70 ? "green" : "amber"} style={{ width: `${score ?? 0}%` }} /></div></div>)}</article>
      </section>
      <section className="report-findings">
        <div className="report-section-heading"><div><span className="section-label">ACTIONABLE FINDINGS</span><h2>What needs attention</h2></div><span className="count">{report.findings.length}</span></div>
        {report.findings.length === 0 ? <p className="empty-state">No findings were detected in the available data.</p> : report.findings.map((finding) => <article className="report-finding" key={`${finding.code}-${finding.source_url ?? finding.title}`}><span className={`finding-dot ${finding.severity === "critical" || finding.severity === "high" ? "high" : "medium"}`} /><div className="finding-content"><div className="finding-title"><span className="finding-code">{finding.code}</span><h3>{finding.title}</h3><span className={`severity severity-${finding.severity}`}>{finding.severity}</span></div><p>{finding.description}</p><p className="recommendation"><b>Suggested action</b> · {finding.recommendation}</p><details><summary>View evidence</summary><pre>{JSON.stringify(finding.evidence, null, 2)}</pre></details></div>{finding.source_url && <a className="arrow" href={finding.source_url} target="_blank" rel="noreferrer" aria-label="Open source on GitHub">↗</a>}</article>)}
      </section>
      <footer><Link className="brand" href="/"><span className="brand-mark">◉</span> OSS PULSE</Link><span>Analyzed {analyzed}</span><span>Coverage first · Unknown signals stay unknown</span></footer>
    </main>
  );
}
