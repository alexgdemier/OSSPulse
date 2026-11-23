import Link from "next/link";
import { notFound } from "next/navigation";
import { FindingsList } from "../../../components/findings-list";

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

type Insight = Finding & { priority_score: number };

type Report = {
  report_id: string;
  analyzed_at: string;
  engine_version: string;
  health_score: number | null;
  coverage: number;
  classification: string;
  repository: { full_name: string; url: string; description: string | null; language: string | null; stars: number; forks: number };
  dimensions: Record<string, number | null>;
  activity?: {
    commits_last_30_days?: number | null;
    commits_last_90_days?: number | null;
    commits_previous_90_days?: number | null;
    commit_activity_change_percent?: number | null;
    active_commit_authors_last_90_days?: number | null;
    open_issues?: number;
    open_pull_requests?: number;
    stale_pull_requests?: number;
    open_issues_with_no_comments?: number;
  };
  findings: Finding[];
  insights: Insight[];
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
  const payload: unknown = await response.json();
  if (!isReport(payload)) {
    return <main className="shell report-shell"><p className="error-banner">This report has an unsupported or incomplete format. Analyze the repository again to create a current report.</p><Link href="/">← Back to OSS Pulse</Link></main>;
  }
  const report = payload;

  const analyzed = new Date(report.analyzed_at).toLocaleString("en", { dateStyle: "medium", timeStyle: "short", timeZone: "UTC", timeZoneName: "short" });
  return (
    <main className="shell report-shell">
      <nav className="nav"><Link className="brand" href="/"><span className="brand-mark">◉</span> OSS PULSE</Link><div className="nav-links"><Link href="/reports">Reports</Link><Link href="/methodology">Methodology</Link><Link className="back-link" href="/">← Analyze another</Link></div></nav>
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
      <section className="activity-summary" aria-label="Repository activity summary">
        <div className="report-section-heading"><div><span className="section-label">OBSERVED ACTIVITY</span><h2>Recent repository signals</h2></div></div>
        <div className="activity-cards">
          <article><span>Commits · 30 days</span><strong>{report.activity?.commits_last_30_days ?? "—"}</strong></article>
          <article><span>Commits · latest 90 days</span><strong>{report.activity?.commits_last_90_days ?? "—"}</strong></article>
          <article><span>Active commit authors · 90 days</span><strong>{report.activity?.active_commit_authors_last_90_days ?? "—"}</strong></article>
          <article><span>Open issues / pull requests</span><strong>{report.activity?.open_issues ?? "—"} / {report.activity?.open_pull_requests ?? "—"}</strong></article>
        </div>
        {typeof report.activity?.commit_activity_change_percent === "number" && <p className="method-note">Commit volume changed {report.activity.commit_activity_change_percent > 0 ? "+" : ""}{report.activity.commit_activity_change_percent}% compared with the previous 90-day window.</p>}
        {report.activity && typeof report.activity.commits_last_90_days !== "number" && <p className="method-note">Commit totals are unavailable because GitHub pagination was incomplete.</p>}
      </section>
      <section className="report-findings">
        <div className="report-section-heading"><div><span className="section-label">ACTIONABLE FINDINGS</span><h2>What needs attention</h2></div><span className="count">{report.insights.length}</span></div>
        {report.insights.length === 0 ? <p className="empty-state">No findings were detected in the available data.</p> : <FindingsList insights={report.insights} />}
      </section>
      <footer><Link className="brand" href="/"><span className="brand-mark">◉</span> OSS PULSE</Link><span>Analyzed {analyzed}</span><span>Coverage first · Unknown signals stay unknown</span></footer>
    </main>
  );
}

function isReport(value: unknown): value is Report {
  if (!value || typeof value !== "object") return false;
  const report = value as Partial<Report>;
  return typeof report.report_id === "string"
    && typeof report.analyzed_at === "string"
    && typeof report.engine_version === "string"
    && typeof report.classification === "string"
    && typeof report.coverage === "number"
    && Array.isArray(report.findings)
    && Array.isArray(report.insights)
    && Boolean(report.repository && typeof report.repository.full_name === "string")
    && Boolean(report.dimensions && typeof report.dimensions === "object");
}
